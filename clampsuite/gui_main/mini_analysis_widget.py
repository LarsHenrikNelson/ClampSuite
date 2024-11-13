import logging

import pyqtgraph as pg
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..gui_widgets import (
    AnalysisButtonsWidget,
    BaselineWidget,
    MainAnalysisWidget,
    FilterWidget,
    LoadAcqWidget,
    mini,
    RCCheckWidget,
    ThreadWorker,
    WorkerSignals,
)

logger = logging.getLogger(__name__)


class MiniAnalysisMain(MainAnalysisWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.signals = WorkerSignals()

        logger.info("Creating Mini analysis GUI")
        # Create tabs for part of the analysis program
        self.signals.file.connect(self.loadPreferences)
        self.signals.file_path.connect(self.loadExperiment)

        self._analysis_widgets = {}

        # Tab 1 layouts
        self.setup_layout = QHBoxLayout()

        self.tab1.setLayout(self.setup_layout)

        self.input_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.input_layout, 0)

        self.baseline_widget = BaselineWidget()
        self.input_layout.addWidget(self.baseline_widget)
        self._analysis_widgets[self.baseline_widget.objectName()] = self.baseline_widget

        self.rc_widget = RCCheckWidget()
        self.input_layout.addWidget(self.rc_widget)
        self._analysis_widgets[self.rc_widget.objectName()] = self.rc_widget

        self.filter_widget = FilterWidget()
        self.input_layout.addWidget(self.filter_widget)
        self._analysis_widgets[self.filter_widget.objectName()] = self.filter_widget

        self.analysis_buttons = AnalysisButtonsWidget()
        self.input_layout.addLayout(self.analysis_buttons)
        self.input_layout.addStretch()

        self.mini_settings = mini.MiniWidget()
        self.setup_layout.addLayout(self.mini_settings)
        self._analysis_widgets[self.mini_settings.objectName()] = self.mini_settings

        # Setup for the drag and drop load layout
        self.analysis_type = "mini"
        self.load_widget = LoadAcqWidget(analysis_type=self.analysis_type)
        self.load_widget.signals.progress.connect(self.updateProgress)
        self.load_widget.signals.dir_path.connect(self.setWorkingDirectory)

        self.setup_layout.addLayout(self.load_widget, 0)

        self.setup_layout.addStretch(1)

        # Tab 2
        self.analysis_widget = mini.MiniAnalysisWidget()
        self.analysis_widget.error.connect(self.errorDialog)
        self.analysis_widget.clicked.connect(self.runFinalAnalysis)
        self.tab2_layout = QHBoxLayout()
        self.tab2.setLayout(self.tab2_layout)
        self.tab2_layout.addWidget(self.analysis_widget)

        # Tab 3 layouts and setup
        self.tab3_layout = QHBoxLayout()
        self.tab3.setLayout(self.tab3_layout)
        self.final_analysis = mini.FinalMiniAnalysis()
        self.tab3_layout.addWidget(self.final_analysis)

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
        self.pbar.setFormat("Finished analysis")
        self.tab_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

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
        for i in self._analysis_widgets.values():
            pref_dict[i.objectName()] = i.getAnalysisSettings()
        logger.info("Mini analysis preferences dictionary created.")
        return pref_dict
