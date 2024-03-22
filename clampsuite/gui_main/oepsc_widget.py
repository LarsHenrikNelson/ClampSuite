import logging
from collections import namedtuple

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
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
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea

from ..functions.utilities import round_sig
from ..gui_widgets.qtwidgets import DragDropWidget, LineEdit, ListView, ThreadWorker
from ..manager import ExpManager
from .acq_inspection import AcqInspectionWidget

XAxisCoord = namedtuple("XAxisCoord", ["x_min", "x_max"])

logger = logging.getLogger(__name__)


class oEPSCWidget(DragDropWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        logger.info("Creating oEPSC/LFP GUI")
        self.signals.file.connect(self.loadPreferences)
        self.signals.file_path.connect(self.loadExperiment)
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
        self.setStyleSheet(
            """QTabWidget::tab-bar 
                                          {alignment: left;}"""
        )

        # Tab 1 layout
        self.tab1 = QWidget()
        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1_scroll.setWidget(self.tab1)
        self.tabs.addTab(self.tab1_scroll, "Setup")
        self.tab1_layout = QVBoxLayout()
        self.tab1.setLayout(self.tab1_layout)
        self.form_layouts = QHBoxLayout()
        self.tab1_layout.addLayout(self.form_layouts, 0)
        self.view_layout_1 = QVBoxLayout()
        self.view_layout_2 = QVBoxLayout()
        self.input_layout_1 = QFormLayout()
        self.input_layout_3 = QFormLayout()
        self.input_layout_2 = QFormLayout()
        self.oepsc_view = ListView()
        self.oepsc_view.model().signals.progress.connect(self.updateProgress)
        self.oepsc_view.model().signals.dir_path.connect(self.setWorkingDirectory)
        self.oepsc_analysis = "oepsc"
        self.oepsc_view.setAnalysisType(self.oepsc_analysis)
        self.acq_label_1 = QLabel("Acquisition(s)")
        self.view_layout_1.addWidget(self.acq_label_1)
        self.view_layout_1.addWidget(self.oepsc_view)
        self.inspect_oepsc_acqs = QPushButton("Inspect acquistions")
        self.inspect_oepsc_acqs.clicked.connect(
            lambda checked: self.inspectAcqs("oepsc")
        )
        self.view_layout_1.addWidget(self.inspect_oepsc_acqs)
        self.del_oepsc_sel = QPushButton("Delete selection")
        self.del_oepsc_sel.clicked.connect(
            lambda checked: self.delSelection(self.oepsc_view, "oepsc")
        )
        self.view_layout_1.addWidget(self.del_oepsc_sel)
        self.form_layouts.addLayout(self.view_layout_1)
        self.form_layouts.addLayout(self.input_layout_1)
        self.form_layouts.addLayout(self.input_layout_3)
        self.lfp_view = ListView()
        self.lfp_view.model().signals.progress.connect(self.updateProgress)
        self.lfp_view.model().signals.dir_path.connect(self.setWorkingDirectory)
        self.lfp_analysis = "lfp"
        self.lfp_view.setAnalysisType(self.lfp_analysis)
        self.acq_label_2 = QLabel("Acquisition(s)")
        self.view_layout_2.addWidget(self.acq_label_2)
        self.view_layout_2.addWidget(self.lfp_view)
        self.inspect_lfp_acqs = QPushButton("Inspect acquistions")
        self.inspect_lfp_acqs.clicked.connect(lambda checked: self.inspectAcqs("lfp"))
        self.view_layout_2.addWidget(self.inspect_lfp_acqs)
        self.del_lfp_sel = QPushButton("Delete selection")
        self.del_lfp_sel.clicked.connect(
            lambda checked: self.delSelection(self.lfp_view, "lfp")
        )
        self.view_layout_2.addWidget(self.del_lfp_sel)
        self.form_layouts.addLayout(self.view_layout_2)
        self.form_layouts.addLayout(self.input_layout_2)

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

        self.o_filter_type_label = QLabel("Filter Type")
        filters = ExpManager.filters
        self.o_filter_selection = QComboBox()
        self.o_filter_selection.addItems(filters)
        self.o_filter_selection.setMinimumContentsLength(len(max(filters, key=len)))
        self.o_filter_selection.setObjectName("o_filter_selection")
        self.o_filter_selection.setCurrentText("fir_zero_2")
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
        self.o_high_pass_edit.setObjectName("o_high_pass_edit")
        self.o_high_pass_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_high_pass_label, self.o_high_pass_edit)

        self.o_high_width_label = QLabel("High-width")
        self.o_high_width_edit = LineEdit()

        self.o_high_width_edit.setObjectName("o_high_width_edit")
        self.o_high_width_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_high_width_label, self.o_high_width_edit)

        self.o_low_pass_label = QLabel("Low-pass")
        self.o_low_pass_edit = LineEdit()
        self.o_low_pass_edit.setObjectName("o_low_pass_edit")
        self.o_low_pass_edit.setEnabled(True)
        self.o_low_pass_edit.setText("600")
        self.input_layout_1.addRow(self.o_low_pass_label, self.o_low_pass_edit)

        self.o_low_width_label = QLabel("Low-width")
        self.o_low_width_edit = LineEdit()
        self.o_low_width_edit.setObjectName("o_low_width_edit")
        self.o_low_width_edit.setText("600")
        self.o_low_width_edit.setEnabled(True)
        self.input_layout_1.addRow(self.o_low_width_label, self.o_low_width_edit)

        self.o_window_label = QLabel("Window type")
        windows = ExpManager.windows
        self.o_window_edit = QComboBox(self)
        self.o_window_edit.setObjectName("o_window_edit")
        self.o_window_edit.addItems(windows)
        self.o_window_edit.setMinimumContentsLength(len(max(windows, key=len)))
        self.input_layout_1.addRow(self.o_window_label, self.o_window_edit)
        self.o_window_edit.currentTextChanged.connect(self.oWindowChanged)

        self.o_beta_sigma_label = QLabel("Beta/Sigma")
        self.o_beta_sigma = QDoubleSpinBox()
        self.o_beta_sigma.setMinimumWidth(70)
        self.o_beta_sigma.setObjectName("o_beta_sigma")
        self.input_layout_1.addRow(self.o_beta_sigma_label, self.o_beta_sigma)

        self.o_polyorder_label = QLabel("Polyorder")
        self.o_polyorder_edit = LineEdit()
        self.o_polyorder_edit.setValidator(QIntValidator())
        self.o_polyorder_edit.setEnabled(True)
        self.o_polyorder_edit.setObjectName("o_polyorder_edit")
        self.o_polyorder_edit.setText("3")
        self.input_layout_1.addRow(self.o_polyorder_label, self.o_polyorder_edit)

        self.input_layout_3.addRow(QLabel(""), QLabel(""))

        self.o_pulse_start = QLabel("Pulse start")
        self.o_pulse_start_edit = LineEdit()
        self.o_pulse_start_edit.setEnabled(True)
        self.o_pulse_start_edit.setObjectName("o_pulse_start_edit")
        self.o_pulse_start_edit.setText("1000")
        self.input_layout_3.addRow(self.o_pulse_start, self.o_pulse_start_edit)

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
        self.curve_fit_type_edit.setMinimumContentsLength(len(max(fit_types, key=len)))
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

        self.lfp_filter_type_label = QLabel("Filter Type")
        self.lfp_filter_selection = QComboBox(self)
        self.lfp_filter_selection.addItems(filters)
        self.lfp_filter_selection.setMinimumContentsLength(len(max(filters, key=len)))
        self.lfp_filter_selection.setObjectName("lfp_filter_selection")
        self.lfp_filter_selection.setCurrentText("fir_zero_2")
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
        self.lfp_high_pass_edit.setObjectName("lfp_high_pass_edit")
        self.lfp_high_pass_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_high_pass_label, self.lfp_high_pass_edit)

        self.lfp_high_width_label = QLabel("High-width")
        self.lfp_high_width_edit = LineEdit()
        self.lfp_high_width_edit.setObjectName("lfp_high_width_edit")
        self.lfp_high_width_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_high_width_label, self.lfp_high_width_edit)

        self.lfp_low_pass_label = QLabel("Low-pass")
        self.lfp_low_pass_edit = LineEdit()
        self.lfp_low_pass_edit.setText("300")
        self.lfp_low_pass_edit.setObjectName("lfp_low_pass_edit")
        self.lfp_low_pass_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_low_pass_label, self.lfp_low_pass_edit)

        self.lfp_low_width_label = QLabel("Low-width")
        self.lfp_low_width_edit = LineEdit()
        self.lfp_low_width_edit.setText("300")
        self.lfp_low_width_edit.setObjectName("lfp_low_width_edit")
        self.lfp_low_width_edit.setEnabled(True)
        self.input_layout_2.addRow(self.lfp_low_width_label, self.lfp_low_width_edit)

        self.lfp_window_label = QLabel("Window type")
        self.lfp_window_edit = QComboBox(self)
        self.lfp_window_edit.addItems(windows)
        self.lfp_window_edit.setMinimumContentsLength(len(max(windows, key=len)))
        self.lfp_window_edit.setObjectName("lfp_window_edit")
        self.input_layout_2.addRow(self.lfp_window_label, self.lfp_window_edit)
        self.lfp_window_edit.currentTextChanged.connect(self.lWindowChanged)

        self.lfp_beta_sigma_label = QLabel("Beta/Sigma")
        self.lfp_beta_sigma = QDoubleSpinBox()
        self.lfp_beta_sigma.setMinimumWidth(70)
        self.lfp_beta_sigma.setObjectName("lfp_beta_sigma")
        self.input_layout_2.addRow(self.lfp_beta_sigma_label, self.lfp_beta_sigma)

        self.lfp_polyorder_label = QLabel("Polyorder")
        self.lfp_polyorder_edit = LineEdit()
        self.lfp_polyorder_edit.setValidator(QDoubleValidator())
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
        self.analyze_acq_button = QPushButton("Analyze acquisition(s)")
        self.tab1_layout.addWidget(self.analyze_acq_button)
        self.analyze_acq_button.clicked.connect(self.analyze)

        self.reset_button = QPushButton("Reset analysis")
        self.tab1_layout.addWidget(self.reset_button)
        self.reset_button.clicked.connect(self.reset)

        # Tab 2 layout
        self.tab2_scroll = QScrollArea()
        self.tab2_scroll.setViewportMargins(10, 10, 10, 10)
        self.tab2_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab2_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab2_scroll.setWidgetResizable(True)
        self.tab2 = QWidget()
        self.tab2_layout = QHBoxLayout()
        self.tab2.setLayout(self.tab2_layout)
        self.tabs.addTab(self.tab2_scroll, "Analysis")
        self.tab2_scroll.setWidget(self.tab2)
        # self.tab2_layout = QHBoxLayout()
        # self.analysis_buttons_layout = QFormLayout()
        # self.tab2_layout.addLayout(self.analysis_buttons_layout)
        # self.tab2.setLayout(self.tab2_layout)

        # Plots
        self.oepsc_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.oepsc_plot.setObjectName("oEPSC plot")
        self.oepsc_plot.setAutoVisible(y=True)
        self.oepsc_plot.setMinimumWidth(500)
        self.oepsc_plot.sigXRangeChanged.connect(lambda: self.getXRange("oepsc_plot"))

        self.lfp_plot = pg.PlotWidget(
            labels={"left": "Amplitude (mV)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.lfp_plot.setObjectName("LFP plot")
        self.lfp_plot.setMinimumWidth(500)
        self.lfp_plot.setAutoVisible(y=True)
        self.lfp_plot.sigXRangeChanged.connect(lambda: self.getXRange("lfp_plot"))

        self.acq_button_dock = QGridLayout()
        # self.acq_button_dock.setColumnStretch(0, 0)
        self.tab2_layout.addLayout(self.acq_button_dock, 0)

        self.tab2_dock = DockArea()
        self.tab2_layout.addWidget(self.tab2_dock, 1)
        self.oepsc_dock = Dock("oEPSC")
        self.tab2_dock.addDock(self.oepsc_dock, "left")
        self.lfp_dock = Dock("LFP")
        self.tab2_dock.addDock(self.lfp_dock, "right")
        self.oepsc_plot_layout = QHBoxLayout()
        self.oepsc_plot_widget = QWidget()
        self.oepsc_dock.addWidget(self.oepsc_plot_widget, 0, 0)
        self.oepsc_plot_widget.setLayout(self.oepsc_plot_layout)
        self.lfp_plot_layout = QHBoxLayout()
        self.lfp_plot_widget = QWidget()
        self.lfp_dock.addWidget(self.lfp_plot_widget, 0, 0)
        self.lfp_plot_widget.setLayout(self.lfp_plot_layout)
        self.o_info_layout = QGridLayout()
        self.lfp_info_layout = QFormLayout()
        self.oepsc_plot_layout.addLayout(self.o_info_layout, 0)
        self.oepsc_plot_layout.addWidget(self.oepsc_plot, 1)
        self.lfp_plot_layout.addLayout(self.lfp_info_layout, 0)
        self.lfp_plot_layout.addWidget(self.lfp_plot, 1)

        # Analysis layout
        self.acquisition_number_label = QLabel("Acquisition")
        self.acq_button_dock.addWidget(self.acquisition_number_label, 0, 0)
        self.acquisition_number = QSpinBox()
        self.acquisition_number.setMaximumWidth(70)
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)
        self.acquisition_number.valueChanged.connect(self.acqSpinbox)
        self.acq_button_dock.addWidget(self.acquisition_number, 0, 1)
        self.acquisition_number.setEnabled(True)

        self.epoch_label = QLabel("Epoch")
        self.acq_button_dock.addWidget(self.epoch_label, 1, 0)
        self.epoch_number = QLineEdit()
        self.epoch_number.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch_number.text())
        )
        self.epoch_number.setMaximumWidth(70)
        self.acq_button_dock.addWidget(self.epoch_number, 1, 1)

        self.final_analysis_button = QPushButton("Final analysis")
        self.acq_button_dock.addWidget(self.final_analysis_button, 2, 0, 1, 2)
        self.final_analysis_button.clicked.connect(self.runFinalAnalysis)
        self.final_analysis_button.setEnabled(True)

        self.acq_button_dock.setRowStretch(3, 10)
        self.acq_button_dock.setColumnStretch(1, 0)
        self.acq_button_dock.setColumnStretch(0, 0)

        self.oepsc_label = QLabel("oEPSC")
        self.o_info_layout.addWidget(self.oepsc_label, 0, 0, 1, 2)

        self.oepsc_amp_label = QLabel("Amplitude (pA)")
        self.o_info_layout.addWidget(self.oepsc_amp_label, 1, 0)
        self.oepsc_amp_edit = QLineEdit()
        self.oepsc_amp_edit.setReadOnly(True)
        self.o_info_layout.addWidget(self.oepsc_amp_edit, 1, 1)

        self.oepsc_charge_label = QLabel("Charge transfer")
        self.o_info_layout.addWidget(self.oepsc_charge_label, 2, 0)
        self.oepsc_charge_edit = QLineEdit()
        self.oepsc_charge_edit.setReadOnly(True)
        self.o_info_layout.addWidget(self.oepsc_charge_edit, 2, 1)

        self.oepsc_edecay_label = QLabel("Est decay (ms)")
        self.o_info_layout.addWidget(self.oepsc_edecay_label, 3, 0)
        self.oepsc_edecay_edit = QLineEdit()
        self.oepsc_edecay_edit.setReadOnly(True)
        self.o_info_layout.addWidget(self.oepsc_edecay_edit, 3, 1)

        self.oepsc_fdecay_label = QLabel("Fit decay (ms)")
        self.o_info_layout.addWidget(self.oepsc_fdecay_label, 4, 0)
        self.oepsc_fdecay_edit = QLineEdit()
        self.oepsc_fdecay_edit.setReadOnly(True)
        self.o_info_layout.addWidget(self.oepsc_fdecay_edit, 4, 1)

        self.set_peak_button = QPushButton("Set point as peak")
        self.o_info_layout.addWidget(self.set_peak_button, 5, 0, 1, 2)
        self.set_peak_button.clicked.connect(self.setoEPSCPeak)
        self.set_peak_button.setEnabled(True)

        self.delete_oepsc_button = QPushButton("Delete oEPSC")
        self.o_info_layout.addWidget(self.delete_oepsc_button, 6, 0, 1, 2)
        self.delete_oepsc_button.clicked.connect(self.deleteoEPSC)
        self.delete_oepsc_button.setEnabled(True)

        self.set_peak_action = QAction("Set point as peak")
        self.set_peak_action.triggered.connect(self.setoEPSCPeak)

        self.delete_oepsc_action = QAction("Delete oEPSC")
        self.delete_oepsc_action.triggered.connect(self.deleteoEPSC)

        o_vb = self.oepsc_plot.getViewBox()
        o_vb.menu.addSeparator()
        o_vb.menu.addAction(self.set_peak_action)
        o_vb.menu.addSeparator()
        o_vb.menu.addAction(self.delete_oepsc_action)

        self.o_info_layout.setRowStretch(7, 10)

        self.lfp_label = QLabel("LFP")
        self.lfp_info_layout.addRow(self.lfp_label)

        self.lfp_fv_label = QLabel("Fiber volley (mV)")
        self.lfp_fv_edit = QLineEdit()
        self.lfp_fv_edit.setReadOnly(True)
        self.lfp_info_layout.addRow(self.lfp_fv_label, self.lfp_fv_edit)

        self.lfp_fp_label = QLabel("Field potential (mV)")
        self.lfp_fp_edit = QLineEdit()
        self.lfp_fp_edit.setReadOnly(True)
        self.lfp_info_layout.addRow(self.lfp_fp_label, self.lfp_fp_edit)

        self.lfp_fp_slope_label = QLabel("FP slope (mV/ms)")
        self.lfp_fp_slope_edit = QLineEdit()
        self.lfp_fp_slope_edit.setReadOnly(True)
        self.lfp_info_layout.addRow(self.lfp_fp_slope_label, self.lfp_fp_slope_edit)

        self.set_fv_button = QPushButton("Set point as fiber volley")
        self.set_fv_button.clicked.connect(self.setPointAsFV)
        self.lfp_info_layout.addRow(self.set_fv_button)
        self.set_fv_button.setEnabled(True)

        self.set_fp_button = QPushButton("Set point as field potential")
        self.set_fp_button.clicked.connect(self.setPointAsFP)
        self.lfp_info_layout.addRow(self.set_fp_button)
        self.set_fp_button.setEnabled(True)

        self.set_slope_start_btn = QPushButton("Set point as slope start")
        self.set_slope_start_btn.clicked.connect(self.setPointAsSlopeStart)
        self.lfp_info_layout.addRow(self.set_slope_start_btn)
        self.set_slope_start_btn.setEnabled(True)

        self.delete_lfp_button = QPushButton("Delete LFP")
        self.delete_lfp_button.clicked.connect(self.deleteLFP)
        self.lfp_info_layout.addRow(self.delete_lfp_button)
        self.delete_lfp_button.setEnabled(True)

        self.set_fv_action = QAction("Set point as fv")
        self.set_fv_action.triggered.connect(self.setPointAsFV)

        self.set_fp_action = QAction("Set point as fp")
        self.set_fp_action.triggered.connect(self.setPointAsFP)

        self.set_slope_action = QAction("Set point as slope")
        self.set_slope_action.triggered.connect(self.setPointAsSlopeStart)

        self.delete_lfp_action = QAction()
        self.delete_lfp_action.triggered.connect(self.deleteLFP)

        self.choose_analysis_type = QMessageBox()
        self.choose_analysis_type.setText("Choose analysis type")
        self.oepsc_type_button = self.choose_analysis_type.addButton(
            "oEPSC", QMessageBox.ActionRole
        )
        self.lfp_type_button = self.choose_analysis_type.addButton(
            "LFP", QMessageBox.ActionRole
        )

        vb = self.lfp_plot.getViewBox()
        vb.menu.addSeparator()
        vb.menu.addAction(self.set_fv_action)
        vb.menu.addAction(self.set_fp_action)
        vb.menu.addAction(self.set_slope_action)
        vb.menu.addSeparator()
        vb.menu.addAction(self.delete_lfp_action)

        # Tab 3 Layout
        self.tab3 = QTabWidget()
        self.tabs.addTab(self.tab3, "Final data")

        self.dlg = QMessageBox(self)

        self.setWidth()

        # Lists
        self.exp_manager = ExpManager()
        self.oepsc_view.setData(self.exp_manager)
        self.lfp_view.setData(self.exp_manager)
        self.inspection_widget = AcqInspectionWidget()
        self.last_oepsc_point_clicked = []
        self.last_lfp_point_clicked = []
        self.last_lfp_point_clicked = []
        self.last_oepsc_point_clicked = []
        self.table_dict = {}
        self.calc_param_clicked = False
        self.need_to_save = False
        self.on_x_set = False
        self.op_x_set = False

        logger.info("Event oEPSC/LFP GUI created.")

    def setWidth(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if not isinstance(i.parentWidget(), QSpinBox):
                i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(80)

    def inspectAcqs(self, analysis_type):
        if not self.exp_manager.acqs_exist("lfp") and not self.exp_manager.acqs_exist(
            "oepsc"
        ):
            self.fileDoesNotExist()
        else:
            self.inspection_widget.clearData()
            self.inspection_widget.setData(analysis_type, self.exp_manager)
            self.inspection_widget.show()

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
        elif text == "ewma" or text == "ewma_a":
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
        elif text == "ewma" or text == "ewma_a":
            self.lfp_order_label.setText("Window size")
            self.lfp_polyorder_label.setText("Sum proportion")
        else:
            self.lfp_order_label.setText("Order")
            self.lfp_polyorder_label.setText("Polyorder")

    def delSelection(self, list_view, exp):
        if not self.exp_manager.acqs_exist(exp):
            logger.info(f"No {exp} acquisitions exist to remove from analysis list.")
            self.fileDoesNotExist()
        else:
            # Deletes the selected acquisitions from the list
            indexes = list_view.selectedIndexes()
            if len(indexes) > 0:
                list_view.deleteSelection(indexes)
                list_view.clearSelection()
                logger.info("Removed acquisitions from analysis.")

    def getXRange(self, plot):
        h = self.acquisition_number.value()
        if plot == "oepsc_plot":
            x = self.oepsc_plot.viewRange()[0]
            if self.exp_manager.acq_exists("oepsc", h):
                self.setOPlotX(x)
        elif plot == "lfp_plot":
            x = self.lfp_plot.viewRange()[0]
            if self.exp_manager.acq_exists("lfp", h):
                self.setLFPPlotX(x)

    def setOPlotX(self, x):
        peak_dir = self.exp_manager.exp_dict["oepsc"][
            self.acquisition_number.value()
        ].peak_direction
        if peak_dir == "positive":
            self.op_x_axis = XAxisCoord(x[0], x[1])
            self.op_x_set = True
        else:
            self.on_x_axis = XAxisCoord(x[0], x[1])
            self.on_x_set = True

    def setOEPSCLimits(self, oepsc_object):
        if not self.on_x_set:
            self.on_x_axis = XAxisCoord(
                oepsc_object.pulse_start - 100,
                oepsc_object.pulse_start + 450,
            )
            self.on_x_set = True
        if not self.op_x_set:
            self.op_x_axis = XAxisCoord(
                oepsc_object.pulse_start - 100,
                oepsc_object.x_array[-1],
            )
            self.op_x_set = True

    def setLFPPlotX(self, x):
        self.lfp_x_axis = XAxisCoord(x[0], x[1])

    def editAttr(self, line_edit, value):
        for i in self.exp_manager.exp_dict.values():
            setattr(
                i[self.acquisition_number.value()],
                line_edit,
                value,
            )
        return True

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
            self.acquisition_number.setMaximum(self.exp_manager.end_acq)
            self.acquisition_number.setMinimum(self.exp_manager.start_acq)
            self.acquisition_number.setValue(self.exp_manager.start_acq)
            self.acqSpinbox(self.exp_manager.start_acq)
            self.tabs.setCurrentIndex(1)
            logger.info("Analysis finished.")
            self.pbar.setFormat("Analysis finished")

    def acqSpinbox(self, h):
        self.oepsc_plot.clear()
        self.lfp_plot.clear()
        oepsc_object = None
        lfp_object = None
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("No acquisitions analyzed, acquisition not set.")
            self.fileDoesNotExist()
            return None
        logger.info("Preparing UI for plotting.")
        self.need_to_save = True
        self.acquisition_number.setDisabled(True)
        self.last_oepsc_point_clicked = []
        self.last_lfp_point_clicked = []
        if self.exp_manager.acq_exists("oepsc", self.acquisition_number.value()):
            logger.info(f"Plotting oEPSC {self.acquisition_number.value()}.")
            oepsc_object = self.exp_manager.exp_dict["oepsc"][
                self.acquisition_number.value()
            ]
            self.setOEPSCLimits(oepsc_object)
            self.oepsc_acq_plot = pg.PlotDataItem(
                x=oepsc_object.plot_acq_x(),
                y=oepsc_object.plot_acq_y(),
                name=str("oepsc_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.oepsc_peak_plot = pg.PlotDataItem(
                x=oepsc_object.plot_x_comps(),
                y=oepsc_object.plot_y_comps(),
                symbol="o",
                symbolSize=8,
                symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
                pen=None,
            )
            self.oepsc_acq_plot.sigPointsClicked.connect(self.oEPSCPlotClicked)
            self.oepsc_plot.addItem(self.oepsc_acq_plot)
            self.oepsc_plot.addItem(self.oepsc_peak_plot)
            if oepsc_object.peak_direction == "negative":
                self.oepsc_plot.setXRange(
                    self.on_x_axis.x_min, self.on_x_axis.x_max, padding=0
                )
            else:
                self.oepsc_plot.setXRange(
                    self.op_x_axis.x_min, self.op_x_axis.x_max, padding=0
                )
            self.oepsc_plot.enableAutoRange(axis="y")
            self.oepsc_plot.setAutoVisible(y=True)
            self.oepsc_amp_edit.setText(str(round_sig(oepsc_object.peak_y)))
            if oepsc_object.find_ct:
                self.oepsc_charge_edit.setText(
                    str(round_sig((oepsc_object.charge_transfer)))
                )
            if oepsc_object.find_edecay:
                self.oepsc_edecay_edit.setText(
                    str(round_sig((oepsc_object.est_decay())))
                )
            logger.info(f"oEPSC acquisition {self.acquisition_number.value()} plotted.")
        else:
            logger.info(f"No oEPSC acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.oepsc_plot.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.oepsc_plot.addItem(text)
        if self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(f"Plotting LFP {self.acquisition_number.value()}.")
            lfp_object = self.exp_manager.exp_dict["lfp"][
                self.acquisition_number.value()
            ]
            self.lfp_acq_plot = pg.PlotDataItem(
                x=lfp_object.plot_acq_x(),
                y=lfp_object.plot_acq_y(),
                name=str("lfp_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=10,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.lfp_plot.addItem(self.lfp_acq_plot)
            if lfp_object.plot_lfp:
                self.lfp_points = pg.PlotDataItem(
                    x=lfp_object.plot_elements_x(),
                    y=lfp_object.plot_elements_y(),
                    symbol="o",
                    symbolSize=8,
                    symbolBrush=[pg.mkBrush("m"), pg.mkBrush("b")],
                    pen=None,
                )
                if lfp_object.reg_line is not np.nan:
                    self.lfp_reg = pg.PlotDataItem(
                        x=lfp_object.slope_x(),
                        y=lfp_object.reg_line,
                        pen=pg.mkPen(color="g", width=4),
                        name="reg_line",
                    )
                self.lfp_plot.addItem(self.lfp_points)
                self.lfp_plot.addItem(self.lfp_reg)
                self.lfp_fv_edit.setText(str(round_sig(lfp_object.fv_y)))
                self.lfp_fp_edit.setText(str(round_sig(lfp_object.fp_y)))
                self.lfp_fp_slope_edit.setText(str(round_sig(lfp_object.slope())))

            self.lfp_acq_plot.sigPointsClicked.connect(self.LFPPlotClicked)
            self.lfp_plot.setXRange(
                self.lfp_x_axis.x_min, self.lfp_x_axis.x_max, padding=0
            )
            self.lfp_plot.enableAutoRange(axis="y")
            self.lfp_plot.setAutoVisible(y=True)
            logger.info(f"LFP acquisition {self.acquisition_number.value()} plotted.")
        else:
            logger.info(f"No LFP acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.lfp_plot.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.lfp_plot.addItem(text)
        if oepsc_object is not None:
            self.epoch_number.setText(oepsc_object.epoch)
        elif lfp_object is not None:
            self.epoch_number.setText(lfp_object.epoch)
        self.acquisition_number.setEnabled(True)

    def reset(self):
        logger.info("Reseting UI.")
        self.oepsc_plot.clear()
        self.lfp_plot.clear()
        self.tab3.clear()
        self.clearTables()
        self.calc_param_clicked = False
        self.inspection_widget.removeFileList()
        self.oepsc_view.clearData()
        self.lfp_view.clearData()
        self.exp_manager = ExpManager()
        self.oepsc_view.setData(self.exp_manager)
        self.lfp_view.setData(self.exp_manager)
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

    def oEPSCPlotClicked(self, item, points):
        logger.info(
            f"oEPSC acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_oepsc_point_clicked:
            self.last_oepsc_point_clicked.resetPen()
            self.last_oepsc_point_clicked.resetBrush()
            self.last_oepsc_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_oepsc_point_clicked = points[0]
        logger.info(
            f"Point {self.last_oepsc_point_clicked.pos()[0]}"
            "set as oEPSC point clicked."
        )

    def LFPPlotClicked(self, item, points):
        logger.info(
            f"oEPSC acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_lfp_point_clicked:
            self.last_lfp_point_clicked.resetPen()
            self.last_lfp_point_clicked.resetBrush()
            self.last_lfp_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_lfp_point_clicked = points[0]
        logger.info(
            f"Point {self.last_lfp_point_clicked.pos()[0]} set as LFP point clicked."
        )

    def setPointAsFV(self):
        """
        This will set the LFP fiber volley as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Fiber volley was not set,"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Fiber volley was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, fiber volley not set.")
            self.fileDoesNotExist("No LFP point was selected, fiber volley not set.")
            return None

        logger.info(f"Setting fiber volley on LFP {self.acquisition_number.value()}.")

        self.need_to_save = True

        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]

        acq.change_fv(x, y)

        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq.slope() is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )

        self.lfp_fv_edit.setText(str(round_sig(acq.fv_y)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None

        logger.info(f"Fiber volley set on LFP {self.acquisition_number.value()}.")

    def setPointAsSlopeStart(self):
        """
        This will set the LFP fiber volley as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Slope start was not set,"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Slope start was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, slope start not set.")
            self.fileDoesNotExist("No LFP point was selected, slope start not set.")
            return None

        logger.info(f"Setting slope start on LFP {self.acquisition_number.value()}.")

        self.need_to_save = True

        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]

        acq.change_slope_start(x, y)

        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq.slope is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fv_edit.setText(str(round_sig(acq.fv_y)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None
        logger.info(f"Slope start set on LFP {self.acquisition_number.value()}.")

    def setPointAsFP(self):
        """
        This will set the LFP field potential as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Field potential was not set,"
                f" acquisition {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Field potential was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, field potential not set.")
            self.fileDoesNotExist("No LFP point was selected, field potential not set.")
            return None

        logger.info(f"Setting slope start on LFP {self.acquisition_number.value()}.")
        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]
        acq.change_fp(x, y)
        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fp_edit.setText(str(round_sig(acq.fp_y)))
        self.lfp_fp_slope_edit.setText(str(round_sig(acq.slope)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None
        logger.info(f"Field potential set on LFP {self.acquisition_number.value()}.")

    def setoEPSCPeak(self):
        """Sets the peak on the oEPSC acquisition.

        Returns:
        -------
        None.
        """
        if not self.exp_manager.acq_exists("oepsc", self.acquisition_number.value()):
            logger.info(
                "oEPSC peak was not set, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "oEPSC peak was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_oepsc_point_clicked is None:
            logger.info("No oEPSC point was selected, peak not set.")
            self.fileDoesNotExist("No oEPSC point was selected, peak not set.")
            return None

        logger.info(f"Setting peak on oEPSC {self.acquisition_number.value()}.")
        acq = self.exp_manager.exp_dict["oepsc"][self.acquisition_number.value()]
        self.need_to_save = True
        x = self.last_oepsc_point_clicked.pos()[0]
        y = self.last_oepsc_point_clicked.pos()[1]
        acq.change_peak(x, y)
        self.oepsc_peak_plot.setData(
            x=acq.plot_x_comps(),
            y=acq.plot_y_comps(),
            symbol="o",
            symbolSize=8,
            symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
            pen=None,
        )
        self.oepsc_amp_edit.setText(str(round_sig(acq.peak_y)))
        self.last_oepsc_point_clicked.resetPen()
        self.last_oepsc_point_clicked.resetBrush()
        self.last_oepsc_point_clicked = None
        logger.info(f"Peak setzs on oEPSC {self.acquisition_number.value()}.")

    def deleteoEPSC(self):
        if not self.exp_manager.acqs_exist("oepsc"):
            logger.info(
                "No acquisition deleted, oepsc acquisition"
                f" {self.acquisition_number.values()} does not exist."
            )
            self.fileDoesNotExist(
                "No acquisition deleted, oepsc acquisition\n"
                f"{self.acquisition_number.values()} does not exist."
            )
        else:
            self.need_to_save = True
            self.oepsc_plot.clear()
            self.exp_manager.delete_acq("oepsc", self.acquisition_number.value())
            logger.info(f"oEPSC Aquisition {self.acquisition_number.value()} deleted.")

    def deleteLFP(self):
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.values()):
            logger.info(
                "No acquisition deleted, lfp acquisition"
                f"{self.acquisition_number.values()} does not exist."
            )
            self.fileDoesNotExist(
                "No acquisition deleted, lfp acquisition\n"
                f"{self.acquisition_number.values()} does not exist."
            )
        else:
            self.need_to_save = True
            self.lfp_plot.clear()
            self.exp_manager.delete_acq("lfp", self.acquisition_number.value())
            logger.info(f"LFP Aquisition {self.acquisition_number.value()} deleted.")

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
        self.exp_manager = ExpManager()
        self.worker = ThreadWorker(self.exp_manager)
        self.worker.addAnalysis(function="load", analysis="oepsc", file_path=directory)
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def createExperiment(self, urls):
        self.pbar.setFormat("Creating experiment")
        self.choose_analysis_type.exec()
        if self.choose_analysis_type.clickedButton() == self.oepsc_type_button:
            self.oepsc_view.model().addData(urls)
            self.pbar.setFormat("oEPSC experiment created")
        else:
            self.lfp_view.model().addData(urls)
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
            self.oepsc_view.setData(self.exp_manager)
            self.set_peak_button.setEnabled(True)
            self.delete_oepsc_button.setEnabled(True)
        if self.exp_manager.acqs_exist("lfp"):
            self.lfp_view.setData(self.exp_manager)
            self.delete_lfp_button.setEnabled(True)
            self.set_fv_button.setEnabled(True)
            self.set_fp_button.setEnabled(True)
            self.lfp_x_axis = XAxisCoord(
                self.lfp_pulse_start_edit.toInt() - 10,
                self.lfp_b_start_edit.toInt() + 250,
            )
        self.acquisition_number.setValue(self.exp_manager.start_acq)
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

        check_box_dict = {}
        check_boxes = self.findChildren(QCheckBox)
        for i in check_boxes:
            if i.objectName() != "":
                check_box_dict[i.objectName()] = i.isChecked()
        pref_dict["check_boxes"] = check_box_dict

        buttons_dict = {}
        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                buttons_dict[i.objectName()] = i.isEnabled()
        pref_dict["buttons"] = buttons_dict

        dspinbox_dict = {}
        dspinboxes = self.findChildren(QDoubleSpinBox)
        for i in dspinboxes:
            if i.objectName() != "":
                dspinbox_dict[i.objectName()] = i.text()
        pref_dict["double_spinboxes"] = dspinbox_dict
        logger.info("Preferences dictionary created.")
        return pref_dict

    def setPreferences(self, pref_dict):
        logger.info("Setting oEPSC/LFP preferences.")
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if i.objectName() != "":
                i.setText(pref_dict["line_edits"][i.objectName()])

        combo_boxes = self.findChildren(QComboBox)
        for i in combo_boxes:
            if i.objectName() != "":
                i.setCurrentText(pref_dict["combo_boxes"][i.objectName()])

        check_boxes = self.findChildren(QCheckBox)
        for i in check_boxes:
            if i.objectName() != "":
                i.setChecked(pref_dict["check_boxes"][i.objectName()])

        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                i.setEnabled(pref_dict["buttons"][i.objectName()])

        dspinboxes = self.findChildren(QDoubleSpinBox)
        for i in dspinboxes:
            if i.objectName() != "":
                i.setValue(float((pref_dict["double_spinboxes"][i.objectName()])))

        logger.info("Preferences set.")
        self.pbar.setFormat("Preferences set")

    def loadPreferences(self, file_name: str):
        self.need_to_save = True
        load_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(load_dict)

    def savePreferences(self, file_path):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(file_path, pref_dict)
        else:
            pass

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

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)
