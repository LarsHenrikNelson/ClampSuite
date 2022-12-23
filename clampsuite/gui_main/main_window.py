from pathlib import Path, PurePath

from PyQt5.QtCore import Qt

# from PyQt5.QtGui import QAction
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolBar,
)

from .current_clamp_widget import currentClampWidget
from .filter_widget import filterWidget
from .mini_analysis_widget import MiniAnalysisWidget
from .oepsc_widget import oEPSCWidget
from .pref_widget import PreferencesWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        style = self.save_button.style()
        icon = style.standardIcon(style.SP_DialogSaveButton)
        self.save_button.setIcon(icon)
        self.tool_bar.addWidget(self.save_button)

        self.open_button = QPushButton()
        style = self.open_button.style()
        icon = style.standardIcon(style.SP_DirOpenIcon)
        self.open_button.setIcon(icon)
        self.tool_bar.addWidget(self.open_button)

        self.preferences_widget = PreferencesWidget()

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.mini_widget = MiniAnalysisWidget()
        self.central_widget.addWidget(self.mini_widget)
        self.oepsc_widget = oEPSCWidget()
        self.central_widget.addWidget(self.oepsc_widget)
        self.current_clamp_widget = currentClampWidget()
        self.central_widget.addWidget(self.current_clamp_widget)
        self.filter_widget = filterWidget()
        self.central_widget.addWidget(self.filter_widget)

        self.setComboBoxSpacing()
        self.working_dir = str(Path().cwd())

    def setComboBoxSpacing(self):
        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            i.view().setSpacing(1)

    def setWidget(self, text):
        if text == "Mini analysis":
            self.central_widget.setCurrentWidget(self.mini_widget)
        elif text == "oEPSC/LFP":
            self.central_widget.setCurrentWidget(self.oepsc_widget)
        elif text == "Current clamp":
            self.central_widget.setCurrentWidget(self.current_clamp_widget)
        elif text == "Filtering setup":
            self.central_widget.setCurrentWidget(self.filter_widget)

    def saveAs(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self,
            directory=self.working_dir,
            caption="Save data as...",
        )
        if save_filename:
            self.working_dir = str(Path(PurePath(save_filename).parent))
            self.central_widget.currentWidget().saveAs(save_filename)

    def loadExperiment(self):
        directory = str(
            QFileDialog.getExistingDirectory(
                self,
                directory=self.working_dir,
                caption="Open folder...",
            )
        )
        if directory:
            path = Path(directory)
            self.working_dir = str(path)
            self.central_widget.currentWidget().loadExperiment(path)
        else:
            pass

    def createExperiment(self):
        directory = str(
            QFileDialog.getOpenFileNames(
                self,
                directory=self.working_dir,
                caption="Open files...",
            )
        )
        if directory:
            self.working_dir = str(PurePath(directory[0]).parent)
            self.central_widget.currentWidget().createExperiment(directory)
        else:
            pass

    def loadPreferences(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, caption="Open file", filter="YAML Files (*.yaml)"
        )
        if len(file_name) == 0:
            # This prevents an error from showing up when the path is not
            # selected
            pass
        else:
            print(file_name)
            self.central_widget.currentWidget().loadPreferences(file_name)

    def savePreferences(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self, "Save preference as...", ""
        )
        if save_filename:
            self.central_widget.currentWidget().savePreferences(save_filename)

    def setAppearance(self):
        # Creates a separate window to set the appearance of the application
        self.preferences_widget.show()

    def closeEvent(self, event):
        if self.central_widget.currentWidget().need_to_save:
            self.saveAs()
        event.accept()
