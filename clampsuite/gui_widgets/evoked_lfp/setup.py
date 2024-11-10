import logging

from PySide6.QtWidgets import QFormLayout

from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class EvokedLFPSettings(FrameWidget):

    def __init__(self, parent=None):
        super().__init__(title="Evoked LFP Settings", parent=parent)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.lfp_pulse_start_edit = LineEdit()
        self.lfp_pulse_start_edit.setEnabled(True)
        self.lfp_pulse_start_edit.setObjectName("pulse_start")
        self.lfp_pulse_start_edit.setText("1000")
        self.layout.addRow("Pulse start", self.lfp_pulse_start_edit)
