from PyQt5.QtWidgets import (
    QFormLayout,
    QComboBox,
)

from .qtwidgets import LineEdit, FrameWidget


class BaselineWidget(FrameWidget):

    def __init__(self, parent=None):
        super(BaselineWidget, self).__init__(parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.b_start_edit = LineEdit(None)
        self.b_start_edit.setObjectName("b_start_edit")
        self.b_start_edit.setEnabled(True)
        self.b_start_edit.setText("0")
        self.layout.addRow("Baseline start (ms)", self.b_start_edit)

        self.b_end_edit = LineEdit(None)
        self.b_end_edit.setObjectName("b_end_edit")
        self.b_end_edit.setEnabled(True)
        self.b_end_edit.setText("80")
        self.layout.addRow("Baseline end (ms)", self.b_end_edit)

        baseline_methods = ["mean", "polynomial"]
        self.baseline_method = QComboBox(None)
        self.baseline_method.addItems(baseline_methods)
        self.baseline_method.setMinimumContentsLength(
            len(max(baseline_methods, key=len))
        )
        self.layout.addRow("Baseline method", self.baseline_method)

    def getBaselineSettings(self):
        baseline_args = {
            "baseline_start": self.b_start_edit.toInt(),
            "baseline_end": self.b_end_edit.toInt(),
        }
        return baseline_args
