# ui_generator.py
from collections.abc import Callable
from dataclasses import fields, is_dataclass
from enum import Enum
from types import NoneType, UnionType
from typing import (
    Any,
    ClassVar,
    Literal,
    Protocol,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


class DataclassProtocol(Protocol):
    """Protocol that matches any dataclass."""

    __dataclass_fields__: ClassVar[dict[str, Any]]


from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# Generic TypeVar bound to any dataclass
DataclassT = TypeVar("DataclassT", bound=DataclassProtocol)


class TupleWidget(QWidget):
    """A horizontal row of input widgets for tuple values."""

    def __init__(self, element_types: tuple[type, ...], factory: "WidgetFactory"):
        super().__init__()
        self._widgets: list[QWidget] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        for i, elem_type in enumerate(element_types):
            if i > 0:
                layout.addWidget(QLabel(","))

            widget = factory.create_widget(elem_type)
            widget.setMinimumWidth(60)
            self._widgets.append(widget)
            layout.addWidget(widget)

        layout.addStretch()

    def get_value(self) -> tuple:
        return tuple(self._get_single_value(w) for w in self._widgets)

    def set_value(self, values: tuple) -> None:
        for widget, value in zip(self._widgets, values):
            self._set_single_value(widget, value)

    def _get_single_value(self, widget: QWidget):
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentData()
        return None

    def _set_single_value(self, widget: QWidget, value) -> None:
        if isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else "")
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.setValue(value or 0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)


class WidgetFactory:
    """Maps Python types to Qt widget creators."""

    def __init__(self):
        self._creators: dict[type, Callable[[], QWidget]] = {
            str: self._create_line_edit,
            int: self._create_spinbox,
            float: self._create_double_spinbox,
            bool: self._create_checkbox,
        }

    def register(self, python_type: type, creator: Callable[[], QWidget]):
        """Register a custom widget creator for a type."""
        self._creators[python_type] = creator

    def create_widget(self, field_type: type) -> QWidget:
        # Check for Optional/Union types (e.g., float | None, Optional[str])
        origin = get_origin(field_type)
        if origin is Union or origin is UnionType:
            inner_type = self._unwrap_optional(field_type)
            if inner_type is not None:
                # Recursively create widget for the inner type
                return self.create_widget(inner_type)

        # Check for Literal type
        if origin is Literal:
            return self._create_literal_combo(field_type)

        # Check for tuple type
        if origin is tuple:
            return self._create_tuple_widget(field_type)

        # Handle Enum types
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return self._create_enum_combo(field_type)

        creator = self._creators.get(field_type)
        if creator:
            return creator()

        raise TypeError(f"No widget registered for type: {field_type}")

    def _unwrap_optional(self, field_type: type) -> type | None:
        """Extract the non-None type from Optional/Union types.

        Returns the inner type if it's Optional (Union with None),
        or None if it's a more complex Union.
        """
        args = get_args(field_type)
        non_none_args = [arg for arg in args if arg is not NoneType]

        # Only handle simple Optional (one type + None)
        if len(non_none_args) == 1:
            return non_none_args[0]
        return None

    def _create_tuple_widget(self, tuple_type) -> TupleWidget:
        """Create a horizontal widget group for tuple elements."""
        element_types = get_args(tuple_type)
        return TupleWidget(element_types, self)

    def _create_literal_combo(self, literal_type) -> QComboBox:
        """Create a combobox from Literal type arguments."""
        widget = QComboBox()
        options = get_args(literal_type)  # Extract literal values

        for option in options:
            # Use str representation for display, store actual value as data
            widget.addItem(str(option), option)

        return widget

    def _create_line_edit(self) -> QLineEdit:
        return QLineEdit()

    def _create_spinbox(self) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(-999999, 999999)
        return widget

    def _create_double_spinbox(self) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(-999999.0, 999999.0)
        widget.setDecimals(3)
        return widget

    def _create_checkbox(self) -> QCheckBox:
        return QCheckBox()

    def _create_enum_combo(self, enum_type: type[Enum]) -> QComboBox:
        widget = QComboBox()
        for member in enum_type:
            widget.addItem(member.name, member)
        return widget


class DataclassForm(QWidget):
    """Generates a form UI from a dataclass."""

    def __init__(
        self,
        dataclass_type: type[DataclassT],
        factory: WidgetFactory | None = None,
    ):
        super().__init__()
        self._dataclass_type = dataclass_type
        self._factory = factory or WidgetFactory()
        self._widgets: dict[str, QWidget] = {}
        self._nested_forms = {}

        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        type_hints = get_type_hints(self._dataclass_type)

        for field in fields(self._dataclass_type):
            field_type = type_hints.get(field.name, field.type)
            label = self._format_label(field.name)

            if is_dataclass(field_type):
                # Nested dataclass → GroupBox with nested form
                group = QGroupBox(label)
                group_layout = QVBoxLayout(group)
                nested_form = DataclassForm(field_type, self._factory)
                group_layout.addWidget(nested_form)
                layout.addRow(group)
                self._nested_forms[field.name] = nested_form
            else:
                # Primitive type → appropriate widget
                widget = self._factory.create_widget(field_type)
                layout.addRow(label, widget)
                self._widgets[field.name] = widget

    def _format_label(self, field_name: str) -> str:
        """Convert snake_case to Title Case."""
        return field_name.replace("_", " ").title()

    def get_values(self) -> dict[str, Any]:
        """Extract current values from the form."""
        values = {}

        for name, widget in self._widgets.items():
            values[name] = self._get_widget_value(widget)

        for name, form in self._nested_forms.items():
            values[name] = form.get_dataclass_instance()

        return values

    def get_dataclass_instance(self):
        """Create a dataclass instance from form values."""
        return self._dataclass_type(**self.get_values())

    def set_values(self, instance) -> None:
        """Populate form from a dataclass instance."""
        for name, widget in self._widgets.items():
            self._set_widget_value(widget, getattr(instance, name))

        for name, form in self._nested_forms.items():
            form.set_values(getattr(instance, name))

    def _get_widget_value(self, widget: QWidget) -> Any:
        if isinstance(widget, TupleWidget):
            return widget.get_value()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentData()
        return None

    def _set_widget_value(self, widget: QWidget, value: Any) -> None:
        if isinstance(widget, TupleWidget):
            widget.set_value(value)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value else "")
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.setValue(value or 0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
