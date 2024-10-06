from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
)

from .qtwidgets import LineEdit, FrameWidget


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

        self.rc_check_start_edit = LineEdit()
        self.rc_check_start_edit.setEnabled(True)
        self.rc_check_start_edit.setObjectName("rc_check_start_edit")
        self.rc_check_start_edit.setText("10000")
        self.layout.addRow("RC check start (ms)", self.rc_check_start_edit)

        self.rc_check_end_edit = LineEdit()
        self.rc_check_end_edit.setEnabled(True)
        self.rc_check_end_edit.setObjectName("rc_check_end_edit")
        self.rc_check_end_edit.setText("10300")
        self.layout.addRow("RC check end (ms)", self.rc_check_end_edit)

    def getRCSettings(self):
        rc_args = {
            "baseline_start": self.b_start_edit.toInt(),
            "baseline_end": self.b_end_edit.toInt(),
        }
        return rc_args
