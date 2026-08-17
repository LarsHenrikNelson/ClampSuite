import logging
from dataclasses import fields
from typing import Literal, get_args, get_origin

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ....functions.template_psc import create_template
from ....preprocess.filter import Filters
from ..generate_form import DataclassForm
from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class FilterSettingsWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(title="Filter Settings", parent=parent)

        self._layout = QVBoxLayout(self)
        args = get_args(Filters)
        values = [i.name for i in args]
        self.selector = QComboBox()
        self.selector.addItems(values)
        self.selector.currentTextChanged.connect(self._on_selection_changed)
        self._layout.addWidget(self.selector)

        self.stack = QStackedWidget()
        self.forms: dict[str, DataclassForm] = {}

        for a in args:
            form = DataclassForm(a)
            self.forms[a.name] = form
            self.stack.addWidget(form)

        self._layout.addWidget(self.stack)
        self._layout.addStretch()

    def _on_selection_changed(self, name: str):
        self.stack.setCurrentWidget(self.forms[name])
