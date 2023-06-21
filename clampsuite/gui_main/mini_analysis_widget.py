import logging

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QFont, QIntValidator, QKeySequence
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
    QShortcut,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea

from ..functions.kde import create_kde
from ..functions.template_psc import create_template
from ..functions.utilities import round_sig
from ..gui_widgets.qtwidgets import DragDropWidget, LineEdit, ListView, ThreadWorker
from ..manager import ExpManager
from .acq_inspection import AcqInspectionWidget

logger = logging.getLogger(__name__)


class MiniAnalysisWidget(DragDropWidget):
    def __init__(self):
        super().__init__()
        self.init_UI()

    def init_UI(self):
        # Create tabs for part of the analysis program
        self.signals.file.connect(self.loadPreferences)
        self.signals.path.connect(self.loadExperiment)
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

        self.dock_area2 = DockArea()

        self.tab3_scroll = QScrollArea()
        self.tab3_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tab3_scroll.setWidgetResizable(True)
        self.dock_area3 = DockArea()

        self.tab_widget.addTab(self.tab1_scroll, "Setup")
        self.tab_widget.addTab(self.dock_area2, "Analysis")
        self.tab_widget.addTab(self.dock_area3, "Final data")

        self.setStyleSheet(
            """QTabWidget::tab-bar
                                          {alignment: left;}"""
        )

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.main_layout.addWidget(self.pbar)

        self.dlg = QMessageBox(self)

        self.inspection_widget = AcqInspectionWidget()

        # Tab 1 layouts
        self.setup_layout = QHBoxLayout()
        self.extra_layout = QVBoxLayout()
        self.other_layout = QHBoxLayout()
        self.input_layout = QFormLayout()
        self.load_layout = QVBoxLayout()
        self.settings_layout = QFormLayout()
        self.template_form = QFormLayout()
        self.tab1.setLayout(self.setup_layout)
        self.setup_layout.addLayout(self.input_layout, 0)
        self.setup_layout.addLayout(self.extra_layout, 1)
        self.setup_layout.addLayout(self.load_layout, 0)
        self.extra_layout.addLayout(self.other_layout, 10)
        self.other_layout.addLayout(self.settings_layout, 0)
        self.other_layout.addLayout(self.template_form, 0)
        self.setup_layout.addStretch(1)

        # Tab1 input
        self.analysis_type = "mini"
        self.load_acq_label = QLabel("Acquisition(s)")
        self.load_layout.addWidget(self.load_acq_label)
        self.load_widget = ListView()
        self.load_widget.model().signals.progress.connect(self.updateProgress)
        self.load_widget.setAnalysisType(self.analysis_type)
        self.load_layout.addWidget(self.load_widget)

        self.b_start_edit = LineEdit()
        self.b_start_edit.setObjectName("b_start_edit")
        self.b_start_edit.setEnabled(True)
        self.b_start_edit.setText("0")
        self.input_layout.addRow("Baseline start (ms)", self.b_start_edit)

        self.b_end_edit = LineEdit()
        self.b_end_edit.setObjectName("b_end_edit")
        self.b_end_edit.setEnabled(True)
        self.b_end_edit.setText("80")
        self.input_layout.addRow("Baseline end (ms)", self.b_end_edit)

        self.rc_checkbox = QCheckBox()
        self.rc_checkbox.setObjectName("rc_checkbox")
        self.rc_checkbox.setChecked(True)
        self.rc_checkbox.setTristate(False)
        self.input_layout.addRow("RC check", self.rc_checkbox)

        self.rc_check_start_edit = LineEdit()
        self.rc_check_start_edit.setEnabled(True)
        self.rc_check_start_edit.setObjectName("rc_check_start_edit")
        self.rc_check_start_edit.setText("10000")
        self.input_layout.addRow("RC check start (ms)", self.rc_check_start_edit)

        self.rc_check_end_edit = LineEdit()
        self.rc_check_end_edit.setEnabled(True)
        self.rc_check_end_edit.setObjectName("rc_check_end_edit")
        self.rc_check_end_edit.setText("10300")
        self.input_layout.addRow("RC check end (ms)", self.rc_check_end_edit)

        filters = ExpManager.filters
        self.filter_selection = QComboBox(self)
        self.filter_selection.addItems(filters)
        self.filter_selection.setMinimumContentsLength(len(max(filters, key=len)))
        self.filter_selection.currentTextChanged.connect(self.setFiltProp)
        self.filter_selection.setObjectName("filter_selection")
        self.input_layout.addRow("Filter type", self.filter_selection)

        self.order_label = QLabel("Order")
        self.order_edit = LineEdit()
        self.order_edit.setValidator(QIntValidator())
        self.order_edit.setObjectName("order_edit")
        self.order_edit.setEnabled(True)
        self.order_edit.setText("201")
        self.input_layout.addRow(self.order_label, self.order_edit)

        self.high_pass_edit = LineEdit()
        self.high_pass_edit.setValidator(QIntValidator())
        self.high_pass_edit.setObjectName("high_pass_edit")
        self.high_pass_edit.setEnabled(True)
        self.input_layout.addRow("High pass", self.high_pass_edit)

        self.high_width_edit = LineEdit()
        self.high_width_edit.setValidator(QIntValidator())
        self.high_width_edit.setObjectName("high_width_edit")
        self.high_width_edit.setEnabled(True)
        self.input_layout.addRow("High width", self.high_width_edit)

        self.low_pass_edit = LineEdit()
        self.low_pass_edit.setValidator(QIntValidator())
        self.low_pass_edit.setObjectName("low_pass_edit")
        self.low_pass_edit.setEnabled(True)
        self.low_pass_edit.setText("600")
        self.input_layout.addRow("Low pass", self.low_pass_edit)

        self.low_width_edit = LineEdit()
        self.low_width_edit.setValidator(QIntValidator())
        self.low_width_edit.setObjectName("low_width_edit")
        self.low_width_edit.setEnabled(True)
        self.low_width_edit.setText("600")
        self.input_layout.addRow("Low width", self.low_width_edit)

        windows = ExpManager.windows
        self.window_edit = QComboBox(self)
        self.window_edit.addItems(windows)
        self.window_edit.setMinimumContentsLength(len(max(windows, key=len)))
        self.window_edit.currentTextChanged.connect(self.windowChanged)
        self.window_edit.setObjectName("window_edit")
        self.input_layout.addRow("Window type", self.window_edit)

        self.beta_sigma_label = QLabel("Beta")
        self.beta_sigma = QDoubleSpinBox()
        self.beta_sigma.setMinimumWidth(70)
        self.beta_sigma.setObjectName("beta_sigma")
        self.input_layout.addRow(self.beta_sigma_label, self.beta_sigma)

        self.polyorder_label = QLabel("Polyorder")
        self.polyorder_edit = LineEdit()
        self.polyorder_edit.setValidator(QIntValidator())
        self.polyorder_edit.setObjectName("polyorder_edit")
        self.polyorder_edit.setEnabled(True)
        self.input_layout.addRow(self.polyorder_label, self.polyorder_edit)

        self.analyze_acq_button = QPushButton("Analyze acquisition(s)")
        self.input_layout.addRow(self.analyze_acq_button)
        self.analyze_acq_button.setObjectName("analyze_acq_button")
        self.analyze_acq_button.clicked.connect(self.analyze)

        self.calculate_parameters = QPushButton("Final analysis")
        self.input_layout.addRow(self.calculate_parameters)
        self.calculate_parameters.setObjectName("calculate_parameters")
        self.calculate_parameters.clicked.connect(self.runFinalAnalysis)

        self.reset_button = QPushButton("Reset analysis")
        self.input_layout.addRow(self.reset_button)
        self.reset_button.clicked.connect(self.reset)

        self.reset_button.setObjectName("reset_button")

        self.sensitivity_edit = LineEdit()
        self.sensitivity_edit.setObjectName("sensitivity_edit")
        self.sensitivity_edit.setEnabled(True)
        self.sensitivity_edit.setText("4")
        self.settings_layout.addRow("Deconvolution threshold", self.sensitivity_edit)

        self.amp_thresh_edit = LineEdit()
        self.amp_thresh_edit.setObjectName("amp_thresh_edit")
        self.amp_thresh_edit.setEnabled(True)
        self.amp_thresh_edit.setText("4")
        self.settings_layout.addRow("Amplitude threshold (pA)", self.amp_thresh_edit)

        self.mini_spacing_edit = LineEdit()
        self.mini_spacing_edit.setObjectName("mini_spacing_edit")
        self.mini_spacing_edit.setEnabled(True)
        self.mini_spacing_edit.setText("2")
        self.settings_layout.addRow("Min mini spacing (ms)", self.mini_spacing_edit)

        self.min_rise_time = LineEdit()
        self.min_rise_time.setObjectName("min_rise_time")
        self.min_rise_time.setEnabled(True)
        self.min_rise_time.setText("0.5")
        self.settings_layout.addRow("Min rise time (ms)", self.min_rise_time)

        self.max_rise_time = LineEdit()
        self.max_rise_time.setObjectName("max_rise_time")
        self.max_rise_time.setEnabled(True)
        self.max_rise_time.setText("4")
        self.settings_layout.addRow("Max rise time (ms)", self.max_rise_time)

        self.min_decay = LineEdit()
        self.min_decay.setObjectName("min_decay")
        self.min_decay.setEnabled(True)
        self.min_decay.setText("0.5")
        self.settings_layout.addRow("Min decay time (ms)", self.min_decay)

        self.event_length = LineEdit()
        self.event_length.setObjectName("event_length")
        self.event_length.setText("30")
        self.settings_layout.addRow("Max event length (ms)", self.event_length)

        self.decay_rise = QCheckBox()
        self.decay_rise.setObjectName("decay_rise")
        self.decay_rise.setChecked(True)
        self.decay_rise.setTristate(False)
        self.settings_layout.addRow("Decay slower than rise time", self.decay_rise)

        self.curve_fit_decay = QCheckBox(self)
        self.curve_fit_decay.setObjectName("curve_fit_decay")
        self.curve_fit_decay.setChecked(False)
        self.curve_fit_decay.setTristate(False)
        self.settings_layout.addRow("Curve fit decay", self.curve_fit_decay)

        fit_types = ["exp", "db_exp"]
        self.curve_fit_edit = QComboBox(self)
        self.curve_fit_edit.addItems(fit_types)
        self.curve_fit_edit.setMinimumContentsLength(len(max(fit_types, key=len)))
        self.curve_fit_edit.setObjectName("curve_fit_type")
        self.settings_layout.addRow("Curve fit type", self.curve_fit_edit)

        self.invert_checkbox = QCheckBox(self)
        self.invert_checkbox.setObjectName("invert_checkbox")
        self.invert_checkbox.setChecked(False)
        self.invert_checkbox.setTristate(False)
        self.settings_layout.addRow(
            "Invert (for positive currents)", self.invert_checkbox
        )

        self.decon_type_edit = QComboBox(self)
        decon_list = ["wiener", "fft", "convolution"]
        self.decon_type_edit.addItems(decon_list)
        self.decon_type_edit.setMinimumContentsLength(len(max(decon_list, key=len)))
        self.decon_type_edit.setObjectName("event_finding_method_edit")
        self.settings_layout.addRow("Event finding method", self.decon_type_edit)

        self.baseline_corr_choice = QCheckBox()
        self.baseline_corr_choice.setChecked(False)
        self.baseline_corr_choice.setTristate(False)
        self.settings_layout.addRow(
            "Baseline correction (experimental)", self.baseline_corr_choice
        )

        self.tau_1_edit = LineEdit()
        self.tau_1_edit.setObjectName("tau_1_edit")
        self.tau_1_edit.setEnabled(True)
        self.tau_1_edit.setText("0.3")
        self.template_form.addRow("Rise tau (ms)", self.tau_1_edit)

        self.tau_2_edit = LineEdit()
        self.tau_2_edit.setObjectName("tau_2_edit")
        self.tau_2_edit.setEnabled(True)
        self.tau_2_edit.setText("5")
        self.template_form.addRow("Decay tau (ms)", self.tau_2_edit)

        self.amplitude_edit = LineEdit()
        self.amplitude_edit.setObjectName("amplitude_edit")
        self.amplitude_edit.setEnabled(True)
        self.amplitude_edit.setText("-20")
        self.template_form.addRow("Amplitude (pA)", self.amplitude_edit)

        self.risepower_edit = LineEdit()
        self.risepower_edit.setObjectName("risepower_edit")
        self.risepower_edit.setEnabled(True)
        self.risepower_edit.setText("0.5")
        self.template_form.addRow("Risepower", self.risepower_edit)

        self.temp_length_edit = LineEdit()
        self.temp_length_edit.setObjectName("temp_length_edit")
        self.temp_length_edit.setEnabled(True)
        self.temp_length_edit.setText("30")
        self.template_form.addRow("Template length (ms)", self.temp_length_edit)

        self.spacer_edit = LineEdit()
        self.spacer_edit.setObjectName("spacer_edit")
        self.spacer_edit.setEnabled(True)
        self.spacer_edit.setText("1.5")
        self.template_form.addRow("Spacer (ms)", self.spacer_edit)

        self.sample_rate_edit = LineEdit()
        self.sample_rate_edit.setObjectName("sample_rate_edit")
        self.sample_rate_edit.setEnabled(True)
        self.sample_rate_edit.setText("10000")
        self.template_form.addRow("Sample rate", self.sample_rate_edit)

        self.template_button = QPushButton("Create template")
        self.template_form.addRow(self.template_button)
        # self.template_button.setMinimumWidth(250)
        self.template_button.clicked.connect(self.createTemplate)
        self.template_button.setObjectName("template_button")

        self.template_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        self.template_plot.setObjectName("Template plot")
        self.template_plot.setMinimumHeight(300)
        self.extra_layout.addWidget(self.template_plot, 10)

        # Setup for the drag and drop load layout
        self.inspect_acqs_button = QPushButton("Inspect acq(s)")
        self.load_layout.addWidget(self.inspect_acqs_button)
        self.inspect_acqs_button.clicked.connect(self.inspectAcqs)

        self.del_sel_button = QPushButton("Delete selection")
        self.load_layout.addWidget(self.del_sel_button)
        self.del_sel_button.clicked.connect(self.delSelection)

        # Tab 2 layouts
        self.d1 = Dock("Overview")
        self.d2 = Dock("Mini")
        self.d3 = Dock("Acq view")
        self.d1.hideTitleBar()
        self.d2.hideTitleBar()
        self.d3.hideTitleBar()
        self.dock_area2.addDock(self.d1, "left")
        self.dock_area2.addDock(self.d2, "right")
        self.dock_area2.addDock(self.d3, "bottom")
        self.acq_scroll = QScrollArea()
        self.acq_scroll.setContentsMargins(20, 20, 20, 20)
        self.acq_widget = QWidget()
        # self.acq_scroll.setMinimumWidth(250)
        self.acq_scroll.setWidget(self.acq_widget)
        self.acq_scroll.setWidgetResizable(True)
        self.d3.addWidget(self.acq_scroll, 0, 0)
        # self.d3.layout.setColumnStretch(0, 0)
        self.acq_buttons = QGridLayout()
        self.acq_widget.setLayout(self.acq_buttons)

        # Tab2 acq_buttons layout
        self.acquisition_number_label = QLabel("Acq number")
        self.acquisition_number_label.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.acquisition_number_label.setMaximumWidth(70)

        self.acq_buttons.addWidget(self.acquisition_number_label, 0, 0)
        self.acquisition_number = QSpinBox()
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)
        self.acquisition_number.setMaximumWidth(70)
        self.acq_buttons.addWidget(self.acquisition_number, 0, 1)
        self.acquisition_number.valueChanged.connect(self.acqSpinbox)

        self.epoch_label = QLabel("Epoch")
        self.epoch_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.acq_buttons.addWidget(self.epoch_label, 1, 0)
        self.epoch_edit = QLineEdit()
        self.epoch_edit.setMaximumWidth(70)
        self.acq_buttons.addWidget(self.epoch_edit, 1, 1)

        self.baseline_mean_label = QLabel("Baseline mean")
        self.baseline_mean_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.acq_buttons.addWidget(self.baseline_mean_label, 2, 0)
        self.baseline_mean_edit = QLineEdit()
        self.baseline_mean_edit.setMaximumWidth(70)
        self.acq_buttons.addWidget(self.baseline_mean_edit, 2, 1)

        self.left_button = QToolButton()
        self.left_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.left_button.pressed.connect(self.leftbutton)
        self.left_button.setArrowType(Qt.LeftArrow)
        self.left_button.setAutoRepeat(True)
        self.left_button.setAutoRepeatInterval(50)
        self.left_button.setMinimumWidth(70)
        self.left_button.setMaximumWidth(70)
        self.acq_buttons.addWidget(self.left_button, 3, 0)

        self.right_button = QToolButton()
        self.right_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.right_button.pressed.connect(self.rightbutton)
        self.right_button.setArrowType(Qt.RightArrow)
        self.right_button.setAutoRepeat(True)
        self.right_button.setAutoRepeatInterval(50)
        self.right_button.setMinimumWidth(70)
        self.right_button.setMaximumWidth(70)
        self.acq_buttons.addWidget(self.right_button, 3, 1)

        self.slider_sensitivity = QSlider()
        self.slider_sensitivity.setObjectName("mini plot slider")
        self.slider_sensitivity.setOrientation(Qt.Horizontal)
        self.slider_sensitivity.setValue(20)
        self.slider_sensitivity.valueChanged.connect(self.slider_value)
        self.acq_buttons.addWidget(self.slider_sensitivity, 4, 0, 1, 2)

        self.create_mini_button = QPushButton("Create new mini")
        self.create_mini_button.clicked.connect(self.createMini)
        self.create_mini_action = QAction("Create new mini")
        self.create_mini_action.triggered.connect(self.createMini)
        self.acq_buttons.addWidget(self.create_mini_button, 5, 0, 1, 2)

        self.delete_acq_button = QPushButton("Delete acquisition")
        self.delete_acq_button.clicked.connect(self.deleteAcq)
        self.acq_buttons.addWidget(self.delete_acq_button, 6, 0, 1, 2)

        self.reset_recent_acq_button = QPushButton("Reset recent deleted acq")
        self.reset_recent_acq_button.clicked.connect(self.resetRecentRejectedAcq)

        self.acq_buttons.addWidget(self.reset_recent_acq_button, 7, 0, 1, 2)

        self.reset_acq_button = QPushButton("Reset deleted acqs")
        self.reset_acq_button.clicked.connect(self.resetRejectedAcqs)

        self.acq_buttons.addWidget(self.reset_acq_button, 8, 0, 1, 2)

        self.acq_buttons.setRowStretch(9, 10)

        self.calculate_parameters_2 = QPushButton("Final analysis")
        self.acq_buttons.addWidget(self.calculate_parameters_2)
        self.calculate_parameters_2.clicked.connect(self.runFinalAnalysis)
        self.acq_buttons.addWidget(self.calculate_parameters_2, 10, 0, 1, 2)

        self.delete_acq_action = QAction("Delete acq")
        self.delete_acq_action.triggered.connect(self.deleteAcq)

        self.reset_recent_acq_action = QAction("Reset recent del acq")
        self.reset_recent_acq_action.triggered.connect(self.resetRecentRejectedAcq)

        self.reset_acq_action = QAction("Reset del acq(s)")
        self.reset_acq_action.triggered.connect(self.resetRejectedAcqs)

        # Filling the plot layout.
        self.p1 = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        self.p1.setObjectName("p1")
        p1pi = self.p1.getViewBox()
        p1pi.menu.addSeparator()
        p1pi.menu.addAction(self.create_mini_action)
        p1pi.menu.addAction(self.delete_acq_action)
        p1pi.menu.addAction(self.reset_recent_acq_action)
        p1pi.menu.addAction(self.reset_acq_action)
        self.d3.addWidget(self.p1, 0, 1)
        self.d3.layout.setColumnStretch(1, 10)

        self.p2 = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        self.p2.setObjectName("p2")
        p2pi = self.p2.getViewBox()
        p2pi.menu.addSeparator()
        p2pi.menu.addAction(self.delete_acq_action)
        p2pi.menu.addAction(self.reset_recent_acq_action)
        p2pi.menu.addAction(self.reset_acq_action)
        self.d1.addWidget(self.p2)

        self.region = pg.LinearRegionItem()

        # Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this
        self.region.sigRegionChanged.connect(self.update)
        self.p1.sigRangeChanged.connect(self.updateRegion)

        # Set the initial bounds of the region and its layer
        # position.
        self.region.setRegion([0, 400])
        self.region.setZValue(10)

        self.mini_view_widget = QWidget()
        self.mini_view_scroll = QScrollArea()
        # self.mini_view_scroll.setMinimumWidth(200)
        self.mini_view_scroll.setContentsMargins(20, 20, 20, 20)
        self.mini_view_scroll.setWidget(self.mini_view_widget)
        self.mini_view_scroll.setWidgetResizable(True)
        self.d2.addWidget(self.mini_view_scroll, 0, 0)
        self.d2.layout.setColumnStretch(0, 0)
        self.mini_layout = QFormLayout()
        self.mini_view_widget.setLayout(self.mini_layout)

        self.mini_number_label = QLabel("Event")
        self.mini_number = QSpinBox()
        self.mini_number.setMaximumWidth(70)
        self.mini_number.setKeyboardTracking(False)
        self.mini_layout.addRow(self.mini_number_label, self.mini_number)
        self.mini_number.setEnabled(True)
        self.mini_number.setMinimumWidth(70)
        self.mini_number.valueChanged.connect(self.mini_spinbox)

        self.mini_baseline_label = QLabel("Baseline (pA)")
        self.mini_baseline_label.setStyleSheet("""color:#00ff00; font-weight:bold""")
        self.mini_baseline = QLineEdit()
        self.mini_baseline.setMaximumWidth(70)
        self.mini_baseline.setReadOnly(True)
        self.mini_layout.addRow(self.mini_baseline_label, self.mini_baseline)

        self.mini_amplitude_label = QLabel("Amplitude (pA)")
        self.mini_amplitude_label.setStyleSheet("""color:#ff00ff; font-weight:bold""")
        self.mini_amplitude = QLineEdit()
        self.mini_amplitude.setMaximumWidth(70)
        self.mini_amplitude.setReadOnly(True)
        self.mini_layout.addRow(self.mini_amplitude_label, self.mini_amplitude)

        self.mini_tau_label = QLabel("Est tau (ms)")
        self.mini_tau = QLineEdit()
        self.mini_tau.setMaximumWidth(70)
        self.mini_tau.setReadOnly(True)
        self.mini_tau_label.setStyleSheet("""color:#0000ff; font-weight: bold;""")
        self.mini_layout.addRow(self.mini_tau_label, self.mini_tau)

        self.mini_rise_time_label = QLabel("Rise time (ms)")
        self.mini_rise_time = QLineEdit()
        self.mini_rise_time.setMaximumWidth(70)
        self.mini_rise_time.setReadOnly(True)
        self.mini_layout.addRow(self.mini_rise_time_label, self.mini_rise_time)

        self.mini_rise_rate_label = QLabel("Rise rate (pA/ms)")
        self.mini_rise_rate = QLineEdit()
        self.mini_rise_rate.setMaximumWidth(70)
        self.mini_rise_rate.setReadOnly(True)
        self.mini_layout.addRow(self.mini_rise_rate_label, self.mini_rise_rate)

        self.delete_mini_button = QPushButton("Delete event")
        self.mini_layout.addRow(self.delete_mini_button)
        self.delete_mini_button.clicked.connect(self.deleteMini)
        self.delete_mini_action = QAction("Delete event")
        self.delete_mini_action.triggered.connect(self.deleteMini)

        self.set_baseline = QPushButton("Set point as baseline")
        self.mini_layout.addRow(self.set_baseline)
        self.set_baseline.clicked.connect(self.setPointAsBaseline)
        self.set_baseline_action = QAction("Set point as baseline")
        self.set_baseline_action.triggered.connect(self.setPointAsBaseline)

        self.set_peak = QPushButton("Set point as peak")
        self.mini_layout.addRow(self.set_peak)
        self.set_peak.clicked.connect(self.setPointAsPeak)
        self.set_peak_action = QAction("Set point as peak")
        self.set_peak_action.triggered.connect(self.setPointAsPeak)

        self.mini_view_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        mp = self.mini_view_plot.getViewBox()
        mp.menu.addSeparator()
        mp.menu.addAction(self.delete_mini_action)
        mp.menu.addAction(self.set_baseline_action)
        mp.menu.addAction(self.set_peak_action)

        # self.mini_view_plot.setMinimumWidth(300)
        self.mini_view_plot.setObjectName("Mini view plot")
        self.d2.addWidget(self.mini_view_plot, 0, 1)
        self.d2.layout.setColumnStretch(1, 10)

        # Tab 3 layouts and setup
        self.table_dock = Dock("Table")
        self.table_dock.hideTitleBar()
        self.ave_mini_dock = Dock("Mini")
        self.ave_mini_dock.hideTitleBar()
        self.data_dock = Dock("Data")
        self.data_dock.hideTitleBar()
        self.dock_area3.addDock(self.table_dock, position="left")
        self.dock_area3.addDock(self.ave_mini_dock, position="right")
        self.dock_area3.addDock(self.data_dock, position="bottom")
        self.ave_mini_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}
        )
        self.ave_mini_dock.addWidget(self.ave_mini_plot)
        self.ave_mini_plot.setObjectName("Ave mini plot")
        self.final_tab_widget = QTabWidget()
        self.final_tab_widget.setMinimumHeight(300)
        self.table_dock.addWidget(self.final_tab_widget)
        self.stem_plot = pg.PlotWidget(labels={"bottom": "Time (ms)"})
        self.amp_dist = pg.PlotWidget()
        self.plot_selector = QComboBox()
        self.plot_selector.setMaximumWidth(100)
        self.plot_selector.currentTextChanged.connect(self.plotRawData)
        self.data_dock.addWidget(self.plot_selector, 0, 0)
        self.data_dock.addWidget(self.stem_plot, 0, 1)
        self.data_dock.addWidget(self.amp_dist, 0, 2)

        self.exp_manager = ExpManager()
        self.load_widget.setData(self.exp_manager)
        self.last_mini_deleted = {}
        self.last_mini_deleted = []
        self.last_mini_point_clicked = None
        self.last_acq_point_clicked = None
        self.mini_spinbox_list = []
        self.last_mini_clicked_1 = []
        self.last_mini_clicked_2 = []
        self.sort_index = []
        self.template = []
        self.mini_spinbox_list = []
        self.minis_deleted = 0
        self.calc_param_clicked = False
        self.table_dict = {}
        self.need_to_save = False
        self.modify = 20

        # Shortcuts
        self.del_mini_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.del_mini_shortcut.activated.connect(self.deleteMini)

        self.create_mini_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.create_mini_shortcut.activated.connect(self.createMini)

        self.set_baseline = QShortcut(QKeySequence("Ctrl + B"), self)
        self.set_baseline.activated.connect(self.setPointAsBaseline)

        self.set_peak = QShortcut(QKeySequence("Ctrl + P"), self)
        self.set_peak.activated.connect(self.setPointAsPeak)

        self.del_acq_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        self.del_acq_shortcut.activated.connect(self.deleteAcq)

        self.setWidth()

    def windowChanged(self, text):
        if text == "Gaussian":
            self.beta_sigma_label.setText("Sigma")
        else:
            self.beta_sigma_label.setText("Beta")

    def setFiltProp(self, text):
        if text == "median":
            self.order_label.setText("Window size")
        elif text == "savgol":
            self.order_label.setText("Window size")
            self.polyorder_label.setText("Polyorder")
        elif text == "ewma":
            self.order_label.setText("Window size")
            self.polyorder_label.setText("Sum proportion")
        else:
            self.order_label.setText("Order")
            self.polyorder_label.setText("Polyorder")

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

    def inspectAcqs(self):
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
        else:
            self.inspection_widget.clearData()
            self.inspection_widget.setData(self.analysis_type, self.exp_manager)
            self.inspection_widget.show()

    def delSelection(self):
        # Deletes the selected acquisitions from the list
        indices = self.load_widget.selectedIndexes()
        if len(indices) > 0:
            self.load_widget.deleteSelection(indices)
            self.load_widget.clearSelection()

    def createTemplate(self):
        self.template_plot.clear()
        amplitude = self.amplitude_edit.toFloat()
        tau_1 = self.tau_1_edit.toFloat()
        tau_2 = self.tau_2_edit.toFloat()
        risepower = self.risepower_edit.toFloat()
        length = self.temp_length_edit.toFloat()
        spacer = self.spacer_edit.toFloat()
        sample_rate = self.sample_rate_edit.toInt()
        template = create_template(
            amplitude,
            tau_1,
            tau_2,
            risepower,
            length,
            spacer,
            sample_rate,
        )
        s_r_c = sample_rate / 1000
        self.template_plot.plot(x=(np.arange(len(template)) / s_r_c), y=template)

    def analyze(self):
        """
        This function creates each MiniAnalysis object and puts
        it into a dictionary. The minis are create within the
        MiniAnalysis objection. Note that the created
        MiniAnalysis object needs to have analyze run. This was
        chosen because it made the initial debugging easier.
        """

        self.p1.clear()
        self.p2.clear()
        self.p1.setAutoVisible(y=True)
        self.p2.enableAutoRange()
        self.mini_view_plot.clear()

        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            self.analyze_acq_button.setEnabled(True)
            return None

        self.need_to_save = True

        self.analyze_acq_button.setEnabled(False)
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)

        # Sets the progress bar to 0
        self.pbar.setFormat("Analyzing...")
        self.pbar.setValue(0)

        # The for loop creates each MiniAnalysis object. Enumerate returns
        # count which is used to adjust the progress bar and acq_components
        # comes from the load_widget
        if (
            self.window_edit.currentText() == "gaussian"
            or self.window_edit.currentText() == "kaiser"
        ):
            window = (self.window_edit.currentText(), self.beta_sigma.value())
        else:
            window = self.window_edit.currentText()
        # I need to just put all the settings into a dictionary,
        # so the functions are not called for every acquisition
        worker = ThreadWorker(
            self.exp_manager,
            "analyze",
            exp=self.analysis_type,
            filter_args={
                "baseline_start": self.b_start_edit.toInt(),
                "baseline_end": self.b_end_edit.toInt(),
                "filter_type": self.filter_selection.currentText(),
                "order": self.order_edit.toInt(),
                "high_pass": self.high_pass_edit.toFloat(),
                "high_width": self.high_width_edit.toFloat(),
                "low_pass": self.low_pass_edit.toFloat(),
                "low_width": self.low_width_edit.toFloat(),
                "window": window,
                "polyorder": self.polyorder_edit.toInt(),
                "rc_check": self.rc_checkbox.isChecked(),
                "rc_check_start": self.rc_check_start_edit.toFloat(),
                "rc_check_end": self.rc_check_end_edit.toFloat(),
                "baseline_corr": self.baseline_corr_choice.isChecked(),
            },
            analysis_args={
                "sensitivity": self.sensitivity_edit.toFloat(),
                "amp_threshold": self.amp_thresh_edit.toFloat(),
                "mini_spacing": self.mini_spacing_edit.toFloat(),
                "min_rise_time": self.min_rise_time.toFloat(),
                "max_rise_time": self.max_rise_time.toFloat(),
                "min_decay_time": self.min_decay.toFloat(),
                "event_length": self.event_length.toInt(),
                "decay_rise": self.decay_rise.isChecked(),
                "invert": self.invert_checkbox.isChecked(),
                "decon_type": self.decon_type_edit.currentText(),
                "curve_fit_decay": self.curve_fit_decay.isChecked(),
                "curve_fit_type": self.curve_fit_edit.currentText(),
            },
            template_args={
                "tmp_amplitude": self.amplitude_edit.toFloat(),
                "tmp_tau_1": self.tau_1_edit.toFloat(),
                "tmp_tau_2": self.tau_2_edit.toFloat(),
                "tmp_risepower": self.risepower_edit.toFloat(),
                "tmp_length": self.temp_length_edit.toFloat(),
                "tmp_spacer": self.spacer_edit.toFloat(),
            },
        )
        worker.signals.progress.connect(self.updateProgress)
        worker.signals.finished.connect(self.setAcquisition)
        QThreadPool.globalInstance().start(worker)

    def setAcquisition(self):
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)

        # Minis always start from 0 since list indexing in python starts
        # at zero. I choose this because it is easier to reference minis
        # when adding or removing minis and python list indexing starts at 0.
        self.mini_number.setMinimum(0)
        # self.mini_spinbox(0)

        # Enabling the buttons since they were temporarily disabled while
        # The acquisitions were analyzed.
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(1)
        self.pbar.setFormat("Analysis finished")

    def acqSpinbox(self, h):
        """This function plots each acquisition and each of its minis."""

        if not self.exp_manager.analyzed:
            self.fileDoesNotExist()
            return None

        # Plots are cleared first otherwise new data is just appended to
        # the plot.
        self.need_to_save = True
        self.p1.clear()
        self.p2.clear()
        self.p1.setAutoVisible(y=True)
        self.p2.enableAutoRange()
        self.mini_view_plot.clear()

        # Reset the clicked points since we do not want to accidentally
        # adjust plot items on the new acquisition
        self.last_acq_point_clicked = None
        self.last_mini_clicked_1 = []
        self.last_mini_clicked_2 = []
        self.last_mini_point_clicked = None

        # sort_index and mini_spinbox_list are used to reference the correct
        # mini when using the mini_spinbox. This was choosen because you cannot
        # sort GUI objects when they are presented on the screen.
        self.sort_index = []
        self.mini_spinbox_list = []

        # Temporarily disable the acquisition number to prevent some weird behavior
        # where the the box will skip every other acquisition.
        self.acquisition_number.setEnabled(False)

        # I choose to just show
        acq_dict = self.exp_manager.exp_dict["mini"]
        if acq_dict.get(self.acquisition_number.value()):
            # Creates a reference to the acquisition object so that the
            # acquisition object does not have to be referenced from
            # acquisition dictionary. Makes it more readable.
            acq_object = acq_dict.get(self.acquisition_number.value())

            # Set the epoch
            self.epoch_edit.setText(acq_object.epoch)

            # Create the acquisitions plot item for the main acquisition plot
            acq_plot = pg.PlotDataItem(
                x=acq_object.plot_acq_x(),
                y=acq_object.plot_acq_y(),
                name=str(self.acquisition_number.text()),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            # Creates the ability to click on specific points in the main
            # acquisition plot window. The function acqPlotClicked stores
            # the point clicked for later use and is used when creating a
            # new mini.
            acq_plot.sigPointsClicked.connect(self.acqPlotClicked)

            # Add the plot item to the plot. Need to do it this way since
            # the ability to the click on specific points is need.
            self.p1.addItem(acq_plot)
            self.p1.setYRange(
                min(acq_object.final_array),
                max(acq_object.final_array),
                padding=0.1,
            )

            # Add the draggable region to p2.
            self.p2.addItem(self.region, ignoreBounds=True)

            # Create the plot with the draggable region. Since there is
            # no interactivity with this plot there is no need to create
            # a plot item.
            self.p2.plot(x=acq_object.plot_acq_x(), y=acq_object.plot_acq_y())

            # Enabled the acquisition number since it was disabled earlier.
            self.acquisition_number.setEnabled(True)

            # Plot the postsynaptic events.
            if acq_object.postsynaptic_events:
                # Create the mini list and the true index of each mini.
                # Since the plot items on a pyqtgraph plot cannot be sorted
                # I had to create a way to correctly reference the position
                # of minis when adding new minis because I ended up just
                # adding the new minis to postsynaptic events list.
                self.sort_index = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].sort_index()
                self.mini_spinbox_list = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].list_of_events()

                # Plot each mini. Since the postsynaptic events are stored in
                # a list you can iterate through the list even if there is just
                # one event because lists are iterable in python.
                for i in self.mini_spinbox_list:
                    # Create the mini plot item that is added to the p1 plot.
                    mini_plot = pg.PlotCurveItem(
                        x=acq_object.postsynaptic_events[i].mini_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].mini_y_comp()[:2],
                        pen="g",
                        name=i,
                        clickable=True,
                    )
                    # Adds the clicked functionality to the mini plot item.
                    mini_plot.sigClicked.connect(self.miniClicked)
                    self.p1.addItem(mini_plot)

                    # Minis plotted on p2 do not need any interactivity. You have
                    # create new mini plot items for each plot because one graphic
                    # item cannot be used in multiple parts of a GUI in Qt.
                    self.p2.plot(
                        x=acq_object.postsynaptic_events[i].mini_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].mini_y_comp()[:2],
                        pen="g",
                    )

                # Set the mini spinbox to the first mini and sets the min
                # an max value. I choose to start the minis at 0 because it
                # is easier to work with mini referenceing
                self.mini_number.setMinimum(0)
                self.mini_number.setMaximum(self.mini_spinbox_list[-1])
                self.mini_number.setValue(0)
                self.mini_spinbox(0)
            else:
                self.acquisition_number.setEnabled(True)
        else:
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.p2.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.p2.addItem(text)
            self.acquisition_number.setEnabled(True)

    def reset(self):
        """
        This function resets all the variables and clears all the plots.
        It takes a while to run.
        """
        self.p1.clear()
        self.p2.clear()
        self.template_plot.clear()
        self.load_widget.clearData()
        self.calc_param_clicked = False
        self.mini_view_plot.clear()
        self.last_mini_point_clicked = None
        self.last_acq_point_clicked = None
        self.last_mini_clicked_1 = []
        self.last_mini_clicked_2 = []
        self.mini_spinbox_list = []
        self.sort_index = []
        self.stem_plot.clear()
        self.amp_dist.clear()
        self.ave_mini_plot.clear()
        self.inspection_widget.clearData()
        self.calc_param_clicked = False
        self.need_to_save = False
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.plot_selector.clear()
        self.pbar.setFormat("Ready to analyze")
        self.pbar.setValue(0)
        self.exp_manager = ExpManager()
        self.load_widget.setData(self.exp_manager)
        self.clearTables()

    def update(self):
        """
        This functions is used for the draggable region.
        See PyQtGraphs documentation for more information.
        """
        self.region.setZValue(10)
        minX, maxX = self.region.getRegion()
        self.p1.setXRange(minX, maxX, padding=0)

    def updateRegion(self, window, viewRange):
        """
        This functions is used for the draggable region.
        See PyQtGraphs documentation for more information
        """
        rgn = viewRange[0]
        self.region.setRegion(rgn)

    def slider_value(self, value):
        self.modify = value

    def leftbutton(self):
        if self.left_button.isDown():
            minX, maxX = self.region.getRegion()
            self.region.setRegion([minX - self.modify, maxX - self.modify])

    def rightbutton(self):
        if self.right_button.isDown():
            minX, maxX = self.region.getRegion()
            self.region.setRegion([minX + self.modify, maxX + self.modify])

    def acqPlotClicked(self, item, points):
        """
        Returns the points clicked in the acquisition plot window.
        """
        if self.last_acq_point_clicked is not None:
            self.last_acq_point_clicked.resetPen()
            self.last_acq_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setSize(size=12)
        self.last_acq_point_clicked = points[0]

    def miniClicked(self, item):
        """
        Set the mini spinbox to the mini that was clicked in the acquisition
        window.
        """
        self.mini_number.setValue(self.sort_index.index(int(item.name())))
        self.mini_spinbox(self.sort_index.index(int(item.name())))

    def mini_spinbox(self, h):
        """
        Function to plot a mini in the mini plot.
        """

        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None

        self.need_to_save = True

        # if h in self.mini_spinbox_list:
        # Clear the last mini_point_clicked
        self.last_mini_point_clicked = None

        # Resets the color of the minis on p1 and p2. In python
        # when you create an object it is given a position in the memory
        # you can create new "pointers" to the object. This makes it
        # easy to modify Qt graphics objects without having to find them
        # under their original parent.
        if self.last_mini_clicked_1:
            self.last_mini_clicked_1.setPen("g")
            self.last_mini_clicked_2.setPen("g")

        # Clear the mini plot
        self.mini_view_plot.clear()

        # Return the correct index of the mini. This is needed because of
        # how new minis are created
        mini_index = self.sort_index[h]

        # Reference the mini.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        mini = acq.postsynaptic_events[mini_index]

        # This allows the window on p1 to follow each mini when using
        # the mini spinbox. The window will only adjust if any part of
        # the mini array falls outside of the current viewable region.
        minX, maxX = self.region.getRegion()
        width = maxX - minX
        if mini.plot_event_x()[0] < minX or mini.plot_event_x()[-1] > maxX:
            self.region.setRegion(
                [
                    int(mini.plot_event_x()[0] - 100),
                    int(mini.plot_event_x()[0] + width - 100),
                ]
            )

        # Create the mini plot item. The x_array is a method call
        # because it needs to be corrected for sample rate and
        # displayed as milliseconds.
        mini_item = pg.PlotDataItem(
            x=mini.plot_event_x(),
            y=mini.plot_event_y(),
            pen=pg.mkPen(linewidth=3),
            symbol="o",
            symbolPen=None,
            symbolBrush="w",
            symbolSize=6,
        )

        # Add clickable functionality to the mini plot item.
        mini_item.sigPointsClicked.connect(self.miniPlotClicked)

        # Plot item for the baseline, peak and estimated tau.
        mini_plot_items = pg.PlotDataItem(
            x=mini.mini_x_comp(),
            y=mini.mini_y_comp(),
            pen=None,
            symbol="o",
            symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m"), pg.mkBrush("b")],
            symbolSize=12,
        )

        # Add the plot items to the mini view widget.
        self.mini_view_plot.addItem(mini_item)
        self.mini_view_plot.addItem(mini_plot_items)

        # Plot the fit taus if curve fit was selected.
        if mini.fit_tau is not np.nan and self.curve_fit_decay.isChecked():
            mini_decay_items = pg.PlotDataItem(
                x=mini.fit_decay_x,
                y=mini.fit_decay_y,
                pen=pg.mkPen((255, 0, 255, 175), width=3),
            )
            self.mini_view_plot.addItem(mini_decay_items)

        # Sets the color of the minis on p1 and p2 so that the mini
        # selected with the spinbox or the mini that was clicked is shown.
        self.p2.listDataItems()[mini_index + 1].setPen("m", width=2)
        self.p1.listDataItems()[mini_index + 1].setPen("m", width=2)

        # Creating a reference to the clicked minis.
        self.last_mini_clicked_2 = self.p2.listDataItems()[mini_index + 1]
        self.last_mini_clicked_1 = self.p1.listDataItems()[mini_index + 1]

        # Set the attributes of the mini on the GUI.
        self.mini_amplitude.setText(str(round_sig(mini.amplitude, sig=4)))
        self.mini_tau.setText(str(round_sig(mini.final_tau_x, sig=4)))
        self.mini_rise_time.setText(str(round_sig(mini.rise_time, sig=4)))
        self.mini_rise_rate.setText(str(round_sig(mini.rise_rate, sig=4)))
        self.mini_baseline.setText(str(round_sig(mini.event_start_y, sig=4)))

    def miniPlotClicked(self, item, points):
        """
        Function to make the mini in the mini view widget
        clickable.

        Returns
        -------
        None
        """
        # Resets the color of the previously clicked mini point.
        if self.last_mini_point_clicked:
            self.last_mini_point_clicked.resetPen()
            self.last_mini_point_clicked = None

        # Set the color and size of the new mini point that
        # was clicked.
        points[0].setPen("m", width=4)
        self.last_mini_point_clicked = points[0]

    def setPointAsPeak(self):
        """
        This will set the mini peak as the point selected on the mini plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None

        if self.last_mini_point_clicked is None:
            return None

        self.need_to_save = True

        # if len(self.last_mini_point_clicked) > 0:
        # X and Y point of the mini point that was clicked. The
        # x point needs to be adjusted back to samples for the
        # change amplitude function in the postsynaptic event
        # object.
        x = self.last_mini_point_clicked.pos()[0]
        y = self.last_mini_point_clicked.pos()[1]

        # Find the index of the mini so that the correct mini is
        # modified.
        mini_index = self.sort_index[int(self.mini_number.text())]
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        mini = acq.postsynaptic_events[mini_index]

        # Pass the x and y points to the change amplitude function
        # for the postsynaptic event.
        mini.change_amplitude(x, y)

        # Redraw the minis on p1 and p2 plots. Note that the last
        # mini clicked provides a "pointed" to the correct plot
        # object on p1 and p2 so that it does not have to be
        # referenced again.
        self.last_mini_clicked_1.setData(
            x=mini.mini_x_comp()[:2],
            y=mini.mini_y_comp()[:2],
            color="m",
            width=2,
        )
        self.last_mini_clicked_2.setData(
            x=mini.mini_x_comp()[:2],
            y=mini.mini_y_comp()[:2],
            color="m",
            width=2,
        )

        # This is need to redraw the mini in the mini view.
        self.mini_spinbox(int(self.mini_number.text()))

        # Reset the last point clicked.
        self.last_mini_point_clicked = []
        # else:
        #     pass

    def setPointAsBaseline(self):
        """
        This will set the baseline as the point selected on the mini plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None

        if self.last_mini_point_clicked is None:
            return None

        self.need_to_save = True

        if self.last_mini_point_clicked is not None:
            # X and Y point of the mini point that was clicked. The
            # x point needs to be adjusted back to samples for the
            # change amplitude function in the postsynaptic event
            # object.
            x = self.last_mini_point_clicked.pos()[0]
            y = self.last_mini_point_clicked.pos()[1]

            # Find the index of the mini so that the correct mini is
            # modified.
            mini_index = self.sort_index[int(self.mini_number.text())]

            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
            mini = acq.postsynaptic_events[mini_index]

            # Pass the x and y points to the change baseline function
            # for the postsynaptic event.
            mini.change_baseline(x, y)

            # Redraw the minis on p1 and p2 plots. Note that the last
            # mini clicked provides a "pointed" to the correct plot
            # object on p1 and p2 so that it does not have to be
            # referenced again.
            self.last_mini_clicked_1.setData(
                x=mini.mini_x_comp()[:2],
                y=mini.mini_y_comp()[:2],
                color="m",
                width=2,
            )
            self.last_mini_clicked_2.setData(
                x=mini.mini_x_comp()[:2],
                y=mini.mini_y_comp()[:2],
                color="m",
                width=2,
            )

            # This is need to redraw the mini in the mini view.
            self.mini_spinbox(int(self.mini_number.text()))

            # Reset the last point clicked.
            self.last_mini_point_clicked = None
        # else:
        #     pass

    def deleteMini(self):
        """
        This function deletes a mini from the acquisition and removes it from the
        GUI.

        Returns
        -------
        None
        """
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None
        self.need_to_save = True

        # self.last_mini_deleted = \
        #     self.acq_object.postsynaptic_events[int(self.mini_number.text())]
        self.last_mini_deleted_number = self.mini_number.text()

        # Clear the mini view plot.
        self.mini_view_plot.clear()

        # Find the correct mini.
        mini_index = self.sort_index[int(self.mini_number.text())]

        # Remove the mini from the plots. +1 is added because the first plot
        # item is the acquisition.
        self.p1.removeItem(self.p1.listDataItems()[mini_index + 1])
        self.p2.removeItem(self.p2.listDataItems()[mini_index + 1])

        # Deleted the mini from the postsynaptic events and final events.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        acq.del_postsynaptic_event(mini_index)

        # Recreate the sort_index and mini_spinboxlist
        self.sort_index = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].sort_index()
        self.mini_spinbox_list = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].list_of_events()

        # Rename the plotted mini's
        for num, i, j in zip(
            self.mini_spinbox_list,
            self.p1.listDataItems()[1:],
            self.p2.listDataItems()[1:],
        ):
            i.opts["name"] = num
            j.opts["name"] = num

        # Clear the last_mini_clicked_1 to prevent erros
        self.last_mini_clicked_1 = []
        self.last_mini_clicked_2 = []

        # Reset the maximum spinbox value
        self.mini_number.setMaximum(self.mini_spinbox_list[-1])

        # Plot the next mini in the list
        self.mini_spinbox(int(self.mini_number.text()))
        self.minis_deleted += 1

    def createMini(self):
        """
        This function is used to create new mini events. By clicking
        on the main acquisition and clicking create new mini's button
        will run this function.
        """

        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None

        self.need_to_save = True

        # Make sure that the last acq point that was clicked exists.
        if self.last_acq_point_clicked is not None:
            x = self.last_acq_point_clicked.pos()[0]

            # The mini needs a baseline of at least 2 milliseconds long.
            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]

            if x > 2:
                # Create the new mini.
                created = acq.create_new_mini(x)

                if not created:
                    self.miniNotCreated()
                    return None

                # Reset the mini_spinbox_list and sort index.
                self.sort_index = acq.sort_index()
                self.mini_spinbox_list = acq.list_of_events()

                # Return the correct position of the mini
                id_value = self.mini_spinbox_list[-1]
                mini = acq.postsynaptic_events[id_value]

                # Add the mini item to the plot and make it clickable for p1.
                mini_plot = pg.PlotCurveItem(
                    x=mini.mini_x_comp()[:2],
                    y=mini.mini_y_comp()[:2],
                    pen="g",
                    name=id_value,
                    clickable=True,
                )
                mini_plot.sigClicked.connect(self.miniClicked)
                self.p1.addItem(mini_plot)
                self.p2.plot(
                    x=mini.mini_x_comp()[:2],
                    y=mini.mini_y_comp()[:2],
                    pen="g",
                    name=id_value,
                )

                # Set the spinbox maximum and current value.
                self.mini_number.setMaximum(self.mini_spinbox_list[-1])
                self.mini_number.setValue(self.sort_index.index(id_value))
                self.mini_spinbox(self.sort_index.index(id_value))

                # Reset the clicked point so a new point is not accidentally created.
                self.last_acq_point_clicked.resetPen()
                self.last_acq_point_clicked = None
            else:
                # Raise error if the point is too close to the beginning.
                self.pointTooCloseToBeginning()
                return None

    def deleteAcq(self):
        """
        Deletes the current acquisition when the delete acquisition
        button is clicked.
        """

        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None

        self.need_to_save = True

        self.recent_reject_acq = {}

        # Add acquisition to be deleted to the deleted acquisitions
        # and the recent deleted acquistion dictionary.
        self.exp_manager.delete_acq("mini", self.acquisition_number.value())

        # Clear plots
        self.p1.clear()
        self.p2.clear()
        self.mini_view_plot.clear()

        # Reset the analysis list and change the acquisition to the next
        # acquisition.
        self.acquisition_number.setValue(self.acquisition_number.value() + 1)

    def resetRejectedAcqs(self):
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None
        self.exp_manager.reset_deleted_acqs("mini")

    def resetRecentRejectedAcq(self):
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None
        number = self.exp_manager.reset_recent_deleted_acq("mini")
        self.acquisition_number.setValue(number)

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist():
            self.fileDoesNotExist()
            return None
        if self.exp_manager.final_analysis is not None:
            self.final_tab_widget.clear()
            self.clearTables()
            self.table_dict = {}
        self.need_to_save = True
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)
        self.calc_param_clicked = True
        self.pbar.setFormat("Analyzing...")
        self.exp_manager.run_final_analysis(acqs_deleted=self.exp_manager.acqs_deleted)
        fa = self.exp_manager.final_analysis
        self.plotAveMini(
            fa.average_mini_x(), fa.average_mini_y(), fa.fit_decay_x(), fa.fit_decay_y()
        )
        for key, df in fa.df_dict.items():
            data_table = pg.TableWidget(sortable=False)
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
        self.plot_selector.clear()
        self.plot_selector.addItems(plots)
        self.plot_selector.setMinimumContentsLength(len(max(plots, key=len)))
        if self.plot_selector.currentText() != "IEI (ms)":
            self.plotRawData(self.plot_selector.currentText())
        self.pbar.setFormat("Finished analysis")
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(2)

    def plotAveMini(self, x, y, decay_x, decay_y):
        self.ave_mini_plot.clear()
        self.ave_mini_plot.plot(x=x, y=y)
        self.ave_mini_plot.plot(x=decay_x, y=decay_y, pen="g")

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

    def fileDoesNotExist(self):
        self.dlg.setWindowTitle("Error")
        self.dlg.setText("No files are loaded or analyzed")
        self.dlg.exec()

    def pointTooCloseToBeginning(self):
        self.dlg.setWindowTitle("Information")
        self.dlg.setText(
            ("The selected point is too close" "to the beginning of the acquisition")
        )
        self.dlg.exec()

    def miniNotCreated(self):
        self.dlg.setWindowTitle("Information")
        self.dlg.setText("Event could not be created")
        self.dlg.exec()

    def loadExperiment(self, directory):
        self.reset()
        self.ave_mini_plot.clear()
        self.pbar.setFormat("Loading...")
        self.exp_manger = ExpManager()
        self.worker = ThreadWorker(
            self.exp_manager, "load", analysis="mini", file_path=directory
        )
        self.worker.signals.progress.connect(self.updateProgress)
        self.worker.signals.finished.connect(self.setLoadData)
        QThreadPool.globalInstance().start(self.worker)

    def setLoadData(self):
        if self.exp_manager.final_analysis is not None:
            fa = self.exp_manager.final_analysis
            self.plotAveMini(
                fa.average_mini_x(),
                fa.average_mini_y(),
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
        self.calculate_parameters_2.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.pbar.setFormat("Loaded")
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.ui_prefs["Acq_number"])

    def saveAs(self, save_filename):
        self.reset_button.setEnabled(False)
        self.pbar.setFormat("Saving...")
        self.pbar.setValue(0)
        pref_dict = self.createPrefDict()
        pref_dict["Final Analysis"] = self.calc_param_clicked
        pref_dict["Acq_number"] = self.acquisition_number.value()
        self.exp_manager.set_ui_prefs(pref_dict)
        self.worker = ThreadWorker(self.exp_manager, "save", file_path=save_filename)
        self.worker.signals.progress.connect(self.updateProgress)
        QThreadPool.globalInstance().start(self.worker)
        self.reset_button.setEnabled(True)
        self.need_to_save = False

    def createExperiment(self, urls):
        self.load_widget.model().addData(urls)

    def createPrefDict(self):
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

        dspinbox_dict = {}
        dspinboxes = self.findChildren(QDoubleSpinBox)
        for i in dspinboxes:
            if i.objectName() != "":
                dspinbox_dict[i.objectName()] = i.text()
        pref_dict["double_spinboxes"] = dspinbox_dict

        slider_dict = {}
        sliders = self.findChildren(QSlider)
        for i in sliders:
            if i.objectName() != "":
                slider_dict[i.objectName()] = i.value()
        pref_dict["sliders"] = slider_dict
        return pref_dict

    def setPreferences(self, pref_dict):
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

        spinboxes = self.findChildren(QDoubleSpinBox)
        for i in spinboxes:
            if i.objectName() != "":
                i.setValue(float(pref_dict["double_spinboxes"][i.objectName()]))

        sliders = self.findChildren(QSlider)
        for i in sliders:
            if i.objectName() != "":
                i.setValue(pref_dict["sliders"][i.objectName()])

    def loadPreferences(self, file_name):
        pref_dict = self.exp_manager.load_ui_prefs(file_name)
        self.setPreferences(pref_dict)

    def savePreferences(self, save_filename):
        pref_dict = self.createPrefDict()
        if pref_dict:
            self.exp_manager.save_ui_prefs(save_filename, pref_dict)

    def updateProgress(self, value):
        if isinstance(value, (int, float)):
            self.pbar.setValue(value)
        elif isinstance(value, str):
            self.pbar.setFormat(value)

    def setAppearancePreferences(self, pref_dict):
        self.p1.setBackground(pref_dict[0])
        self.p1.getAxis("left").setPen(pref_dict[1])
        self.p1.getAxis("left").setTextPen(pref_dict[1])
        self.p1.getAxis("bottom").setPen(pref_dict[1])
        self.p1.getAxis("bottom").setTextPen(pref_dict[1])
        self.p2.setBackground(pref_dict[2])
        self.p2.getAxis("left").setPen(pref_dict[3])
        self.p2.getAxis("left").setTextPen(pref_dict[3])
        self.p2.getAxis("bottom").setPen(pref_dict[3])
        self.p2.getAxis("bottom").setTextPen(pref_dict[3])
        self.mini_view_plot.setBackground(pref_dict[4])
        self.mini_view_plot.getAxis("left").setPen(pref_dict[5])
        self.mini_view_plot.getAxis("left").setTextPen(pref_dict[5])
        self.mini_view_plot.getAxis("bottom").setPen(pref_dict[5])
        self.mini_view_plot.getAxis("bottom").setTextPen(pref_dict[5])


if __name__ == "__main__":
    MiniAnalysisWidget()
