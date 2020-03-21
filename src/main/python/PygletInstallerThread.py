import logging
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

"""
Installs Pyglet :)
"""
class PygletInstallerThread(QThread):
    jakDoMaminky = pyqtSignal()
    error = pyqtSignal('QString')

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            import subprocess
            import sys
            # Hacks used:
            # https://stackoverflow.com/questions/12332975/installing-python-module-within-code
            # https://stackoverflow.com/questions/14050281/how-to-check-if-a-python-module-exists-without-importing-it
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-input", "pyglet"])
            self.jakDoMaminky.emit()
        except Exception as e:
            logger.error(f'Installing pyglet failed: {e}')
            self.error.emit(f'Nepodarilo sa nainštalovať pyglet. Skús to manuálne (pip install pyglet). Ak sa ti to nepodarí, napíš mi na Discorde (sobkulir) aleob na r.sobkuliak@gmail.com.')
