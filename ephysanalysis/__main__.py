import os
import sys

from PySide6.QtWidgets import QApplication
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette

from .gui_main.main_window import MainWindow


def main():
    os.environ["QT_API"] = "pyside6"
    app = QApplication([])
    dark_stylesheet = qdarkstyle.load_stylesheet(qt_api="pyside6", palette=DarkPalette)
    app.setStyleSheet(dark_stylesheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
