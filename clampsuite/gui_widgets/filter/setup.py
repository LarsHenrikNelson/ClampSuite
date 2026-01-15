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

from ...functions.template_psc import create_template
from ...preprocess.filter import Filters
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
        self.forms: dict[str, SingleForm] = {}

        for a in args:
            form = SingleForm(a)
            self.forms[a.filter_family] = form
            self.stack.addWidget(form)

        self._layout.addWidget(self.stack)
        self._layout.addStretch()

    def _on_selection_changed(self, name: str):
        self.stack.setCurrentWidget(self.forms[name])


class SingleForm(QWidget):
    def __init__(self, tuple_class: type):
        super().__init__()
        self.tuple_class = tuple_class
        self.fields: dict[str, QWidget] = {}

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        for f in fields(tuple_class):
            widget = self._create_widget(f.type, f.default)
            self.fields[f.name] = widget
            layout.addRow(f.name, widget)

    def _create_widget(self, field_type, defaults) -> QWidget:
        if field_type is Literal:
            widget = QComboBox()
            widget.addItems(get_args(field_type))
            widget.setMinimumContentsLength(len(max(defaults, key=len)))
        else:
            widget = LineEdit()
            widget.setText(str(defaults))
        return widget
