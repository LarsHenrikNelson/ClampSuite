import logging
from typing import _LiteralGenericAlias, get_args

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

from ...functions.filtering.filters import Filters
from ...functions.template_psc import create_template
from ..qtwidgets import FrameWidget, LineEdit

logger = logging.getLogger(__name__)


class FilterSettingsWidget(FrameWidget):
    def __init__(self, parent=None):
        super().__init__(title="Filter Settings", parent=parent)

        self.layout = QVBoxLayout(self)
        args = get_args(Filters)
        values = [i._field_defaults["filter_family"] for i in args]
        self.selector = QComboBox()
        self.selector.addItems(values)
        self.selector.currentTextChanged.connect(self._on_selection_changed)
        self.layout.addWidget(self.selector)

        self.stack = QStackedWidget()
        self.forms: dict[str, SingleForm] = {}

        for a in args:
            form = SingleForm(a)
            self.forms[a._field_defaults["filter_family"]] = form
            self.stack.addWidget(form)

        self.layout.addWidget(self.stack)
        self.layout.addStretch()

    def _on_selection_changed(self, name: str):
        self.stack.setCurrentWidget(self.forms[name])


class SingleForm(QWidget):
    def __init__(self, tuple_class: type):
        super().__init__()
        self.tuple_class = tuple_class
        self.fields: dict[str, QWidget] = {}

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        defaults = tuple_class._field_defaults
        annotations = tuple_class.__annotations__
        for field in tuple_class._fields:
            widget = self._create_widget(annotations[field], defaults[field])
            self.fields[field] = widget
            layout.addRow(field, widget)

    def _create_widget(self, field_type, defaults) -> QWidget:
        if isinstance(field_type, (_LiteralGenericAlias)):
            widget = QComboBox()
            widget.addItems(get_args(field_type))
            widget.setMinimumContentsLength(len(max(defaults, key=len)))
        else:
            widget = LineEdit()
            widget.setText(str(defaults))
        return widget
