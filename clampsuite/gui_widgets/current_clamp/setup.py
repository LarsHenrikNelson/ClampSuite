from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
)

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
        self.iv_start_edit.setValidator(QIntValidator())
        self.input_layout.addRow(self.iv_start_label, self.iv_start_edit)

        self.iv_end_label = QLabel("IV curve end")
        self.iv_end_edit = LineEdit()
        self.iv_end_edit.setObjectName("iv_end_edit")
        self.iv_end_edit.setText("6")
        self.iv_end_edit.setValidator(QIntValidator())
        self.input_layout.addRow(self.iv_end_label, self.iv_end_edit)

    def getAnalysisSettings(self):
        analysis_args = {
            "threshold": self.min_spike_threshold_edit.toInt(),
            "min_spikes": self.min_spikes_edit.toInt(),
            "threshold_method": self.threshold_method.currentText(),
            "iv_start": self.iv_start_edit.toInt(),
            "iv_end": self.iv_end_edit.toInt(),
        }
        return analysis_args

    def setAnalysisSettings(self, settings: dict[str, str | int | float | bool]):
        self.min_spike_threshold_edit.setText(settings["min_spike_threshold"])
        self.min_spikes_edit.setText(settings["min_spikes"])
        self.threshold_method.setCurrentText(settings["threshold_method"])
        self.iv_start_edit.setText(settings["iv_start"])
        self.iv_end_edit.setText(settings["iv_end"])
