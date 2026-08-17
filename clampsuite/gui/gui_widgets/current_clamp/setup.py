from typing import get_args

from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel

from ....functions.current_clamp.spike_threshold import ThresholdType
from ..qtwidgets import FrameWidget, LineEdit


class CurrentClampSettingsWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Current clamp",
            parent=parent,
        )
        self.input_layout = QFormLayout()

        self.setLayout(self.input_layout)

        self.setObjectName("current_clamp_setup")

        self.min_spike_threshold_label = QLabel("Min spike voltage (mV)")
        self.min_spike_threshold_edit = LineEdit()
        self.min_spike_threshold_edit.setObjectName("min_spike_threshold")
        self.min_spike_threshold_edit.setEnabled(True)
        self.min_spike_threshold_edit.setText("0")
        self.input_layout.addRow(
            self.min_spike_threshold_label, self.min_spike_threshold_edit
        )

        self.threshold_method = QComboBox()
        methods = get_args(ThresholdType)
        self.threshold_method.addItems(methods)
        self.threshold_method.setMinimumContentsLength(len(max(methods, key=len)))
        self.threshold_method.setObjectName("threshold_method")
        self.input_layout.addRow("Threshold method", self.threshold_method)

        self.min_spikes_edit = LineEdit()
        self.min_spikes_edit.setObjectName("min_spikes")
        self.min_spikes_edit.setText("1")
        self.min_spikes_edit.setValidator(QIntValidator())
        self.input_layout.addRow("Min spikes", self.min_spikes_edit)

        self.fit_sag_decay = QComboBox()
        methods = [0, 1, 2]
        self.fit_sag_decay.addItems([str(m) for m in methods])
        self.fit_sag_decay.setMinimumContentsLength(
            len(max([str(m) for m in methods], key=len))
        )
        self.fit_sag_decay.setObjectName("fit_sag_decay")
        self.input_layout.addRow("Fit Sag Decay", self.fit_sag_decay)

        self.side = QComboBox()
        methods = ["left", "right"]
        self.side.addItems([str(m) for m in methods])
        self.side.setMinimumContentsLength(len(max([str(m) for m in methods], key=len)))
        self.side.setObjectName("side")
        self.input_layout.addRow("Side", self.side)

        self.proportion = LineEdit()
        self.proportion.setObjectName("proportion")
        self.proportion.setText("0.6")
        self.proportion.setValidator(QDoubleValidator())
        self.input_layout.addRow("Min spikes", self.proportion)

        self.iv_start_label = QLabel("IV curve start (pA)")
        self.iv_start_edit = LineEdit()
        self.iv_start_edit.setObjectName("iv_start_edit")
        self.iv_start_edit.setText("1")
        self.input_layout.addRow(self.iv_start_label, self.iv_start_edit)

        self.iv_end_label = QLabel("IV curve end (pA)")
        self.iv_end_edit = LineEdit()
        self.iv_end_edit.setObjectName("iv_end_edit")
        self.iv_end_edit.setText("6")
        self.input_layout.addRow(self.iv_end_label, self.iv_end_edit)

    def getAnalysisSettings(self):
        acquisition_args = {
            "threshold": self.min_spike_threshold_edit.toFloat(),
            "min_spikes": self.min_spikes_edit.toInt(),
            "threshold_method": self.threshold_method.currentText(),
            "fit_sag_decay": int(self.fit_sag_decay.currentText()),
            "side": self.side.currentText(),
            "proportion": self.proportion.toFloat(),
        }
        final_analysis_args = {
            "iv_start": self.iv_start_edit.toFloat(),
            "iv_end": self.iv_end_edit.toFloat(),
        }
        return acquisition_args, final_analysis_args

    def setAnalysisSettings(self, settings: dict[str, str | int | float | bool]):
        self.min_spike_threshold_edit.setText(settings["min_spike_threshold"])
        self.min_spikes_edit.setText(settings["min_spikes"])
        self.threshold_method.setCurrentText(settings["threshold_method"])
        self.side.setCurrentText(settings["side"])
        self.proportion.setText(settings["proprotion"])
        self.iv_start_edit.setText(settings["iv_start"])
        self.iv_end_edit.setText(settings["iv_end"])
