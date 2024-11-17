import logging
from pathlib import Path, PurePath

from PySide6.QtWidgets import (
    QTabWidget,
    QWidget,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Slot, Qt, Signal

from .qtwidgets import QExpManager


logger = logging.getLogger(__name__)


class MainAnalysisWidget(QWidget):
    acq = Signal(int)
    error = Signal(str)
    clicked = Signal(bool)
    file = Signal(str)
    file_path = Signal(Path)
    dir_path = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAcceptDrops(True)

        self.setStyleSheet(
            """QTabWidget::tab-bar
                                          {alignment: left;}"""
        )

        self.parent_layout = QVBoxLayout()
        self.main_layout = QHBoxLayout()
        self.parent_layout.addLayout(self.main_layout)
        self.setLayout(self.parent_layout)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.parent_layout.addWidget(self.pbar)

        self.tab1 = QWidget()
        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setViewportMargins(10, 10, 10, 10)
        self.tab1_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1_scroll.setWidget(self.tab1)
        self.tabs.addTab(self.tab1_scroll, "Setup")

        self.tab2 = QWidget()
        self.tab2_scroll = QScrollArea()
        self.tab2_scroll.setViewportMargins(10, 10, 10, 10)
        self.tab2_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab2_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab2_scroll.setWidgetResizable(True)
        self.tab2_scroll.setWidget(self.tab2)
        self.tabs.addTab(self.tab2_scroll, "Analysis")

        self.tab3 = QWidget()
        self.tab3_scroll = QScrollArea()
        self.tab3_scroll.setViewportMargins(10, 10, 10, 10)
        self.tab3_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab3_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab3_scroll.setWidgetResizable(True)
        self.tab3_scroll.setWidget(self.tab3)
        self.tabs.addTab(self.tab3_scroll, "Final data")

        self.exp_manager = QExpManager()
        self.exp_manager.set_callback(self.updateProgress)

        self.dlg = QMessageBox(self)

    def dragEnterEvent(self, e):
        """
        This function will detect the drag enter event from the mouse on the
        main window
        """
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        """
        This function will detect the drag move event on the main window
        """
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    @Slot(object)
    def dropEvent(self, e):
        """
        This function will enable the drop file directly on to the
        main window. The file location will be stored in the self.filename
        """
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            url = e.mimeData().urls()[0]
            fname = PurePath(str(url.toLocalFile()))
            if fname.suffix == ".yaml":
                self.file.emit(fname)
            elif Path(fname).is_dir():
                self.file_path.emit(Path(fname))
            else:
                e.ignore()
        else:
            e.ignore()

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def createPrefDict(self):
        logger.info("Creating preferences dictionary.")
        pref_dict = {}
        for i in self._analysis_widgets.values():
            pref_dict[i.objectName()] = i.getAnalysisSettings()
        logger.info(f"{self.widget_name} preferences dictionary created.")
        return pref_dict

    def setPreferences(self, pref_dict: dict[str, dict[str, int | float | str]]):
        logger.info(f"Setting {self.widget_name} preferences.")

        for key, values in pref_dict.items():
            self._analysis_widgets[key].setAnalysisSettings(values)
            logger.info(f"Preferences set for {key} widget.")
        self.pbar.setFormat("Preferences set")

    def loadPreferences(self, file_name: str | PurePath):
        self.need_to_save = True
        load_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(load_dict)

    def savePreferences(self, fle_path: str | PurePath):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(fle_path, pref_dict)
        else:
            pass

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setFormat(f"Acquisition {value} analyzed")
            # self.pbar.setFormat(f"{value}")
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def setWorkingDirectory(self, path):
        self.dir_path.emit(path)

    def needToSave(self):
        return self.exp_manager.need_to_save

    def errorDialog(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        self.dlg.exec()

    def analyze(self):
        raise (NotImplementedError)
