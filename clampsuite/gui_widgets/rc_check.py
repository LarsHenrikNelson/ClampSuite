from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
)

from .qtwidgets import FrameWidget, LineEdit


class RCCheckWidget(FrameWidget):

    def __init__(self, parent=None):
        super(RCCheckWidget, self).__init__(parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.rc_checkbox = QCheckBox()
        self.rc_checkbox.setObjectName("rc_checkbox")
        self.rc_checkbox.setChecked(True)
        self.rc_checkbox.setTristate(False)
        self.layout.addRow("RC check", self.rc_checkbox)

        self.rc_check_start = LineEdit()
        self.rc_check_start.setEnabled(True)
        self.rc_check_start.setObjectName("rc_check_start")
        self.rc_check_start.setText("10000")
        self.layout.addRow("RC check start (ms)", self.rc_check_start)

        self.rc_check_end = LineEdit()
        self.rc_check_end.setEnabled(True)
        self.rc_check_end.setObjectName("rc_check_end")
        self.rc_check_end.setText("10300")
        self.layout.addRow("RC check end (ms)", self.rc_check_end)

    def getSettings(self):
        rc_args = {
            "rc_check": self.rc_checkbox.isChecked(),
            "rc_check_start": self.rc_check_start_edit.toFloat(),
            "rc_check_end": self.rc_check_end.toFloat(),
        }
        return rc_args

    def setSettings(self, settings: dict[str, str | int | bool]):
        self.rc_check.setChecked(settings["rc_check"])
        self.rc_check_start.setText(settings["rc_check_start"])
        self.rc_check_end.setText(settings["rc_check_end"])
