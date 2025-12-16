import logging
from pathlib import Path, PurePath

from PySide6.QtGui import QAction, QIcon, QPixmap, Qt
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
    QBoxLayout,
    QWidget,
)

from ..functions.startup import check_dir
from .current_clamp_widget import CurrentClampWidget
from .mini_analysis_widget import MiniAnalysisMain
from .oepsc_widget import EvokedPSCLFPWidget
from .pref_widget import PreferencesWidget
from .home_widget import HomeWidget


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Creating GUI")
        self.initUI()
        # self.setWidget("Mini analysis")

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
        self.tool_bar.setIconSize(QtCore.QSize(32, 32))
        self.addToolBar(self.tool_bar)

        # self.widget_chooser = QComboBox()
        # self.tool_bar.addWidget(self.widget_chooser)
        # widgets = ["Mini analysis", "oEPSC/LFP", "Current clamp", "Filtering setup"]
        # self.widget_chooser.addItems(widgets)
        # self.widget_chooser.setMinimumContentsLength(len(max(widgets, key=len)))
        # self.widget_chooser.currentTextChanged.connect(self.setWidget)

        homeicon = QIcon(QPixmap(":/icons/home.png"))
        home = QAction(homeicon, "Home", self)
        self.tool_bar.addAction(home)

        newicon = QIcon(QPixmap(":/icons/new-folder.png"))
        new = QAction(newicon, "New experiment", self)
        self.tool_bar.addAction(new)

        saveicon = QIcon(QPixmap(":/icons/save.png"))
        save = QAction(saveicon, "Save", self)
        self.tool_bar.addAction(save)

        foldericon = QIcon(QPixmap(":/icons/folder-open.png"))
        folder = QAction(foldericon, "Folder", self)
        self.tool_bar.addAction(folder)

        self.preferences_widget = PreferencesWidget()

        self.central_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.current_widget = HomeWidget()
        self._current_widget = "Home"
        self.current_widget.clicked.connect(self.setWidget)
        self.main_layout.addWidget(self.current_widget, 0, Qt.AlignCenter)

        self.working_dir = str(Path().home())

        home.triggered.connect(lambda _: self.setWidget("Home"))

        self.load_dialog_open = False
        logger.info(f"Working directory set to: {self.working_dir}")

    def setComboBoxSpacing(self):
        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            i.view().setSpacing(1)

    def setWidget(self, text):
        if text != self._current_widget:
            self.main_layout.removeWidget(self.current_widget)
            self.to_delete = self.current_widget
            del self.current_widget
            self.to_delete.hide()
            self.to_delete.deleteLater()
            if text == "Mini analysis":
                logger.info("Creating MiniAnalysisMain")
                self.current_widget = MiniAnalysisMain()
                logger.info("Central widget set as Mini analysis")
            elif text == "Evoked PSC/LFP":
                self.current_widget = EvokedPSCLFPWidget()
                logger.info("Central widget set as Evoked PSC/LFP")
            elif text == "Current clamp":
                self.current_widget = CurrentClampWidget()
                logger.info("Central widget set as Current clamp")
            elif text == "Home":
                self.current_widget = HomeWidget()
                logger.info("Central widget set as Home")

            self._current_widget = text

            if text != "Home":
                self.current_widget.dir_path.connect(self.setWorkingDirectory)
                self.main_layout.addWidget(self.current_widget, Qt.AlignCenter)
            else:
                self.current_widget.clicked.connect(self.setWidget)
                self.main_layout.addWidget(self.current_widget, 0, Qt.AlignCenter)

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
            self.current_widget.saveAs(save_filename)
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
            self.current_widget.loadExperiment(path)
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
            self.current_widget.createExperiment(directory)
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
            self.current_widget.loadPreferences(file_name)
            logger.info("Preferences loaded")
        else:
            logger.info("No preferences loaded")

    def savePreferences(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self, "Save preference as...", ""
        )
        if save_filename:
            logger.info("Saving preferences")
            self.current_widget.savePreferences(save_filename)
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
        if self.current_widget.needToSave():
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
        pass
        # for key, value in self.gui_widgets.items():
        #     temp_path = self.program_directory / (key + ".yaml")
        #     if temp_path.exists():
        #         logger.info(f"Loading {key} preferences from {temp_path}")
        #         # value.loadPreferences(self.program_directory / (key + ".yaml"))
        #     else:
        #         logger.info(f"Loading {key} preferences to {temp_path}")
        #         value.savePreferences(self.program_directory / key)
