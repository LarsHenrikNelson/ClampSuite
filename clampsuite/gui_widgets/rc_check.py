from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
)

from .qtwidgets import FrameWidget, LineEdit


class RCCheckWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(title="RC Check", parent=parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.setObjectName("rc_check")

        self.rc_checkbox = QCheckBox()
        self.rc_checkbox.setChecked(True)
        self.rc_checkbox.setTristate(False)
        self.layout.addRow("RC check", self.rc_checkbox)

        self.rc_check_start = LineEdit()
        self.rc_check_start.setEnabled(True)
        self.rc_check_start.setText("10000")
        self.layout.addRow("Start (ms)", self.rc_check_start)

        self.rc_check_end = LineEdit()
        self.rc_check_end.setEnabled(True)
        self.rc_check_end.setText("10300")
        self.layout.addRow("End (ms)", self.rc_check_end)

        self.pulse_start = LineEdit()
        self.pulse_start.setEnabled(True)
        self.pulse_start.setText("10100")
        self.layout.addRow("Pulse start (ms)", self.pulse_start)

        self.pulse_end = LineEdit()
        self.pulse_end.setEnabled(True)
        self.pulse_end.setText("10200")
        self.layout.addRow("Pulse end (ms)", self.pulse_end)

        self.pulse_amplitude = LineEdit()
        self.pulse_amplitude.setEnabled(True)
        self.pulse_amplitude.setText("10")
        self.layout.addRow("Pulse amplitude (mV)", self.pulse_amplitude)

    def getAnalysisSettings(self):
        rc_args = {
            "rc_check": self.rc_checkbox.isChecked(),
            "start": self.rc_check_start.toFloat(),
            "end": self.rc_check_end.toFloat(),
        }
        return rc_args

    def setSettings(self, settings: dict[str, str | int | bool]):
        self.rc_check.setChecked(settings["rc_check"])
        self.rc_check_start.setText(settings["rc_check_start"])
        self.rc_check_end.setText(settings["rc_check_end"])
