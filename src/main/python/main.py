import json
import logging
import multiprocessing
import os
import runpy
import sys
import uuid
from datetime import datetime
from multiprocessing import Process
from sys import platform
from threading import Thread

import pyglet
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QStatusBar, QMessageBox, QHeaderView,
                             QPushButton, QApplication, QMainWindow, QShortcut)
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from downloader_thread import DownloaderThread

IS_PRODUCTION = True
APP_NAME = 'Para'
APP_VERSION = "0.0.1"

logger = logging.getLogger(__name__)


def logging_setup(base_dir):
    # Log to file in prod
    if IS_PRODUCTION:
        logs_dir = os.path.join(base_dir, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_path = os.path.join(logs_dir, 'logs.txt')
        logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class State:
    def __init__(self):
        self._set_base_dir()
        self.download_url = 'https://people.ksp.sk/~faiface/osp_games/all.zip'
        self.hidden_staging_url = 'https://people.ksp.sk/~faiface/osp_games/stag.zip'
        self.games = []
        self.games_root_dir = os.path.join(self.base_dir, 'games')
        self.games_all_dir = os.path.join(self.games_root_dir, 'all')
        try:
            if not os.path.exists(self.games_all_dir):
                os.makedirs(self.games_all_dir)
        except Exception as e:
            msg = f'Creation of the directory {os.path.abspath(self.games_all_dir)} failed: {e}'
            logger.critical(msg)
            # State is initialized before all the Qt machinery starts, therefore quit() is used. 
            print(msg)
            quit()

    def _set_base_dir(self):
        self.base_dir = ''
        if platform == "win32":
            self.base_dir = os.path.join(os.getenv('APPDATA'), APP_NAME)
        else:
            # Directory of the executed script
            # SO: https://stackoverflow.com/questions/4934806/how-can-i-find-scripts-directory-with-python

            # ~/.para/
            self.base_dir = os.path.join(os.expanduser("~"), '.para')

    def update_game_data(self):
        if not os.path.isdir(self.games_all_dir):
            self.games = []
            return

        game_dirs = []
        try:
            game_dirs = [f.path for f in os.scandir(self.games_all_dir) if f.is_dir()]
        except IOError:
            # We just log it and continue, it is not fatal, although suspicious.
            logger.debug(f'The directory with games does not exist {os.path.abspath(self.games_all_dir)}.')

        self.games = []
        for game_dir in game_dirs:
            metafile_name = os.path.join(game_dir, 'para_info.txt')
            try:
                with open(metafile_name, 'r') as metafile:
                    game_info = json.load(metafile)
                    game_info['path'] = game_dir
                    self.games.append(game_info)
            except IOError as exc:
                logger.error(f'A para_info.txt for {game_dir} is corrupted or missing: {exc}')
                raise

        self.games.sort(key=lambda game: game['releaseDate'], reverse=True)


class MainWindow(QMainWindow):
    def __init__(self, state, parent=None):
        super(MainWindow, self).__init__(parent)
        self.state = state
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setGeometry(600, 400, 600, 400)
        self._init_table()
        self._init_button()
        self.update_table_safe()

        def on_server_change():
            self.state.downloadUrl = self.state.hiddenStagingUrl
            self.msg_dialog(QMessageBox.Information, 'Server zmenený', self.state.downloadUrl)

        # Backdoor
        self.changeServer = QShortcut(QKeySequence('Ctrl+U'), self)
        self.changeServer.activated.connect(on_server_change)

        main_widget = QWidget(self)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)

        v_box_layout = QVBoxLayout(main_widget)
        v_box_layout.addWidget(self.updateBtn)
        v_box_layout.addWidget(self.tbl)
        main_widget.setLayout(v_box_layout)
        self.set_status("I'm the Status Bar")
        self.show()

    def set_status(self, msg):
        status = QStatusBar()
        status.showMessage(msg)
        self.setStatusBar(status)

    def _init_button(self):
        self.updateBtn = QPushButton('Aktualizuj hry')
        self.updateBtn.setToolTip('Stiahnuť najnovšie hry')
        self.updateBtn.resize(self.updateBtn.sizeHint())
        self.updateBtn.clicked.connect(self.download_games)

    def _init_table(self):
        header_labels = ['Názov', 'Autor', 'Dátum vzniku', 'Spusti']
        self.tbl = QTableWidget(0, len(header_labels))
        self.tbl.setHorizontalHeaderLabels(header_labels)
        header = self.tbl.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def msg_dialog(self, icon, txt, msg):
        dialog = QMessageBox()
        dialog.setIcon(icon)
        dialog.setText(txt)
        dialog.setInformativeText(msg)
        dialog.setWindowTitle('PARAnormal activity!')
        dialog.exec_()

    def download_games(self):
        def before_download():
            self.tbl.clearContents()
            self.tbl.setRowCount(0)
            self.updateBtn.setEnabled(False)

        def after_download():
            self.updateBtn.setEnabled(True)

        downloader_thread = DownloaderThread(self.state)
        before_download()
        downloader_thread.start()
        downloader_thread.hotofka.connect(self.update_table_safe)
        downloader_thread.finished.connect(after_download)
        downloader_thread.error.connect(lambda msg: self.msg_dialog(QMessageBox.Critical, 'Nastala chyba...', msg))
        downloader_thread.progress.connect(lambda msg: self.set_status(msg))

    def update_table_safe(self):
        try:
            self.update_table()
        except Exception as e:
            logger.info(f'Unable to update table: {e}')
            self.msg_dialog(QMessageBox.Critical, 'Nepodarilo sa načítať hry zo súboru.',
                            'Skús stiahnúť najnovšiu verziu hier - "Aktualizovať hry". '
                            'Ak chyba pretrváva, kontaktuj prosím sobkulir na Discorde alebo r.sobkuliak@gmail.com')

    def update_table(self):
        self.state.update_game_data()
        games = self.state.games
        self.tbl.setRowCount(len(games))
        for i, game in enumerate(games):
            play_button = QPushButton(self.tbl)
            play_button.setText('Hraj')

            def handler(game_dir):
                return lambda: self.start_game_process(game_dir)
            play_button.clicked.connect(handler(game))

            self.tbl.setItem(i, 0, QTableWidgetItem(game["name"]))
            self.tbl.setItem(i, 1, QTableWidgetItem(game["author"]))
            release_date = datetime.strptime(game["releaseDate"], '%Y-%m-%d %H:%M')
            self.tbl.setItem(i, 2, QTableWidgetItem(release_date.strftime('%Y-%m-%d')))
            self.tbl.setCellWidget(i, 3, play_button)

        self.tbl.resizeColumnsToContents()

    @staticmethod
    def start_game_process(game):
        logger.info(f'Starting game: {game["path"]}')
        p = Process(target=start_game_thread, args=(game['path'],))
        p.daemon = True
        p.start()


