from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
)

from ..manager import ExpManager
from .qtwidgets import FrameWidget, LineEdit


class FilterWidget(FrameWidget):
    filters = ExpManager.filters

    def __init__(self, parent=None):
        super(FilterWidget, self).__init__(parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.filter_selection = QComboBox(self)
        self.filter_selection.addItems(self.filters)
        self.filter_selection.setMinimumContentsLength(len(max(self.filters, key=len)))
        self.filter_selection.currentTextChanged.connect(self.setFiltProp)
        self.filter_selection.setObjectName("filter_selection")
        self.layout.addRow("Filter type", self.filter_selection)

        self.order_label = QLabel("Order")
        self.order_edit = LineEdit()
        self.order_edit.setValidator(QIntValidator())
        self.order_edit.setObjectName("order_edit")
        self.order_edit.setEnabled(True)
        self.order_edit.setText("201")
        self.layout.addRow(self.order_label, self.order_edit)

        self.high_pass_edit = LineEdit()
        self.high_pass_edit.setValidator(QIntValidator())
        self.high_pass_edit.setObjectName("high_pass_edit")
        self.high_pass_edit.setEnabled(True)
        self.layout.addRow("High pass", self.high_pass_edit)

        self.high_width_edit = LineEdit()
        self.high_width_edit.setValidator(QIntValidator())
        self.high_width_edit.setObjectName("high_width_edit")
        self.high_width_edit.setEnabled(True)
        self.layout.addRow("High width", self.high_width_edit)

        self.low_pass_edit = LineEdit()
        self.low_pass_edit.setValidator(QIntValidator())
        self.low_pass_edit.setObjectName("low_pass_edit")
        self.low_pass_edit.setEnabled(True)
        self.low_pass_edit.setText("600")
        self.layout.addRow("Low pass", self.low_pass_edit)

        self.low_width_edit = LineEdit()
        self.low_width_edit.setValidator(QIntValidator())
        self.low_width_edit.setObjectName("low_width_edit")
        self.low_width_edit.setEnabled(True)
        self.low_width_edit.setText("600")
        self.layout.addRow("Low width", self.low_width_edit)

        windows = ExpManager.windows
        self.window_edit = QComboBox(self)
        self.window_edit.addItems(windows)
        self.window_edit.setMinimumContentsLength(len(max(windows, key=len)))
        self.window_edit.currentTextChanged.connect(self.windowChanged)
        self.window_edit.setObjectName("window_edit")
        self.layout.addRow("Window type", self.window_edit)

        self.beta_sigma_label = QLabel("Beta")
        self.beta_sigma = QDoubleSpinBox()
        self.beta_sigma.setMinimumWidth(70)
        self.beta_sigma.setObjectName("beta_sigma")
        self.layout.addRow(self.beta_sigma_label, self.beta_sigma)

        self.polyorder_label = QLabel("Polyorder")
        self.polyorder_edit = LineEdit()
        self.polyorder_edit.setValidator(QIntValidator())
        self.polyorder_edit.setObjectName("polyorder_edit")
        self.polyorder_edit.setEnabled(True)
        self.layout.addRow(self.polyorder_label, self.polyorder_edit)

    def getSettings(self):
        if (
            self.window_edit.currentText() == "gaussian"
            or self.window_edit.currentText() == "kaiser"
        ):
            window = (self.window_edit.currentText(), self.beta_sigma.value())
        else:
            window = self.window_edit.currentText()

        filter_args = (
            {
                "filter_type": self.filter_selection.currentText(),
                "order": self.order_edit.toInt(),
                "high_pass": self.high_pass_edit.toFloat(),
                "high_width": self.high_width_edit.toFloat(),
                "low_pass": self.low_pass_edit.toFloat(),
                "low_width": self.low_width_edit.toFloat(),
                "window": window,
                "polyorder": self.polyorder_edit.toInt(),
            },
        )
        return filter_args

    def windowChanged(self, text):
        if text == "gaussian":
            self.beta_sigma_label.setText("Sigma")
        else:
            self.beta_sigma_label.setText("Beta")

    def setFiltProp(self, text):
        if text == "median":
            self.order_label.setText("Window size")
        elif text == "savgol":
            self.order_label.setText("Window size")
            self.polyorder_label.setText("Polyorder")
        elif text == "ewma" or text == "ewma_a":
            self.order_label.setText("Window size")
            self.polyorder_label.setText("Sum proportion")
        else:
            self.order_label.setText("Order")
            self.polyorder_label.setText("Polyorder")
