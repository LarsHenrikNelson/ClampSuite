import logging
from pathlib import Path, PurePath

import yaml
from PySide6.QtCore import (
    QAbstractListModel,
    QMutex,
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QLineEdit,
    QListView,
    QSpinBox,
    QWidget,
)

from ...manager import ExpManager

logger = logging.getLogger(__name__)


class AnalysisWidget(QWidget):
    acq = Signal(int)
    error = Signal(str)
    clicked = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.acquisition_number = QSpinBox()
        self.acquisition_number.setMaximumWidth(70)
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)

    def acqChanged(self):
        self.acq.emit(self.acquisition_number.value())

    def errorDialog(self, text):
        self.error.emit(text)

    def acqSpinbox(self, acq_number):
        raise (NotImplementedError)

    def editAttr(self, line_edit, value):
        if (
            not self.exp_manager.acqs_exist(self.objectName())
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict[self.objectName()]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return False
        else:
            logger.info(
                f"Editing acquisition attribute {self.acquisition_number.value()}."
            )
            acq = self.exp_manager.exp_dict[self.objectName()][
                self.acquisition_number.value()
            ]
            setattr(acq, line_edit, value)
            logger.info(
                f"Set {value} for {line_edit} on aquisition\
                    {self.acquisition_number.value()}."
            )
            return True

    # Below are the must have 'virtual functions' for ClampSuite
    def reset(self):
        raise (NotImplementedError)

    def deleteAcq(self):
        raise (NotImplementedError)

    def resetRejectedAcqs(self):
        raise (NotImplementedError)

    def resetRecentRejectAcq(self):
        raise (NotImplementedError)

    def runFinalAnalysis(self):
        raise (NotImplementedError)


class QExpManager(ExpManager):
    def __init__(self):
        self.need_to_save = False

    def needToSave(self, save: bool):
        self.need_to_save = save

    def set_ui_prefs(self, pref_dict: dict) -> None:
        self.ui_prefs = pref_dict
        self.ui_prefs["Deleted acqs"] = {}

    def save_ui_prefs(self, file_path: PurePath | Path | str, ui_prefs) -> None:
        self.callback_func("Saving preferences")
        with open(f"{file_path}.yaml", "w") as file:
            yaml.dump(ui_prefs, file)
        self.callback_func("Saved preferences")


class FrameWidget(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(parent=parent)

        self.setTitle(title)
        # self.setObjectName("parent")

        # self.setFrameStyle(QFrame.Panel | QFrame.Plain)
        self.setStyleSheet(
            r"""QGroupBox 
            {
                border: 1px solid; border-color: #404040;
                border-radius: 6px;
                margin-top: 12px;
                padding: 0px 0px;
                font-weight: bold}
            """
        )


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


class ThreadWorker(QRunnable):
    """
    This class is used to create a 'runner' in a different thread than the
    main GUI. This prevents that GUI from freezing during saving.
    """

    def __init__(self, exp_manager):
        super().__init__()

        self.exp_manager = exp_manager
        self.signals = WorkerSignals()
        self.mutex = QMutex()
        self.function = []
        self.kwargs = []

    def addAnalysis(self, function, **kwargs):
        self.function.append(function)
        self.kwargs.append(kwargs)

    @Slot()
    def run(self):
        self.mutex.lock()
        for func, args in zip(self.function, self.kwargs):
            if "exp" in args.keys():
                exp = args.pop("exp")
            if isinstance(self.exp_manager, dict):
                self._run_function(func, self.exp_manager[exp], args)
            else:
                self._run_function(func, self.exp_manager, args)
        self.mutex.unlock()
        self.signals.finished.emit("Finished")


class WorkerSignals(QObject):
    """
    This is general 'worker' that provides feedback from events to the window.
    The 'worker' also provides a 'runner' to the main GUI thread to prevent it
    from freezing when there are long running events.
    """

    file = Signal(str)
    progress = Signal(str)
    finished = Signal(str)
    file_path = Signal(str)
    dir_path = Signal(str)
    clicked = Signal(str)
    error = Signal(str)
    acq = Signal(int)


class ListModel(QAbstractListModel):
    """
    The model contains all the load data for the list view. Qt works using a
    model-view-controller framework so the view should not contain any data
    analysis or loading, it just facilities the transfer of the data to the model.
    The model is used to add, remove, and modify the data through the use of a
    controller which in Qt is often built into the models.
    """

    def __init__(self):
        super().__init__()
        self.acq_names = []
        self.signals = WorkerSignals()

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            x = self.acq_names[index.row()]
            return x

    def rowCount(self, index):
        return len(self.acq_names)

    def setAnalysisType(self, analysis):
        """
        This function sets the analysis type for the model which is used to set the
        acquisition type that is created in dropEvent().
        """
        self.analysis_type = analysis

    def deleteSelection(self, index):
        keys = list(self.exp_manager.acquisitions.keys())
        keys.sort()

        # Need to catch cases where the index does not exist anymore.
        # I cannot figure out why Qt keeps returning the extra index.
        if index > len(keys):
            pass
        else:
            self.removeRow(index)
            key = keys[index]
            del self.exp_manager.acquisitions[key]
            self.layoutChanged.emit()
            self.sortNames()

    def clearData(self):
        self.acq_dict = {}
        self.acq_names = []
        self.exp_manager = None

    def addData(self, urls):
        if not isinstance(urls[0], str):
            urls = [str(url.toLocalFile()) for url in urls]
        worker = ThreadWorker(self.exp_manager)
        worker.addAnalysis("create_exp", analysis=self.analysis_type, file=urls)
        self.signals.dir_path.emit(str(Path(urls[0]).parent))
        worker.signals.progress.connect(self.updateProgress)
        worker.signals.finished.connect(self.acqsAdded)
        QThreadPool.globalInstance().start(worker)

    def acqsAdded(self, value):
        self.sortNames()
        self.layoutChanged.emit()

    def updateProgress(self, value):
        self.signals.progress.emit(value)

    def sortNames(self):
        acq_list = list(self.exp_manager.acquisitions.keys())
        acq_list.sort()
        self.acq_names = [self.exp_manager.acquisitions[i].name for i in acq_list]

    def setLoadData(self, exp_manager):
        self.exp_manager = exp_manager


class ListView(QListView):
    """
    This is a custom listview that allows for drag and drop loading of
    scanimage matlab files.
    """

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setDropIndicatorShown(True)
        self.setModel(ListModel())
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

    @Slot(QObject)
    def dropEvent(self, e):
        """
        This function will enable the drop file directly on to the
        main window. The file location will be stored in the self.filename
        """
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            self.model().addData(e.mimeData().urls())
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
        self.model().addData(urls)
        self.model().layoutChanged.emit()

    def setAnalysisType(self, analysis):
        self.model().setAnalysisType(analysis)

    def setData(self, exp_manager):
        self.model().setLoadData(exp_manager)


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
