import logging
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    Qt,
    QThreadPool,
    Slot,
)
from PySide6.QtWidgets import (
    QLabel,
    QListView,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QAbstractItemView,
)

from .acq_inspection import AcqInspectionWidget
from .qtwidgets import ThreadWorker, WorkerSignals

logger = logging.getLogger(__name__)


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
        keys = list(self.exp_manager.exp_dict[self.analysis_type].keys())
        keys.sort()

        # Need to catch cases where the index does not exist anymore.
        # I cannot figure out why Qt keeps returning the extra index.
        if index > len(keys):
            pass
        else:
            self.removeRow(index)
            key = keys[index]
            del self.exp_manager.exp_dict[self.analysis_type][key]
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
        acq_list = list(self.exp_manager.exp_dict[self.analysis_type].keys())
        acq_list.sort()
        self.acq_names = [
            self.exp_manager.exp_dict[self.analysis_type][i].name for i in acq_list
        ]

    def setLoadData(self, exp_manager):
        self.exp_manager = exp_manager


class ListView(QListView):
    """
    This is a custom listview that allows for drag and drop loading of
    scanimage matlab files.
    """

    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)

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

    @Slot()
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


class LoadAcqWidget(QVBoxLayout):

    def __init__(self, analysis_type: str, parent=None):
        super(LoadAcqWidget, self).__init__(parent)
        self.signals = WorkerSignals()

        self.inspection_widget = AcqInspectionWidget()
        self.exp_manager = None
        self.dlg = QMessageBox()

        self.analysis_type = analysis_type
        self.load_acq_label = QLabel("Acquisition(s)")
        self.addWidget(self.load_acq_label)
        self.load_widget = ListView()
        self.load_widget.model().signals.progress.connect(self.updateProgress)
        self.load_widget.model().signals.dir_path.connect(self.setWorkingDirectory)
        self.load_widget.setAnalysisType(self.analysis_type)
        self.addWidget(self.load_widget)

        self.inspect_acqs_button = QPushButton("Inspect acq(s)")
        self.inspect_acqs_button.clicked.connect(self.inspectAcqs)
        self.addWidget(self.inspect_acqs_button)

        self.del_sel_button = QPushButton("Delete selection")
        self.addWidget(self.del_sel_button)
        self.del_sel_button.clicked.connect(self.delSelection)

    def delSelection(self):
        if self.exp_manager is None or not self.exp_manager.acqs_exist(
            self.analysis_type
        ):
            logger.info("No acquisitions exist to remove from analysis list.")
            self.errorDialog("No acquisitions exist to remove from analysis list.")
        else:
            # Deletes the selected acquisitions from the list
            indices = self.load_widget.selectedIndexes()
            if len(indices) > 0:
                self.load_widget.deleteSelection(indices)
                self.load_widget.clearSelection()
                logger.info("Removed acquisitions from analysis.")

    def inspectAcqs(self):
        if self.exp_manager is None or not self.exp_manager.acqs_exist(
            self.analysis_type
        ):
            logger.info("No acquisitions exist to inspect.")
            self.errorDialog("No acquisitions exist to inspect.")
        else:
            logger.info("Opening acquisition inspection widget.")
            self.inspection_widget.clearData()
            self.inspection_widget.setData(self.analysis_type, self.exp_manager)
            self.inspection_widget.show()

    def errorDialog(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        self.dlg.exec()

    def updateProgress(self, value):
        self.signals.progress.emit(value)

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)

    def addData(self, urls):
        self.load_widget.model().addData(urls)

    def setData(self, exp_manager):
        self.load_widget.setData(exp_manager)

    def clearData(self):
        self.inspection_widget.clearData()
        self.load_widget.clearData()