def start_game(game_dir):
    try:
        os.chdir(os.path.abspath(game_dir))
        sys.path.append(os.getcwd())

        # Pyglet does look in __main__ dir, not cwd. Therefore
        # explicit path specification is need.
        pyglet.resource.path = [os.getcwd()]
        runpy.run_path(os.path.join(game_dir, 'game.py'), run_name='__main__')
    except Exception as e:
        f_path = os.path.join(game_dir, f'crash_report_{uuid.uuid4()}.txt')
        logging.basicConfig(filename=f_path, filemode='a', format='%(asctime)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
        logger.critical(f'Game crashed: {e}')
        # Print more info (stacktrace)
        import traceback
        logger.critical(traceback.format_exc())
        raise


# Because of Windows sharing window of forked process (or something like that)
# we need to spawn a new thread.
def start_game_thread(game_dir):
    thread = Thread(target=start_game, args=(game_dir,))
    thread.start()
    thread.join()


if __name__ == '__main__':
    app_ctx = ApplicationContext()  # 1. Instantiate ApplicationContext    import sys

    # Fix for spawning multiple windows after freeze: https://github.com/mherrmann/fbs/issues/87

    multiprocessing.freeze_support()

    state = State()
    logging_setup(state.base_dir)
    app = QApplication(sys.argv)
    w = MainWindow(state)
    exit_code = app_ctx.app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
