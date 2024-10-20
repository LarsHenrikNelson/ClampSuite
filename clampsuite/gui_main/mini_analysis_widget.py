import logging

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..functions.kde import create_kde
from ..gui_widgets import (
    AnalysisButtonsWidget,
    BaselineWidget,
    DragDropWidget,
    FilterWidget,
    LoadAcqWidget,
    mini,
    RCCheckWidget,
    ThreadWorker,
    WorkerSignals,
    QExpManager,
)

logger = logging.getLogger(__name__)


class MiniAnalysisWidget(DragDropWidget):
    def __init__(self, parent=None):
        super(DragDropWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.signals = WorkerSignals()

        logger.info("Creating Mini analysis GUI")
        # Create tabs for part of the analysis program
        self.signals.file.connect(self.loadPreferences)
        self.signals.file_path.connect(self.loadExperiment)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1 = QWidget()
        self.tab1_scroll.setWidget(self.tab1)

        self.analysis_widget = mini.AnalysisWidget()
        self.analysis_widget.clicked.connect(self.runFinalAnalysis)

        self.tab3_scroll = QScrollArea()
        self.tab3_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setWidgetResizable(True)
        self.dock_area3 = DockArea()

        self.tab_widget.addTab(self.tab1_scroll, "Setup")
        self.tab_widget.addTab(self.analysis_widget, "Analysis")
        self.tab_widget.addTab(self.dock_area3, "Final data")

        self.setStyleSheet(
            """QTabWidget::tab-bar
                                          {alignment: left;}"""
        )

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.main_layout.addWidget(self.pbar)

        self.dlg = QMessageBox(self)

        # Tab 1 layouts
        self.setup_layout = QHBoxLayout()

        self.tab1.setLayout(self.setup_layout)

        self.input_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.input_layout, 0)

        self.baseline_widget = BaselineWidget()
        self.input_layout.addWidget(self.baseline_widget)

        self.rc_widget = RCCheckWidget()
        self.input_layout.addWidget(self.rc_widget)

        self.filter_widget = FilterWidget()
        self.input_layout.addWidget(self.filter_widget)

        self.analysis_buttons = AnalysisButtonsWidget()
        self.input_layout.addLayout(self.analysis_buttons)
        self.input_layout.addStretch()

        self.mini_settings = mini.MiniWidget()
        self.setup_layout.addLayout(self.mini_settings)

        # Setup for the drag and drop load layout
        self.analysis_type = "mini"
        self.load_widget = LoadAcqWidget(analysis_type=self.analysis_type)
        self.load_widget.signals.progress.connect(self.updateProgress)
        self.load_widget.signals.dir_path.connect(self.setWorkingDirectory)

        self.setup_layout.addLayout(self.load_widget, 0)

        self.setup_layout.addStretch(1)

        # Tab 3 layouts and setup
        self.table_dock = Dock("Data (table)")
        self.ave_event_dock = Dock("Average Event")
        self.data_dock = Dock("Data (visualization)")
        self.dock_area3.addDock(self.table_dock, position="left")
        self.dock_area3.addDock(self.ave_event_dock, position="right")
        self.dock_area3.addDock(self.data_dock, position="bottom")
        self.ave_event_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.ave_event_plot.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_plot.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_dock.addWidget(self.ave_event_plot)
        self.ave_event_plot.setObjectName("Ave event plot")
        self.final_tab_widget = QTabWidget()
        self.final_tab_widget.setMinimumHeight(300)
        self.table_dock.addWidget(self.final_tab_widget)
        self.stem_plot = pg.PlotWidget(labels={"bottom": "Time (ms)"}, useOpenGL=True)
        self.amp_dist = pg.PlotWidget(useOpenGL=True)
        self.plot_selector = QComboBox()
        self.plot_selector.setMaximumWidth(100)
        self.plot_selector.currentTextChanged.connect(self.plotRawData)
        self.data_dock.addWidget(self.plot_selector, 0, 0)
        self.data_dock.addWidget(self.stem_plot, 0, 1)
        self.data_dock.addWidget(self.amp_dist, 0, 2)

        self.exp_manager = QExpManager()
        self.exp_manager.set_callback(self.updateProgress)
        self.load_widget.setData(self.exp_manager)
        self.analysis_widget.setData(self.exp_manager)
        self.setWidth()

    def clearTables(self):
        if self.table_dict:
            for i in self.table_dict.values():
                i.clear()
                i.hide()
                i.deleteLater()
            self.table_dict = {}

    # This needs to be fixed because it changes the lineedits that
    # are part of the spinboxes which is not ideal. Need to create
    # a dict to hold the lineedits.
    def setWidth(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if not isinstance(i.parentWidget(), QSpinBox):
                i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(80)

        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            i.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            i.adjustSize()

    def analyze(self):
        """
        This function creates each MiniAnalysis object and puts
        it into a dictionary. The events are create within the
        EventAnalysis objection. Note that the created
        EventAnalysis object needs to have analyze run. This was
        chosen because it made the initial debugging easier.
        """
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("No acquisitions, analysis ended.")
            self.errorDialog("No acquisitions, analysis ended.")
            return None

        logger.info("Analysis started.")
        self.pbar.setFormat("Analyzing...")
        self.pbar.setValue(0)

        self.exp_manger.needToSave(True)

        # The for loop creates each EventAnalysis object. Enumerate returns
        # count which is used to adjust the progress bar and acq_components
        # comes from the load_widget

        # I need to just put all the settings into a dictionary,
        # so the functions are not called for every acquisition
        worker = ThreadWorker(self.exp_manager)
        filter_args = {}
        filter_args.update(self.baseline_widget.getAnalysisSettings())
        filter_args.update(self.filter_widget.getAnalysisSettings())

        mini_settings = self.mini_settings.getAnalysisSettings()
        analysis_args = {}
        analysis_args.update(mini_settings["mini_settings"])
        analysis_args.update(self.rc_widget.getAnalysisSettings())

        worker.addAnalysis(
            "analyze",
            exp=self.analysis_type,
            filter_args=filter_args,
            analysis_args=analysis_args,
            template_args=mini_settings["template_settings"],
        )
        worker.signals.progress.connect(self.updateProgress)
        worker.signals.finished.connect(self.setAcquisition)
        logger.info("Starting analysis thread.")
        QThreadPool.globalInstance().start(worker)

    def reset(self):
        logger.info("Resetting UI.")
        """
        This function resets all the variables and clears all the plots.
        It takes a while to run.
        """
        self.load_widget.clearData()
        self.calc_param_clicked = False
        self.stem_plot.clear()
        self.amp_dist.clear()
        self.ave_event_plot.clear()
        self.inspection_widget.clearData()
        self.calc_param_clicked = False
        self.exp_manager.needToSave(False)
        self.plot_selector.clear()
        self.pbar.setValue(0)
        self.exp_manager.clear()
        self.clearTables()
        self.pbar.setFormat("Ready to analyze")
        logger.info("UI Reset. Ready to analyze.")

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not run final analysis, no acquisitions analyzed.")
            self.errorDialog("Did not run final analysis, no acquisitions analyzed.")
            return None
        logger.info("Beginning final analysis.")
        self.calc_param_clicked = True
        if self.exp_manager.final_analysis is not None:
            logger.info("Clearing previous analysis.")
            self.final_tab_widget.clear()
            self.clearTables()
            self.table_dict = {}
        self.exp_manager.needToSave(True)

        self.pbar.setFormat("Analyzing...")
        logger.info("Experiment manager started final analysis")
        self.exp_manager.run_final_analysis(acqs_deleted=self.exp_manager.acqs_deleted)
        logger.info("Experiment manager finished final analysis.")
        fa = self.exp_manager.final_analysis
        self.plotAveEvent(
            fa.average_event_x(),
            fa.average_event_y(),
            fa.fit_decay_x(),
            fa.fit_decay_y(),
        )
        logger.info("Plotted average event")
        for key, df in fa.df_dict.items():
            data_table = pg.TableWidget(sortable=False)
            self.table_dict[key] = data_table
            data_table.setData(df.T.to_dict("dict"))
            self.final_tab_widget.addTab(data_table, key)
        logger.info("Set final data into tables.")
        plots = [
            "Amplitude (pA)",
            "Est tau (ms)",
            "Rise time (ms)",
            "Rise rate (pA/ms)",
            "IEI (ms)",
        ]
        self.plot_selector.clear()
        self.plot_selector.addItems(plots)
        self.plot_selector.setMinimumContentsLength(len(max(plots, key=len)))
        if self.plot_selector.currentText() != "IEI (ms)":
            self.plotRawData(self.plot_selector.currentText())
        self.pbar.setFormat("Finished analysis")
        self.tab_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

    def plotAveEvent(self, x, y, decay_x, decay_y):
        self.ave_event_plot.clear()
        self.ave_event_plot.plot(x=x, y=y, pen=pg.mkPen(width=3))
        self.ave_event_plot.plot(
            x=decay_x, y=decay_y, pen=pg.mkPen({"color": "#34E44B", "width": 2})
        )

    def plotRawData(self, y: str):
        if self.exp_manager.final_analysis is not None and y != "":
            if y != "IEI (ms)":
                self.plotStemData(y)
            else:
                self.stem_plot.clear()
            self.plotAmpDist(y)

    def plotStemData(self, column: str):
        self.stem_plot.clear()
        fa = self.exp_manager.final_analysis
        x_values = fa.timestamp_array()
        y_values = fa.get_raw_data(column)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(x_values, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        head_item = pg.PlotDataItem(
            x=x_values,
            y=y_values,
            pen=None,
            symbol="o",
            symbolSize=2,
            symbolPen=None,
            symbolBrush="w",
        )
        self.stem_plot.addItem(stem_item)
        self.stem_plot.addItem(head_item)
        self.stem_plot.setLabel(axis="left", text=f"{column}")

    def plotAmpDist(self, column: str):
        self.amp_dist.clear()
        fa = self.exp_manager.final_analysis
        log_y, x = create_kde(
            fa.df_dict["Raw data"],
            self.plot_selector.currentText(),
        )
        y = fa.get_raw_data(self.plot_selector.currentText())
        dist_item = pg.PlotDataItem(
            x=x,
            y=log_y,
            fillLevel=0,
            fillOutline=True,
            fillBrush=pg.mkBrush("#bf00bf50"),
        )
        self.amp_dist.addItem(dist_item)
        self.amp_dist.setXRange(np.nanmin(y), np.nanmax(y))
        y_values = np.full(y.shape, max(log_y) * 0.05)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(y, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        self.amp_dist.addItem(stem_item)

    def errorDialog(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        self.dlg.exec()

    def eventNotCreated(self):
        self.dlg.setWindowTitle("Information")
        self.dlg.setText("Event could not be created")
        self.dlg.exec()

    def loadExperiment(self, directory):
        logger.info(f"Loading experiment from {directory}.")
        self.reset()
        self.pbar.setFormat("Loading...")
        self.exp_manger.clear()
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis("load", analysis="mini", file_path=directory)
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def setLoadData(self):
        if self.exp_manager.final_analysis is not None:
            logger.info("Setting previously analyzed data.")
            self.pbar.setFormat("Setting previously analyzed data.")
            fa = self.exp_manager.final_analysis
            self.plotAveEvent(
                fa.average_event_x(),
                fa.average_event_y(),
                fa.fit_decay_x(),
                fa.fit_decay_y(),
            )
            for key, df in fa.df_dict.items():
                data_table = pg.TableWidget()
                self.table_dict[key] = data_table
                data_table.setData(df.T.to_dict("dict"))
                self.final_tab_widget.addTab(data_table, key)
            plots = [
                "Amplitude (pA)",
                "Est tau (ms)",
                "Rise time (ms)",
                "Rise rate (pA/ms)",
                "IEI (ms)",
            ]
            self.plot_selector.addItems(plots)
        self.pbar.setFormat("Loaded")
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.ui_prefs["Acq_number"])
        logger.info("Experiment successfully loaded.")
        self.pbar.setFormat("Experiment successfully loaded")

    def saveAs(self, save_filename):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("There is no data to save")
            self.errorDialog("There is no data to save")
        else:
            logger.info("Saving experiment.")
            self.reset_button.setEnabled(False)
            self.pbar.setFormat("Saving...")
            self.pbar.setValue(0)
            pref_dict = self.createPrefDict()
            pref_dict["Final Analysis"] = self.calc_param_clicked
            pref_dict["Acq_number"] = self.acquisition_number.value()
            self.exp_manager.set_ui_prefs(pref_dict)
            self.worker = ThreadWorker(self.exp_manager)
            self.worker.addAnalysis("save", file_path=save_filename)
            self.worker.signals.progress.connect(self.updateProgress)
            self.worker.signals.finished.connect(self.finishedSaving)
            QThreadPool.globalInstance().start(self.worker)
            self.reset_button.setEnabled(True)
            self.exp_manager.needToSave(False)

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def createExperiment(self, urls):
        self.pbar("Creating experiment")
        self.load_widget.addData(urls)
        self.pbar("Experiment created")

    def createPrefDict(self):
        logger.info("Creating preferences dictionary.")
        pref_dict = {}
        pref_dict["baseline"] = self.baseline_widget.getSettings()
        pref_dict["filter"] = self.filter_widget.getSettings()
        pref_dict["rc_check"] = self.rc_widget.getSettings()
        pref_dict["mini"] = self.mini_settings.getSettings()
        return pref_dict

    def setPreferences(self, pref_dict: dict[dict[str, int | float | str]]):
        logger.info("Setting MiniAnalysis preferences.")

        self.baseline_widget.setSettings(pref_dict["baseline"])
        self.filter_widget.getSettings(pref_dict["filter"])
        self.rc_widget.getSettings(pref_dict["rc_check"])
        self.mini_settings.getSettings(pref_dict["mini"])

        logger.info("Preferences set.")
        self.pbar.setFormat("Preferences set")

    def loadPreferences(self, file_name):
        pref_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(pref_dict)

    def savePreferences(self, save_filename):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(save_filename, pref_dict)

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setFormat(f"Acquisition {value} analyzed")
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)
