import logging

import sys
from pathlib import Path, PurePath

import pyqtgraph as pg

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QSplashScreen

from .gui_main.main_window import MainWindow
from .gui_widgets.palettes import DarkPalette


def check_dir():
    p = Path.home()
    h = ".clampsuite"
    prog_dir = Path(p / h)
    if not prog_dir.exists():
        prog_dir.mkdir()
    return prog_dir


def main(logger):
    if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication([])

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption("foreground", "#C9CDD0")

    wdir = PurePath(__file__).parent
    logo_path = str(wdir / "logo/d_logo.png")
    pic = QPixmap(logo_path)
    splash = QSplashScreen(pic)
    splash.show()

    app.setStyle("Fusion")
    app.setPalette(DarkPalette())
    app.setWindowIcon(QIcon(pic))
    window = MainWindow()
    window.setWindowTitle("ClampSuite")
    window.show()
    splash.finish(window)
    app.aboutToQuit.connect(lambda: logger.info("Closing ClampSuite"))
    sys.exit(app.exec())


if __name__ == "__main__":
    logger = logging.getLogger("clampsuite")
    logger.setLevel(logging.INFO)
    prog_dir = check_dir()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    fh = logging.FileHandler(prog_dir / "clampsuite_log.log", mode="w")
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.info("Starting ClampSuite")

    main(logger)
