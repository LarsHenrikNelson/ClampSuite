import logging
import sys

import pyqtgraph as pg

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, QTimer
from PySide6.QtWidgets import QApplication, QSplashScreen

from .functions.startup import check_dir
from .gui_main.main_window import MainWindow
from .gui_widgets.palettes import DarkPalette

from . import resources  # noqa: F401

try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "mycompany.myproduct.subproduct.version"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


def main(logger):
    # if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    #     QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    #     QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication([])

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption("foreground", "#FCFCFC")

    icon = QIcon(":/icons/logo-favicon.ico")
    pic = QPixmap(icon.pixmap(QSize(512, 512)))
    splash = QSplashScreen(pic)
    splash.show()
    timer = QTimer()
    timer.singleShot(5000, lambda x: x)
    app.setStyle("Fusion")
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    app.setPalette(DarkPalette())
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowTitle("ClampSuite")
    window.setProgramDirectory()
    window.loadPresets()
    splash.finish(window)
    window.show()
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
