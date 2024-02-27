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
from ..gui_widgets.qtwidgets import (
    DragDropWidget,
    LineEdit,
    ListView,
    ThreadWorker,
    WorkerSignals,
)
from ..manager import ExpManager
from .acq_inspection import AcqInspectionWidget, DeconInspectionWidget

logger = logging.getLogger(__name__)


class MiniAnalysisWidget(DragDropWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.plot_dict = {}
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
        self.decon_plot = DeconInspectionWidget()

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
        self.load_widget.model().signals.dir_path.connect(self.setWorkingDirectory)
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

        self.event_spacing_edit = LineEdit()
        self.event_spacing_edit.setObjectName("mini_spacing_edit")
        self.event_spacing_edit.setEnabled(True)
        self.event_spacing_edit.setText("2")
        self.settings_layout.addRow("Min event spacing (ms)", self.event_spacing_edit)

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
        self.event_length.setObjectName("mini_length")
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
        self.decon_type_edit.setObjectName("mini_finding_method_edit")
        self.settings_layout.addRow("Event finding method", self.decon_type_edit)

        self.baseline_corr_choice = QCheckBox()
        self.baseline_corr_choice.setChecked(False)
        self.baseline_corr_choice.setTristate(False)
        # self.settings_layout.addRow(
        #     "Baseline correction (experimental)", self.baseline_corr_choice
        # )

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

        self.template_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict["Template plot"] = self.template_plot
        self.template_plot.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.template_plot.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
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
        self.d2 = Dock("Event")
        self.d3 = Dock("Acq view")
        self.dock_area2.addDock(self.d1, "left")
        self.dock_area2.addDock(self.d2, "right")
        self.dock_area2.addDock(self.d3, "bottom")
        self.acq_scroll = QScrollArea()
        self.acq_scroll.setContentsMargins(20, 20, 20, 20)
        self.acq_widget = QWidget()
        # self.acq_scroll.setMinimumWidth(250)
        # self.acq_scroll.setWidget(self.acq_widget)
        # self.acq_scroll.setWidgetResizable(True)
        self.d3.addWidget(self.acq_widget, 0, 0)
        self.d2.layout.setColumnMinimumWidth(0, 120)
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
        self.slider_sensitivity.setObjectName("event plot slider")
        self.slider_sensitivity.setOrientation(Qt.Horizontal)
        self.slider_sensitivity.setValue(20)
        self.slider_sensitivity.valueChanged.connect(self.slider_value)
        self.acq_buttons.addWidget(self.slider_sensitivity, 4, 0, 1, 2)

        self.create_event_button = QPushButton("Create new event")
        self.create_event_button.clicked.connect(self.createEvent)
        self.create_event_action = QAction("Create new event")
        self.create_event_action.triggered.connect(self.createEvent)
        self.acq_buttons.addWidget(self.create_event_button, 5, 0, 1, 2)

        self.acq_buttons.setRowStretch(6, 10)

        self.delete_acq_button = QPushButton("Delete acquisition")
        self.delete_acq_button.clicked.connect(self.deleteAcq)
        self.acq_buttons.addWidget(self.delete_acq_button, 7, 0, 1, 2)

        self.reset_recent_acq_button = QPushButton("Reset recent deleted acq")
        self.reset_recent_acq_button.clicked.connect(self.resetRecentRejectedAcq)
        self.acq_buttons.addWidget(self.reset_recent_acq_button, 8, 0, 1, 2)

        self.reset_acq_button = QPushButton("Reset deleted acqs")
        self.reset_acq_button.clicked.connect(self.resetRejectedAcqs)
        self.acq_buttons.addWidget(self.reset_acq_button, 9, 0, 1, 2)

        self.decon_acq_button = QPushButton("Plot deconvolution")
        self.decon_acq_button.clicked.connect(self.plotDeconvolution)
        self.acq_buttons.addWidget(self.decon_acq_button, 10, 0, 1, 2)

        self.acq_buttons.setRowStretch(11, 10)

        self.calculate_parameters_2 = QPushButton("Final analysis")
        self.acq_buttons.addWidget(self.calculate_parameters_2)
        self.calculate_parameters_2.clicked.connect(self.runFinalAnalysis)
        self.acq_buttons.addWidget(self.calculate_parameters_2, 12, 0, 1, 2)

        self.delete_acq_action = QAction("Delete acq")
        self.delete_acq_action.triggered.connect(self.deleteAcq)

        self.reset_recent_acq_action = QAction("Reset recent del acq")
        self.reset_recent_acq_action.triggered.connect(self.resetRecentRejectedAcq)

        self.reset_acq_action = QAction("Reset del acq(s)")
        self.reset_acq_action.triggered.connect(self.resetRejectedAcqs)

        # Filling the plot layout.
        self.p1 = pg.PlotWidget(
            useOpenGL=True,
        )
        self.plot_dict["p1"] = self.p1
        self.p1.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.p1.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.p1.setObjectName("p1")
        p1pi = self.p1.getViewBox()
        p1pi.menu.addSeparator()
        p1pi.menu.addAction(self.create_event_action)
        p1pi.menu.addAction(self.delete_acq_action)
        p1pi.menu.addAction(self.reset_recent_acq_action)
        p1pi.menu.addAction(self.reset_acq_action)
        self.d3.addWidget(self.p1, 0, 1)
        self.d3.layout.setColumnStretch(1, 10)

        self.p2 = pg.PlotWidget(useOpenGL=True)
        self.plot_dict["p2"] = self.p2
        self.p2.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.p2.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
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

        self.event_view_widget = QWidget()
        # self.event_view_scroll = QScrollArea()
        # self.event_view_scroll.setMinimumWidth(200)
        # self.event_view_scroll.setContentsMargins(20, 20, 20, 20)
        # self.event_view_scroll.setWidget(self.event_view_widget)
        # self.event_view_scroll.setWidgetResizable(True)
        self.d2.addWidget(self.event_view_widget, 0, 0)
        self.d2.layout.setColumnMinimumWidth(0, 120)
        self.event_layout = QFormLayout()
        self.event_view_widget.setLayout(self.event_layout)

        self.event_number_label = QLabel("Event")
        self.event_number = QSpinBox()
        self.event_number.setMaximumWidth(70)
        self.event_number.setKeyboardTracking(False)
        self.event_layout.addRow(self.event_number_label, self.event_number)
        self.event_number.setEnabled(True)
        self.event_number.setMinimumWidth(70)
        self.event_number.valueChanged.connect(self.eventSpinbox)

        self.event_baseline_label = QLabel("Baseline (pA)")
        self.event_baseline_label.setStyleSheet("""color:#00ff00; font-weight:bold""")
        self.event_baseline = QLineEdit()
        self.event_baseline.setMaximumWidth(70)
        self.event_baseline.setReadOnly(True)
        self.event_layout.addRow(self.event_baseline_label, self.event_baseline)

        self.event_amplitude_label = QLabel("Amplitude (pA)")
        self.event_amplitude_label.setStyleSheet("""color:#ff00ff; font-weight:bold""")
        self.event_amplitude = QLineEdit()
        self.event_amplitude.setMaximumWidth(70)
        self.event_amplitude.setReadOnly(True)
        self.event_layout.addRow(self.event_amplitude_label, self.event_amplitude)

        self.event_tau_label = QLabel("Est tau (ms)")
        self.event_tau = QLineEdit()
        self.event_tau.setMaximumWidth(70)
        self.event_tau.setReadOnly(True)
        self.event_tau_label.setStyleSheet("""color:#0000ff; font-weight: bold;""")
        self.event_layout.addRow(self.event_tau_label, self.event_tau)

        self.event_rise_time_label = QLabel("Rise time (ms)")
        self.event_rise_time = QLineEdit()
        self.event_rise_time.setMaximumWidth(70)
        self.event_rise_time.setReadOnly(True)
        self.event_layout.addRow(self.event_rise_time_label, self.event_rise_time)

        self.event_rise_rate_label = QLabel("Rise rate (pA/ms)")
        self.event_rise_rate = QLineEdit()
        self.event_rise_rate.setMaximumWidth(70)
        self.event_rise_rate.setReadOnly(True)
        self.event_layout.addRow(self.event_rise_rate_label, self.event_rise_rate)

        self.delete_event_button = QPushButton("Delete event")
        self.event_layout.addRow(self.delete_event_button)
        self.delete_event_button.clicked.connect(self.deleteEvent)
        self.delete_event_action = QAction("Delete event")
        self.delete_event_action.triggered.connect(self.deleteEvent)

        self.set_baseline = QPushButton("Set point as baseline")
        self.event_layout.addRow(self.set_baseline)
        self.set_baseline.clicked.connect(self.setPointAsBaseline)
        self.set_baseline_action = QAction("Set point as baseline")
        self.set_baseline_action.triggered.connect(self.setPointAsBaseline)

        self.set_peak = QPushButton("Set point as peak")
        self.event_layout.addRow(self.set_peak)
        self.set_peak.clicked.connect(self.setPointAsPeak)
        self.set_peak_action = QAction("Set point as peak")
        self.set_peak_action.triggered.connect(self.setPointAsPeak)

        self.event_view_plot = pg.PlotWidget(useOpenGL=True)
        self.event_view_plot.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.event_view_plot.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        mp = self.event_view_plot.getViewBox()
        mp.menu.addSeparator()
        mp.menu.addAction(self.delete_event_action)
        mp.menu.addAction(self.set_baseline_action)
        mp.menu.addAction(self.set_peak_action)

        # self.event_view_plot.setMinimumWidth(300)
        self.event_view_plot.setObjectName("Event view plot")
        self.d2.addWidget(self.event_view_plot, 0, 1)
        self.d2.layout.setColumnStretch(1, 10)

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

        self.exp_manager = ExpManager()
        self.load_widget.setData(self.exp_manager)
        self.last_event_deleted = {}
        self.last_event_deleted = []
        self.last_event_point_clicked = None
        self.last_acq_point_clicked = None
        self.event_spinbox_list = []
        self.last_event_clicked_1 = []
        self.last_event_clicked_2 = []
        self.sort_index = []
        self.template = []
        self.event_spinbox_list = []
        self.events_deleted = 0
        self.calc_param_clicked = False
        self.table_dict = {}
        self.need_to_save = False
        self.modify = 20

        # Shortcuts
        self.del_event_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.del_event_shortcut.activated.connect(self.deleteEvent)

        self.create_event_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.create_event_shortcut.activated.connect(self.createEvent)

        self.set_baseline = QShortcut(QKeySequence("Ctrl + B"), self)
        self.set_baseline.activated.connect(self.setPointAsBaseline)

        self.set_peak = QShortcut(QKeySequence("Ctrl + P"), self)
        self.set_peak.activated.connect(self.setPointAsPeak)

        self.del_acq_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        self.del_acq_shortcut.activated.connect(self.deleteAcq)

        self.setWidth()
        logger.info("Event analysis GUI created.")

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
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("No acquisitions exist to inspect.")
            self.errorDialog("No acquisitions exist to inspect.")
        else:
            logger.info("Opening acquisition inspection widget.")
            self.inspection_widget.clearData()
            self.inspection_widget.setData(self.analysis_type, self.exp_manager)
            self.inspection_widget.show()

    def delSelection(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("No acquisitions exist to remove from analysis list.")
            self.errorDialog("No acquisitions exist to remove from analysis list.")
        else:
            # Deletes the selected acquisitions from the list
            indices = self.load_widget.selectedIndexes()
            if len(indices) > 0:
                self.load_widget.deleteSelection(indices)
                self.load_widget.clearSelection()
                logger.info("Removed acquisitions from analysis.")

    def createTemplate(self):
        logger.info("Creating event template.")
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
        logger.info("Event template created and plotted.")

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
            self.analyze_acq_button.setEnabled(True)
            return None

        logger.info("Analysis started.")
        self.pbar.setFormat("Analyzing...")
        self.pbar.setValue(0)

        self.p1.clear()
        self.p2.clear()
        self.p1.setAutoVisible(y=True)
        self.p2.enableAutoRange()
        self.event_view_plot.clear()

        self.need_to_save = True

        self.analyze_acq_button.setEnabled(False)
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)

        # The for loop creates each EventAnalysis object. Enumerate returns
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
        worker = ThreadWorker(self.exp_manager)
        worker.addAnalysis(
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
            },
            analysis_args={
                "sensitivity": self.sensitivity_edit.toFloat(),
                "amp_threshold": self.amp_thresh_edit.toFloat(),
                "mini_spacing": self.event_spacing_edit.toFloat(),
                "min_rise_time": self.min_rise_time.toFloat(),
                "max_rise_time": self.max_rise_time.toFloat(),
                "min_decay_time": self.min_decay.toFloat(),
                "event_length": self.event_length.toInt(),
                "decay_rise": self.decay_rise.isChecked(),
                "invert": self.invert_checkbox.isChecked(),
                "decon_type": self.decon_type_edit.currentText(),
                "curve_fit_decay": self.curve_fit_decay.isChecked(),
                "curve_fit_type": self.curve_fit_edit.currentText(),
                "baseline_corr": self.baseline_corr_choice.isChecked(),
                "rc_check": self.rc_checkbox.isChecked(),
                "rc_check_start": self.rc_check_start_edit.toFloat(),
                "rc_check_end": self.rc_check_end_edit.toFloat(),
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
        logger.info("Starting analysis thread.")
        QThreadPool.globalInstance().start(worker)

    def setAcquisition(self):
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)

        # Events always start from 0 since list indexing in python starts
        # at zero. I choose this because it is easier to reference events
        # when adding or removing events and python list indexing starts at 0.
        self.event_number.setMinimum(0)
        # self.eventSpinbox(0)

        # Enabling the buttons since they were temporarily disabled while
        # The acquisitions were analyzed.
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(1)
        logger.info("Analysis finished.")
        self.pbar.setFormat("Analysis finished")
        logger.info("First acquisition set.")

    def acqSpinbox(self, h):
        """This function plots each acquisition and each of its events."""

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

        # Plots are cleared first otherwise new data is just appended to
        # the plot.
        logger.info("Preparing UI for plotting.")
        self.need_to_save = True
        self.p1.clear()
        self.p2.clear()
        self.p1.setAutoVisible(y=True)
        self.p2.enableAutoRange()
        self.event_view_plot.clear()

        # Reset the clicked points since we do not want to accidentally
        # adjust plot items on the new acquisition
        self.last_acq_point_clicked = None
        self.last_event_clicked_1 = []
        self.last_event_clicked_2 = []
        self.last_event_point_clicked = None

        # sort_index and event_spinbox_list are used to reference the correct
        # event when using the eventSpinbox. This was choosen because you cannot
        # sort GUI objects when they are presented on the screen.
        self.sort_index = []
        self.event_spinbox_list = []

        # I choose to just show
        acq_dict = self.exp_manager.exp_dict["mini"]
        if self.acquisition_number.value() in acq_dict:
            logger.info(f"Plotting acquisition {self.acquisition_number.value()}.")

            # Temporarily disable the acquisition number to prevent some weird behavior
            # where the the box will skip every other acquisition.
            self.acquisition_number.setEnabled(False)

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
            # new event.
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
            logger.info(f"Acquisition {self.acquisition_number.value()} plotted.")

            # Plot the postsynaptic events.
            if acq_object.postsynaptic_events:
                logger.info(
                    f"Plotting acquisition {self.acquisition_number.value()} events."
                )

                # Create the event list and the true index of each event.
                # Since the plot items on a pyqtgraph plot cannot be sorted
                # I had to create a way to correctly reference the position
                # of events when adding new events because I ended up just
                # adding the new events to postsynaptic events list.
                self.sort_index = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].sort_index()
                self.event_spinbox_list = self.exp_manager.exp_dict["mini"][
                    self.acquisition_number.value()
                ].list_of_events()

                # Plot each event. Since the postsynaptic events are stored in
                # a list you can iterate through the list even if there is just
                # one event because lists are iterable in python.

                for i in self.event_spinbox_list:
                    # Create the event plot item that is added to the p1 plot.
                    event_plot = pg.PlotCurveItem(
                        x=acq_object.postsynaptic_events[i].event_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].event_y_comp()[:2],
                        pen="g",
                        name=i,
                        clickable=True,
                    )
                    # Adds the clicked functionality to the event plot item.
                    event_plot.sigClicked.connect(self.eventClicked)
                    self.p1.addItem(event_plot)

                    # Events plotted on p2 do not need any interactivity. You have
                    # create new event plot items for each plot because one graphic
                    # item cannot be used in multiple parts of a GUI in Qt.
                    self.p2.plot(
                        x=acq_object.postsynaptic_events[i].event_x_comp()[:2],
                        y=acq_object.postsynaptic_events[i].event_y_comp()[:2],
                        pen="g",
                    )

                # Set the event spinbox to the first event and sets the min
                # an max value. I choose to start the events at 0 because it
                # is easier to work with event referenceing
                self.event_number.setMinimum(0)
                self.event_number.setMaximum(self.event_spinbox_list[-1])
                self.event_number.setValue(0)
                self.eventSpinbox(0)
                logger.info(
                    f"Acquisition {self.acquisition_number.value()} has no events to\
                         plot."
                )
            else:
                logger.info(
                    f"Acquisition {self.acquisition_number.value()}: Events plotted."
                )
        else:
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.p2.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.p2.addItem(text)
            self.acquisition_number.setEnabled(True)

    def reset(self):
        logger.info("Resetting UI.")
        """
        This function resets all the variables and clears all the plots.
        It takes a while to run.
        """
        self.p1.clear()
        self.p2.clear()
        self.template_plot.clear()
        self.load_widget.clearData()
        self.calc_param_clicked = False
        self.event_view_plot.clear()
        self.last_event_point_clicked = None
        self.last_acq_point_clicked = None
        self.last_event_clicked_1 = []
        self.last_event_clicked_2 = []
        self.event_spinbox_list = []
        self.sort_index = []
        self.stem_plot.clear()
        self.amp_dist.clear()
        self.ave_event_plot.clear()
        self.inspection_widget.clearData()
        self.calc_param_clicked = False
        self.need_to_save = False
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.plot_selector.clear()
        self.pbar.setValue(0)
        self.exp_manager = ExpManager()
        self.load_widget.setData(self.exp_manager)
        self.clearTables()
        self.pbar.setFormat("Ready to analyze")
        logger.info("UI Reset. Ready to analyze.")

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
        logger.info(f"Acquisition {self.acquisition_number.value()} point clicked.")
        if self.last_acq_point_clicked is not None:
            self.last_acq_point_clicked.resetPen()
            self.last_acq_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setSize(size=12)
        self.last_acq_point_clicked = points[0]
        logger.info(
            f"Point {self.last_acq_point_clicked.pos()[0]} set as point clicked."
        )

    def eventClicked(self, item):
        """
        Set the event spinbox to the event that was clicked in the acquisition
        window.
        """
        logger.info("Event clicked.")
        index = self.sort_index.index(int(item.name()))
        self.event_number.setValue(index)
        self.eventSpinbox(index)
        logger.info(f"Event {index} set a current event.")

    def eventSpinbox(self, h):
        """
        Function to plot a event in the event plot.
        """

        if not self.exp_manager.acqs_exist("mini"):
            logger.info(
                "Event was not plotted, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                "Event was not plotted,\n"
                f" {self.acquisition_number.value()} does not exist."
            )
            return None

        # Return the correct index of the event. This is needed because of
        # how new events are created
        event_index = self.sort_index[h]

        logger.info(
            f"Plotting event {event_index} on acquisition \
                  {self.acquisition_number.value()}."
        )

        self.need_to_save = True

        # if h in self.event_spinbox_list:
        # Clear the last event_point_clicked
        self.last_event_point_clicked = None

        # Resets the color of the events on p1 and p2. In python
        # when you create an object it is given a position in the memory
        # you can create new "pointers" to the object. This makes it
        # easy to modify Qt graphics objects without having to find them
        # under their original parent.
        if self.last_event_clicked_1:
            self.last_event_clicked_1.setPen("g")
            self.last_event_clicked_2.setPen("g")

        # Clear the event plot
        self.event_view_plot.clear()

        # Reference the event.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        event = acq.postsynaptic_events[event_index]

        # This allows the window on p1 to follow each event when using
        # the event spinbox. The window will only adjust if any part of
        # the event array falls outside of the current viewable region.
        minX, maxX = self.region.getRegion()
        width = maxX - minX
        if event.plot_event_x()[0] < minX or event.plot_event_x()[-1] > maxX:
            self.region.setRegion(
                [
                    int(event.plot_event_x()[0] - 100),
                    int(event.plot_event_x()[0] + width - 100),
                ]
            )

        # Create the event plot item. The x_array is a method call
        # because it needs to be corrected for sample rate and
        # displayed as milliseconds.
        event_item = pg.PlotDataItem(
            x=event.plot_event_x(),
            y=event.plot_event_y(),
            symbol="o",
            symbolPen=None,
            symbolBrush="#C9CDD0",
            symbolSize=6,
        )

        # Add clickable functionality to the event plot item.
        event_item.sigPointsClicked.connect(self.eventPlotClicked)

        # Plot item for the baseline, peak and estimated tau.
        event_plot_items = pg.PlotDataItem(
            x=event.event_x_comp(),
            y=event.event_y_comp(),
            pen=None,
            symbol="o",
            symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m"), pg.mkBrush("b")],
            symbolSize=12,
        )

        # Add the plot items to the event view widget.
        self.event_view_plot.addItem(event_item)
        self.event_view_plot.addItem(event_plot_items)

        # Plot the fit taus if curve fit was selected.
        if event.fit_tau is not np.nan and self.curve_fit_decay.isChecked():
            event_decay_items = pg.PlotDataItem(
                x=event.fit_decay_x,
                y=event.fit_decay_y,
                pen=pg.mkPen((255, 0, 255, 175), width=3),
            )
            self.event_view_plot.addItem(event_decay_items)

        # Sets the color of the events on p1 and p2 so that the event
        # selected with the spinbox or the event that was clicked is shown.
        self.p2.listDataItems()[event_index + 1].setPen("m", width=2)
        self.p1.listDataItems()[event_index + 1].setPen("m", width=2)

        # Creating a reference to the clicked events.
        self.last_event_clicked_2 = self.p2.listDataItems()[event_index + 1]
        self.last_event_clicked_1 = self.p1.listDataItems()[event_index + 1]

        # Set the attributes of the event on the GUI.
        self.event_amplitude.setText(str(round_sig(event.amplitude, sig=4)))
        self.event_tau.setText(str(round_sig(event.final_tau_x, sig=4)))
        self.event_rise_time.setText(str(round_sig(event.rise_time, sig=4)))
        self.event_rise_rate.setText(str(round_sig(event.rise_rate, sig=4)))
        self.event_baseline.setText(str(round_sig(event.event_start_y, sig=4)))

        logger.info("Event plotted.")

    def eventPlotClicked(self, item, points):
        """
        Function to make the event in the event view widget
        clickable.

        Returns
        -------
        None
        """
        # Resets the color of the previously clicked event point.
        event_index = self.sort_index[int(self.event_number.text())]

        logger.info(f"Point clicked on event {event_index}.")
        if self.last_event_point_clicked:
            self.last_event_point_clicked.resetPen()
            self.last_event_point_clicked = None

        # Set the color and size of the new event point that
        # was clicked.
        points[0].setPen("m", width=4)
        self.last_event_point_clicked = points[0]

        logger.info(f"Point {self.last_event_point_clicked.pos()[0]} clicked.")

    def setPointAsPeak(self):
        """
        This will set the event peak as the point selected on the event plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                "Event peak was not set, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                "Event peak was not set, acquisition\n"
                f" {self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_event_point_clicked is None:
            logger.info("No event peak was selected, peak not set.")
            self.errorDialog("No event peak was selected, peak not set.")
            return None

        self.need_to_save = True

        # Find the index of the event so that the correct event is
        # modified.
        event_index = self.sort_index[int(self.event_number.text())]
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        event = acq.postsynaptic_events[event_index]

        logger.info(
            f"Setting peak on event {event_index} on \
                acquisition {self.acquisition_number.value()}."
        )

        # if len(self.last_event_point_clicked) > 0:
        # X and Y point of the event point that was clicked. The
        # x point needs to be adjusted back to samples for the
        # change amplitude function in the postsynaptic event
        # object.
        x = self.last_event_point_clicked.pos()[0]
        y = self.last_event_point_clicked.pos()[1]

        # Pass the x and y points to the change amplitude function
        # for the postsynaptic event.
        event.change_amplitude(x, y)

        # Redraw the events on p1 and p2 plots. Note that the last
        # event clicked provides a "pointed" to the correct plot
        # object on p1 and p2 so that it does not have to be
        # referenced again.
        self.last_event_clicked_1.setData(
            x=event.event_x_comp()[:2],
            y=event.event_y_comp()[:2],
            color="m",
            width=2,
        )
        self.last_event_clicked_2.setData(
            x=event.event_x_comp()[:2],
            y=event.event_y_comp()[:2],
            color="m",
            width=2,
        )

        # This is need to redraw the event in the event view.
        self.eventSpinbox(int(self.event_number.text()))

        # Reset the last point clicked.
        self.last_event_point_clicked = None

        logger.info(
            f"Peak set on event {event_index} on \
                acquisition {self.acquisition_number.value()}."
        )

    def setPointAsBaseline(self):
        """
        This will set the baseline as the point selected on the event plot and
        update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                "Event baseline was not set,"
                f" acquisition {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                "Event baseline was not set,\n"
                f"acquisition {self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_event_point_clicked is None:
            logger.info("No event baseline was selected, baseline not set.")
            self.errorDialog("No event baseline was selected, baseline not set.")
            return None

        self.need_to_save = True

        if self.last_event_point_clicked is not None:
            # Find the index of the event so that the correct event is
            # modified.
            event_index = self.sort_index[int(self.event_number.text())]

            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
            event = acq.postsynaptic_events[event_index]

            logger.info(
                f"Setting point as peak on event {event_index} on \
                    acquisition {self.acquisition_number.value()}."
            )
            # X and Y point of the event point that was clicked. The
            # x point needs to be adjusted back to samples for the
            # change amplitude function in the postsynaptic event
            # object.
            x = self.last_event_point_clicked.pos()[0]
            y = self.last_event_point_clicked.pos()[1]

            # Pass the x and y points to the change baseline function
            # for the postsynaptic event.
            event.change_baseline(x, y)

            # Redraw the events on p1 and p2 plots. Note that the last
            # event clicked provides a "pointed" to the correct plot
            # object on p1 and p2 so that it does not have to be
            # referenced again.
            self.last_event_clicked_1.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                color="m",
                width=2,
            )
            self.last_event_clicked_2.setData(
                x=event.event_x_comp()[:2],
                y=event.event_y_comp()[:2],
                color="m",
                width=2,
            )

            # This is need to redraw the event in the event view.
            self.eventSpinbox(int(self.event_number.text()))

            # Reset the last point clicked.
            self.last_event_point_clicked = None
        # else:
        #     pass

        logger.info(
            f"Baseline set on event {event_index} on \
                acquisition {self.acquisition_number.value()}."
        )

    def deleteEvent(self):
        """
        This function deletes a event from the acquisition and removes it from the
        GUI.

        Returns
        -------
        None
        """
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                f"No event deleted, acquisition {self.acquisition_number.value()}"
                "does not exist."
            )
            self.errorDialog(
                "No event deleted, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None
        self.need_to_save = True

        # Find the correct event.
        event_index = self.sort_index[int(self.event_number.text())]

        logger.info(
            f"Deleting event {event_index} on acquisition \
                  {self.acquisition_number.value()}."
        )

        # self.last_event_deleted = \
        #     self.acq_object.postsynaptic_events[int(self.event_number.text())]
        self.last_event_deleted_number = self.event_number.text()

        # Clear the event view plot.
        self.event_view_plot.clear()

        # Remove the event from the plots. +1 is added because the first plot
        # item is the acquisition.
        self.p1.removeItem(self.p1.listDataItems()[event_index + 1])
        self.p2.removeItem(self.p2.listDataItems()[event_index + 1])

        # Deleted the event from the postsynaptic events and final events.
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        acq.del_postsynaptic_event(event_index)

        # Recreate the sort_index and event_spinbox_list
        self.sort_index = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].sort_index()
        self.event_spinbox_list = self.exp_manager.exp_dict["mini"][
            self.acquisition_number.value()
        ].list_of_events()

        # Rename the plotted event's
        for num, i, j in zip(
            self.event_spinbox_list,
            self.p1.listDataItems()[1:],
            self.p2.listDataItems()[1:],
        ):
            i.opts["name"] = num
            j.opts["name"] = num

        # Clear the last_event_clicked_1 to prevent erros
        self.last_event_clicked_1 = []
        self.last_event_clicked_2 = []

        # Reset the maximum spinbox value
        self.event_number.setMaximum(self.event_spinbox_list[-1])

        # Plot the next event in the list
        self.eventSpinbox(int(self.event_number.text()))
        self.events_deleted += 1

        logger.info(
            f"Deleted event {event_index} on acquisition \
                {self.acquisition_number.value()}."
        )

    def createEvent(self):
        """
        This function is used to create new event events. By clicking
        on the main acquisition and clicking create new event's button
        will run this function.
        """

        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                "No event created, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.errorDialog(
                "No event created, acquisition\n"
                f" {self.acquisition_number.value()} does not exist."
            )
            return None

        self.need_to_save = True

        # Make sure that the last acq point that was clicked exists.
        if self.last_acq_point_clicked is not None:
            logger.info(
                f"Creating event on acquisition {self.acquisition_number.value()}."
            )
            x = self.last_acq_point_clicked.pos()[0]

            # The event needs a baseline of at least 2 milliseconds long.
            acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]

            if x > 2:
                # Create the new event.
                created = acq.create_new_event(x)

                if not created:
                    self.errorDialog(
                        f"Could not create event at {x}\n"
                        f" on acquisition {self.acquisition_number.value()}"
                    )
                    self.logger.info(
                        f"Could not create event at {x}"
                        f" on acquisition {self.acquisition_number.value()}"
                    )
                    return None

                # Reset the event_spinbox_list and sort index.
                self.sort_index = acq.sort_index()
                self.event_spinbox_list = acq.list_of_events()

                # Return the correct position of the event
                id_value = self.event_spinbox_list[-1]
                event = acq.postsynaptic_events[id_value]

                # Add the event item to the plot and make it clickable for p1.
                event_plot = pg.PlotCurveItem(
                    x=event.event_x_comp()[:2],
                    y=event.event_y_comp()[:2],
                    pen="g",
                    name=id_value,
                    clickable=True,
                )
                event_plot.sigClicked.connect(self.eventClicked)
                self.p1.addItem(event_plot)
                self.p2.plot(
                    x=event.event_x_comp()[:2],
                    y=event.event_y_comp()[:2],
                    pen="g",
                    name=id_value,
                )

                # Set the spinbox maximum and current value.
                self.event_number.setMaximum(self.event_spinbox_list[-1])
                self.event_number.setValue(self.sort_index.index(id_value))
                self.eventSpinbox(self.sort_index.index(id_value))

                # Reset the clicked point so a new point is not accidentally created.
                self.last_acq_point_clicked.resetPen()
                self.last_acq_point_clicked = None

                logger.info(
                    f"Event created on acquisition {self.acquisition_number.value()}."
                )
            else:
                # Raise error if the point is too close to the beginning.
                self.errorDialog(
                    "The selected point is too close\n"
                    "to the beginning of the acquisition"
                )
                logger.info("No event created, selected point to close to beginning.")
                return None

    def plotDeconvolution(self):
        if not self.exp_manager.acq_exists("mini", self.acquisition_number.value()):
            logger.info(
                "No deconvolution plotted, acquisition"
                f" {self.acquisition_number.value()} do not exist."
            )
            self.errorDialog(
                "No deconvolution plotted, acquisition\n"
                f" {self.acquisition_number.value()} do not exist."
            )
            return None
        acq = self.exp_manager.exp_dict["mini"][self.acquisition_number.value()]
        decon, baseline = acq.plot_deconvolved_acq()
        self.decon_plot.plotData(decon, baseline, np.arange(decon.size))
        self.decon_plot.show()
        logger.info("Plotted deconvolution")

    def deleteAcq(self):
        """
        Deletes the current acquisition when the delete acquisition
        button is clicked.
        """

        if not self.exp_manager.acqs_exist("mini"):
            logger.info(
                f"Acquisition {self.acquisition_number.value()} was not"
                " deleted, no acquisitions exist."
            )
            self.errorDialog(
                f"Acquisition {self.acquisition_number.value()} was not\n"
                " deleted, no acquisitions exist."
            )
            return None

        logger.info(f"Deleting aquisition {self.acquisition_number.value()}.")
        self.need_to_save = True

        self.recent_reject_acq = {}

        # Add acquisition to be deleted to the deleted acquisitions
        # and the recent deleted acquistion dictionary.
        self.exp_manager.delete_acq("mini", self.acquisition_number.value())

        # Clear plots
        self.p1.clear()
        self.p2.clear()
        self.event_view_plot.clear()

        # Reset the analysis list and change the acquisition to the next
        # acquisition.
        self.acquisition_number.setValue(self.acquisition_number.value() + 1)
        logger.info(f"Aquisition {self.acquisition_number.value()} deleted.")

    def resetRejectedAcqs(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not reset acquistions, no acquisitions exist.")
            self.errorDialog("Did not reset acquistions, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting deleted acquisitions.")
            self.exp_manager.reset_deleted_acqs("mini")
            logger.info("Deleted acquisitions reset.")
            self.pbar.setFormat("Reset deleted acquisitions.")

    def resetRecentRejectedAcq(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not reset recent acquistion, no acquisitions exist.")
            self.errorDialog("Did not reset recent acquistion, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting most recent deleted acquisition.")
            number = self.exp_manager.reset_recent_deleted_acq("mini")
            if number != 0:
                self.acquisition_number.setValue(number)
                logger.info(f"Acquisition {number} reset.")
                self.pbar.setFormat(f"Reset acquisition {number}.")
            else:
                logger.info("No acquisition to reset.")
                self.pbar.setFormat("No acquisition to reset.")

    def runFinalAnalysis(self):
        if not self.exp_manager.acqs_exist("mini"):
            logger.info("Did not run final analysis, no acquisitions analyzed.")
            self.errorDialog("Did not run final analysis, no acquisitions analyzed.")
            return None
        logger.info("Beginning final analysis.")
        self.calculate_parameters.setEnabled(False)
        self.calculate_parameters_2.setEnabled(False)
        self.calc_param_clicked = True
        if self.exp_manager.final_analysis is not None:
            logger.info("Clearing previous analysis.")
            self.final_tab_widget.clear()
            self.clearTables()
            self.table_dict = {}
        self.need_to_save = True

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
        self.calculate_parameters.setEnabled(True)
        self.calculate_parameters_2.setEnabled(True)
        self.tab_widget.setCurrentIndex(2)
        logger.info("Plotted final data.")
        logger.info("Finished analyzing.")
        self.pbar.setFormat("Final analysis finished")

    def plotAveEvent(self, x, y, decay_x, decay_y):
        self.ave_event_plot.clear()
        self.ave_event_plot.plot(x=x, y=y)
        self.ave_event_plot.plot(x=decay_x, y=decay_y, pen="g")

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
        self.exp_manger = ExpManager()
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
        self.calculate_parameters_2.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
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
            self.need_to_save = False

    def finishedSaving(self):
        self.pbar.setFormat("Finished saving")
        logger.info("Finished saving.")

    def createExperiment(self, urls):
        self.pbar("Creating experiment")
        self.load_widget.model().addData(urls)
        self.pbar("Experiment created")

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
        logger.info("Preferences dictionary created.")
        return pref_dict

    def setPreferences(self, pref_dict):
        logger.info("Setting MiniAnalysis preferences.")
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
        self.event_view_plot.setBackground(pref_dict[4])
        self.event_view_plot.getAxis("left").setPen(pref_dict[5])
        self.event_view_plot.getAxis("left").setTextPen(pref_dict[5])
        self.event_view_plot.getAxis("bottom").setPen(pref_dict[5])
        self.event_view_plot.getAxis("bottom").setTextPen(pref_dict[5])

    def setWorkingDirectory(self, path):
        self.signals.dir_path.emit(path)
