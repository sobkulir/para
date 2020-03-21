import logging
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QStatusBar, QMessageBox, QHeaderView,
    QPushButton, QApplication, QMainWindow, QShortcut)
from PyQt5.QtGui import QIcon, QKeySequence

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
        self.downloadUrl = 'https://people.ksp.sk/~faiface/osp/hry.zip'
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
                # The user doesn't have to know everything...

class MainWindow(QMainWindow):
    def __init__(self, state, parent=None):
        super(MainWindow, self).__init__(parent)
        self.state = state
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setWindowIcon(QIcon('icon.png'))
        self.setGeometry(600, 400, 600, 400)
        self._initTable()
        self._initButton()
        self.updateTable()

        def onServerChange():
            self.state.downloadUrl = 'https://people.ksp.sk/~faiface/osp/stag.zip'
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
        self.state.updateGameData()
        games = self.state.games
        self.tbl.setRowCount(len(games))
        self.tableButtons = []

        for i, game in enumerate(games):
            updateBtn = QPushButton(self.tbl)
            updateBtn.setText('Hraj')
            updateBtn.clicked.connect(lambda: self.preStartGame(game))
            self.tableButtons.append(updateBtn)
            self.tbl.setItem(i,0,QTableWidgetItem(game["name"]))
            self.tbl.setItem(i,1,QTableWidgetItem(game["author"]))
            self.tbl.setItem(i,2,QTableWidgetItem(game["releaseDate"]))
            self.tbl.setCellWidget(i, 3, updateBtn)
        
        self.tbl.resizeColumnsToContents()

    def installPyglet(self, game):
        def beforeInstallation():
            self.updateBtn.setEnabled(False)
            for btn in self.tableButtons:
                btn.setEnabled(False)

        def afterInstallation():
            self.updateBtn.setEnabled(True)
            for btn in self.tableButtons:
                btn.setEnabled(True)

        from PygletInstallerThread import PygletInstallerThread
        self.installerThread = PygletInstallerThread()
        beforeInstallation()
        self.installerThread.start()
        self.installerThread.finished.connect(afterInstallation)
        self.installerThread.error.connect(lambda msg: self.msgDialog(QMessageBox.Critical, msg))
        self.installerThread.jakDoMaminky.connect(lambda: self.startGame(game))
        self.msgDialog(QMessageBox.Information, 'Inštaluje sa pyglet :)',
'''
Všetko je tak ako má byť, nenastala chyba. Inštaluje sa balíček pyglet, ktorý je potrebný k easygame. Nestihol som sem \
doprogramovať progress bar, takže ako náhradu ti sem dám pár básničiek (FB: Špatné básně):
Báseň o sprše a gravitaci
-------------------
Když si dávám sprchu,
voda na mě teče
svrchu.

Báseň o rozdělávání ohně v ráji
-------------------
Dones dřevo,
Evo.

Normální lidská existence vol. 2
-------------------
Moje tři neteře
mají v součtu
tři páteře.
Zdravý holky to jsou.
''')

    def preStartGame(self, game):
        try:
            import pyglet
            self.startGame(game)
        except:
            self.installPyglet(game)

    def startGame(self, game):
        import subprocess
        import sys 
        import os
        subprocess.Popen([sys.executable, os.path.join(game['path'], 'main.py')])

if __name__ == '__main__':
    import sys
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext    import sys
    state = State()
    loggingSetup(state.baseDir)
    app = QApplication(sys.argv)
    w = MainWindow(state)
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(app.exec_())
