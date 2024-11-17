import logging

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QPushButton, QButtonGroup

from ..gui_widgets import FlowLayout

logger = logging.getLogger(__name__)


class HomeWidget(QWidget):
    clicked = Signal(str)

    def __init__(self, parent=None, button_map: dict[int, str] = None):
        super().__init__(parent)

        self.layout = FlowLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(300, 300)

        # self.button_map = {0: "Mini analysis", 1: "Current clamp", 2: "Evoked PSC/LFP"}
        self.button_map = button_map

        self.button_group = QButtonGroup()
        self.button_group.buttonClicked.connect(self.analysisButton)

        self.mini_button = QPushButton()
        self.button_group.addButton(self.mini_button, 0)
        temp_pixmap = QPixmap(":/icons/mini-acq-sq.png")
        mini_icon = QIcon(temp_pixmap)
        self.mini_button.setIcon(mini_icon)
        self.mini_button.setIconSize(temp_pixmap.rect().size())
        self.layout.addWidget(self.mini_button)

        self.evoked_psc_button = QPushButton()
        self.button_group.addButton(self.evoked_psc_button, 1)
        temp_pixmap = QPixmap(":/icons/pos_neg-sq.png")
        mini_icon = QIcon(temp_pixmap)
        self.evoked_psc_button.setIcon(mini_icon)
        self.evoked_psc_button.setIconSize(temp_pixmap.rect().size())
        self.layout.addWidget(self.evoked_psc_button)

        self.cc_button = QPushButton()
        self.button_group.addButton(self.cc_button, 2)
        temp_pixmap = QPixmap(":/icons/current_clamp_pulse-sq.png")
        mini_icon = QIcon(temp_pixmap)
        self.cc_button.setIcon(mini_icon)
        self.cc_button.setIconSize(temp_pixmap.rect().size())
        self.layout.addWidget(self.cc_button)

    def analysisButton(self, button: QPushButton):
        button_id = self.button_group.id(button)
        self.clicked.emit(self.button_map[button_id])

    def needToSave(self):
        return False
