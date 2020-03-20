import sys

from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QStatusBar,
    QPushButton, QApplication, QMainWindow)

DEBUG = True
APP_NAME = 'para'

def printdb(*args):
    if DEBUG:
        print(args)

class State:
    def __init__(self):
        import os
        from sys import platform

        self.downloadUrl = 'https://raw.github.com/sobkulir/test/master/hry.zip'
        self.games = []
        baseDir = ''
        if platform == "win32":
            baseDir = os.path.join(os.getenv('APPDATA'), APP_NAME)
        else:
            # Directory of the executed script
            # SO: https://stackoverflow.com/questions/4934806/how-can-i-find-scripts-directory-with-python
            baseDir = os.path.dirname(os.path.realpath(__file__))
        
        self.gamesRootDir = os.path.join(baseDir, 'games')
        self.gamesAllDir = os.path.join(self.gamesRootDir, 'all')
        try:
            if not os.path.isdir(self.gamesAllDir):
                os.makedirs(self.gamesAllDir)
        except OSError:
            printdb(f'Creation of the directory {self.gamesAllDir} failed')
            # TODO: Report uzivatelovi!

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
            printdb(exc)
            # TODO: Error: Checkli sme priecinok, ale aj ak neexistuje, treba reportnut

        self.games = []
        for gameDir in gameDirs:
            metafileName = os.path.join(gameDir, 'para_info.txt')
            try:
                with open(metafileName, 'r') as metafile: 
                    gameInfo = json.load(metafile)
                    gameInfo['path'] = gameDir
                    self.games.append(gameInfo)
            except IOError as exc:
                printdb(exc)
                # TODO: Ukaz nieco uzivatelovi
                print(f'Nemôžem otvoriť súbor {metafileName}. Existuje?')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setGeometry(870, 20, 400, 400)
        self.state = State()
        self._initTable()
        self._initButton()
        self.updateTable()

        main_widget = QWidget(self)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)

        vBoxLayout = QVBoxLayout(main_widget)
        vBoxLayout.addWidget(self.btn)
        vBoxLayout.addWidget(self.tbl)
        main_widget.setLayout(vBoxLayout)
        status = QStatusBar()
        status.showMessage("I'm the Status Bar")
        self.setStatusBar(status)
        self.show()

    def _initButton(self):
        label = 'Aktualizuj hry'
        self.btn = QPushButton(label)
        self.btn.setToolTip('Stiahnuť najnovšie verzie hier.')
        self.btn.resize(self.btn.sizeHint())
        setLabel = lambda prog: self.btn.setText(f'{label} ({prog}%)')
        self.btn.clicked.connect(self.downloadGames)

    def _initTable(self):        
        header_labels = ['Názov', 'Autor', 'Dátum vzniku', 'Spusti']
        self.tbl = QTableWidget(0,len(header_labels))
        self.tbl.setHorizontalHeaderLabels(header_labels)

    def downloadGames(self):
        import DownloaderThread
        self.downloaderThread = DownloaderThread.DownloaderThread(self.state)
        self.downloaderThread.start()
        printdb('spusteny thread')

    def updateTable(self):
        self.state.updateGameData()
        self.tbl.clearContents()
        self.tbl.setRowCount(0)

        games = self.state.games
        self.tbl.setRowCount(len(games))

        for i, game in enumerate(games):
            btn = QPushButton(self.tbl)
            btn.setText('Hraj')
            btn.clicked.connect(lambda: self.startGame(game))
            self.tbl.setItem(i,0,QTableWidgetItem(game["name"]))
            self.tbl.setItem(i,1,QTableWidgetItem(game["author"]))
            self.tbl.setItem(i,2,QTableWidgetItem(game["releaseDate"]))
            self.tbl.setCellWidget(i, 3, btn)

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
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())