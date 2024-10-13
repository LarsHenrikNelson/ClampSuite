import logging
from pathlib import PurePath
from typing import Union

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction, QFont, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..functions.utilities import round_sig
from ..gui_widgets import DragDropWidget, LineEdit, LoadAcqWidget, ThreadWorker
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
        self.tab_2 = QWidget()
        self.main_widget.addTab(self.tab_2, "Analysis")
        self.setup_layout = QHBoxLayout()
        self.h_layout = QHBoxLayout()
        self.tab_1.setLayout(self.setup_layout)
        self.tab_2.setLayout(self.h_layout)
        self.input_layout = QFormLayout()
        self.acq_layout = QVBoxLayout()
        self.setup_layout.addLayout(self.acq_layout, 0)
        self.setup_layout.addLayout(self.input_layout, 0)
        self.setup_layout.addStretch(1)
        self.plot_layout = QHBoxLayout()
        self.analysis_buttons = QFormLayout()
        self.h_layout.addLayout(self.plot_layout, 1)
        self.plot_layout.addLayout(self.analysis_buttons, 0)

        # Input widgets and labels (Tab 1)
        self.analysis_type = "current_clamp"
        self.load_widget = LoadAcqWidget(self.analysis_type)
        self.load_widget.signals.progress.connect(self.updateProgress)
        self.load_widget.signals.dir_path.connect(self.setWorkingDirectory)
        self.acq_layout.addLayout(self.load_widget)

        self.b_start_label = QLabel("Baseline start (ms)")
        self.b_start_edit = LineEdit()
        self.b_start_edit.setObjectName("b_start_edit")
        self.b_start_edit.setEnabled(True)
        self.b_start_edit.setText("0")
        self.input_layout.addRow(self.b_start_label, self.b_start_edit)

        self.b_end_label = QLabel("Baseline end (ms)")
        self.b_end_edit = LineEdit()
        self.b_end_edit.setObjectName("b_end_edit")
        self.b_end_edit.setEnabled(True)
        self.b_end_edit.setText("300")
        self.input_layout.addRow(self.b_end_label, self.b_end_edit)

        # self.pulse_start_label = QLabel("Pulse start (ms)")
        # self.pulse_start_edit = LineEdit()
        # self.pulse_start_edit.setObjectName("pulse_start_edit")
        # self.pulse_start_edit.setEnabled(True)
        # self.pulse_start_edit.setText("300")
        # self.input_layout.addRow(self.pulse_start_label, self.pulse_start_edit)

        # self.pulse_end_label = QLabel("Pulse end (ms)")
        # self.pulse_end_edit = LineEdit()
        # self.pulse_end_edit.setObjectName("pulse_end_edit")
        # self.pulse_end_edit.setEnabled(True)
        # self.pulse_end_edit.setText("1002")
        # self.input_layout.addRow(self.pulse_end_label, self.pulse_end_edit)

        # self.ramp_start_label = QLabel("Ramp start (ms)")
        # self.ramp_start_edit = LineEdit()
        # self.ramp_start_edit.setObjectName("ramp_start_edit")
        # self.ramp_start_edit.setEnabled(True)
        # self.ramp_start_edit.setText("300")
        # self.input_layout.addRow(self.ramp_start_label, self.ramp_start_edit)

        # self.ramp_end_label = QLabel("Ramp end (ms)")
        # self.ramp_end_edit = LineEdit()
        # self.ramp_end_edit.setObjectName("ramp_end_edit")
        # self.ramp_end_edit.setEnabled(True)
        # self.ramp_end_edit.setText("4000")
        # self.input_layout.addRow(self.ramp_end_label, self.ramp_end_edit)

        self.min_spike_threshold_label = QLabel("Min spike threshold (mV)")
        self.min_spike_threshold_edit = LineEdit()
        self.min_spike_threshold_edit.setObjectName("min_spike_threshold")
        self.min_spike_threshold_edit.setEnabled(True)
        self.min_spike_threshold_edit.setText("-15")
        self.input_layout.addRow(
            self.min_spike_threshold_label, self.min_spike_threshold_edit
        )

        self.threshold_method = QComboBox()
        methods = ["third_derivative", "max_curvature", "legacy"]
        self.threshold_method.addItems(methods)
        self.threshold_method.setMinimumContentsLength(len(max(methods, key=len)))

        self.threshold_method.setObjectName("threshold_method")
        self.input_layout.addRow("Threshold method", self.threshold_method)

        self.min_spikes_label = QLabel("Min spikes")
        self.min_spikes_edit = LineEdit()
        self.min_spikes_edit.setObjectName("min_spikes")
        self.min_spikes_edit.setText("1")
        self.min_spikes_edit.setValidator(QIntValidator())
        self.input_layout.addRow(self.min_spikes_label, self.min_spikes_edit)

        self.iv_start_label = QLabel("IV curve start")
        self.iv_start_edit = LineEdit()
        self.iv_start_edit.setObjectName("iv_start_edit")
        self.iv_start_edit.setText("1")
        self.input_layout.addRow(self.iv_start_label, self.iv_start_edit)

        self.iv_end_label = QLabel("IV curve end")
        self.iv_end_edit = LineEdit()
        self.iv_end_edit.setObjectName("iv_end_edit")
        self.iv_end_edit.setText("6")
        self.input_layout.addRow(self.iv_end_label, self.iv_end_edit)

        self.analyze_acq_button = QPushButton("Analyze acquisition(s)")
        self.analyze_acq_button.setObjectName("analyze_acq_button")
        self.input_layout.addRow(self.analyze_acq_button)
        self.analyze_acq_button.clicked.connect(self.analyze)

        self.calculate_parameters = QPushButton("Final analysis")
        self.calculate_parameters.setObjectName("calculate_parameters")
        self.input_layout.addRow(self.calculate_parameters)
        self.calculate_parameters.clicked.connect(self.runFinalAnalysis)

        self.reset_button = QPushButton("Reset analysis")
        self.input_layout.addRow(self.reset_button)
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setObjectName("reset_button")

        # Analysis layout setup (tab 2)
        self.acquisition_number_label = QLabel("Acq number")
        self.acquisition_number = QSpinBox()
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)
        self.acquisition_number.valueChanged.connect(self.spinbox)
        self.analysis_buttons.addRow(
            self.acquisition_number_label, self.acquisition_number
        )

        self.epoch_number = LineEdit()
        self.analysis_buttons.addRow("Epoch", self.epoch_number)
        self.epoch_number.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch_number.toText())
        )

        self.pulse_amp_num = LineEdit()
        self.analysis_buttons.addRow("Pulse amp", self.pulse_amp_num)
        self.pulse_amp_num.editingFinished.connect(
            lambda: self.editAttr("pulse_amp", self.pulse_amp_num.toFloat())
        )

        self.pulse_pattern = QLineEdit()
        self.pulse_pattern.editingFinished.connect(
            lambda: self.editAttr("pulse_pattern", self.pulse_pattern.text())
        )
        self.analysis_buttons.addRow("Pulse pattern", self.pulse_pattern)

        self.cycle = LineEdit()
        self.cycle.editingFinished.connect(
            lambda: self.editAttr("cycle", self.cycle.toInt())
        )
        self.analysis_buttons.addRow("Cycle", self.cycle)

        self.baseline_mean_edit = QLineEdit()
        self.analysis_buttons.addRow("Baseline mean (mV)", self.baseline_mean_edit)

        self.delta_v_edit = QLineEdit()
        self.analysis_buttons.addRow("Delta V (mV)", self.delta_v_edit)

        self.voltage_sag_edit = QLineEdit()
        self.analysis_buttons.addRow("Voltage sag (mV)", self.voltage_sag_edit)

        self.spike_threshold_edit = QLineEdit()
        self.analysis_buttons.addRow("Spike threshold (mV)", self.spike_threshold_edit)

        self.half_width_edit = QLineEdit()
        self.analysis_buttons.addRow("Half-width (ms)", self.half_width_edit)

        self.spike_rate_label = QLabel("Spike rate")
        self.spike_rate_edit = QLineEdit()
        self.analysis_buttons.addRow(self.spike_rate_label, self.spike_rate_edit)

        self.ahp_label = QLabel("AHP (mv)")
        self.ahp_edit = QLineEdit()
        self.analysis_buttons.addRow(self.ahp_label, self.ahp_edit)

        self.baseline_stability_label = QLabel("Baseline stability")
        self.baseline_stability_edit = QLineEdit()
        self.analysis_buttons.addRow(
            self.baseline_stability_label, self.baseline_stability_edit
        )

        self.set_spike_threshold = QPushButton("Set spike threshold")
        self.set_spike_threshold.clicked.connect(self.setSpikeThreshold)
        self.analysis_buttons.addRow(self.set_spike_threshold)

        self.delete_event_button = QPushButton("Delete acquisition")
        self.delete_event_button.clicked.connect(self.deleteAcq)
        self.analysis_buttons.addRow(self.delete_event_button)

        self.reset_recent_reject_button = QPushButton(
            "Reset recent rejected acquisition"
        )
        self.reset_recent_reject_button.clicked.connect(self.resetRecentRejectAcq)
        self.analysis_buttons.addRow(self.reset_recent_reject_button)

        self.reset_rejected_acqs_button = QPushButton("Reset rejected acquistions")
        self.reset_rejected_acqs_button.clicked.connect(self.resetRejectedAcqs)
        self.analysis_buttons.addRow(self.reset_rejected_acqs_button)

        self.calculate_params_2 = QPushButton("Final analysis")
        self.calculate_params_2.setObjectName("calculate_params_2")
        self.analysis_buttons.addRow(self.calculate_params_2)
        self.calculate_params_2.clicked.connect(self.runFinalAnalysis)

        self.tab2_dock = DockArea()
        self.plot_layout.addWidget(self.tab2_dock, 1)
        self.d1 = Dock("Acquisition")
        self.d2 = Dock("First spike")
        self.tab2_dock.addDock(self.d1, "left")
        self.tab2_dock.addDock(self.d2, "right")

        self.plot_widget = pg.PlotWidget(useOpenGL=True)
        self.plot_widget.setMinimumWidth(300)
        self.d1.addWidget(self.plot_widget)

        self.delete_acq_action = QAction("Delete acq")
        self.delete_acq_action.triggered.connect(self.deleteAcq)

        self.reset_recent_acq_action = QAction("Reset recent del acq")
        self.reset_recent_acq_action.triggered.connect(self.resetRecentRejectAcq)

        self.reset_acq_action = QAction("Reset del acq(s)")
        self.reset_acq_action.triggered.connect(self.resetRejectedAcqs)

        self.spike_plot = pg.PlotWidget(useOpenGL=True)
        self.spike_plot.setMinimumWidth(300)
        self.d2.addWidget(self.spike_plot)

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

        # Other UI
        vb = self.plot_widget.getViewBox()
        vb.menu.addSeparator()
        vb.menu.addAction(self.delete_acq_action)
        vb.menu.addAction(self.reset_recent_acq_action)
        vb.menu.addAction(self.reset_acq_action)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.main_layout.addWidget(self.pbar, 0)

        self.dlg = QMessageBox(self)

        self.last_acq_point_clicked = None

        self.exp_manager = ExpManager()
        self.exp_manager.set_callback(self.updateProgress)
        self.load_widget.setData(self.exp_manager)

        # Create PlotDataItems for easy reuse
        self.acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 0, 0, 0),
            symbolPen=(0, 0, 0, 0),
        )

        self.acq_plot.sigPointsClicked.connect(self.plotClicked)
        self.plot_widget.addItem(self.acq_plot)

        self.delta_v_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen="r",
        )
        self.plot_widget.addItem(self.delta_v_data)

        self.vsag_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen="#fcbb2f",
        )
        self.plot_widget.addItem(self.vsag_data)

        self.spike_peaks_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="y",
        )
        self.plot_widget.addItem(self.spike_peaks_data)

        self.ahp_acq_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="#E867E8",
        )
        self.plot_widget.addItem(self.ahp_acq_data)

        self.ahp_spike_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="m",
        )
        self.spike_plot.addItem(self.ahp_spike_data)

        self.st_data_spk_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.spike_plot.addItem(self.st_data_spk_plot)

        self.st_data_acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.plot_widget.addItem(self.st_data_acq_plot)

        self.spk_width_acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=pg.mkPen("g", width=4),
        )
        self.plot_widget.addItem(self.spk_width_acq_plot)

        self.spk_width_spk_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=pg.mkPen("g", width=4),
        )
        self.spike_plot.addItem(self.spk_width_spk_plot)

        self.clickable_spike_data = pg.PlotDataItem(
            x=[],
            y=[],
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 0, 0, 0),
            symbolPen=(0, 0, 0, 0),
        )
        self.clickable_spike_data.sigPointsClicked.connect(self.plotClicked)
        self.spike_plot.addItem(self.clickable_spike_data)

        self.spk_data_plots_cleared = True

        self.pbar.setFormat("Ready to analyze")
        self.setWidth()
        logger.info("Current clamp UI created.")

    def editAttr(self, line_edit, value):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return False
        else:
            logger.info(
                f"Editing aquisition attribute {self.acquisition_number.value()}."
            )
            acq = self.exp_manager.exp_dict["current_clamp"][
                self.acquisition_number.value()
            ]
            setattr(acq, line_edit, value)
            logger.info(
                f"Set {value} for {line_edit} on aquisition\
                    {self.acquisition_number.value()}."
            )
            return True

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

    def clearAcqPlots(self):
        if not self.spk_data_plots_cleared:
            self.spike_peaks_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="y",
            )
            self.spk_width_acq_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("g", width=4),
            )

            self.st_data_acq_plot.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="b",
            )

            self.ahp_acq_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="m",
            )

            self.clickable_spike_data.setData(
                x=[],
                y=[],
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.spk_width_spk_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("g", width=4),
            )

            self.st_data_spk_plot.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="b",
            )

            self.ahp_spike_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="m",
            )
            self.spk_data_plots_cleared = True

    def reset(self):
        logger.info("Resetting UI.")
        self.need_to_save = False
        self.acq_dict = {}
        self.load_widget.clearData()
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.deleted_acqs = {}
        self.recent_reject_acq = {}
        self.pref_dict = {}
        self.calc_param_clicked = False
        self.need_to_save = False
        self.df_tabs.clear()
        self.plot_tabs.clear()
        self.clearPlots()
        self.clearTables()
        self.plot_dict = {}
        self.table_dict = {}
        self.clearAcqPlots()
        self.acq_plot.setData(
            x=[],
            y=[],
            pen=pg.mkPen("w"),
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 0, 0, 0),
            symbolPen=(0, 0, 0, 0),
        )

        self.delta_v_data.setData(
            x=[],
            y=[],
            pen=pg.mkPen(color="r", width=2),
        )
        self.vsag_data.setData(
            x=[],
            y=[],
            pen=pg.mkPen(color="m", width=2),
        )
        self.exp_manager = ExpManager()
        self.last_acq_point_clicked = None
        self.load_widget.setData(self.exp_manager)
        self.pbar.setValue(0)
        self.pbar.setFormat("Ready to analyze")
        logger.info("UI Reset. Ready to analyze.")

    def clearPlots(self):
        for i in self.plot_dict.values():
            i.clear()
            i.hide()
            i.deleteLater()

    def clearTables(self):
        for i in self.table_dict.values():
            i.clear()
            i.hide()
            i.deleteLater()

    def spinbox(self, _):
        if not self.exp_manager.analyzed:
            logger.info(
                "No acquisitions analyzed,"
                f" acquisition {self.acquisition_number.value()} not set."
            )
            self.errorDialog(
                "No acquisitions analyzed,\n"
                f"acquisition {self.acquisition_number.value()} not set."
            )
            return None

        logger.info("Preparing UI for plotting.")
        self.acquisition_number.setEnabled(False)
        if self.last_acq_point_clicked:
            self.plot_widget.removeItem(self.last_acq_point_clicked[0])
            self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        self.need_to_save = True
        self.plot_widget.enableAutoRange()
        self.spike_plot.enableAutoRange()
        if (
            self.acquisition_number.value()
            in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"Plotting acquisition {self.acquisition_number.value()}.")
            acq_object = self.exp_manager.exp_dict["current_clamp"][
                self.acquisition_number.value()
            ]
            self.epoch_number.setText(acq_object.epoch)
            self.pulse_amp_num.setText(str(acq_object.pulse_amp))
            self.pulse_pattern.setText(acq_object.pulse_pattern)
            self.cycle.setText(str(acq_object.cycle))
            self.baseline_mean_edit.setText(
                str(round_sig(acq_object.baseline_mean, sig=4))
            )
            self.delta_v_edit.setText(str(round_sig(acq_object.delta_v, sig=4)))
            self.voltage_sag_edit.setText(str(round_sig(acq_object.voltage_sag, sig=4)))
            self.spike_threshold_edit.setText(
                str(round_sig(acq_object.spike_threshold, sig=4))
            )
            self.spike_rate_edit.setText(
                str(round_sig(acq_object.hertz_exact(), sig=4))
            )
            self.half_width_edit.setText(str(round_sig(acq_object.spike_width())))
            self.ahp_edit.setText(str(round_sig(acq_object.ahp_y, sig=4)))
            self.baseline_stability_edit.setText(
                str(round_sig(acq_object.baseline_stability, sig=4))
            )
            self.acq_plot.setData(
                x=acq_object.plot_acq_x(),
                y=acq_object.plot_acq_y(),
                pen=pg.mkPen("w"),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.delta_v_data.setData(
                x=acq_object.plot_deltav_x(),
                y=acq_object.plot_deltav_y(),
                pen=pg.mkPen(color="r", width=2),
            )

            self.vsag_data.setData(
                x=acq_object.plot_voltage_sag_x(),
                y=acq_object.plot_voltage_sag_y(),
                pen=pg.mkPen(color="m", width=2),
            )
            if not np.isnan(acq_object.peaks[0]):
                self.spike_peaks_data.setData(
                    x=acq_object.spike_peaks_x(),
                    y=acq_object.spike_peaks_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="y",
                )
                self.spk_width_acq_plot.setData(
                    x=acq_object.spike_width_x(),
                    y=acq_object.spike_width_y(),
                    pen=pg.mkPen("g", width=4),
                )

                self.st_data_acq_plot.setData(
                    x=acq_object.plot_st_x(),
                    y=acq_object.plot_st_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="b",
                )

                self.ahp_acq_data.setData(
                    x=acq_object.plot_ahp_x(),
                    y=acq_object.plot_ahp_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="m",
                )

                self.clickable_spike_data.setData(
                    x=acq_object.spike_x_array(),
                    y=acq_object.first_ap,
                    symbol="o",
                    symbolSize=8,
                    symbolBrush=(0, 0, 0, 0),
                    symbolPen=(0, 0, 0, 0),
                )

                self.spk_width_spk_plot.setData(
                    x=acq_object.spike_width_x(),
                    y=acq_object.spike_width_y(),
                    pen=pg.mkPen("g", width=4),
                )

                self.st_data_spk_plot.setData(
                    x=acq_object.plot_st_x(),
                    y=acq_object.plot_st_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="b",
                )

                self.ahp_spike_data.setData(
                    x=acq_object.plot_ahp_x(),
                    y=acq_object.plot_ahp_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="m",
                )
                self.spk_data_plots_cleared = False
            else:
                self.clearAcqPlots()
        else:
            self.clearAcqPlots()
            self.acq_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("w"),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.delta_v_data.setData(
                x=[],
                y=[],
                pen="r",
            )
            self.vsag_data.setData(
                x=[],
                y=[],
                pen="m",
            )
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.plot_widget.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.plot_widget.addItem(text)
        self.acquisition_number.setEnabled(True)

    def plotClicked(self, item, points):
        logger.info(
            f"Current clamp acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_acq_point_clicked:
            self.plot_widget.removeItem(self.last_acq_point_clicked[0])
            self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        acq_point_clicked = pg.PlotDataItem(
            x=[points[0].pos()[0]],
            y=[points[0].pos()[1]],
            pen=None,
            symbol="o",
            symbolPen=pg.mkPen("#E867E8", width=3),
        )
        self.plot_widget.addItem(acq_point_clicked)
        self.last_acq_point_clicked = (acq_point_clicked, points[0].pos())

        spike_point_clicked = pg.PlotDataItem(
            x=[points[0].pos()[0]],
            y=[points[0].pos()[1]],
            pen=None,
            symbol="o",
            symbolPen=pg.mkPen("#E867E8", width=3),
        )
        self.spike_plot.addItem(spike_point_clicked)
        self.last_spike_point_clicked = (spike_point_clicked, points[0].pos())

        logger.info(f"Point {self.last_spike_point_clicked[1][0]} clicked.")

    def setSpikeThreshold(self):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return None

        if self.last_acq_point_clicked is None:
            logger.info("No point was selected, peak not set.")
            self.errorDialog("No point was selected, peak not set.")
            return None

        acq = self.exp_manager.exp_dict["current_clamp"][
            self.acquisition_number.value()
        ]
        self.need_to_save = True
        x = self.last_acq_point_clicked[1][0]
        y = self.last_acq_point_clicked[1][1]
        acq.set_spike_threshold(x, y)

        self.plot_widget.removeItem(self.last_acq_point_clicked[0])
        self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        self.st_data_spk_plot.setData(
            x=acq.plot_st_x(),
            y=acq.plot_st_y(),
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.st_data_acq_plot.setData(
            x=acq.plot_st_x(),
            y=acq.plot_st_y(),
            pen=None,
            symbol="o",
            symbolBrush="b",
        )

        self.spk_width_acq_plot.setData(
            x=acq.spike_width_x(),
            y=acq.spike_width_y(),
            pen=pg.mkPen("g", width=4),
        )

        self.spk_width_spk_plot.setData(
            x=acq.spike_width_x(),
            y=acq.spike_width_y(),
            pen=pg.mkPen("g", width=4),
        )

        logger.info(f"Spike threshold set {self.acquisition_number.value()}.")

    def deleteAcq(self):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return None

        logger.info(f"Deleting acquisition {self.acquisition_number.value()}.")
        self.need_to_save = False
        self.exp_manager.delete_acq("current_clamp", self.acquisition_number.value())

        # Clear plots
        self.plot_widget.clear()
        logger.info(f"Deleted acquisition {self.acquisition_number.value()}.")

    def resetRejectedAcqs(self):
        if not self.exp_manager.acqs_exist("current_clamp"):
            logger.info("Did not reset acquistions, no acquisitions exist.")
            self.errorDialog("Did not reset acquistions, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting deleted acquisitions.")
            self.exp_manager.reset_deleted_acqs("current_clamp")
            logger.info("Deleted acquisitions reset.")
            self.pbar.setFormat("Reset deleted acquisitions.")

    def resetRecentRejectAcq(self):
        if not self.exp_manager.acqs_exist("current_clamp"):
            logger.info("Did not reset recent acquistion, no acquisitions exist.")
            self.errorDialog("Did not reset recent acquistion, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting most recent deleted acquisition.")
            number = self.exp_manager.reset_recent_deleted_acq("current_clamp")
            if number != 0:
                self.acquisition_number.setValue(number)
                logger.info(f"Acquisition {number} reset.")
                self.pbar.setFormat(f"Reset acquisition {number}.")
            else:
                logger.info("No acquisition to reset.")
                self.pbar.setFormat("No acquisition to reset.")

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
        line_edits = self.findChildren(QLineEdit)
        line_edit_dict = {}
        for i in line_edits:
            if i.objectName() != "":
                line_edit_dict[i.objectName()] = i.text()
        pref_dict["line_edits"] = line_edit_dict
        combo_box_dict = {}
        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            if i.objectName() != "":
                combo_box_dict[i.objectName()] = i.currentText()
        pref_dict["combo_boxes"] = combo_box_dict
        logger.info("Preferences dictionary created.")
        self.pbar.setFormat("Preferences dictionary created.")
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
