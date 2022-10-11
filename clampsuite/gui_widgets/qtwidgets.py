from copy import deepcopy
from glob import glob
import json
from pathlib import PurePath, Path, PurePosixPath, PureWindowsPath

from PyQt5.QtWidgets import (
    QLineEdit,
    QWidget,
    QListView,
    QSpinBox,
)
from PyQt5.QtCore import (
    QRunnable,
    pyqtSlot,
    QObject,
    pyqtSignal,
    Qt,
    QAbstractListModel,
)

from .utility_classes import NumpyEncoder, YamlWorker
from ..acq import Acq


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
            y = float(self.text())
            x = int(y)
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
    path = pyqtSignal(object)


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
        self.setModel(ListModel())

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
            self.model().addAcq(e.mimeData().urls())
        else:
            e.ignore()

    def clearData(self):
        self.model().clearData()
        self.model().layoutChanged.emit()

    def deleteSelection(self, index_list):
        rows = [i.row() for i in index_list]
        indexes = sorted(rows, reverse=True)
        for i in indexes:
            self.model().deleteSelection(i)
            self.model().layoutChanged.emit()
            self.clearSelection()

    def addAcq(self, urls):
        self.model().addAcq(urls)
        self.model().layoutChanged.emit()

    def setAnalysisType(self, analysis):
        self.model().setAnalysisType(analysis)

    def setLoadData(self, acq_dict):
        self.model().setLoadData(acq_dict)


class ListModel(QAbstractListModel):
    """
    The model contains all the load data for the list view. Qt works using a
    model-view-controller framework so the view should not contain any data
    analysis or loading, it just facilities the transfer of the data to the model.
    The model is used to add, remove, and modify the data through the use of a
    controller which in Qt is often built into the models.
    """

    def __init__(
        self,
        acq_dict=None,
        fname_list=None,
    ):
        super().__init__()
        self.acq_dict = acq_dict or {}
        self.fname_list = fname_list or []
        self.acq_names = []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            x = self.acq_names[index.row()]
            return x

    def rowCount(self, index):
        return len(self.acq_dict)

    def setAnalysisType(self, analysis):
        """
        This function sets the analysis type for the model which is used to set the
        acquisition type that is created in dropEvent().
        """
        self.analysis_type = analysis

    def deleteSelection(self, index):
        keys = list(self.acq_dict.keys())

        # Need to catch cases where the index does not exist anymore.
        # I cannot figure out why Qt keeps returning the extra index.
        if index > len(keys):
            pass
        else:
            self.removeRow(index)
            key = keys[index]
            del self.acq_dict[key]
            del self.fname_list[index]
            self.layoutChanged.emit()
            self.acq_names = [i.name for i in self.acq_dict.values()]

    def clearData(self):
        self.acq_dict = {}
        self.fname_list = []
        self.acq_names = []

    def addAcq(self, urls):
        for url in urls:
            fname = PurePath(str(url.toLocalFile()))
            if fname not in self.fname_list and not Path(fname).is_dir():
                obj = Acq(self.analysis_type, fname)
                obj.load_acq()

                # Add the acquisition to the model dictionary. This
                # dictionary will be be added to the gui widget when
                # the analysis is run.
                self.acq_dict[obj.acq_number] = obj
                self.fname_list += [obj.path]
                self.acq_names += [obj.name]
        self.sortDict()
        self.layoutChanged.emit()

    def sortDict(self):
        acq_list = list(self.acq_dict.keys())
        acq_list.sort(key=lambda x: int(x))
        self.acq_dict = {i: self.acq_dict[i] for i in acq_list}
        self.acq_names = [i.name for i in self.acq_dict.values()]
        self.fname_list.sort(key=lambda x: int(x.stem.split("_")[1]))

    def setLoadData(self, acq_dict):
        self.acq_dict = acq_dict
        self.acq_names = [i.name for i in acq_dict.values()]
        self.layoutChanged.emit()


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


class DragDropWidget(QWidget):
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
            elif Path(fname).is_dir():
                self.signals.path.emit(Path(fname))
            else:
                e.ignore()
        else:
            e.ignore()
