import logging
import sys
from pathlib import PurePath

import pyqtgraph as pg

# from PySide6 import QtCore
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from .functions.startup import check_dir
from .gui_main.main_window import MainWindow
from .gui_widgets.palettes import DarkPalette


def main(logger):
    # if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    #     QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    #     QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication([])

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption("foreground", "#FCFCFC")

    wdir = PurePath(__file__).parent
    logo_path = str(wdir / "logo/d_logo.png")
    pic = QPixmap(logo_path)
    splash = QSplashScreen(pic)
    splash.show()
    app.setStyle("Fusion")
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    app.setPalette(DarkPalette())
    app.setWindowIcon(QIcon(pic))
    window = MainWindow()
    window.setWindowTitle("ClampSuite")
    window.setProgramDirectory()
    window.loadPresets()
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
