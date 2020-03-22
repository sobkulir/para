import logging
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QStatusBar, QMessageBox, QHeaderView,
    QPushButton, QApplication, QMainWindow, QShortcut)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QProcess

IS_PRODUCTION = True
APP_NAME = 'Para'
APP_VERSION = "0.0.1"

logger = logging.getLogger(__name__)

def loggingSetup(baseDir):
    # Log to file in prod
    if IS_PRODUCTION:
        import os
        from datetime import datetime
        from utils import ensureDirExist
        logsDir = os.path.join(baseDir, 'logs')
        ensureDirExist(logsDir)
        fname = os.path.join(logsDir, datetime.now().strftime('para_%H_%M_%d_%m_%Y.log'))
        logging.basicConfig(filename=fname, filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    
class State:
    def __init__(self):
        import os

        self._setBaseDir()
        self.downloadUrl = 'https://people.ksp.sk/~faiface/osp_games/all.zip'
        self.hiddenStagingUrl = 'https://people.ksp.sk/~faiface/osp_games/stag.zip'
        self.games = []        
        self.gamesRootDir = os.path.join(self.baseDir, 'games')
        self.gamesAllDir = os.path.join(self.gamesRootDir, 'all')
        try:
            from utils import ensureDirExist
            ensureDirExist(self.gamesAllDir)
        except Exception as e:
            msg = f'Creation of the directory {os.path.abspath(self.gamesAllDir)} failed: {e}'
            logger.critical(msg)
            # State is initialized before all the Qt machinery starts, therefore quit() is used. 
            print(msg)
            quit()

    def _setBaseDir(self):
        import os
        from sys import platform

        self.baseDir = ''
        if platform == "win32":
            self.baseDir = os.path.join(os.getenv('APPDATA'), APP_NAME)
        else:
            # Directory of the executed script
            # SO: https://stackoverflow.com/questions/4934806/how-can-i-find-scripts-directory-with-python
            from os.path import expanduser
            # ~/.para/
            self.baseDir = os.path.join(expanduser("~"), '.para')

    def updateGameData(self):
        import json
        import os
        
        if not os.path.isdir(self.gamesAllDir):
            self.games = []
            return

        gameDirs = []
        try:
            gameDirs = [f.path for f in os.scandir(self.gamesAllDir) if f.is_dir()]
        except IOError as exc:
            # We just log it and continue, it is not fatal, altough suspicious.
            logger.debug(f'The directory with games does not exist {os.path.abspath(self.gamesAllDir)}.')

        self.games = []
        for gameDir in gameDirs:
            metafileName = os.path.join(gameDir, 'para_info.txt')
            try:
                with open(metafileName, 'r') as metafile: 
                    gameInfo = json.load(metafile)
                    gameInfo['path'] = gameDir
                    self.games.append(gameInfo)
            except IOError as exc:
                logger.error(f'A para_info.txt for {gameDir} is corrupted or missing: {exc}')
                # The user doesn't have to know everything...

        self.games.sort(key=lambda game: game['releaseDate'], reverse=True)

class MainWindow(QMainWindow):
    def __init__(self, state, parent=None):
        super(MainWindow, self).__init__(parent)
        self.state = state
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setGeometry(600, 400, 600, 400)
        self._initTable()
        self._initButton()
        self.updateTable()

        def onServerChange():
            self.state.downloadUrl = self.state.hiddenStagingUrl
            self.msgDialog(QMessageBox.Information, 'Server zmenený', self.state.downloadUrl)
        
        # Backdoor
        self.changeServer = QShortcut(QKeySequence('Ctrl+U'), self)
        self.changeServer.activated.connect(onServerChange)

        main_widget = QWidget(self)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)

        vBoxLayout = QVBoxLayout(main_widget)
        vBoxLayout.addWidget(self.updateBtn)
        vBoxLayout.addWidget(self.tbl)
        main_widget.setLayout(vBoxLayout)
        self.setStatus("I'm the Status Bar")
        self.show()

    def setStatus(self, msg):
        status = QStatusBar()
        status.showMessage(msg)
        self.setStatusBar(status)

    def _initButton(self):
        self.updateBtn = QPushButton('Aktualizuj hry')
        self.updateBtn.setToolTip('Stiahnuť najnovšie hry')
        self.updateBtn.resize(self.updateBtn.sizeHint())
        self.updateBtn.clicked.connect(self.downloadGames)

    def _initTable(self):        
        header_labels = ['Názov', 'Autor', 'Dátum vzniku', 'Spusti']
        self.tbl = QTableWidget(0,len(header_labels))
        self.tbl.setHorizontalHeaderLabels(header_labels)
        header = self.tbl.horizontalHeader()       
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def msgDialog(self, icon, txt, msg):
        dialog = QMessageBox()
        dialog.setIcon(icon)
        dialog.setText(txt)
        dialog.setInformativeText(msg)
        dialog.setWindowTitle('PARAnormal activity!')
        dialog.exec_()

    def downloadGames(self):
        def beforeDownload():
            self.tbl.clearContents()
            self.tbl.setRowCount(0)
            self.updateBtn.setEnabled(False)
        
        def afterDownload():
            self.updateBtn.setEnabled(True)

        import DownloaderThread
        self.downloaderThread = DownloaderThread.DownloaderThread(self.state)
        beforeDownload()
        self.downloaderThread.start()
        self.downloaderThread.jakDoMaminky.connect(self.updateTable)
        self.downloaderThread.finished.connect(afterDownload)
        self.downloaderThread.error.connect(lambda msg: self.msgDialog(QMessageBox.Critical, 'Nastala chyba...', msg))
        self.downloaderThread.progress.connect(lambda msg: self.setStatus(msg))

    def updateTable(self):
        import datetime
        self.state.updateGameData()
        games = self.state.games
        self.tbl.setRowCount(len(games))
        self.tableButtons = []

        for i, game in enumerate(games):
            updateBtn = QPushButton(self.tbl)
            updateBtn.setText('Hraj')
            def onClick(game):
                return lambda: self.startGameProcess(game)
            updateBtn.clicked.connect(onClick(game))
            self.tableButtons.append(updateBtn)
            self.tbl.setItem(i,0,QTableWidgetItem(game["name"]))
            self.tbl.setItem(i,1,QTableWidgetItem(game["author"]))
            releaseDate = datetime.datetime.strptime(game["releaseDate"], '%Y-%m-%d %H:%M')
            self.tbl.setItem(i,2,QTableWidgetItem(releaseDate.strftime('%Y-%m-%d')))
            self.tbl.setCellWidget(i, 3, updateBtn)
        
        self.tbl.resizeColumnsToContents()

    def startGameProcess(self, game):
        logger.info(f'Starting game: {game["path"]}')
        from multiprocessing import Process, Queue
        p = Process(target=startGameThread, args=(game['path'],))
        p.daemon = True
        p.start()

def startGame(gameDir):
    import os
    import sys
    os.chdir(os.path.abspath(gameDir))
    sys.path.append(os.getcwd())
    import pyglet
    # Pyglet does look in __main__ dir, not cwd. Therefore
    # explicit path specifitaction is need.
    pyglet.resource.path = [os.getcwd()]

    # And Run!
    import runpy
    runpy.run_path(os.path.join(gameDir, 'game.py'))

# Because of Windows sharing window of forked process (or something like that)
# we need to spawn a new thread.
def startGameThread(gameDir):
    from threading import Thread
    thread = Thread(target = startGame, args=(gameDir, ))
    thread.start()
    thread.join()


if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext    import sys
    
    # Fix for spawning multiple windows after freeze: https://github.com/mherrmann/fbs/issues/87
    import multiprocessing
    multiprocessing.freeze_support()

    import sys
    state = State()
    loggingSetup(state.baseDir)
    app = QApplication(sys.argv)
    w = MainWindow(state)
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
