import logging
import os
import shutil
import zipfile

import requests
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ExitThread(Exception):
    """
    An exception used for a hacky thread exit.
    """
    pass


class DownloaderThread(QThread):
    """
    Downloads and extracts new games in a separate thread.
    """
    hotofka = pyqtSignal()
    error = pyqtSignal('QString')
    progress = pyqtSignal('QString')

    def __init__(self, read_only_state):
        QThread.__init__(self)
        self.games_root_dir = read_only_state.games_root_dir
        self.games_all_dir = read_only_state.games_all_dir
        self.url = read_only_state.download_url

    def __del__(self):
        self.wait()

    def _download(self, url, games_root_dir):
        """
        Returns a relative path to the dowloaded file.
        TODO: Define error behaviour.
        """
        try:
            self.progress.emit(f'Sťahovanie (hľadám páru)')
            r = requests.get(url, stream=True)
            fsize = int(r.headers['Content-Length'])
            zip_path = os.path.join(games_root_dir, f'games.zip')
            with open(zip_path, 'wb') as fd:
                logger.info(f'Finished {zip_path} download and extraction.')
                read = 0
                chunk_size = 128 * 1024
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)
                    read = min(read + chunk_size, fsize)
                    self.progress.emit(f'Sťahovanie {int(100 * read / fsize)}%')
        except Exception as e:
            logger.error(f'Unable to download games: {e}')
            self.error.emit('Funguje ti internet? Nepodarilo sa stiahnuť nové hry :( '
                            'Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
            raise ExitThread

        return zip_path

    def _extract(self, zip_path, games_root_dir):
        """
        Extracs zipPath to gamesAllDir.
        Returns a directory name of extracted games.
        """
        self.progress.emit(f'Extrahovanie (nenaimplementoval som progres)')
        games_new_dir = os.path.join(games_root_dir, 'new')
        # Clear directory for extracted zip file.
        shutil.rmtree(games_new_dir, ignore_errors=True)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipRef:
                zipRef.extractall(games_new_dir)
        except Exception as e:
            logger.error(f'Unable to extract games: {e}')
            self.error.emit('Extrahovanie zlyhalo, nepodarilo sa stiahnuť nové hry :( '
                            'Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
            raise ExitThread

        return games_new_dir

    def _replace_game_directory(self, games_new_dir, games_all_dir):
        """
        Replaces gamesNewDir with gamesAllDir.
        """

        self.progress.emit(f'Výmena zložiek')
        if os.path.isdir(games_all_dir):
            try:
                shutil.rmtree(games_all_dir)
            except Exception as e:
                logger.error(f'Unable to delete current games directory: {e}')
                self.error.emit(f'Nepodarilo sa odstrániť aktuálne hry z "{games_all_dir}" :( '
                                f'Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
                raise ExitThread

        # Hotofka.
        os.rename(games_new_dir, games_all_dir)

    def run(self):
        try:
            logger.info(f'Starting {self.url} download and extraction.')
            zip_path = self._download(self.url, self.games_root_dir)
            new_dir = self._extract(zip_path, self.games_root_dir)
            self._replace_game_directory(new_dir, self.games_all_dir)
            self.hotofka.emit()
            logger.info(f'Finished {self.url} download and extraction.')
        except ExitThread:
            pass
        except Exception as e:
            logger.error(f'Unknown error while fetching games: {e}')
            self.error.emit(f'Nepodarilo sa aktualizovať hry :( '
                            f'Napíš mi na Discorde (sobkulir) alebo na email r.sobkuliak@gmail.com.')
