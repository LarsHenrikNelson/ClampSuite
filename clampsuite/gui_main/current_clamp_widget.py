import logging
from pathlib import PurePath
from typing import Union

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..gui_widgets import (
    DragDropWidget,
    LoadAcqWidget,
    ThreadWorker,
    current_clamp,
    BaselineWidget,
    AnalysisButtonsWidget,
)
from ..manager import ExpManager

logger = logging.getLogger(__name__)


class currentClampWidget(DragDropWidget):
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

        self.signals.file.connect(self.loadPreferences)
        self.signals.file_path.connect(self.loadExperiment)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_widget = QTabWidget()
        self.main_widget.setStyleSheet("""QTabWidget::tab-bar {alignment: left;}""")
        self.main_layout.addWidget(self.main_widget)

        self.tab_1 = QWidget()
        self.main_widget.addTab(self.tab_1, "Setup")

        self.setup_layout = QHBoxLayout()
        self.tab_1.setLayout(self.setup_layout)
        self.acq_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.acq_layout, 0)
        self.v_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.v_layout)

        self.tab_2 = QWidget()
        self.main_widget.addTab(self.tab_2, "Analysis")
        self.h_layout = QHBoxLayout()
        self.tab_2.setLayout(self.h_layout)

        self._analysis_widgets = {}

        self.baseline_settings = BaselineWidget()
        self.v_layout.addWidget(self.baseline_settings)
        self._analysis_widgets[self.baseline_settings.objectName()] = (
            self.baseline_settings
        )

        self.cc_settings = current_clamp.CurrentClammpSettingsWidget()
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

        # Tab 3 layout
        self.tab3_dock = DockArea()
        self.df_dock = Dock("Data")
        self.tab3_dock.addDock(self.df_dock, "left")
        self.df_tabs = QTabWidget()
        self.df_tabs.setUsesScrollButtons(True)
        self.df_dock.addWidget(self.df_tabs)
        self.plot_dock = Dock("Plots")
        self.tab3_dock.addDock(self.plot_dock, "right")
        self.plot_tabs = QTabWidget()
        self.plot_tabs.setUsesScrollButtons(True)
        self.plot_dock.addWidget(self.plot_tabs)
        self.main_widget.addTab(self.tab3_dock, "Final data")
        self.plot_tabs.setStyleSheet("""QTabWidget::tab-bar {alignment: left;}""")
        self.df_tabs.setUsesScrollButtons(True)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.main_layout.addWidget(self.pbar, 0)

        self.exp_manager = ExpManager()
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
        if not self.exp_manager.acqs_exist("current_clamp"):
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
        if not self.exp_manager.acqs_exist("current_clamp"):
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
            iv_start=self.iv_start_edit.toInt(), iv_end=self.iv_end_edit.toInt()
        )
        logger.info("Experiment manager finished final analysis.")
        fi_an = self.exp_manager.final_analysis
        for key, value in fi_an.df_dict.items():
            table = pg.TableWidget(sortable=False)
            table.setData(value.T.to_dict())
            self.table_dict["key"] = table
            self.df_tabs.addTab(table, key)
        logger.info("Set final data into tables.")
        self.plotIVCurve("Delta V (mV)")
        self.plotIVCurve("Voltage sag (mV)")
        if fi_an.hertz:
            self.plotSpikeFrequency(fi_an.df_dict["Hertz"].copy())
        if fi_an.pulse_ap:
            self.plotAP(fi_an.df_dict["Pulse APs"].copy(), "Pulse")
        if fi_an.ramp_ap:
            self.plotAP(fi_an.df_dict["Ramp APs"].copy(), "Ramp")
        self.calculate_parameters.setEnabled(True)
        self.main_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

    def plotIVCurve(self, column: str):
        iv_curve_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict[f"{column} iv_curve_plot"] = iv_curve_plot
        self.plot_tabs.addTab(iv_curve_plot, f"{column} IV curve")
        fa = self.exp_manager.final_analysis
        deltav_df = fa.df_dict[column]
        iv_x = fa.df_dict[f"{column} IV x"]
        iv_y = fa.df_dict[f"{column} IV lines"]
        iv_curve_plot.addLegend()
        epochs = iv_y.columns.to_list()
        for i in epochs:
            if iv_x[i].isna().all():
                pass
            else:
                pencil = pg.mkPen(color=pg.Color(int(i)))
                brush = pg.mkBrush(color=pg.intColor(int(i)))
                iv_curve_plot.plot(iv_x[i].to_numpy(), iv_y[i].to_numpy(), pen=pencil)
                iv_curve_plot.plot(
                    deltav_df["Pulse amp (pA)"].to_numpy(),
                    deltav_df[i].to_numpy(),
                    pen=None,
                    symbol="o",
                    symbolPen=pencil,
                    symbolBrush=brush,
                    name=f"Epoch {i}",
                )

    def plotSpikeFrequency(self, hertz):
        spike_curve_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict["spike_curve_plot"] = spike_curve_plot
        self.plot_tabs.addTab(spike_curve_plot, "Spike curve")
        pulse_amp = hertz.pop("Pulse amp (pA)").to_numpy()
        plot_epochs = hertz.columns.to_list()
        spike_curve_plot.addLegend()
        for i in plot_epochs:
            pencil = pg.mkPen(color=pg.intColor(i))
            brush = pg.mkBrush(color=pg.intColor(i))
            spike_curve_plot.plot(
                pulse_amp,
                hertz[i].to_numpy(),
                symbol="o",
                pen=pencil,
                name=f"Epoch {i}",
                symbolPen=pencil,
                symbolBrush=brush,
            )

    def plotAP(self, df: pd.DataFrame, ap_type: str):
        pulse_ap_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict[f"{ap_type}_ap_plot"] = pulse_ap_plot
        self.plot_tabs.addTab(pulse_ap_plot, f"{ap_type} AP")
        pulse_ap_plot.addLegend()
        if len(df.columns) > 1:
            for i in df.columns:
                array = df[i].to_numpy()
                pencil = pg.mkPen(color=pg.intColor(i))
                pulse_ap_plot.plot(
                    np.arange(len(array)) / 10, array, pen=pencil, name=f"Epoch {i}"
                )
        else:
            i = df.columns[0]
            array = df[i]
            pulse_ap_plot.plot(np.arange(len(array)) / 10, array, name=f"Epoch {i}")

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

    def errorDialog(self, text):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText(text)
        self.dlg.exec()

    def saveAs(self, file_path: Union[str, PurePath]):
        if not self.exp_manager.acqs_exist("current_clamp"):
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

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def loadPreferences(self, file_name: Union[str, PurePath]):
        self.need_to_save = True
        load_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(load_dict)

    def savePreferences(self, fle_path: Union[str, PurePath]):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(fle_path, pref_dict)
        else:
            pass

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setFormat(f"Acquisition {value} analyzed")
            # self.pbar.setFormat(f"{value}")
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)

    def needToSave(self):
        return self.exp_manager.need_to_save
