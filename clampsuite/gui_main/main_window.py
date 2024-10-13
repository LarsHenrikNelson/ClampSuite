import logging
from pathlib import Path, PurePath

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QToolBar,
)

from ..functions.startup import check_dir
from .current_clamp_widget import currentClampWidget
from .filter_widget import filterWidget
from .mini_analysis_widget import MiniAnalysisWidget
from .oepsc_widget import oEPSCWidget
from .pref_widget import PreferencesWidget

# from ..gui_widgets.qtwidgets import WorkerSignals

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Creating GUI")
        self.initUI()
        self.setWidget("Mini analysis")

    def initUI(self):
        self.setWindowTitle("Electrophysiology Analysis")

        # Set the menu bar
        self.bar = self.menuBar()
        self.file_menu = self.bar.addMenu("File")
        self.preferences_menu = self.bar.addMenu("Preferences")

        self.open_new_file = QAction("Create experiment", self)
        self.open_new_file.setStatusTip("Create experiment")
        self.open_new_file.setShortcut("Ctrl+E")
        self.open_new_file.triggered.connect(self.createExperiment)
        self.file_menu.addAction(self.open_new_file)

        self.load_exp = QAction("Load experiment", self)
        self.load_exp.setStatusTip("Load experiment")
        self.load_exp.setShortcut("Ctrl+O")
        self.load_exp.triggered.connect(self.loadExperiment)
        self.file_menu.addAction(self.load_exp)

        self.saveFile = QAction("Save", self)
        self.saveFile.setStatusTip("Save file")
        self.saveFile.setShortcut("Ctrl+S")
        self.saveFile.triggered.connect(self.saveAs)
        self.file_menu.addAction(self.saveFile)

        self.loadPref = QAction("Load analysis preferences", self)
        self.loadPref.setStatusTip("Load analysis preferences")
        self.loadPref.triggered.connect(self.loadPreferences)
        self.file_menu.addAction(self.loadPref)

        self.savePref = QAction("Save analysis preferences", self)
        self.savePref.setStatusTip("Save analysis preferences")
        self.savePref.triggered.connect(self.savePreferences)
        self.file_menu.addAction(self.savePref)

        self.setApplicationPreferences = QAction("Set preferences", self)
        self.setApplicationPreferences.triggered.connect(self.setAppearance)
        self.preferences_menu.addAction(self.setApplicationPreferences)

        self.tool_bar = QToolBar()
        self.addToolBar(self.tool_bar)

        self.widget_chooser = QComboBox()
        self.tool_bar.addWidget(self.widget_chooser)
        widgets = ["Mini analysis", "oEPSC/LFP", "Current clamp", "Filtering setup"]
        self.widget_chooser.addItems(widgets)
        self.widget_chooser.setMinimumContentsLength(len(max(widgets, key=len)))
        self.widget_chooser.currentTextChanged.connect(self.setWidget)

        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.saveAs)
        style = self.save_button.style()
        icon = style.standardIcon(QStyle.SP_DialogSaveButton)
        self.save_button.setIcon(icon)
        self.tool_bar.addWidget(self.save_button)

        self.open_button = QPushButton()
        self.open_button.clicked.connect(self.loadData)
        style = self.open_button.style()
        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        self.open_button.setIcon(icon)
        self.tool_bar.addWidget(self.open_button)

        self.preferences_widget = PreferencesWidget()

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        logger.info("Creating analysis widgets")
        logger.info("Creating MiniAnalysisWidget")
        self.mini_widget = MiniAnalysisWidget()
        self.mini_widget.signals.dir_path.connect(self.setWorkingDirectory)
        self.central_widget.addWidget(self.mini_widget)
        logger.info("Creating oEPSCWidget")
        self.oepsc_widget = oEPSCWidget()
        self.oepsc_widget.signals.dir_path.connect(self.setWorkingDirectory)
        self.central_widget.addWidget(self.oepsc_widget)
        logger.info("Creating currentClampWidget")
        self.current_clamp_widget = currentClampWidget()
        self.current_clamp_widget.signals.dir_path.connect(self.setWorkingDirectory)
        self.central_widget.addWidget(self.current_clamp_widget)
        logger.info("Creating filterWidget")
        self.filter_widget = filterWidget()
        self.central_widget.addWidget(self.filter_widget)
        logger.info("Analysis widgets created")

        self.gui_widgets = {
            "MiniAnalysisWidget": self.mini_widget,
            "oEPSCWidget": self.oepsc_widget,
            "CurrentClampWidget": self.current_clamp_widget,
            # "FilterWidget": self.filter_widget,
        }
        self.current_widget = ""
        self.setComboBoxSpacing()
        self.working_dir = str(Path().home())

        self.load_dialog_open = False
        logger.info(f"Working directory set to: {self.working_dir}")

    def setComboBoxSpacing(self):
        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            i.view().setSpacing(1)

    def setWidget(self, text):
        if text == "Mini analysis":
            self.central_widget.setCurrentWidget(self.mini_widget)
            self.current_widget = "MiniAnalysisWidget"
            logger.info("Central widget set as MiniAnalysisWidget")
        elif text == "oEPSC/LFP":
            self.central_widget.setCurrentWidget(self.oepsc_widget)
            self.current_widget = "oEPSCWidget"
            logger.info("Central widget set as oEPSCWidget")
        elif text == "Current clamp":
            self.central_widget.setCurrentWidget(self.current_clamp_widget)
            self.current_widget = "CurrentClampWidget"
            logger.info("Central widget set as currentClampWidget")
        elif text == "Filtering setup":
            self.central_widget.setCurrentWidget(self.filter_widget)
            self.current_widget = "FilterWidget"
            logger.info("Central widget set as filterWidget")

    def saveAs(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self,
            dir=self.working_dir,
            caption="Save data as...",
        )
        if save_filename:
            logger.info("Saving analysis.")
            self.working_dir = str(Path(PurePath(save_filename).parent))
            logger.info(f"Working directory set to: {self.working_dir}")
            self.central_widget.currentWidget().saveAs(save_filename)
            logger.info("Analysis saved.")

    def loadExperiment(self):
        directory = str(
            QFileDialog.getExistingDirectory(
                self,
                dir=self.working_dir,
                caption="Open folder...",
            )
        )
        if directory:
            logger.info("Loading experiment.")
            path = Path(directory)
            self.working_dir = str(path)
            self.central_widget.currentWidget().loadExperiment(path)
            logger.info("Experiment loaded.")

    def createExperiment(self):
        directory, _ = QFileDialog.getOpenFileNames(
            self,
            dir=self.working_dir,
            caption="Open files...",
        )
        if len(directory) > 0:
            logger.info("Creating/appending new experiment.")
            self.working_dir = str(PurePath(directory[0]).parent)
            logger.info(f"Working directory set to: {self.working_dir}")
            self.central_widget.currentWidget().createExperiment(directory)
            logger.info("Experiment created/appended.")

    def loadData(self):
        self.load_dialog_open = True
        self.dlg = QMessageBox()
        self.dlg.setText("Create or load exp?")
        self.dlg.setWindowTitle("Experiment")
        self.dlg.setText("Create or load exp?")
        self.dlg_open_button = QPushButton("Create exp")
        # open_button.clicked.connect(self.createExperiment)
        self.dlg_load_button = QPushButton("Load exp")
        # load_button.clicked.connect(self.loadExperiment)
        self.dlg.addButton(self.dlg_open_button, QMessageBox.ActionRole)
        self.dlg.addButton(self.dlg_load_button, QMessageBox.ActionRole)
        self.dlg.exec()
        if self.dlg.clickedButton() == self.dlg_open_button:
            self.createExperiment()
        else:
            self.loadExperiment()

    def loadPreferences(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, caption="Open file", filter="YAML Files (*.yaml)"
        )
        if len(file_name) > 0:
            logger.info("Loading preferences")
            self.central_widget.currentWidget().loadPreferences(file_name)
            logger.info("Preferences loaded")
        else:
            logger.info("No preferences loaded")

    def savePreferences(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self, "Save preference as...", ""
        )
        if save_filename:
            logger.info("Saving preferences")
            self.central_widget.currentWidget().savePreferences(save_filename)
            self.gui_widgets[self.current_widget].savePreferences(
                self.program_directory / self.current_widget
            )
            logger.info("Preferences saved")
        else:
            logger.info("No preferences saved")

    def setAppearance(self):
        # Creates a separate window to set the appearance of the application
        self.preferences_widget.show()

    def closeEvent(self, event):
        if self.central_widget.currentWidget().need_to_save:
            msgbox = QMessageBox()
            msgbox.setInformativeText("Do you want to save your changes?")
            msgbox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)
            msgbox.setDefaultButton(QMessageBox.Save)
            ret = msgbox.exec()

            if ret == QMessageBox.Save:
                self.saveAs()
        event.accept()

    def setWorkingDirectory(self, path):
        self.working_dir = path
        logger.info(f"Working directory set to: {self.working_dir}")

    def setProgramDirectory(self):
        self.program_directory = check_dir()
        logger.info(f"Program directory set as {self.program_directory}")

    def loadPresets(self):
        for key, value in self.gui_widgets.items():
            temp_path = self.program_directory / (key + ".yaml")
            if temp_path.exists():
                logger.info(f"Loading {key} preferences from {temp_path}")
                value.loadPreferences(self.program_directory / (key + ".yaml"))
            else:
                logger.info(f"Loading {key} preferences to {temp_path}")
                value.savePreferences(self.program_directory / key)
