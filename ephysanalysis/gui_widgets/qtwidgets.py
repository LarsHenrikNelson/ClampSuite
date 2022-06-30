from copy import deepcopy
from glob import glob
import json
from pathlib import PurePath

from PyQt5.QtWidgets import (
    QLineEdit,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QListView,
    QSpinBox,
    QStyledItemDelegate,
    QScrollArea,
    QHBoxLayout,
    QLabel,
    QAbstractItemDelegate,
)
from PyQt5.QtCore import (
    QRunnable,
    pyqtSlot,
    QObject,
    pyqtSignal,
    Qt,
    QAbstractListModel,
    QPointF,
    QLineF,
    QSize,
)

from .utility_classes import NumpyEncoder, YamlWorker
from ..functions.utilities import load_scanimage_file


class LineEdit(QLineEdit):
    """
    This is a subclass of QLineEdit that returns values that are usable for
    Python.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def toInt(self):
        if len(self.text()) == 0:
            x = None
        else:
            x = int(self.text())
        return x

    def toText(self):
        if len(self.text()) == 0:
            x = None
        else:
            x = self.text()
        return x

    def toFloat(self):
        if len(self.text()) == 0:
            x = None
        else:
            x = float(self.text())
        return x


class SaveWorker(QRunnable):
    """
    This class is used to create a 'runner' in a different thread than the
    main GUI. This prevents that GUI from freezing during saving.
    """

    def __init__(self, save_filename, dictionary):
        super().__init__()

        self.save_filename = save_filename
        self.dictionary = dictionary
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        for i, key in enumerate(self.dictionary.keys()):
            x = self.dictionary[key]
            with open(f"{self.save_filename}_{x.name}.json", "w") as write_file:
                json.dump(x.__dict__, write_file, cls=NumpyEncoder)
            self.signals.progress.emit(
                int((100 * (i + 1) / len(self.dictionary.keys())))
            )
        self.signals.finished.emit("Saved")


class MiniSaveWorker(QRunnable):
    """
    This class is used to create a 'runner' in a different thread than the
    main GUI. This prevents that GUI from freezing during saving. This is a
    variant of the SaveWorker class used for the MiniAnalysisWidgit since a
    specific function needs to be run on the mini-dictionary to prevent it
    from taking up a lot of space in the json file.
    """

    def __init__(self, save_filename, dictionary):
        super().__init__()

        self.save_filename = save_filename
        self.dictionary = dictionary
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        for i, key in enumerate(self.dictionary.keys()):
            x = deepcopy(self.dictionary[key])
            x.save_postsynaptic_events()
            with open(f"{self.save_filename}_{x.name}.json", "w") as write_file:
                json.dump(x.__dict__, write_file, cls=NumpyEncoder)
            self.signals.progress.emit(
                int((100 * (i + 1) / len(self.dictionary.keys())))
            )
        self.signals.finished.emit("Saved")


class WorkerSignals(QObject):
    """
    This is general 'worker' that provides feedback from events to the window. 
    The 'worker' also provides a 'runner' to the main GUI thread to prevent it
    from freezing when there are long running events.
    """

    dictionary = pyqtSignal(dict)
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)


class ListView(QListView):
    """
    This is a custom listview that allows for drag and drop loading of
    scanimage matlab files.
    """

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(self.MultiSelection)
        self.setDropIndicatorShown(True)

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

    def dropEvent(self, e):
        """
		This function will enable the drop file directly on to the 
		main window. The file location will be stored in the self.filename
		"""
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            for url in e.mimeData().urls():
                fname = PurePath(str(url.toLocalFile()))
                if fname.suffix == ".mat":
                    if fname.stem not in self.model().fname_list:
                        self.model().acq_list += [load_scanimage_file(fname)]
                        self.model().fname_list += [fname.stem]
            self.model().acq_list.sort(key=lambda x: int(x[0].split("_")[-1]))
            self.model().fname_list.sort(key=lambda x: int(x.split("_")[-1]))
            self.model().layoutChanged.emit()
        else:
            e.ignore()


class ListModel(QAbstractListModel):
    def __init__(self, acq_list=None, fname_list=None, header_name="Acquisition(s)"):
        super().__init__()
        self.acq_list = acq_list or []
        self.fname_list = fname_list or []
        self.header_name = header_name

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            acq_component = self.acq_list[index.row()]
            return acq_component[0]

    def headerData(self, name, role):
        if role == Qt.ItemDataRole.DisplayRole:
            name = self.header_name
            return name

    def add_acq(self, fname):
        acq_components = load_scanimage_file(fname)
        self.fname_list += [fname]
        self.acq_list += [acq_components]

    def rowCount(self, index):
        return len(self.acq_list)


class StringBox(QSpinBox):
    def __init__(self, parent=None):
        super(StringBox, self).__init__(parent)
        strings = []
        self.setStrings(strings)

    def setStrings(self, strings):
        strings = list(strings)
        self._strings = tuple(strings)
        self._values = dict(zip(strings, range(len(strings))))
        self.setRange(0, len(strings) - 1)

    def textFromValue(self, value):

        # returning string from index
        # _string = tuple
        return self._strings[value]


class DragDropScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.signals = WorkerSignals()

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

    @pyqtSlot()
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
                pref_dict = YamlWorker.load_yaml(fname)
                self.signals.dictionary.emit(pref_dict)
            else:
                e.ignore()
        else:
            e.ignore()
