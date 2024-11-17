import logging
from collections import namedtuple

import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..gui_widgets import (
    AnalysisButtonsWidget,
    BaselineWidget,
    FilterWidget,
    LoadAcqWidget,
    MainAnalysisWidget,
    QExpManager,
    ThreadWorker,
    evoked_lfp,
    evoked_psc,
)
from ..gui_widgets.qtwidgets import FrameWidget

XAxisCoord = namedtuple("XAxisCoord", ["x_min", "x_max"])

logger = logging.getLogger(__name__)


class EvokedPSCLFPWidget(MainAnalysisWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.exp_manager = QExpManager()

        self.initUI()

    def initUI(self):
        logger.info("Creating oEPSC/LFP GUI")
        self.file.connect(self.loadPreferences)
        self.file_path.connect(self.loadExperiment)
        self.setStyleSheet(
            """QTabWidget::tab-bar 
                                          {alignment: left;}"""
        )

        # Tab 1 layout
        self.tab1_layout = QVBoxLayout()
        self.tab1.setLayout(self.tab1_layout)

        self.widget_layout = QHBoxLayout()
        self.tab1_layout.addLayout(self.widget_layout)

        self._psc_analysis_widgets = {}

        self.psc_widget = FrameWidget(title="Evoked PSC")
        self.psc_layout = QHBoxLayout()
        self.psc_widget.setLayout(self.psc_layout)
        self.widget_layout.addWidget(self.psc_widget)

        self.psc_load_widget = LoadAcqWidget(analysis_type="oepsc")
        self.psc_layout.addLayout(self.psc_load_widget)

        self.psc_settings_layout = QVBoxLayout()
        self.psc_layout.addLayout(self.psc_settings_layout)

        self.psc_baseline_widget = BaselineWidget()
        self.psc_settings_layout.addWidget(self.psc_baseline_widget)
        self._psc_analysis_widgets[self.psc_baseline_widget.objectName()] = (
            self.psc_baseline_widget
        )

        self.psc_filter_widget = FilterWidget()
        self.psc_settings_layout.addWidget(self.psc_filter_widget)
        self._psc_analysis_widgets[self.psc_filter_widget.objectName()] = (
            self.psc_filter_widget
        )
        self.evoked_psc_settings = evoked_psc.EvokedPSCSettingsWidget()
        self.psc_settings_layout.addWidget(self.evoked_psc_settings)
        self._psc_analysis_widgets[self.evoked_psc_settings.objectName()] = (
            self.evoked_psc_settings
        )

        # LFP input
        self._lfp_analysis_widgets = {}

        self.lfp_widget = FrameWidget(title="Evoked LFP")
        self.lfp_layout = QHBoxLayout()
        self.lfp_widget.setLayout(self.lfp_layout)
        self.widget_layout.addWidget(self.lfp_widget)

        self.lfp_load_widget = LoadAcqWidget(analysis_type="oepsc")
        self.lfp_layout.addLayout(self.lfp_load_widget)

        self.lfp_settings_layout = QVBoxLayout()
        self.lfp_layout.addLayout(self.lfp_settings_layout)

        self.lfp_baseline_widget = BaselineWidget()
        self.lfp_settings_layout.addWidget(self.lfp_baseline_widget)
        self._lfp_analysis_widgets[self.lfp_baseline_widget.objectName()] = (
            self.lfp_baseline_widget
        )

        self.lfp_filter_widget = FilterWidget()
        self.lfp_settings_layout.addWidget(self.lfp_filter_widget)
        self._lfp_analysis_widgets[self.lfp_filter_widget.objectName()] = (
            self.lfp_filter_widget
        )
        self.evoked_lfp_settings = evoked_lfp.EvokedLFPSettings()
        self.lfp_settings_layout.addWidget(self.evoked_lfp_settings)
        self._lfp_analysis_widgets[self.evoked_lfp_settings.objectName()] = (
            self.evoked_lfp_settings
        )

        self.lfp_settings_layout.addStretch()

        self.analysis_buttons = AnalysisButtonsWidget()
        self.tab1_layout.addLayout(self.analysis_buttons)

        # Tab 2 layout)
        self.tab2_layout = QHBoxLayout()
        self.tab2.setLayout(self.tab2_layout)

        self.tab2_dock = DockArea()
        self.tab2_layout.addWidget(self.tab2_dock)

        self.psc_dock = Dock("Evoked PSC")
        self.tab2_dock.addDock(self.psc_dock, "left")
        self.psc_analysis = evoked_psc.EvokedPSCAnalysisWidget()
        self.psc_dock.addWidget(self.psc_analysis)

        self.lfp_dock = Dock("Evoked LFP")
        self.tab2_dock.addDock(self.lfp_dock, "right")
        self.lfp_analysis = evoked_lfp.EvokedLFPAnalysisWidget()
        self.lfp_dock.addWidget(self.lfp_analysis)

        self.dlg = QMessageBox(self)

        self.choose_analysis_type = QMessageBox()
        self.choose_analysis_type.setText("Choose analysis type")
        self.oepsc_type_button = self.choose_analysis_type.addButton(
            "Evoked PSC", QMessageBox.ActionRole
        )
        self.lfp_type_button = self.choose_analysis_type.addButton(
            "Evoked LFP", QMessageBox.ActionRole
        )

        self.setWidth()

        # Lists
        self.exp_manager = QExpManager()
        self.exp_manager.set_callback(self.updateProgress)
        self.table_dict = {}
        self.calc_param_clicked = False
        self.need_to_save = False

        logger.info("Event oEPSC/LFP GUI created.")

    def setWidth(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if not isinstance(i.parentWidget(), QSpinBox):
                i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(80)

    def analyze(self):
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("No acquisitions, analysis ended.")
            self.fileDoesNotExist()
            return None

        logger.info("Analysis started.")
        self.pbar.setFormat("Analyzing...")
        self.pbar.setValue(0)

        self.on_x_set = False
        self.op_x_set = False
        lfp_x_set = False
        self.need_to_save = True
        if (
            self.o_window_edit.currentText() == "gaussian"
            or self.o_window_edit.currentText() == "kaiser"
        ):
            o_window = (self.o_window_edit.currentText(), self.o_beta_sigma.value())
        else:
            o_window = self.o_window_edit.currentText()
        if (
            self.lfp_window_edit.currentText() == "gaussian"
            or self.lfp_window_edit.currentText() == "kaiser"
        ):
            lfp_window = (
                self.lfp_window_edit.currentText(),
                self.lfp_beta_sigma.value(),
            )
        else:
            lfp_window = self.lfp_window_edit.currentText()
        threadpool = QThreadPool().globalInstance()
        worker = ThreadWorker(self.exp_manager)
        if self.exp_manager.acqs_exist("oepsc"):
            worker.addAnalysis(
                "analyze",
                exp="oepsc",
                filter_args={
                    "baseline_start": self.o_b_start_edit.toFloat(),
                    "baseline_end": self.o_b_end_edit.toFloat(),
                    "filter_type": self.o_filter_selection.currentText(),
                    "order": self.o_order_edit.toInt(),
                    "high_pass": self.o_high_pass_edit.toFloat(),
                    "high_width": self.o_high_width_edit.toFloat(),
                    "low_pass": self.o_low_pass_edit.toFloat(),
                    "low_width": self.o_low_width_edit.toFloat(),
                    "window": o_window,
                    "polyorder": self.o_polyorder_edit.toFloat(),
                },
                template_args=None,
                analysis_args={
                    "pulse_start": self.o_pulse_start_edit.toFloat(),
                    "n_window_start": self.o_neg_start_edit.toFloat(),
                    "n_window_end": self.o_neg_end_edit.toFloat(),
                    "p_window_start": self.o_pos_start_edit.toFloat(),
                    "p_window_end": self.o_pos_end_edit.toFloat(),
                    "find_ct": self.charge_transfer_edit.isChecked(),
                    "find_est_decay": self.est_decay_edit.isChecked(),
                    "curve_fit_decay": self.curve_fit_decay.isChecked(),
                    "curve_fit_type": self.curve_fit_type_edit.currentText(),
                },
            )
        if self.exp_manager.acqs_exist("lfp"):
            worker.addAnalysis(
                "analyze",
                exp="lfp",
                filter_args={
                    "baseline_start": self.lfp_b_start_edit.toFloat(),
                    "baseline_end": self.lfp_b_end_edit.toFloat(),
                    "filter_type": self.lfp_filter_selection.currentText(),
                    "order": self.lfp_order_edit.toInt(),
                    "high_pass": self.lfp_high_pass_edit.toFloat(),
                    "high_width": self.lfp_high_width_edit.toFloat(),
                    "low_pass": self.lfp_low_pass_edit.toFloat(),
                    "low_width": self.lfp_low_width_edit.toFloat(),
                    "window": lfp_window,
                    "polyorder": self.lfp_polyorder_edit.toFloat(),
                },
                template_args=None,
                analysis_args={
                    "pulse_start": self.lfp_pulse_start_edit.toFloat(),
                },
            )
        worker.signals.progress.connect(self.updateProgress)
        worker.signals.finished.connect(self.setAcquisition)
        threadpool.start(worker)
        if not lfp_x_set:
            self.lfp_x_axis = XAxisCoord(
                self.lfp_pulse_start_edit.toInt() - 10,
                self.lfp_b_start_edit.toInt() + 250,
            )

    def setAcquisition(self):
        if QThreadPool.globalInstance().activeThreadCount() == 0:
            self.psc_analysis.setAcquisition()
            self.lfp_analysis.setAcquisition()
            self.tabs.setCurrentIndex(1)
            logger.info("Analysis finished.")
            self.pbar.setFormat("Analysis finished")

    def reset(self):
        logger.info("Reseting UI.")
        self.oepsc_plot.clear()
        self.lfp_plot.clear()
        self.tab3.clear()
        self.clearTables()
        self.calc_param_clicked = False
        self.inspection_widget.removeFileList()
        self.exp_manager = QExpManager()
        self.need_to_save = False
        self.pbar.setFormat("Ready to analyze")
        self.pbar.setValue(0)
        self.tabs.setCurrentIndex(0)
        logger.info("UI reset.")

    def clearTables(self):
        for i in self.table_dict.values():
            i.clear()
            i.hide()
            i.deleteLater()
        self.table_dict = {}

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("Did not run final analysis, no acquisitions analyzed.")
            self.fileDoesNotExist(
                "Did not run final analysis, no acquisitions analyzed."
            )
            return None
        logger.info("Beginning final analysis.")
        self.need_to_save = True
        self.final_analysis_button.setEnabled(False)
        self.calc_param_clicked = True
        self.exp_manager.run_final_analysis()
        fa = self.exp_manager.final_analysis
        for key, df in fa.df_dict.items():
            table = pg.TableWidget()
            self.table_dict[key] = table
            self.tab3.addTab(table, key)
            table.setData(df.T.to_dict("dict"))
        self.final_analysis_button.setEnabled(True)
        self.tabs.setCurrentIndex(2)
        self.pbar.setFormat("Final analysis finished")

    def saveAs(self, file_path):
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("There is no data to save")
            self.fileDoesNotExist("There is no data to save")
            return None
        logger.info("Saving experiment.")
        self.pbar.setValue(0)
        self.pbar.setFormat("Saving...")
        pref_dict = self.createPrefDict()
        pref_dict["Acq_number"] = self.acquisition_number.value()

        pref_dict["Final Analysis"] = self.calc_param_clicked
        self.exp_manager.set_ui_prefs(pref_dict)
        self.pbar_count = 0
        self.pbar.setFormat("Saving files...")
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis("save", file_path=file_path)
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.finishedSaving)
        QThreadPool.globalInstance().start(self.worker)
        self.pbar.setFormat("Data saved")
        self.need_to_save = False

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def loadExperiment(self, directory):
        logger.info(f"Loading experiment from {directory}.")
        self.reset()
        self.pbar.setFormat("Loading...")
        self.pbar.setValue(0)
        self.exp_manager = QExpManager()
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis(function="load", analysis="oepsc", file_path=directory)
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def createExperiment(self, urls):
        self.pbar.setFormat("Creating experiment")
        self.choose_analysis_type.exec()
        if self.choose_analysis_type.clickedButton() == self.oepsc_type_button:
            self.pbar.setFormat("oEPSC experiment created")
        else:
            self.pbar.setFormat("LFP experiment created")

    def setLoadData(self):
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            self.acquisition_number.setMaximum(self.exp_manager.start_acq)
            self.acquisition_number.setMinimum(self.exp_manager.end_acq)
        if self.exp_manager.ui_prefs:
            self.setPreferences(self.exp_manager.ui_prefs)
        if self.exp_manager.acqs_exist("oepsc"):
            self.set_peak_button.setEnabled(True)
            self.delete_oepsc_button.setEnabled(True)
        if self.exp_manager.acqs_exist("lfp"):
            self.delete_lfp_button.setEnabled(True)
            self.set_fv_button.setEnabled(True)
            self.set_fp_button.setEnabled(True)
            self.lfp_x_axis = XAxisCoord(
                self.lfp_pulse_start_edit.toInt() - 10,
                self.lfp_b_start_edit.toInt() + 250,
            )
        self.acquisition_number.setValue(self.exp_manager.start_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setEnabled(True)
        fa = self.exp_manager.final_analysis
        if fa is not None:
            logger.info("Setting previously analyzed data.")
            self.pbar.setFormat("Setting previously analyzed data.")
            for key, df in fa.df_dict.items():
                table = pg.TableWidget()
                self.table_dict[key] = table
                self.tab3.addTab(table, key)
                table.setData(df.T.to_dict("dict"))
        self.pbar.setFormat("Data loaded")
        self.analyze_acq_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.acquisition_number.setEnabled(True)
        self.final_analysis_button.setEnabled(True)
        logger.info("Experiment successfullzsy loaded.")
        self.pbar.setFormat("Experiment successfully loaded")

    def createPrefDict(self):
        logger.info("Creating preferences dictionary.")
        lfp_pref_dict = {}
        for i in self._lfp_analysis_widgets.values():
            lfp_pref_dict[i.objectName()] = i.getAnalysisSettings()
        psc_pref_dict = {}
        for i in self._psc_analysis_widgets.values():
            psc_pref_dict[i.objectName()] = i.getAnalysisSettings()
        pref_dict = {"lfp": lfp_pref_dict, "psc": psc_pref_dict}
        logger.info(f"{self.widget_name} preferences dictionary created.")
        return pref_dict

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setFormat(f"Acquisition {value} analyzed")
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def fileDoesNotExist(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        # self.dlg.setText("No files are loaded or analyzed")
        self.dlg.exec()

    def loadPreferences(self):
        pass

    def needToSave(self):
        return self.exp_manager.need_to_save
