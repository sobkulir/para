import logging
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QStatusBar, QMessageBox,
    QPushButton, QApplication, QMainWindow)

IS_PRODUCTION = False
APP_NAME = 'Para'
APP_VERSION = "1.0.0"

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
        self.downloadUrl = 'https://raw.github.com/sobkulir/test/master/hry.zip'
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
            self.baseDir = os.path.dirname(os.path.realpath(__file__))

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
                logger.error(f'A para_info.txt for {self.gameDir} is corrupted or missing: {exc}')
                # TODO: Ukaz nieco uzivatelovi
                print(f'Nemôžem otvoriť súbor {metafileName}. Existuje?')

class MainWindow(QMainWindow):
    def __init__(self, state, parent=None):
        super(MainWindow, self).__init__(parent)
        self.state = state
        self.setGeometry(870, 20, 400, 400)
        self._initTable()
        self._initButton()
        self.updateTable()

        main_widget = QWidget(self)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)

        vBoxLayout = QVBoxLayout(main_widget)
        vBoxLayout.addWidget(self.updateBtn)
        vBoxLayout.addWidget(self.tbl)
        main_widget.setLayout(vBoxLayout)
        status = QStatusBar()
        status.showMessage("I'm the Status Bar")
        self.setStatusBar(status)
        self.show()

    def _initButton(self):
        self.updateBtn = QPushButton('Aktualizuj hry')
        self.updateBtn.setToolTip('Stiahnuť najnovšie hry')
        self.updateBtn.resize(self.updateBtn.sizeHint())
        self.updateBtn.clicked.connect(self.downloadGames)

    def _initTable(self):        
        header_labels = ['Názov', 'Autor', 'Dátum vzniku', 'Spusti']
        self.tbl = QTableWidget(0,len(header_labels))
        self.tbl.setHorizontalHeaderLabels(header_labels)

    def errorDialog(self, msg):
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText('Nastala chyba...')
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
        self.downloaderThread.error.connect(lambda msg: self.errorDialog(msg))

    def updateTable(self):
        self.state.updateGameData()
        games = self.state.games
        self.tbl.setRowCount(len(games))

        for i, game in enumerate(games):
            updateBtn = QPushButton(self.tbl)
            updateBtn.setText('Hraj')
            updateBtn.clicked.connect(lambda: self.startGame(game))
            self.tbl.setItem(i,0,QTableWidgetItem(game["name"]))
            self.tbl.setItem(i,1,QTableWidgetItem(game["author"]))
            self.tbl.setItem(i,2,QTableWidgetItem(game["releaseDate"]))
            self.tbl.setCellWidget(i, 3, updateBtn)

    def startGame(self, game):
        import subprocess
        import sys
        import os

        # Hacks used:
        # https://stackoverflow.com/questions/12332975/installing-python-module-within-code
        # https://stackoverflow.com/questions/14050281/how-to-check-if-a-python-module-exists-without-importing-it
        try:
            import pyglet
        except:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyglet"])

        subprocess.Popen([sys.executable, os.path.join(game['path'], 'main.py')])

if __name__ == '__main__':
    import sys
    state = State()
    loggingSetup(state.baseDir)
    app = QApplication(sys.argv)
    w = MainWindow(state)
    sys.exit(app.exec_())
