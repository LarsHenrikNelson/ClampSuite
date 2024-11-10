import logging
from pathlib import Path, PurePath

from PySide6.QtWidgets import QTabWidget, QProgressBar
from PySide6.QtCore import Slot, Qt

from .qtwidgets import WorkerSignals


logger = logging.getLogger(__name__)


class MainAnalysisWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.signals = WorkerSignals()

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)

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
                self.signals.file.emit(fname)
            elif Path(fname).is_dir():
                self.signals.file_path.emit(Path(fname))
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

        logger.info("Preferences set.")
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
        self.signals.dir_path.emit(path)

    def needToSave(self):
        return self.exp_manager.need_to_save
