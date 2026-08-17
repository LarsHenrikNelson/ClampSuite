import logging
from pathlib import PurePath
from typing import Union

import pyqtgraph as pg
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
)

from ..manager import ExpManager
from .gui_widgets import (
    AnalysisButtonsWidget,
    BaselineWidget,
    LoadAcqWidget,
    MainAnalysisWidget,
    ThreadWorker,
    current_clamp,
)

logger = logging.getLogger(__name__)


class CurrentClampWidget(MainAnalysisWidget):
    """
    This the currentClampAnalysis widget. The primary functions are carried
    out by the CurrentClamp class. The final analysis and output is done by
    functions contained within the currentClampAnalysis widget.
    """

    def __init__(self):
        super().__init__()
        self.initUI()

        # pg.setConfigOptions(antialias=True)

    def initUI(self):
        logger.info("Creating current clamp UI.")
        self.acq_dict = {}
        self.hertz_y = []
        self.deleted_acqs = {}
        self.pref_dict = {}
        self.recent_reject_acq = {}
        self.calc_param_clicked = False
        self.need_to_save = False
        self.final_obj = None
        self.plot_dict = {}
        self.table_dict = {}

        self.file.connect(self.loadPreferences)
        self.file_path.connect(self.loadExperiment)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_widget = QTabWidget()
        self.main_widget.setStyleSheet("""QTabWidget::tab-bar {alignment: left;}""")
        self.main_layout.addWidget(self.main_widget)

        self.setup_layout = QHBoxLayout()
        self.tab1.setLayout(self.setup_layout)
        self.acq_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.acq_layout, 0)
        self.v_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.v_layout)

        self._analysis_widgets = {}

        self.baseline_settings = BaselineWidget()
        self.v_layout.addWidget(self.baseline_settings)
        self._analysis_widgets[self.baseline_settings.objectName()] = (
            self.baseline_settings
        )

        self.cc_settings = current_clamp.CurrentClampSettingsWidget()
        self.v_layout.addWidget(self.cc_settings)
        self._analysis_widgets[self.cc_settings.objectName()] = self.cc_settings

        self.analysis_buttons = AnalysisButtonsWidget()
        self.v_layout.addLayout(self.analysis_buttons)

        self.v_layout.addStretch()
        self.setup_layout.addStretch(1)

        # Input widgets and labels (Tab 1)
        self.analysis_type = "current_clamp"
        self.load_widget = LoadAcqWidget(self.analysis_type)
        self.load_widget.signals.progress.connect(self.updateProgress)
        self.load_widget.signals.dir_path.connect(self.setWorkingDirectory)
        self.acq_layout.addLayout(self.load_widget)

        # Analysis layout setup (tab 2)
        self.tab2_layout = QHBoxLayout()
        self.tab2.setLayout(self.tab2_layout)

        self.analysis_widget = current_clamp.CurrentClampAnalysisWidget()
        self.tab2_layout.addWidget(self.analysis_widget)

        # Tab 3 layout
        self.tab3_layout = QHBoxLayout()
        self.tab3.setLayout(self.tab3_layout)
        self.final_analysis = current_clamp.FinalCurrentClampAnalysis()
        self.tab3_layout.addWidget(self.final_analysis)

        self.exp_manager.set_callback(self.updateProgress)
        self.load_widget.setData(self.exp_manager)

        self.pbar.setFormat("Ready to analyze")
        self.setWidth()
        logger.info("Current clamp UI created.")

    def setWidth(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if not isinstance(i.parentWidget(), QSpinBox):
                i.setMinimumWidth(80)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(100)

    def analyze(self):
        if not self.exp_manager.acqs_exist():
            logger.info("No acquisitions loaded, analysis ended.")
            self.errorDialog("No acquisitions loaded, analysis ended.")
            self.analyze_acq_button.setEnabled(True)
        else:
            logger.info("Analysis started.")
            self.need_to_save = True
            self.analyze_acq_button.setEnabled(False)
            self.pbar.setFormat("Analyzing...")
            self.pbar.setValue(0)
            self.worker = ThreadWorker(self.exp_manager)
            self.worker.addAnalysis(
                "analyze",
                exp="current_clamp",
                filter_args={
                    "baseline_start": self.b_start_edit.toInt(),
                    "baseline_end": self.b_end_edit.toInt(),
                    "filter_type": "None",
                },
                template_args=None,
                analysis_args={
                    "threshold": self.min_spike_threshold_edit.toInt(),
                    "min_spikes": self.min_spikes_edit.toInt(),
                    "threshold_method": self.threshold_method.currentText(),
                },
            )
            self.worker.signals.progress.connect(self.updateProgress)
            self.worker.signals.finished.connect(self.setAcquisition)
            logger.info("Starting analysis thread.")
            QThreadPool.globalInstance().start(self.worker)

    def setAcquisition(self):
        logger.info("Analysis finished.")
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)
        self.spinbox(self.exp_manager.start_acq)
        self.analyze_acq_button.setEnabled(True)
        self.main_widget.setCurrentIndex(1)
        self.pbar.setFormat("Analysis finished")
        logger.info("Firsts acquisition set.")

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist():
            logger.info("Did not run final analysis, no acquisitions analyzed.")
            self.errorDialog("Did not run final analysis, no acquisitions analyzed.")
            return None

        logger.info("Beginning final analysis.")
        self.need_to_save = True
        self.calc_param_clicked = True
        self.calculate_parameters.setEnabled(False)
        if self.exp_manager.final_analysis is not None:
            self.final_obj = None
            self.df_tabs.clear()
            self.plot_tabs.clear()
            self.clearPlots()
            self.clearTables()
            self.plot_dict = {}
            self.table_dict = {}
        self.pbar.setFormat("Analyzing...")
        logger.info("Experiment manager started final analysis")
        self.exp_manager.run_final_analysis(
            "current_clamp",
            iv_start=self.iv_start_edit.toInt(),
            iv_end=self.iv_end_edit.toInt(),
        )
        logger.info("Experiment manager finished final analysis.")
        self.calculate_parameters.setEnabled(True)
        self.main_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

    def createExperiment(self, urls):
        self.pbar.setFormat("Creating experiment")
        self.load_widget.addData(urls)
        self.pbar.setFormat("Experiment created")

    def loadExperiment(self, directory: Union[str, PurePath]):
        logger.info(f"Loading experiment from {directory}.")
        self.reset()
        self.pbar.setFormat("Loading...")
        self.analyze_acq_button.setEnabled(False)
        self.calculate_parameters.setEnabled(False)
        self.exp_manger = ExpManager()
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis(
            function="load",
            analysis="current_clamp",
            file_path=directory,
        )
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def setLoadData(self):
        self.load_widget.setData(self.exp_manager)
        if self.exp_manager.final_analysis is not None:
            logger.info("Setting previously analyzed data.")
            self.pbar.setFormat("Setting previously analyzed data.")
            fa = self.exp_manager.final_analysis
            for key, value in fa.df_dict.items():
                table = pg.TableWidget(sortable=False)
                table.setData(value.T.to_dict())
                self.table_dict["key"] = table
                self.df_tabs.addTab(table, key)
            self.plotIVCurve("Delta V (mV)")
            if "Voltage sag (mV)" in fa.df_dict.keys():
                self.plotIVCurve("Voltage sag (mV)")
            if fa.hertz:
                self.plotSpikeFrequency(fa.df_dict["Hertz"].copy())
            if fa.pulse_ap:
                self.plotAP(fa.df_dict["Pulse APs"].copy(), "Pulse")
            if fa.ramp_ap:
                self.plotAP(fa.df_dict["Ramp APs"].copy(), "Ramp")
            self.pbar.setFormat("Final data loaded")
        self.calculate_parameters.setEnabled(True)
        self.analyze_acq_button.setEnabled(True)
        self.acquisition_number.setEnabled(True)
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)
        self.spinbox(self.exp_manager.start_acq)
        logger.info("Experiment successfully loaded.")
        self.pbar.setFormat("Experiment successfully loaded")

    def setPreferences(self, pref_dict: dict):
        logger.info("Setting CurrentClamp preferences.")
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if i.objectName() != "":
                i.setText(pref_dict["line_edits"][i.objectName()])
        logger.info("Preferences set.")
        self.pbar.setFormat("Preferences set")

    def createPrefDict(self):
        logger.info("Creating preferences dictionary.")
        self.pbar.setFormat("Creating preferences dictionary.")
        pref_dict = {}
        for value in self._analysis_widgets.values():
            pref_dict[value.objectName()] = value.getAnalysisSettings()
        logger.info("Current clamp preferences dictionary created.")
        return pref_dict

    def saveAs(self, file_path: Union[str, PurePath]):
        if not self.exp_manager.acqs_exist():
            self.errorDialog("No data to save")
        else:
            logger.info("Saving experiment.")
            self.reset_button.setEnabled(False)
            self.pbar.setValue(0)
            self.pbar.setFormat("Saving...")
            pref_dict = self.createPrefDict()
            pref_dict["Final Analysis"] = self.calc_param_clicked
            pref_dict["Acq_number"] = self.acquisition_number.value()
            self.exp_manager.set_ui_prefs(pref_dict)
            self.worker = ThreadWorker(self.exp_manager)
            self.worker.addAnalysis("save", file_path=file_path)
            self.worker.signals.progress.connect(self.updateProgress)
            self.worker.signals.finished.connect(self.finishedSaving)
            QThreadPool.globalInstance().start(self.worker)
            self.reset_button.setEnabled(True)
            self.need_to_save = False
