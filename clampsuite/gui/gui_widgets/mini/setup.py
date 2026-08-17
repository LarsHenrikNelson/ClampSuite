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

from ....analysis import AnalysisRegistry
from ....functions.template_psc import TemplateParams, create_template
from ..generate_form import DataclassForm
from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class MiniSettingsWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(title="Mini Settings", parent=parent)

        self.setObjectName("mini_settings")

        config = AnalysisRegistry.get_epoch_config("current_clamp")
        self.input_layout = DataclassForm(config)

        self.box_layout = QHBoxLayout()

        self.setLayout(self.box_layout)
        self.box_layout.addWidget(self.input_layout)

    def getAnalysisSettings(self):
        return self.input_layout.get_values()

    def setAnalysisSettings(self, settings: dict[str, str | int | bool]):
        # self.sensitivity_edit.setText(settings["sensitivity"])
        # self.amp_thresh_edit.setText(settings["amp_threshold"])
        # self.event_spacing_edit.setText(settings["mini_spacing"])
        # self.min_rise_time.setText(settings["min_rise_time"])
        # self.max_rise_time.setText(settings["max_rise_time"])
        # self.min_decay.setText(settings["min_decay_time"])
        # self.event_length.setText(settings["event_length"])
        # self.decay_rise.setChecked(settings["decay_rise"])
        # self.invert_checkbox.setChecked(settings["invert"])
        # self.decon_type_edit.setCurrentText(settings["decon_type"])
        # self.curve_fit_decay.setChecked(settings["curve_fit_decay"])
        # self.curve_fit_edit.setCurrentText(settings["curve_fit_type"])
        pass


class TemplateWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(title="Mini template", parent=parent)

        self.setObjectName("template_settings")

        self.box_layout = QHBoxLayout()
        self.setLayout(self.box_layout)
        self.widget = DataclassForm(TemplateParams)
        self.box_layout.addWidget(self.widget)

    def getAnalysisSettings(self):
        return self.widget.get_values()

    def setAnalysisSettings(self, settings: dict[str, str | int | float]):
        # self.amplitude_edit.setText("")
        pass


class MiniWidget(QVBoxLayout):
    def __init__(self, parent=None):
        super(MiniWidget, self).__init__(parent)

        # self.setContentsMargins(0, 0, 0, 0)

        self.setObjectName("mini_widget")

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
        settings = self.template_settings.getAnalysisSettings()
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

    def getAnalysisSettings(self):
        temp = {
            "template_settings": self.template_settings.getAnalysisSettings(),
            "mini_settings": self.mini_settings.getAnalysisSettings(),
        }
        return temp
