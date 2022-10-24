from pathlib import Path, PurePath

from PyQt5.QtCore import Qt

# from PyQt5.QtGui import QAction
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolBar,
)

from .current_clamp_widget import currentClampWidget
from .filter_widget import filterWidget
from .mini_analysis_widget import MiniAnalysisWidget
from .oepsc_widget import oEPSCWidget
from .pref_widget import PreferencesWidget
from ..gui_widgets.utility_classes import YamlWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.set_widget("Mini Analysis")

    def initUI(self):
        self.setWindowTitle("Electrophysiology Analysis")

        # Set the menu bar
        self.bar = self.menuBar()
        self.file_menu = self.bar.addMenu("File")
        self.preferences_menu = self.bar.addMenu("Preferences")

        self.openFile = QAction("Open", self)
        self.openFile.setStatusTip("Open file")
        self.openFile.setShortcut("Ctrl+O")
        self.openFile.triggered.connect(self.open_files)
        self.file_menu.addAction(self.openFile)

        self.saveFile = QAction("Save", self)
        self.saveFile.setStatusTip("Save file")
        self.saveFile.setShortcut("Ctrl+S")
        self.saveFile.triggered.connect(self.save_as)
        self.file_menu.addAction(self.saveFile)

        self.loadPref = QAction("Load analysis preferences", self)
        self.loadPref.setStatusTip("Load analysis preferences")
        self.loadPref.triggered.connect(self.load_preferences)
        self.file_menu.addAction(self.loadPref)

        self.savePref = QAction("Save analysis preferences", self)
        self.savePref.setStatusTip("Save analysis preferences")
        self.savePref.triggered.connect(self.save_preferences)
        self.file_menu.addAction(self.savePref)

        self.setApplicationPreferences = QAction("Set preferences", self)
        self.setApplicationPreferences.triggered.connect(self.set_appearance)
        self.preferences_menu.addAction(self.setApplicationPreferences)

        self.tool_bar = QToolBar()
        self.addToolBar(self.tool_bar)

        self.widget_chooser = QComboBox()
        self.tool_bar.addWidget(self.widget_chooser)
        widgets = ["Mini Analysis", "oEPSC", "Current Clamp", "Filtering setup"]
        self.widget_chooser.addItems(widgets)
        self.widget_chooser.setMinimumContentsLength(len(max(widgets, key=len)))
        self.widget_chooser.currentTextChanged.connect(self.set_widget)

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

    def set_widget(self, text):
        if text == "Mini Analysis":
            self.central_widget.setCurrentWidget(self.mini_widget)
        elif text == "oEPSC":
            self.central_widget.setCurrentWidget(self.oepsc_widget)
        elif text == "Current Clamp":
            self.central_widget.setCurrentWidget(self.current_clamp_widget)
        elif text == "Filtering setup":
            self.central_widget.setCurrentWidget(self.filter_widget)

    def save_as(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self,
            directory=self.working_dir,
            caption="Save data as...",
        )
        if save_filename:
            self.working_dir = str(Path(PurePath(save_filename).parent))
            self.central_widget.currentWidget().save_as(save_filename)

    def open_files(self):
        directory = str(
            QFileDialog.getExistingDirectory(
                self,
                directory=self.working_dir,
                caption="Open files...",
            )
        )
        if directory:
            path = Path(directory)
            self.working_dir = str(path)
            self.central_widget.currentWidget().open_files(path)
        else:
            pass

    def load_preferences(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, caption="Open file", filter="YAML Files (*.yaml)"
        )
        if len(file_name) == 0:
            # This prevents an error from showing up when the path is not
            # selected
            pass
        else:
            self.central_widget.currentWidget().load_preferences(file_name)

    def save_preferences(self):
        save_filename, _extension = QFileDialog.getSaveFileName(
            self, "Save preference as...", ""
        )
        if save_filename:
            self.central_widget.currentWidget().save_preferences(save_filename)

    def set_appearance(self):
        # Creates a separate window to set the appearance of the application
        self.preferences_widget.show()

    def startup_function(self):
        p = Path.home()
        h = "EphysAnalysisProgram"
        file_name = "Preferences.yaml"

        if Path(p / h).exists():
            if Path(p / h / file_name).exists():
                pref_dict = YamlWorker.load_yaml(p / h / file_name)
            else:
                pass
        else:
            Path(p / h).mkdir()

    def closeEvent(self, event):
        if self.central_widget.currentWidget().need_to_save:
            self.save_as()
        event.accept()
