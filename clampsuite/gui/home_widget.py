import logging

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QButtonGroup, QPushButton, QWidget

from .gui_widgets import FlowLayout

logger = logging.getLogger(__name__)


class HomeWidget(QWidget):
    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = FlowLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(300, 300)

        self._buttons = [
            (0, "Mini analysis", ":/icons/mini-acq-sq.png"),
            (1, "Evoked PSC/LFP", ":/icons/pos_neg-sq.png"),
            (2, "Current clamp", ":/icons/current_clamp_pulse-sq.png"),
        ]
        self.button_map = {}
        self.button_group = QButtonGroup()
        self.create_buttons(self._buttons)

        self.button_group.buttonClicked.connect(self.analysisButton)

    def analysisButton(self, button: QPushButton):
        button_id = self.button_group.id(button)
        self.clicked.emit(self.button_map[button_id])

    def create_buttons(self, buttons):
        for i in buttons:
            button = QPushButton()
            self.button_group.addButton(button, i[0])
            temp_pixmap = QPixmap(i[2])
            mini_icon = QIcon(temp_pixmap)
            button.setIcon(mini_icon)
            button.setIconSize(temp_pixmap.rect().size())
            self.layout.addWidget(button)
            self.button_map[i[0]] = i[1]

    def needToSave(self):
        return False
