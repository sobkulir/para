import logging
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

"""
An exception used for a hacky thread exit.
"""
class ExitThread(Exception):
    pass

"""
Downloads and extracts new games in a separate thread.
"""
class DownloaderThread(QThread):
    jakDoMaminky = pyqtSignal()
    error = pyqtSignal('QString')

    def __init__(self, readOnlyState):
        QThread.__init__(self)
        self.gamesRootDir = readOnlyState.gamesRootDir
        self.gamesAllDir = readOnlyState.gamesAllDir
        self.url = readOnlyState.downloadUrl

    def __del__(self):
        self.wait()

    """
    Returns a relative path to the dowloaded file.
    TODO: Define error behaviour.
    """
    def _download(self, url, gamesRootDir):
        import requests
        import zipfile
        import os
        try: 
            r = requests.get(url, stream=True)
            fsize = int(r.headers['Content-Length'])
            zipPath = os.path.join(gamesRootDir, f'games.zip')
            with open(zipPath, 'wb') as fd:
                logger.info(f'Finished {zipPath} download and extraction.')
                read = 0
                chunkSz = 1024
                for chunk in r.iter_content(chunk_size=chunkSz):
                    fd.write(chunk)
                    read = min(read + chunkSz, fsize)
                    # self.progressClbk(int(100 * read / fsize))
        except Exception as e:
            logger.error(f'Unable to download games: {e}')
            self.error.emit('Funguje ti internet? Nepodarilo sa stiahnuť nové hry :( Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
            raise ExitThread

        return zipPath

    """
    Extracs zipPath to gamesAllDir.
    Returns a directory name of extracted games.
    """
    def _extract(self, zipPath, gamesRootDir, gamesAllDir):
        import shutil
        import os
        import zipfile
        
        gamesNewDir = os.path.join(gamesRootDir, 'new')
        # Clear directory for extracted zip file.
        shutil.rmtree(gamesNewDir, ignore_errors=True)
        try:
            with zipfile.ZipFile(zipPath, 'r') as zipRef:
                zipRef.extractall(gamesNewDir)
        except Exception as e:
            logger.error(f'Unable to extract games: {e}')
            self.error.emit('Extrahovanie zlyhalo, nepodarilo sa stiahnuť nové hry :( Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
            raise ExitThread
        
        return gamesNewDir

    """
    Replaces gamesNewDir with gamesAllDir.
    """
    def _replaceGameDirectory(self, gamesNewDir, gamesAllDir):
        import os
        import shutil

        if os.path.isdir(gamesAllDir):
            try:
                shutil.rmtree(gamesAllDir)
            except Exception as e:
                logger.error(f'Unable to delete current games directory: {e}')
                self.error.emit(f'Nepodarilo sa odstrániť aktuálne hry z "{gamesAllDir}" :( Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
                raise ExitThread

        # Hotofka.
        os.rename(gamesNewDir, gamesAllDir)

    def run(self):
        try:
            logger.info(f'Starting {self.url} download and extraction.')
            zipPath = self._download(self.url, self.gamesRootDir)
            newDir = self._extract(zipPath, self.gamesRootDir, self.gamesAllDir)
            self._replaceGameDirectory(newDir, self.gamesAllDir)
            
            logger.info(f'Finished {self.url} download and extraction.')
            self.jakDoMaminky.emit()
        except ExitThread:
            pass
        except Exception as e:
            logger.error(f'Unknown error while fetching games: {e}')
            self.error.emit(f'Nepodarilo sa aktualizovať hry :( Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
