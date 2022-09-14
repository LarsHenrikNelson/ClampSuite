from collections import namedtuple
from glob import glob
import json
from math import log10, floor, isnan, nan
from pathlib import Path

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QProgressBar,
    QMessageBox,
    QTabWidget,
    QScrollArea,
    QDoubleSpinBox,
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtCore import QThreadPool
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
import pyqtgraph as pg

from .acq_inspection import AcqInspectionWidget
from ..final_analysis.final_evoked import FinalEvokedCurrent
from ..gui_widgets.qtwidgets import (
    LineEdit,
    SaveWorker,
    YamlWorker,
    ListModel,
    ListView,
    DragDropWidget,
)
from ..acq.acq import Acq
from ..load_analysis.load_classes import LoadEvokedCurrentData

XAxisCoord = namedtuple("XAxisCoord", ["x_min", "x_max"])


class oEPSCWidget(DragDropWidget):
    def __init__(self):

        super().__init__()

        self.initUI()

    def initUI(self):

        self.signals.dictionary.connect(self.set_preferences)
        self.signals.path.connect(self.open_files)
        self.parent_layout = QVBoxLayout()
        self.main_layout = QHBoxLayout()
        self.parent_layout.addLayout(self.main_layout)
        self.setLayout(self.parent_layout)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        self.pbar.setFormat("")
        self.parent_layout.addWidget(self.pbar)
        self.tab1 = QWidget()
        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setWidget(self.tab1)
        self.tab2_scroll = QScrollArea()
        self.tab2_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab2_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab2_scroll.setWidgetResizable(True)
        self.tab2 = QWidget()
        self.tab2_scroll.setWidget(self.tab2)
        self.tab3 = QTabWidget()
        self.tabs.addTab(self.tab1, "Setup")
        self.tabs.addTab(self.tab2_scroll, "Analysis")
        self.tabs.addTab(self.tab3, "Final Data")

        self.setStyleSheet(
            """QTabWidget::tab-bar 
                                          {alignment: left;}"""
        )

        # Tab 1 layout
        self.tab1_layout = QVBoxLayout()
        self.form_layouts = QHBoxLayout()
        self.view_layout_1 = QVBoxLayout()
        self.view_layout_2 = QVBoxLayout()
        self.input_layout_1 = QFormLayout()
        self.input_layout_3 = QFormLayout()
        self.input_layout_2 = QFormLayout()
        self.oepsc_view = ListView()
        self.oepsc_model = ListModel()
        self.oepsc_view.setModel(self.oepsc_model)
        self.oepsc_analysis = "oepsc"
        self.oepsc_model.setAnalysisType(self.oepsc_analysis)
        self.view_layout_1.addWidget(self.oepsc_view)
        self.inspect_oepsc_acqs = QPushButton("Inspect acquistions")
        self.inspect_oepsc_acqs.clicked.connect(
            lambda checked: self.inspect_acqs(self.oepsc_model)
        )
        self.view_layout_1.addWidget(self.inspect_oepsc_acqs)
        self.del_oepsc_sel = QPushButton("Delete selection")
        self.del_oepsc_sel.clicked.connect(
            lambda checked: self.delSelection(self.oepsc_model, self.oepsc_view)
        )
        self.view_layout_1.addWidget(self.del_oepsc_sel)
        self.form_layouts.addLayout(self.view_layout_1)
        self.form_layouts.addLayout(self.input_layout_1)
        self.form_layouts.addLayout(self.input_layout_3)
        self.lfp_view = ListView()
        self.lfp_model = ListModel()
        self.lfp_view.setModel(self.lfp_model)
        self.lfp_analysis = "lfp"
        self.lfp_model.setAnalysisType(self.lfp_analysis)
        self.view_layout_2.addWidget(self.lfp_view)
        self.inspect_lfp_acqs = QPushButton("Inspect acquistions")
        self.inspect_lfp_acqs.clicked.connect(
            lambda checked: self.inspect_acqs(self.lfp_model)
        )
        self.view_layout_2.addWidget(self.inspect_lfp_acqs)
        self.del_lfp_sel = QPushButton("Delete selection")
        self.del_lfp_sel.clicked.connect(
            lambda checked: self.delSelection(self.lfp_model, self.lfp_view)
        )
        self.view_layout_2.addWidget(self.del_lfp_sel)
        self.form_layouts.addLayout(self.view_layout_2)
        self.form_layouts.addLayout(self.input_layout_2)
        self.tab1.setLayout(self.tab1_layout)
        self.tab1_layout.addLayout(self.form_layouts, 0)

        # Tab 2 layout
        self.tab2_layout = QHBoxLayout()
        self.analysis_buttons_layout = QFormLayout()
        self.tab2_layout.addLayout(self.analysis_buttons_layout)
        self.tab2.setLayout(self.tab2_layout)

        # Tab 3 Layout
        self.raw_datatable = pg.TableWidget(sortable=False)
        self.tab3.addTab(self.raw_datatable, "Raw data")
        self.final_datatable = pg.TableWidget(sortable=False)
        self.tab3.addTab(self.final_datatable, "Final data")

        # Plots
        self.oepsc_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        self.oepsc_plot.setObjectName("oEPSC plot")
        self.oepsc_plot.setAutoVisible(y=True)
        self.oepsc_plot.setMinimumWidth(500)
        self.oepsc_plot.sigXRangeChanged.connect(lambda: self.getXRange("oepsc_plot"))

        self.lfp_plot = pg.PlotWidget(
            labels={"left": "Amplitude (mV)", "bottom": "Time (ms)"}
        )
        self.lfp_plot.setObjectName("LFP plot")
        self.lfp_plot.setMinimumWidth(500)
        self.lfp_plot.setAutoVisible(y=True)
        self.lfp_plot.sigXRangeChanged.connect(lambda: self.getXRange("lfp_plot"))

        self.oepsc_plot_layout = QHBoxLayout()
        self.lfp_plot_layout = QHBoxLayout()
        self.o_info_layout = QFormLayout()
        self.lfp_info_layout = QFormLayout()
        self.plot_layout = QHBoxLayout()
        self.oepsc_plot_layout.addLayout(self.o_info_layout, 0)
        self.oepsc_plot_layout.addWidget(self.oepsc_plot, 1)
        self.lfp_plot_layout.addLayout(self.lfp_info_layout, 0)
        self.lfp_plot_layout.addWidget(self.lfp_plot, 1)
        self.plot_layout.addLayout(self.oepsc_plot_layout, 1)
        self.plot_layout.addLayout(self.lfp_plot_layout, 1)
        self.tab2_layout.addLayout(self.plot_layout, 1)

        # oEPSC buttons and line edits
        self.oepsc_input = QLabel("oEPSC")
        self.input_layout_1.addRow(self.oepsc_input)

        self.o_b_start_label = QLabel("Baseline start")
        self.o_b_start_edit = LineEdit()
        self.o_b_start_edit.setEnabled(True)
        self.o_b_start_edit.setObjectName("o_b_start_edit")
        self.o_b_start_edit.setText("850")
        self.input_layout_1.addRow(self.o_b_start_label, self.o_b_start_edit)

        self.o_b_end_label = QLabel("Baseline end")
        self.o_b_end_edit = LineEdit()
        self.o_b_end_edit.setEnabled(True)
        self.o_b_end_edit.setObjectName("o_b_end_edit")
        self.o_b_end_edit.setText("950")
        self.input_layout_1.addRow(self.o_b_end_label, self.o_b_end_edit)

        self.o_sample_rate_label = QLabel("Sample rate")
        self.o_sample_rate_edit = LineEdit()
        self.o_sample_rate_edit.setEnabled(True)
        self.o_sample_rate_edit.setObjectName("o_sample_rate_edit")
        self.o_sample_rate_edit.setText("10000")
        self.input_layout_1.addRow(self.o_sample_rate_label, self.o_sample_rate_edit)

        self.o_filter_type_label = QLabel("Filter Type")
        filters = [
            "remez_2",
            "remez_1",
            "fir_zero_2",
            "fir_zero_1",
            "savgol",
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
            "None",
        ]
        self.o_filter_selection = QComboBox()
        self.o_filter_selection.addItems(filters)
        self.o_filter_selection.setObjectName("o_filter_selection")
        self.o_filter_selection.setCurrentText("savgol")
        self.input_layout_1.addRow(self.o_filter_type_label, self.o_filter_selection)
        self.o_filter_selection.currentTextChanged.connect(self.setOFiltProp)

        self.o_order_label = QLabel("Order")
        self.o_order_edit = LineEdit()
        self.o_order_edit.setValidator(QIntValidator())
        self.o_order_edit.setEnabled(True)
        self.o_order_edit.setObjectName("o_order_edit")
        self.o_order_edit.setText("5")
        self.input_layout_1.addRow(self.o_order_label, self.o_order_edit)

        self.o_high_pass_label = QLabel("High-pass")
        self.o_high_pass_edit = LineEdit()
        self.o_high_pass_edit.setValidator(QIntValidator())
        self.o_high_pass_edit.setObjectName("o_high_pass_edit")
        self.o_high_pass_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_high_pass_label, self.o_high_pass_edit)

        self.o_high_width_label = QLabel("High-width")
        self.o_high_width_edit = LineEdit()
        self.o_high_width_edit.setValidator(QIntValidator())
        self.o_high_width_edit.setObjectName("o_high_width_edit")
        self.o_high_width_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_high_width_label, self.o_high_width_edit)

        self.o_low_pass_label = QLabel("Low-pass")
        self.o_low_pass_edit = LineEdit()
        self.o_low_pass_edit.setValidator(QIntValidator())
        self.o_low_pass_edit.setObjectName("o_low_pass_edit")
        self.o_low_pass_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_low_pass_label, self.o_low_pass_edit)

        self.o_low_width_label = QLabel("Low-width")
        self.o_low_width_edit = LineEdit()
        self.o_low_width_edit.setValidator(QIntValidator())
        self.o_low_width_edit.setObjectName("o_low_width_edit")
        self.o_low_width_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_low_width_label, self.o_low_width_edit)

        self.o_window_label = QLabel("Window type")
        windows = [
            "hann",
            "hamming",
            "blackmmaharris",
            "barthann",
            "nuttall",
            "blackman",
            "tukey",
            "kaiser",
            "gaussian",
            "parzen",
            "exponential",
        ]
        self.o_window_edit = QComboBox(self)
        self.o_window_edit.setObjectName("o_window_edit")
        self.o_window_edit.addItems(windows)
        self.input_layout_1.addRow(self.o_window_label, self.o_window_edit)
        self.o_window_edit.currentTextChanged.connect(self.oWindowChanged)

        self.o_beta_sigma_label = QLabel("Beta/Sigma")
        self.o_beta_sigma = QDoubleSpinBox()
        self.o_beta_sigma.setObjectName("o_beta_sigma")
        self.input_layout_1.addRow(self.o_beta_sigma_label, self.o_beta_sigma)

        self.o_polyorder_label = QLabel("Polyorder")
        self.o_polyorder_edit = LineEdit()
        self.o_polyorder_edit.setValidator(QIntValidator())
        self.o_polyorder_edit.setEnabled(True)
        self.o_polyorder_edit.setObjectName("o_polyorder_edit")
        self.o_polyorder_edit.setText("3")
        self.input_layout_1.addRow(self.o_polyorder_label, self.o_polyorder_edit)

        self.o_pulse_start = QLabel("Pulse start")
        self.o_pulse_start_edit = LineEdit()
        self.o_pulse_start_edit.setValidator(QDoubleValidator())
        self.o_pulse_start_edit.setEnabled(True)
        self.o_pulse_start_edit.setObjectName("o_pulse_start_edit")
        self.o_pulse_start_edit.setText("1000")
        self.input_layout_1.addRow(self.o_pulse_start, self.o_pulse_start_edit)

        self.input_layout_3.addRow(QLabel(""), QLabel(""))

        self.o_neg_window_start = QLabel("Negative window start")
        self.o_neg_start_edit = LineEdit()
        self.o_neg_start_edit.setValidator(QDoubleValidator())
        self.o_neg_start_edit.setEnabled(True)
        self.o_neg_start_edit.setObjectName("o_pulse_start_edit")
        self.o_neg_start_edit.setText("1001")
        self.input_layout_3.addRow(self.o_neg_window_start, self.o_neg_start_edit)

        self.o_neg_window_end = QLabel("Negative window end")
        self.o_neg_end_edit = LineEdit()
        self.o_neg_end_edit.setValidator(QDoubleValidator())
        self.o_neg_end_edit.setObjectName("o_neg_end_edit")
        self.o_neg_end_edit.setEnabled(True)
        self.o_neg_end_edit.setText("1050")
        self.input_layout_3.addRow(self.o_neg_window_end, self.o_neg_end_edit)

        self.o_pos_window_start = QLabel("Positive window start")
        self.o_pos_start_edit = LineEdit()
        self.o_pos_start_edit.setValidator(QDoubleValidator())
        self.o_pos_start_edit.setEnabled(True)
        self.o_pos_start_edit.setObjectName("o_pos_start_edit")
        self.o_pos_start_edit.setText("1045")
        self.input_layout_3.addRow(self.o_pos_window_start, self.o_pos_start_edit)

        self.o_pos_window_end = QLabel("Positive window end")
        self.o_pos_end_edit = LineEdit()
        self.o_pos_end_edit.setValidator(QDoubleValidator())
        self.o_pos_end_edit.setEnabled(True)
        self.o_pos_end_edit.setObjectName("o_pos_end_edit")
        self.o_pos_end_edit.setText("1055")
        self.input_layout_3.addRow(self.o_pos_window_end, self.o_pos_end_edit)

        self.charge_transfer_label = QLabel("Charge transfer")
        self.charge_transfer_edit = QCheckBox(self)
        self.charge_transfer_edit.setObjectName("charge_transfer")
        self.charge_transfer_edit.setChecked(False)
        self.charge_transfer_edit.setTristate(False)
        self.input_layout_3.addRow(
            self.charge_transfer_label, self.charge_transfer_edit
        )

        self.est_decay_label = QLabel("Est decay")
        self.est_decay_edit = QCheckBox(self)
        self.est_decay_edit.setObjectName("est_decay")
        self.est_decay_edit.setChecked(False)
        self.est_decay_edit.setTristate(False)
        self.input_layout_3.addRow(self.est_decay_label, self.est_decay_edit)

        self.curve_fit_decay_label = QLabel("Curve fit decay")
        self.curve_fit_decay = QCheckBox(self)
        self.curve_fit_decay.setObjectName("curve_fit_decay")
        self.curve_fit_decay.setChecked(False)
        self.curve_fit_decay.setTristate(False)
        self.input_layout_3.addRow(self.curve_fit_decay_label, self.curve_fit_decay)

        self.curve_fit_type_label = QLabel("Curve fit type")
        fit_types = ["s_exp", "db_exp"]
        self.curve_fit_type_edit = QComboBox(self)
        self.curve_fit_type_edit.addItems(fit_types)
        self.curve_fit_type_edit.setObjectName("curve_fit_type")
        self.input_layout_3.addRow(self.curve_fit_type_label, self.curve_fit_type_edit)

        # LFP input
        self.lfp_input = QLabel("LFP")
        self.input_layout_2.addRow(self.lfp_input)

        self.lfp_b_start_label = QLabel("Baseline start")
        self.lfp_b_start_edit = LineEdit()
        self.lfp_b_start_edit.setEnabled(True)
        self.lfp_b_start_edit.setObjectName("lfp_b_start_edit")
        self.lfp_b_start_edit.setText("850")
        self.input_layout_2.addRow(self.lfp_b_start_label, self.lfp_b_start_edit)

        self.lfp_b_end_label = QLabel("Baseline end")
        self.lfp_b_end_edit = LineEdit()
        self.lfp_b_end_edit.setEnabled(True)
        self.lfp_b_end_edit.setObjectName("lfp_b_end_edit")
        self.lfp_b_end_edit.setText("950")
        self.input_layout_2.addRow(self.lfp_b_end_label, self.lfp_b_end_edit)

        self.lfp_sample_rate_label = QLabel("Sample rate")
        self.lfp_sample_rate_edit = LineEdit()
        self.lfp_sample_rate_edit.setEnabled(True)
        self.lfp_sample_rate_edit.setObjectName("lfp_sample_rate_edit")
        self.lfp_sample_rate_edit.setText("10000")
        self.input_layout_2.addRow(
            self.lfp_sample_rate_label, self.lfp_sample_rate_edit
        )

        self.lfp_filter_type_label = QLabel("Filter Type")
        filters = [
            "remez_2",
            "remez_1",
            "fir_zero_2",
            "fir_zero_1",
            "savgol",
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
            "None",
        ]
        self.lfp_filter_selection = QComboBox(self)
        self.lfp_filter_selection.addItems(filters)
        self.lfp_filter_selection.setObjectName("lfp_filter_selection")
        self.lfp_filter_selection.setCurrentText("savgol")
        self.input_layout_2.addRow(
            self.lfp_filter_type_label, self.lfp_filter_selection
        )
        # This has to be added after the labels it changes
        self.lfp_filter_selection.currentTextChanged.connect(self.setlFiltProp)

        self.lfp_order_label = QLabel("Order")
        self.lfp_order_edit = LineEdit()
        self.lfp_order_edit.setValidator(QIntValidator())
        self.lfp_order_edit.setEnabled(True)
        self.lfp_order_edit.setObjectName("lfp_order_edit")
        self.lfp_order_edit.setText("5")
        self.input_layout_2.addRow(self.lfp_order_label, self.lfp_order_edit)

        self.lfp_high_pass_label = QLabel("High-pass")
        self.lfp_high_pass_edit = LineEdit()
        self.lfp_high_pass_edit.setValidator(QIntValidator())
        self.lfp_high_pass_edit.setObjectName("lfp_high_pass_edit")
        self.lfp_high_pass_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_high_pass_label, self.lfp_high_pass_edit)

        self.lfp_high_width_label = QLabel("High-width")
        self.lfp_high_width_edit = LineEdit()
        self.lfp_high_width_edit.setValidator(QIntValidator())
        self.lfp_high_width_edit.setObjectName("lfp_high_width_edit")
        self.lfp_high_width_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_high_width_label, self.lfp_high_width_edit)

        self.lfp_low_pass_label = QLabel("Low-pass")
        self.lfp_low_pass_edit = LineEdit()
        self.lfp_low_pass_edit.setValidator(QIntValidator())
        self.lfp_low_pass_edit.setObjectName("lfp_low_pass_edit")
        self.lfp_low_pass_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_low_pass_label, self.lfp_low_pass_edit)

        self.lfp_low_width_label = QLabel("Low-width")
        self.lfp_low_width_edit = LineEdit()
        self.lfp_low_width_edit.setValidator(QIntValidator())
        self.lfp_low_width_edit.setObjectName("lfp_low_width_edit")
        self.lfp_low_width_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_low_width_label, self.lfp_low_width_edit)

        self.lfp_window_label = QLabel("Window type")
        windows = [
            "hann",
            "hamming",
            "blackmmaharris",
            "barthann",
            "nuttall",
            "blackman",
            "tukey",
            "kaiser",
            "gaussian",
            "parzen",
            "exponential",
        ]
        self.lfp_window_edit = QComboBox(self)
        self.lfp_window_edit.addItems(windows)
        self.lfp_window_edit.setObjectName("lfp_window_edit")
        self.input_layout_2.addRow(self.lfp_window_label, self.lfp_window_edit)
        self.lfp_window_edit.currentTextChanged.connect(self.lWindowChanged)

        self.lfp_beta_sigma_label = QLabel("Beta/Sigma")
        self.lfp_beta_sigma = QDoubleSpinBox()
        self.lfp_beta_sigma.setObjectName("lfp_beta_sigma")
        self.input_layout_2.addRow(self.lfp_beta_sigma_label, self.lfp_beta_sigma)

        self.lfp_polyorder_label = QLabel("Polyorder")
        self.lfp_polyorder_edit = LineEdit()
        self.lfp_polyorder_edit.setValidator(QIntValidator())
        self.lfp_polyorder_edit.setObjectName("lfp_polyorder_edit")
        self.lfp_polyorder_edit.setEnabled(True)
        self.lfp_polyorder_edit.setText("3")
        self.input_layout_2.addRow(self.lfp_polyorder_label, self.lfp_polyorder_edit)

        self.lfp_pulse_start = QLabel("Pulse start")
        self.lfp_pulse_start_edit = LineEdit()
        self.lfp_pulse_start_edit.setEnabled(True)
        self.lfp_pulse_start_edit.setObjectName("lfp_pulse_start_edit")
        self.lfp_pulse_start_edit.setText("1000")
        self.input_layout_2.addRow(self.lfp_pulse_start, self.lfp_pulse_start_edit)

        # Tab1 buttons
        self.analyze_acq_button = QPushButton("Analyze acquisitions")
        self.tab1_layout.addWidget(self.analyze_acq_button)
        self.analyze_acq_button.clicked.connect(self.analyze)

        self.reset_button = QPushButton("Reset analysis")
        self.tab1_layout.addWidget(self.reset_button)
        self.reset_button.clicked.connect(self.reset)

        # Analysis layout
        self.acquisition_number_label = QLabel("Acq number")
        self.acquisition_number = QSpinBox()
        self.acquisition_number.valueChanged.connect(self.acqSpinbox)
        self.o_info_layout.addRow(
            self.acquisition_number_label, self.acquisition_number
        )
        self.acquisition_number.setEnabled(False)

        self.epoch_label = QLabel("Epoch")
        self.epoch_number = QLineEdit()
        self.o_info_layout.addRow(self.epoch_label, self.epoch_number)

        self.final_analysis_button = QPushButton("Final analysis")
        self.o_info_layout.addRow(self.final_analysis_button)
        self.final_analysis_button.clicked.connect(self.final_analysis)
        self.final_analysis_button.setEnabled(False)

        self.oepsc_amp_label = QLabel("Amplitude")
        self.oepsc_amp_edit = QLineEdit()
        self.o_info_layout.addRow(self.oepsc_amp_label, self.oepsc_amp_edit)

        self.oepsc_charge_label = QLabel("Charge transfer")
        self.oepsc_charge_edit = QLineEdit()
        self.o_info_layout.addRow(self.oepsc_charge_label, self.oepsc_charge_edit)

        self.oepsc_edecay_label = QLabel("Est decay")
        self.oepsc_edecay_edit = QLineEdit()
        self.o_info_layout.addRow(self.oepsc_edecay_label, self.oepsc_edecay_edit)

        self.oepsc_fdecay_label = QLabel("Fit decay")
        self.oepsc_fdecay_edit = QLineEdit()
        self.o_info_layout.addRow(self.oepsc_fdecay_label, self.oepsc_fdecay_edit)

        self.set_peak_button = QPushButton("Set point as peak")
        self.set_peak_button.clicked.connect(self.set_oepsc_peak)
        self.o_info_layout.addRow(self.set_peak_button)
        self.set_peak_button.setEnabled(False)

        self.delete_oepsc_button = QPushButton("Delete oEPSC")
        self.delete_oepsc_button.clicked.connect(self.delete_oepsc)
        self.o_info_layout.addRow(self.delete_oepsc_button)
        self.delete_oepsc_button.setEnabled(False)

        self.lfp_fv_label = QLabel("Fiber volley")
        self.lfp_fv_edit = QLineEdit()
        self.lfp_info_layout.addRow(self.lfp_fv_label, self.lfp_fv_edit)

        self.lfp_fp_label = QLabel("Field potential")
        self.lfp_fp_edit = QLineEdit()
        self.lfp_info_layout.addRow(self.lfp_fp_label, self.lfp_fp_edit)

        self.lfp_fp_slope_label = QLabel("FP slope")
        self.lfp_fp_slope_edit = QLineEdit()
        self.lfp_info_layout.addRow(self.lfp_fp_slope_label, self.lfp_fp_slope_edit)

        self.set_fv_button = QPushButton("Set point as fiber volley")
        self.set_fv_button.clicked.connect(self.set_point_as_fv)
        self.lfp_info_layout.addRow(self.set_fv_button)
        self.set_fv_button.setEnabled(False)

        self.set_fp_button = QPushButton("Set point as field potential")
        self.set_fp_button.clicked.connect(self.set_point_as_fp)
        self.lfp_info_layout.addRow(self.set_fp_button)
        self.set_fp_button.setEnabled(False)

        self.delete_lfp_button = QPushButton("Delete LFP")
        self.delete_lfp_button.clicked.connect(self.delete_lfp)
        self.lfp_info_layout.addRow(self.delete_lfp_button)
        self.delete_lfp_button.setEnabled(False)

        self.threadpool = QThreadPool()
        self.set_width()

        # Lists
        self.last_oepsc_point_clicked = []
        self.last_lfp_point_clicked = []
        self.oepsc_acq_dict = {}
        self.lfp_acq_dict = {}
        self.last_lfp_point_clicked = []
        self.last_oepsc_point_clicked = []
        self.oepsc_acqs_deleted = 0
        self.lfp_acqs_deleted = 0
        self.pref_dict = {}
        self.deleted_lfp_acqs = {}
        self.deleted_opesc_acqs = {}
        self.calc_param_clicked = False
        self.final_data = None
        self.inspection_widget = None
        self.need_to_save = False

    def set_width(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(100)

    def inspect_acqs(self, list_model):
        # Creates a separate window to view the loaded acquisitions
        if self.inspection_widget is None:
            self.inspection_widget = AcqInspectionWidget()
            self.inspection_widget.setFileList(list_model.acq_dict)
            self.inspection_widget.show()
        else:
            self.inspection_widget.close()
            self.inspection_widget = None

    def oWindowChanged(self, text):
        if text == "Gaussian":
            self.o_beta_sigma_label.setText("Sigma")
        else:
            self.o_beta_sigma_label.setText("Beta")

    def setOFiltProp(self, text):
        if text == "median":
            self.o_order_label.setText("Window size")
        elif text == "savgol":
            self.o_order_label.setText("Window size")
            self.o_polyorder_label.setText("Polyorder")
        elif text == "ewma":
            self.o_order_label.setText("Window size")
            self.o_polyorder_label.setText("Sum proportion")
        else:
            self.o_order_label.setText("Order")
            self.o_polyorder_label.setText("Polyorder")

    def lWindowChanged(self, text):
        if text == "Gaussian":
            self.lfp_beta_sigma_label.setText("Sigma")
        else:
            self.lfp_beta_sigma_label.setText("Beta")

    def setlFiltProp(self, text):
        if text == "median":
            self.lfp_order_label.setText("Window size")
        elif text == "savgol":
            self.lfp_order_label.setText("Window size")
            self.lfp_polyorder_label.setText("Polyorder")
        elif text == "ewma":
            self.lfp_order_label.setText("Window size")
            self.lfp_polyorder_label.setText("Sum proportion")
        else:
            self.lfp_order_label.setText("Order")
            self.lfp_polyorder_label.setText("Polyorder")

    def delSelection(self, list_model, list_view):
        # Deletes the selected acquisitions from the list
        indexes = list_view.selectedIndexes()
        if len(indexes) > 0:
            list_model.deleteSelection(indexes)
            list_view.clearSelection()

    def getXRange(self, plot):
        h = str(self.acquisition_number.text())
        if plot == "oepsc_plot":
            x = self.oepsc_plot.viewRange()[0]
            if self.oepsc_acq_dict.get(h):
                self.setOPlotX(x)
            else:
                pass
        elif plot == "lfp_plot":
            x = self.lfp_plot.viewRange()[0]
            if self.lfp_acq_dict.get(h):
                self.setLFPPlotX(x)
            else:
                pass

    def setOPlotX(self, x):
        peak_dir = self.oepsc_acq_dict[
            str(self.acquisition_number.text())
        ].peak_direction
        if peak_dir == "positive":
            self.op_x_axis = XAxisCoord(x[0], x[1])
        else:
            self.on_x_axis = XAxisCoord(x[0], x[1])

    def setLFPPlotX(self, x):
        self.lfp_x_axis = XAxisCoord(x[0], x[1])

    def analyze(self):
        on_x_set = False
        op_x_set = False
        lfp_x_set = False
        self.need_to_save = True
        if self.oepsc_acq_dict or self.lfp_acq_dict:
            self.oepsc_acq_dict = {}
            self.lfp_acq_dict = {}
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
        if not self.oepsc_model.acq_dict and not self.lfp_model.acq_dict:
            self.file_does_not_exist()
        if self.oepsc_model.acq_dict:
            self.set_peak_button.setEnabled(True)
            self.delete_oepsc_button.setEnabled(True)
            self.oepsc_acq_dict = self.oepsc_model.acq_dict
            for count, o_acq in enumerate(self.oepsc_acq_dict.values()):
                o_acq.analyze(
                    sample_rate=self.o_sample_rate_edit.toInt(),
                    baseline_start=self.o_b_start_edit.toFloat(),
                    baseline_end=self.o_b_end_edit.toFloat(),
                    filter_type=self.o_filter_selection.currentText(),
                    order=self.o_order_edit.toInt(),
                    high_pass=self.o_high_pass_edit.toInt(),
                    high_width=self.o_high_width_edit.toInt(),
                    low_pass=self.o_low_pass_edit.toInt(),
                    low_width=self.o_low_width_edit.toInt(),
                    window=o_window,
                    polyorder=self.o_polyorder_edit.toInt(),
                    pulse_start=self.o_pulse_start_edit.toInt(),
                    n_window_start=self.o_neg_start_edit.toFloat(),
                    n_window_end=self.o_neg_end_edit.toFloat(),
                    p_window_start=self.o_pos_start_edit.toFloat(),
                    p_window_end=self.o_pos_end_edit.toFloat(),
                    find_ct=self.charge_transfer_edit.isChecked(),
                    find_est_decay=self.est_decay_edit.isChecked(),
                    curve_fit_decay=self.curve_fit_decay.isChecked(),
                    curve_fit_type=self.curve_fit_type_edit.currentText(),
                )
                if not on_x_set and o_acq.peak_direction == "negative":
                    self.on_x_axis = XAxisCoord(
                        self.o_pulse_start_edit.toInt() - 100,
                        self.o_pulse_start_edit.toInt() + 450,
                    )
                    on_x_set = True
                elif not op_x_set and o_acq.peak_direction == "positive":
                    self.op_x_axis = XAxisCoord(
                        self.o_pulse_start_edit.toInt() - 100,
                        o_acq.x_array[-1],
                    )
                    op_x_set = True
        if self.lfp_model.acq_dict:
            self.delete_lfp_button.setEnabled(True)
            self.set_fv_button.setEnabled(True)
            self.set_fp_button.setEnabled(True)
            self.lfp_acq_dict = self.lfp_model.acq_dict
            for count, lfp_acq in enumerate(self.lfp_acq_dict.values()):
                lfp_acq.analyze(
                    sample_rate=self.lfp_sample_rate_edit.toInt(),
                    baseline_start=self.lfp_b_start_edit.toFloat(),
                    baseline_end=self.lfp_b_end_edit.toFloat(),
                    filter_type=self.lfp_filter_selection.currentText(),
                    order=self.lfp_order_edit.toInt(),
                    high_pass=self.lfp_high_pass_edit.toInt(),
                    high_width=self.lfp_high_width_edit.toInt(),
                    low_pass=self.lfp_low_pass_edit.toInt(),
                    low_width=self.lfp_low_width_edit.toInt(),
                    window=lfp_window,
                    polyorder=self.lfp_polyorder_edit.toInt(),
                    pulse_start=self.lfp_pulse_start_edit.toFloat(),
                )
                if not lfp_x_set:
                    self.lfp_x_axis = XAxisCoord(
                        self.lfp_pulse_start_edit.toInt() - 10,
                        self.lfp_b_start_edit.toInt() + 250,
                    )
        # self.pbar.setValue(int(((count+1)/len(self.analysis_list))*100))
        if self.oepsc_acq_dict:
            acq_number = list(self.oepsc_acq_dict.keys())
        else:
            acq_number = list(self.lfp_acq_dict.keys())
        self.acquisition_number.setMaximum(int(acq_number[-1]))
        self.acquisition_number.setMinimum(int(acq_number[0]))
        self.acquisition_number.setValue(int(acq_number[0]))
        self.acqSpinbox(int(acq_number[0]))
        self.analyze_acq_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.acquisition_number.setEnabled(True)
        self.final_analysis_button.setEnabled(True)
        self.pbar.setFormat("Analysis finished")

    def acqSpinbox(self, h):
        self.need_to_save = True
        self.acquisition_number.setDisabled(True)
        self.oepsc_plot.clear()
        self.lfp_plot.clear()
        self.last_oepsc_point_clicked = []
        self.last_lfp_point_clicked = []
        if self.oepsc_acq_dict.get(str(h)):
            self.oepsc_object = self.oepsc_acq_dict[str(self.acquisition_number.text())]
            self.oepsc_acq_plot = pg.PlotDataItem(
                x=self.oepsc_object.x_array,
                y=self.oepsc_object.filtered_array,
                name=str("oepsc_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.oepsc_peak_plot = pg.PlotDataItem(
                x=self.oepsc_object.plot_x_comps(),
                y=self.oepsc_object.plot_y_comps(),
                symbol="o",
                symbolSize=8,
                symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
                pen=None,
            )
            self.oepsc_acq_plot.sigPointsClicked.connect(self.oepsc_plot_clicked)
            self.oepsc_plot.addItem(self.oepsc_acq_plot)
            self.oepsc_plot.addItem(self.oepsc_peak_plot)
            if self.oepsc_object.peak_direction == "negative":
                self.oepsc_plot.setXRange(
                    self.on_x_axis.x_min, self.on_x_axis.x_max, padding=0
                )
            else:
                self.oepsc_plot.setXRange(
                    self.op_x_axis.x_min, self.op_x_axis.x_max, padding=0
                )
            self.oepsc_plot.enableAutoRange(axis="y")
            self.oepsc_plot.setAutoVisible(y=True)
            self.oepsc_amp_edit.setText(str(self.round_sig(self.oepsc_object.peak_y)))
            if self.oepsc_object.find_ct:
                self.oepsc_charge_edit.setText(
                    str(self.round_sig((self.oepsc_object.charge_transfer)))
                )
        else:
            pass
        if self.lfp_acq_dict.get(str(h)):
            self.lfp_object = self.lfp_acq_dict[str(self.acquisition_number.text())]
            self.lfp_acq_plot = pg.PlotDataItem(
                x=self.lfp_object.x_array,
                y=self.lfp_object.filtered_array,
                name=str("lfp_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=10,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.lfp_points = pg.PlotDataItem(
                x=self.lfp_object.plot_elements_x(),
                y=self.lfp_object.plot_elements_y(),
                symbol="o",
                symbolSize=8,
                symbolBrush="m",
                pen=None,
            )
            if self.lfp_object.reg_line is not np.nan:
                self.lfp_reg = pg.PlotDataItem(
                    x=self.lfp_object.plot_slope_x(),
                    y=self.lfp_object.reg_line,
                    pen=pg.mkPen(color="g", width=4),
                    name="reg_line",
                )
            self.lfp_acq_plot.sigPointsClicked.connect(self.lfp_plot_clicked)
            self.lfp_plot.addItem(self.lfp_acq_plot)
            self.lfp_plot.addItem(self.lfp_points)
            self.lfp_plot.addItem(self.lfp_reg)
            self.lfp_plot.setXRange(
                self.lfp_x_axis.x_min, self.lfp_x_axis.x_max, padding=0
            )
            self.lfp_plot.enableAutoRange(axis="y")
            self.lfp_plot.setAutoVisible(y=True)
            self.lfp_fv_edit.setText(str(self.round_sig(self.lfp_object.fv_y)))
            self.lfp_fp_edit.setText(str(self.round_sig(self.lfp_object.fp_y)))
            self.lfp_fp_slope_edit.setText(str(self.round_sig(self.lfp_object.slope)))
        else:
            pass
        if self.oepsc_acq_dict.get(str(h)):
            self.epoch_number.setText(self.oepsc_object.epoch)
        elif self.lfp_acq_dict.get(str(h)):
            self.epoch_number.setText(self.lfp_object.epoch)
        else:
            pass
        self.acquisition_number.setEnabled(True)

    def reset(self):
        self.oepsc_plot.clear()
        self.lfp_plot.clear()
        self.oepsc_acq_dict = {}
        self.lfp_acq_dict = {}
        del self.final_data
        self.oepsc_acqs_deleted = 0
        self.lfp_acqs_deleted = 0
        self.deleted_lfp_acqs = {}
        self.deleted_opesc_acqs = {}
        self.calc_param_clicked = False
        self.analyze_acq_button.setEnabled(True)
        self.lfp_info_layout.setEnabled(False)
        self.delete_oepsc_button.setEnabled(False)
        self.acquisition_number.setEnabled(False)
        self.final_analysis_button.setEnabled(False)
        self.set_fv_button.setEnabled(False)
        self.set_fp_button.setEnabled(False)
        self.final_data = None
        self.oepsc_model.clearData()
        self.lfp_model.clearData()
        self.need_to_save = False
        self.pbar.setFormat("Ready to analyze")
        self.pbar.setValue(0)

    def oepsc_plot_clicked(self, item, points):
        if len(self.last_oepsc_point_clicked) > 0:
            self.last_oepsc_point_clicked[0].resetPen()
            self.last_oepsc_point_clicked[0].resetBrush()
            self.last_oepsc_point_clicked[0].setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_oepsc_point_clicked = points

    def lfp_plot_clicked(self, item, points):
        if len(self.last_lfp_point_clicked) > 0:
            self.last_lfp_point_clicked[0].resetPen()
            self.last_lfp_point_clicked[0].resetBrush()
            self.last_lfp_point_clicked[0].setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_lfp_point_clicked = points

    def set_point_as_fv(self):
        """
        This will set the LFP fiber volley as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        self.need_to_save = True
        x = (
            self.last_lfp_point_clicked[0].pos()[0]
            * self.lfp_acq_dict[self.acquisition_number.text()].s_r_c
        )
        y = self.last_lfp_point_clicked[0].pos()[1]
        self.lfp_acq_dict[self.acquisition_number.text()].change_fv(x, y)
        self.lfp_points.setData(
            x=self.lfp_object.plot_elements_x(),
            y=self.lfp_object.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if self.lfp_object.slope is not np.nan:
            self.lfp_reg.setData(
                x=self.lfp_object.plot_slope_x(),
                y=self.lfp_object.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fv_edit.setText(str(self.round_sig(self.lfp_object.fv_y)))
        self.last_lfp_point_clicked[0].resetPen()
        self.last_lfp_point_clicked[0].resetBrush()
        self.last_lfp_point_clicked = []

    def set_point_as_fp(self):
        """
        This will set the LFP field potential as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        self.need_to_save = True
        x = (
            self.last_lfp_point_clicked[0].pos()[0]
            * self.lfp_acq_dict[self.acquisition_number.text()].s_r_c
        )
        y = self.last_lfp_point_clicked[0].pos()[1]
        self.lfp_acq_dict[self.acquisition_number.text()].change_fp(x, y)
        self.lfp_points.setData(
            x=self.lfp_acq_dict[self.acquisition_number.text()].plot_elements_x(),
            y=self.lfp_acq_dict[self.acquisition_number.text()].plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if self.lfp_object.slope is not np.nan:
            self.lfp_reg.setData(
                x=self.lfp_object.plot_slope_x(),
                y=self.lfp_object.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fp_edit.setText(str(self.round_sig(self.lfp_object.fp_y)))
        self.lfp_fp_slope_edit.setText(str(self.round_sig(self.lfp_object.slope)))
        self.last_lfp_point_clicked[0].resetPen()
        self.last_lfp_point_clicked[0].resetBrush()
        self.last_lfp_point_clicked = []

    def set_oepsc_peak(self):
        self.need_to_save = True
        x = (
            self.last_oepsc_point_clicked[0].pos()[0]
            * self.oepsc_acq_dict[self.acquisition_number.text()].s_r_c
        )
        y = self.last_oepsc_point_clicked[0].pos()[1]
        self.oepsc_acq_dict[self.acquisition_number.text()].change_peak(x, y)
        self.oepsc_peak_plot.setData(
            x=self.oepsc_acq_dict[self.acquisition_number.text()].plot_x_comps(),
            y=self.oepsc_acq_dict[self.acquisition_number.text()].plot_y_comps(),
            symbol="o",
            symbolSize=8,
            symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
            pen=None,
        )
        self.oepsc_amp_edit.setText(
            str(
                self.round_sig(
                    self.oepsc_acq_dict[self.acquisition_number.text()].peak_y
                )
            )
        )
        self.last_oepsc_point_clicked[0].resetPen()
        self.last_oepsc_point_clicked[0].resetBrush()
        self.last_oepsc_point_clicked = []

    def delete_oepsc(self):
        self.need_to_save = True
        self.oepsc_plot.clear()
        self.deleted_opesc_acqs[
            str(self.acquisition_number.text())
        ] = self.oepsc_acq_dict[str(self.acquisition_number.text())]
        del self.oepsc_acq_dict[str(self.acquisition_number.text())]
        self.oepsc_acqs_deleted += 1

    def delete_lfp(self):
        self.need_to_save = True
        self.lfp_plot.clear()
        self.deleted_lfp_acqs[str(self.acquisition_number.text())] = self.lfp_acq_dict[
            str(self.acquisition_number.text())
        ]
        del self.lfp_acq_dict[str(self.acquisition_number.text())]
        self.l_analysis_list.remove(int(self.acquisition_number.text()))
        self.lfp_acqs_deleted += 1

    def file_does_not_exist(self):
        self.dlg = QMessageBox(self)
        self.dlg.setWindowTitle("Error")
        self.dlg.setText("File does not exist")
        self.dlg.exec()

    def round_sig(self, x, sig=4):
        if isnan(x):
            return np.nan
        elif x == 0:
            return 0
        elif x != 0 or x is not np.nan or nan:
            return round(x, sig - int(floor(log10(abs(x)))) - 1)

    def final_analysis(self):
        self.need_to_save = True
        if self.final_data is not None:
            del self.final_data
        self.final_analysis_button.setEnabled(False)
        self.calc_param_clicked = True
        if self.oepsc_acq_dict and self.lfp_acq_dict:
            self.final_data = FinalEvokedCurrent(self.oepsc_acq_dict, self.lfp_acq_dict)
        elif self.oepsc_acq_dict and not self.lfp_acq_dict:
            self.final_data = FinalEvokedCurrent(self.oepsc_acq_dict)
        else:
            self.final_data = FinalEvokedCurrent(
                o_acq_dict=None, lfp_acq_dict=self.lfp_acq_dict
            )
        self.raw_datatable.setData(self.final_data.raw_df.T.to_dict("dict"))
        self.final_datatable.setData(self.final_data.final_df.T.to_dict("dict"))
        self.final_analysis_button.setEnabled(True)

    def save_as(self, save_filename):
        self.pbar.setValue(0)
        self.pbar.setFormat("Saving...")
        self.create_pref_dict()
        self.pref_dict["Acq_number"] = self.acquisition_number.value()
        self.pref_dict["Final Analysis"] = self.calc_param_clicked
        if self.lfp_acq_dict:
            self.pref_dict["LFP name"] = self.lfp_acq_dict[
                list(self.lfp_acq_dict.keys())[0]
            ].name.split("_")[0]
        else:
            self.pref_dict["LFP name"] = None
        if self.oepsc_acq_dict:
            self.pref_dict["oEPSC name"] = self.oepsc_acq_dict[
                list(self.oepsc_acq_dict.keys())[0]
            ].name.split("_")[0]
        else:
            self.pref_dict["oEPSC name"] = None
        YamlWorker.save_yaml(self.pref_dict, save_filename)
        if self.final_data is not None:
            self.final_data.save_data(save_filename)
        self.pbar_number = len(self.oepsc_acq_dict) + len(self.lfp_acq_dict)
        self.update_number = 0
        if self.oepsc_acq_dict:
            self.pbar.setFormat("Saving oEPSC files...")
            worker1 = SaveWorker(save_filename, self.oepsc_acq_dict)
            worker1.signals.progress.connect(self.update_save_progress)
            self.threadpool.start(worker1)
        if self.lfp_acq_dict:
            self.pbar.setFormat("Saving LFP files...")
            worker2 = SaveWorker(save_filename, self.lfp_acq_dict)
            worker2.signals.progress.connect(self.update_save_progress)
            self.threadpool.start(worker2)
        self.pbar.setFormat("Data saved")
        self.need_to_save = False

    def open_files(self, directory):
        self.reset()
        self.pbar.setFormat("Loading...")
        load_dict = YamlWorker.load_yaml(directory)
        file_list = list(directory.glob("*.json"))
        if not file_list:
            self.file_list = None
        else:
            for i in file_list:
                if i.name.split("_")[-2] == load_dict["oEPSC name"]:
                    x = Acq("oepsc", i)
                    x.load_acq()
                    self.oepsc_acq_dict[x.acq_number] = x
                else:
                    x = Acq("lfp", i)
                    x.load_acq()
                    self.lfp_acq_dict[x.acq_number] = x
        if self.oepsc_acq_dict:
            self.acquisition_number.setMaximum(
                int(list(self.oepsc_acq_dict.keys())[-1])
            )
            self.acquisition_number.setMinimum(int(list(self.oepsc_acq_dict.keys())[0]))
            self.oepsc_model.setLoadData(self.oepsc_acq_dict)
            self.set_peak_button.setEnabled(True)
            self.delete_oepsc_button.setEnabled(True)
        elif self.lfp_acq_dict:
            self.acquisition_number.setMaximum(int(list(self.lfp_acq_dict.keys())[-1]))
            self.acquisition_number.setMinimum(int(list(self.lfp_acq_dict.keys())[0]))
            self.lfp_model.setLoadData(self.lfp_acq_dict)
            self.delete_lfp_button.setEnabled(True)
            self.set_fv_button.setEnabled(True)
            self.set_fp_button.setEnabled(True)
        else:
            pass
        self.set_preferences(load_dict)
        self.acquisition_number.setValue(load_dict["Acq_number"])
        self.acquisition_number.setEnabled(True)
        if load_dict["Final Analysis"]:
            excel_file = list(directory.glob("*.xlsx"))[0]
            save_values = pd.read_excel(excel_file, sheet_name=None)
            self.final_data = LoadEvokedCurrentData(save_values)
            self.raw_datatable.setData(self.final_data.raw_df.T.to_dict("dict"))
            self.final_datatable.setData(self.final_data.final_df.T.to_dict("dict"))
        self.analyze_acq_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.acquisition_number.setEnabled(True)
        self.final_analysis_button.setEnabled(True)

    def create_pref_dict(self):
        line_edits = self.findChildren(QLineEdit)
        line_edit_dict = {}
        for i in line_edits:
            if i.objectName() != "":
                line_edit_dict[i.objectName()] = i.text()
        self.pref_dict["line_edits"] = line_edit_dict

        combo_box_dict = {}
        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            if i.objectName() != "":
                combo_box_dict[i.objectName()] = i.currentText()
        self.pref_dict["combo_boxes"] = combo_box_dict

        check_box_dict = {}
        check_boxes = self.findChildren(QCheckBox)
        for i in check_boxes:
            if i.objectName() != "":
                check_box_dict[i.objectName()] = i.isChecked()
        self.pref_dict["check_boxes"] = check_box_dict

        buttons_dict = {}
        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                buttons_dict[i.objectName()] = i.isEnabled()
        self.pref_dict["buttons"] = buttons_dict

        dspinbox_dict = {}
        dspinboxes = self.findChildren(QDoubleSpinBox)
        for i in dspinboxes:
            if i.objectName() != "":
                dspinbox_dict[i.objectName()] = i.text()
        self.pref_dict["double_spinboxes"] = dspinbox_dict

    def set_preferences(self, pref_dict):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if i.objectName() != "":
                try:
                    i.setText(pref_dict["line_edits"][i.objectName()])
                except:
                    pass

        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            if i.objectName() != "":
                try:
                    i.setCurrentText(pref_dict["combo_boxes"][i.objectName()])
                except:
                    pass

        check_boxes = self.findChildren(QCheckBox)
        for i in check_boxes:
            if i.objectName() != "":
                try:
                    i.setChecked(pref_dict["check_boxes"][i.objectName()])
                except:
                    pass

        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                try:
                    i.setEnabled(pref_dict["buttons"][i.objectName()])
                except:
                    pass

        dspinboxes = self.findChildren(QDoubleSpinBox)
        for i in dspinboxes:
            if i.objectName() != "":
                try:
                    i.setvalue(pref_dict["double_spinboxes"][i.objectName()])
                except:
                    pass

    def load_preferences(self, file_name):
        load_dict = YamlWorker.load_yaml(file_name)
        self.set_preferences(load_dict)

    def save_preferences(self, save_filename):
        self.create_pref_dict()
        if self.pref_dict:
            YamlWorker.save_yaml(self.pref_dict, save_filename)
        else:
            pass

    def update_save_progress(self, progress):
        self.update_number += 1
        self.pbar.setValue(100 * self.update_number / self.pbar_number)

    def progress_finished(self, finished):
        self.pbar.setFormat(finished)


if __name__ == "__main__":
    oEPSCWidget()
