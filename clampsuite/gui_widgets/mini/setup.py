import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from ...functions.template_psc import create_template
from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class MiniSettingsWidget(FrameWidget):

    def __init__(self, parent=None):
        super(MiniSettingsWidget, self).__init__(parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.sensitivity_edit = LineEdit()
        self.sensitivity_edit.setObjectName("sensitivity_edit")
        self.sensitivity_edit.setEnabled(True)
        self.sensitivity_edit.setText("4")
        self.layout.addRow("Deconvolution threshold", self.sensitivity_edit)

        self.amp_thresh_edit = LineEdit()
        self.amp_thresh_edit.setObjectName("amp_thresh_edit")
        self.amp_thresh_edit.setEnabled(True)
        self.amp_thresh_edit.setText("4")
        self.layout.addRow("Amplitude threshold (pA)", self.amp_thresh_edit)

        self.event_spacing_edit = LineEdit()
        self.event_spacing_edit.setObjectName("mini_spacing_edit")
        self.event_spacing_edit.setEnabled(True)
        self.event_spacing_edit.setText("2")
        self.layout.addRow("Min event spacing (ms)", self.event_spacing_edit)

        self.min_rise_time = LineEdit()
        self.min_rise_time.setObjectName("min_rise_time")
        self.min_rise_time.setEnabled(True)
        self.min_rise_time.setText("0.5")
        self.layout.addRow("Min rise time (ms)", self.min_rise_time)

        self.max_rise_time = LineEdit()
        self.max_rise_time.setObjectName("max_rise_time")
        self.max_rise_time.setEnabled(True)
        self.max_rise_time.setText("4")
        self.layout.addRow("Max rise time (ms)", self.max_rise_time)

        self.min_decay = LineEdit()
        self.min_decay.setObjectName("min_decay")
        self.min_decay.setEnabled(True)
        self.min_decay.setText("0.5")
        self.layout.addRow("Min decay time (ms)", self.min_decay)

        self.event_length = LineEdit()
        self.event_length.setObjectName("mini_length")
        self.event_length.setText("30")
        self.layout.addRow("Max event length (ms)", self.event_length)

        self.decay_rise = QCheckBox()
        self.decay_rise.setObjectName("decay_rise")
        self.decay_rise.setChecked(True)
        self.decay_rise.setTristate(False)
        self.layout.addRow("Decay slower than rise time", self.decay_rise)

        self.curve_fit_decay = QCheckBox(self)
        self.curve_fit_decay.setObjectName("curve_fit_decay")
        self.curve_fit_decay.setChecked(False)
        self.curve_fit_decay.setTristate(False)
        self.layout.addRow("Curve fit decay", self.curve_fit_decay)

        fit_types = ["exp", "db_exp"]
        self.curve_fit_edit = QComboBox(self)
        self.curve_fit_edit.addItems(fit_types)
        self.curve_fit_edit.setMinimumContentsLength(len(max(fit_types, key=len)))
        self.curve_fit_edit.setObjectName("curve_fit_type")
        self.layout.addRow("Curve fit type", self.curve_fit_edit)

        self.invert_checkbox = QCheckBox(self)
        self.invert_checkbox.setObjectName("invert_checkbox")
        self.invert_checkbox.setChecked(False)
        self.invert_checkbox.setTristate(False)
        self.layout.addRow("Invert (for positive currents)", self.invert_checkbox)

        self.decon_type_edit = QComboBox(self)
        decon_list = ["wiener", "fft", "convolution"]
        self.decon_type_edit.addItems(decon_list)
        self.decon_type_edit.setMinimumContentsLength(len(max(decon_list, key=len)))
        self.decon_type_edit.setObjectName("mini_finding_method_edit")
        self.layout.addRow("Event finding method", self.decon_type_edit)

    def getSettings(self):
        analysis_args = (
            {
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
        )
        return analysis_args


class TemplateWidget(FrameWidget):

    def __init__(self, parent=None):
        super(TemplateWidget, self).__init__(parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.tau_1_edit = LineEdit()
        self.tau_1_edit.setObjectName("tau_1_edit")
        self.tau_1_edit.setEnabled(True)
        self.tau_1_edit.setText("0.3")
        self.layout.addRow("Rise tau (ms)", self.tau_1_edit)

        self.tau_2_edit = LineEdit()
        self.tau_2_edit.setObjectName("tau_2_edit")
        self.tau_2_edit.setEnabled(True)
        self.tau_2_edit.setText("5")
        self.layout.addRow("Decay tau (ms)", self.tau_2_edit)

        self.amplitude_edit = LineEdit()
        self.amplitude_edit.setObjectName("amplitude_edit")
        self.amplitude_edit.setEnabled(True)
        self.amplitude_edit.setText("-20")
        self.layout.addRow("Amplitude (pA)", self.amplitude_edit)

        self.risepower_edit = LineEdit()
        self.risepower_edit.setObjectName("risepower_edit")
        self.risepower_edit.setEnabled(True)
        self.risepower_edit.setText("0.5")
        self.layout.addRow("Risepower", self.risepower_edit)

        self.temp_length_edit = LineEdit()
        self.temp_length_edit.setObjectName("temp_length_edit")
        self.temp_length_edit.setEnabled(True)
        self.temp_length_edit.setText("30")
        self.layout.addRow("Template length (ms)", self.temp_length_edit)

        self.spacer_edit = LineEdit()
        self.spacer_edit.setObjectName("spacer_edit")
        self.spacer_edit.setEnabled(True)
        self.spacer_edit.setText("1.5")
        self.layout.addRow("Spacer (ms)", self.spacer_edit)

        self.sample_rate_edit = LineEdit()
        self.sample_rate_edit.setObjectName("sample_rate_edit")
        self.sample_rate_edit.setEnabled(True)
        self.sample_rate_edit.setText("10000")
        self.layout.addRow("Sample rate", self.sample_rate_edit)

    def getSettings(self):
        template_args = {
            "amplitude": self.amplitude_edit.toFloat(),
            "tau_1": self.tau_1_edit.toFloat(),
            "tau_2": self.tau_2_edit.toFloat(),
            "risepower": self.risepower_edit.toFloat(),
            "length": self.temp_length_edit.toFloat(),
            "spacer": self.spacer_edit.toFloat(),
            "sample_rate": self.sample_rate_edit.toInt(),
        }
        return template_args


class MiniWidget(QVBoxLayout):

    def __init__(self, parent=None):
        super(MiniWidget, self).__init__(parent)

        # self.setContentsMargins(0, 0, 0, 0)

        self.extra_layout = QVBoxLayout()
        self.addLayout(self.extra_layout)

        self.other_layout = QHBoxLayout()
        self.extra_layout.addLayout(self.other_layout, 10)

        self.mini_settings = MiniSettingsWidget()
        self.other_layout.addWidget(self.mini_settings)

        self.template_layout = QVBoxLayout()
        self.template_settings = TemplateWidget()
        self.template_layout.addWidget(self.template_settings)

        self.template_button = QPushButton("Show template")
        self.template_layout.addWidget(self.template_button)
        self.template_button.clicked.connect(self.createTemplate)
        self.template_button.setObjectName("template_button")

        self.other_layout.addLayout(self.template_layout)

        self.template_plot = pg.PlotWidget(useOpenGL=True)
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

    def createTemplate(self):
        self.template_plot.clear()
        settings = self.template_settings.getSettings()
        template = create_template(
            settings["amplitude"],
            settings["tau_1"],
            settings["tau_2"],
            settings["risepower"],
            settings["length"],
            settings["spacer"],
            settings["sample_rate"],
        )
        s_r_c = settings["sample_rate"] / 1000
        self.template_plot.plot(
            x=(np.arange(len(template)) / s_r_c), y=template, pen=pg.mkPen(width=3)
        )

    def getSettings(self):
        temp = {
            "template_settings": self.template_settings.getSettings(),
            "mini_settings": self.mini_settings.getSettings(),
        }
        return temp
