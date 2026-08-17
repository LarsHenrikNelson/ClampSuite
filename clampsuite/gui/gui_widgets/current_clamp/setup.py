from typing import get_args

from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QHBoxLayout

from ....analysis import AnalysisRegistry
from ....functions.current_clamp.spike_threshold import ThresholdType
from ..generate_form import DataclassForm
from ..qtwidgets import FrameWidget, LineEdit


class CurrentClampSettingsWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Current clamp",
            parent=parent,
        )
        config = AnalysisRegistry.get_epoch_config("current_clamp")
        self.input_layout = DataclassForm(config)

        self.box_layout = QHBoxLayout()

        self.setLayout(self.box_layout)
        self.box_layout.addWidget(self.input_layout)

        self.setObjectName("current_clamp_setup")

    def getAnalysisSettings(self):
        return self.input_layout.get_values()

    # def setAnalysisSettings(self, settings: dict[str, str | int | float | bool]):
    #     self.min_spike_threshold_edit.setText(settings["min_spike_threshold"])
    #     self.min_spikes_edit.setText(settings["min_spikes"])
    #     self.threshold_method.setCurrentText(settings["threshold_method"])
    #     self.side.setCurrentText(settings["side"])
    #     self.proportion.setText(settings["proprotion"])
    #     self.iv_start_edit.setText(settings["iv_start"])
    #     self.iv_end_edit.setText(settings["iv_end"])
