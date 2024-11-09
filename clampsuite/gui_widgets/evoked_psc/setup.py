import logging

from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout

from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class EvokedPSCSettingsWidget(FrameWidget):

    def __init__(self, parent=None):
        super().__init__(title="Evoked PSC Settings", parent=parent)

        self.setObjectName("evoked_psc_settings")

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.pulse_start = LineEdit()
        self.pulse_start.setEnabled(True)
        self.pulse_start.setObjectName("pulse_start")
        self.pulse_start.setText("1000")
        self.layout.addRow("Pulse start", self.pulse_start)

        self.neg_start = LineEdit()
        self.neg_start.setValidator(QDoubleValidator())
        self.neg_start.setEnabled(True)
        self.neg_start.setObjectName("neg_start")
        self.neg_start.setText("1001")
        self.layout.addRow("Negative window start", self.neg_start)

        self.neg_end = LineEdit()
        self.neg_end.setValidator(QDoubleValidator())
        self.neg_end.setObjectName("neg_end")
        self.neg_end.setEnabled(True)
        self.neg_end.setText("1050")
        self.layout.addRow("Negative window end", self.neg_end)

        self.pos_start = LineEdit()
        self.pos_start.setValidator(QDoubleValidator())
        self.pos_start.setEnabled(True)
        self.pos_start.setObjectName("pos_start")
        self.pos_start.setText("1045")
        self.layout.addRow("Positive window start", self.pos_start)

        self.pos_end = LineEdit()
        self.pos_end.setValidator(QDoubleValidator())
        self.pos_end.setEnabled(True)
        self.pos_end.setObjectName("pos_end")
        self.pos_end.setText("1055")
        self.layout.addRow("Positive window end", self.pos_end)

        self.charge_transfer = QCheckBox(self)
        self.charge_transfer.setObjectName("charge_transfer")
        self.charge_transfer.setChecked(False)
        self.charge_transfer.setTristate(False)
        self.layout.addRow("Charge transfer", self.charge_transfer)

        self.est_decay = QCheckBox(self)
        self.est_decay.setObjectName("est_decay")
        self.est_decay.setChecked(False)
        self.est_decay.setTristate(False)
        self.layout.addRow("Est decay", self.est_decay)

        self.curve_fit_decay = QCheckBox(self)
        self.curve_fit_decay.setObjectName("curve_fit_decay")
        self.curve_fit_decay.setChecked(False)
        self.curve_fit_decay.setTristate(False)
        self.layout.addRow("Curve fit decay", self.curve_fit_decay)

        fit_types = ["s_exp", "db_exp"]
        self.curve_fit_type = QComboBox(self)
        self.curve_fit_type.setMinimumContentsLength(len(max(fit_types, key=len)))
        self.curve_fit_type.addItems(fit_types)
        self.curve_fit_type.setObjectName("curve_fit_type")
        self.layout.addRow("Curve fit type", self.curve_fit_type)
