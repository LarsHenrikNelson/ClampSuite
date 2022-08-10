import sys

from PyQt5.QtWidgets import QApplication
import qdarkstyle

from .gui_main.main_window import MainWindow


def main():
    app = QApplication([])
    dark_stylesheet = qdarkstyle.load_stylesheet()
    app.setStyleSheet(dark_stylesheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
