from PyQt5.QtCore import QThread

"""
Downloads and extracts new games in a separate thread.
"""
class DownloaderThread(QThread):
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
                read = 0
                chunkSz = 1024
                for chunk in r.iter_content(chunk_size=chunkSz):
                    fd.write(chunk)
                    read = min(read + chunkSz, fsize)
                    # self.progressClbk(int(100 * read / fsize))
        except Exception as exc:
            printdb(exc)
            # TODO: Ukaz nieco uzivatelovi
            print('Funguje ti internet?')
        
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
        except Exception as exc:
            printdb(f'In extract: {exc}')
            # TODO: Ukaz nieco uzivatelovi
        
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
            except:
                printdb(f'Cannot remove current games directory.')
                # TODO: Toto treba rozumne oznamit uzivatelovi.

        # Hotofka.
        os.rename(gamesNewDir, gamesAllDir)

    def run(self):
        zipPath = self._download(self.url, self.gamesRootDir)
        newDir = self._extract(zipPath, self.gamesRootDir, self.gamesAllDir)
        self._replaceGameDirectory(newDir, self.gamesAllDir)

        #self.emit(SIGNAL('add_post(QString)'), top_post)
