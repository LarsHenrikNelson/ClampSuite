from PyQt5.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QLabel,
    QFormLayout,
    QApplication,
    QLayout,
    QVBoxLayout,
    QTabWidget,
    QListWidget,
    QColorDialog,
    QStackedLayout,
    QGraphicsView,
    QGridLayout,
)

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import qdarkstyle


class PreferencesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.tabs_widget = QListWidget()
        self.tabs_widget.addItems(
            [
                "Application settings",
                "Mini Analysis",
                "oEPSC Analysis",
                "Current Clamp Analysis",
            ]
        )
        self.tabs_widget.setSelectionMode(QListWidget.SingleSelection)
        self.tabs_widget.setSelectionBehavior(QListWidget.SelectItems)
        self.tabs_widget.itemClicked.connect(self.set_widget)
        self.layout.addWidget(self.tabs_widget)
        self.tabs_widget.setMaximumWidth(self.tabs_widget.sizeHintForColumn(0))
        self.tabs_widget.setCurrentRow(0)

        self.stackedlayout = QStackedLayout()
        self.layout.addLayout(self.stackedlayout)
        self.stackedlayout.setCurrentIndex(0)

        # Appearence tab
        self.app_appearance = QWidget()
        self.tab1_layout = QFormLayout()
        self.app_appearance.setLayout(self.tab1_layout)

        self.theme_label = QLabel("Theme")
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Dark style", "Light style"])
        self.theme_box.currentTextChanged.connect(self.style_choice)
        self.tab1_layout.addRow(self.theme_label, self.theme_box)
        self.stackedlayout.addWidget(self.app_appearance)

        # Mini Analysis tab
        self.mini_tab = MiniAnalysisSettings()
        self.stackedlayout.addWidget(self.mini_tab)

        # oEPSC analysis tab
        self.oepsc_tab = OESPCAnalysisSettings()
        self.stackedlayout.addWidget(self.oepsc_tab)

    def set_widget(self, clicked_item):
        if clicked_item.text() == "Application settings":
            self.stackedlayout.setCurrentIndex(0)
        elif clicked_item.text() == "Mini Analysis":
            self.stackedlayout.setCurrentIndex(1)
        else:
            pass

    def style_choice(self, text):
        if text == "Dark style":
            stylesheet = qdarkstyle.load_stylesheet(qdarkstyle.dark.palette.DarkPalette)
        else:
            stylesheet = qdarkstyle.load_stylesheet(
                qdarkstyle.light.palette.LightPalette
            )
        app = QApplication.instance()
        app.setStyleSheet(stylesheet)


class MiniAnalysisSettings(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 0)
        self.setLayout(self.layout)
        self.setObjectName("Mini analysis settings")

        self.template_label = QLabel("Template plot")
        self.template_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.template_label, 0, 0, 1, 2)
        self.template_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.template_axis_label, 1, 0)
        self.template_axis_color = QPushButton()
        self.template_axis_color.setObjectName("Template plot axis")
        self.template_axis_color.clicked.connect(
            lambda checked: self.setColor(
                self.template_axis_color, "Template plot", "axis"
            )
        )
        self.layout.addWidget(self.template_axis_color, 1, 1)

        self.template_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.template_bgd_label, 2, 0)
        self.template_bgd_color = QPushButton()
        self.template_bgd_color.setObjectName("Template plot background")
        self.template_bgd_color.clicked.connect(
            lambda checked: self.setColor(
                self.template_bgd_color, "Template plot", "background"
            )
        )
        self.layout.addWidget(self.template_bgd_color, 2, 1)

        self.template_line_label = QLabel("Template", alignment=Qt.AlignRight)
        self.layout.addWidget(self.template_line_label, 1, 2)
        self.template_line_color = QPushButton()
        self.template_line_color.setObjectName("Template plot line")
        self.template_line_color.clicked.connect(
            lambda checked: self.setColor(
                self.template_line_color, "Template plot", "line"
            )
        )
        self.layout.addWidget(self.template_line_color, 1, 3)

        self.layout.setRowMinimumHeight(3, 10)

        self.p1_label = QLabel("Inspection plot")
        self.p1_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.p1_label, 4, 0, 1, 2)
        self.p1_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p1_axis_label, 5, 0)
        self.p1_axis_color = QPushButton()
        self.p1_axis_color.setObjectName("Inspection plot axis")
        self.p1_axis_color.clicked.connect(
            lambda checked: self.setColor(self.p1_axis_color, "p1", "axis")
        )
        self.layout.addWidget(self.p1_axis_color, 5, 1)

        self.p1_acq_label = QLabel("Acquisition", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p1_acq_label, 5, 2)
        self.p1_acq_color = QPushButton()
        self.p1_acq_color.setObjectName("Inspection plot acq")
        self.p1_acq_color.clicked.connect(
            lambda checked: self.setColor(self.p1_acq_color, "p1", "acq")
        )
        self.layout.addWidget(self.p1_acq_color, 5, 3)

        self.p1_mini_s_label = QLabel("Mini selected", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p1_mini_s_label, 5, 4)
        self.p1_mini_s_color = QPushButton()
        self.p1_mini_s_color.setObjectName("Inspection plot mini_s")
        self.p1_mini_s_color.clicked.connect(
            lambda checked: self.setColor(self.p1_mini_s_color, "p1", "mini")
        )
        self.layout.addWidget(self.p1_mini_s_color, 5, 5)

        self.p1_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p1_bgd_label, 6, 0)
        self.p1_bgd_color = QPushButton()
        self.p1_bgd_color.setObjectName("Inspection plot background")
        self.p1_bgd_color.clicked.connect(
            lambda checked: self.setColor(self.p1_bgd_color, "p1", "background")
        )
        self.layout.addWidget(self.p1_bgd_color, 6, 1)

        self.p1_mini_u_label = QLabel("Mini unselected", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p1_mini_u_label, 6, 2)
        self.p1_mini_u_color = QPushButton()
        self.p1_mini_u_color.setObjectName("Inspection plot mini_u")
        self.p1_mini_u_color.clicked.connect(
            lambda checked: self.setColor(self.p1_mini_u_color, "p1", "mini")
        )
        self.layout.addWidget(self.p1_mini_u_color, 6, 3)

        self.layout.setRowMinimumHeight(7, 10)

        self.p2_label = QLabel("Scroll plot")
        self.p2_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.p2_label, 8, 0, 1, 2)
        self.p2_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p2_axis_label, 9, 0)
        self.p2_axis_color = QPushButton()
        self.p2_axis_color.setObjectName("Scroll plot axis")
        self.p2_axis_color.clicked.connect(
            lambda checked: self.setColor(self.p2_axis_color, "p2", "axis")
        )
        self.layout.addWidget(self.p2_axis_color, 9, 1)

        self.p2_acq_label = QLabel("Acquisition", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p2_acq_label, 9, 2)
        self.p2_acq_color = QPushButton()
        self.p2_acq_color.setObjectName("Scroll plot acq")
        self.p2_acq_color.clicked.connect(
            lambda checked: self.setColor(self.p2_acq_color, "p2", "acq")
        )
        self.layout.addWidget(self.p2_acq_color, 9, 3)

        self.p2_mini_s_label = QLabel("Mini selected", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p2_mini_s_label, 9, 4)
        self.p2_mini_s_color = QPushButton()
        self.p2_mini_s_color.setObjectName("Scroll plot mini_s")
        self.p2_mini_s_color.clicked.connect(
            lambda checked: self.setColor(self.p2_mini_s_color, "p2", "mini")
        )
        self.layout.addWidget(self.p2_mini_s_color, 9, 5)

        self.p2_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p2_bgd_label, 10, 0)
        self.p2_bgd_color = QPushButton()
        self.p2_bgd_color.setObjectName("Scroll plot background")
        self.p2_bgd_color.clicked.connect(
            lambda checked: self.setColor(self.p2_bgd_color, "p2", "background")
        )
        self.layout.addWidget(self.p2_bgd_color, 10, 1)

        self.p2_mini_u_label = QLabel("Mini unselected", alignment=Qt.AlignRight)
        self.layout.addWidget(self.p2_mini_u_label, 10, 2)
        self.p2_mini_u_color = QPushButton()
        self.p2_mini_u_color.setObjectName("Scroll plot mini_u")
        self.p2_mini_u_color.clicked.connect(
            lambda checked: self.setColor(self.p2_mini_u_color, "p2", "mini")
        )
        self.layout.addWidget(self.p2_mini_u_color, 10, 3)

        self.layout.setRowMinimumHeight(11, 10)

        self.mini_label = QLabel("Mini plot")
        self.mini_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.mini_label, 12, 0, 1, 2)
        self.mini_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_axis_label, 13, 0)
        self.mini_axis_color = QPushButton()
        self.mini_axis_color.setObjectName("Mini plot axis")
        self.mini_axis_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_axis_color, "Mini view plot", "axis"
            )
        )
        self.layout.addWidget(self.mini_axis_color, 13, 1)

        self.mini_acq_label = QLabel("Mini acquisition", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_acq_label, 13, 2)
        self.mini_acq_color = QPushButton()
        self.mini_acq_color.setObjectName("Mini acq")
        self.mini_acq_color.clicked.connect(
            lambda checked: self.setColor(self.mini_acq_color, "Mini view plot", "mini")
        )
        self.layout.addWidget(self.mini_acq_color, 13, 3)

        self.mini_peak_label = QLabel("Mini peak", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_peak_label, 13, 4)
        self.mini_peak_color = QPushButton()
        self.mini_peak_color.setObjectName("Mini peak")
        self.mini_peak_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_peak_color, "Mini view plot", "mini"
            )
        )
        self.layout.addWidget(self.mini_peak_color, 13, 5)

        self.mini_ftau_label = QLabel("Mini fit tau", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_ftau_label, 13, 6)
        self.mini_ftau_color = QPushButton()
        self.mini_ftau_color.setObjectName("Mini fit tau")
        self.mini_ftau_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_ftau_color, "Mini view plot", "mini"
            )
        )
        self.layout.addWidget(self.mini_ftau_color, 13, 7)

        self.mini_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_bgd_label, 14, 0)
        self.mini_bgd_color = QPushButton()
        self.mini_bgd_color.setObjectName("Mini plot background")
        self.mini_bgd_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_bgd_color, "Mini view plot", "background"
            )
        )
        self.layout.addWidget(self.mini_bgd_color, 14, 1)

        self.mini_base_label = QLabel("Mini baseline", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_base_label, 14, 2)
        self.mini_base_color = QPushButton()
        self.mini_base_color.setObjectName("Mini baseline")
        self.mini_base_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_base_color, "Mini view plot", "mini"
            )
        )
        self.layout.addWidget(self.mini_base_color, 14, 3)

        self.mini_etau_label = QLabel("Mini est tau", alignment=Qt.AlignRight)
        self.layout.addWidget(self.mini_etau_label, 14, 4)
        self.mini_etau_color = QPushButton()
        self.mini_etau_color.setObjectName("Mini est tau")
        self.mini_etau_color.clicked.connect(
            lambda checked: self.setColor(
                self.mini_etau_color, "Mini view plot", "mini"
            )
        )
        self.layout.addWidget(self.mini_etau_color, 14, 5)

        self.layout.setRowMinimumHeight(15, 10)

        self.ave_mini_label = QLabel("Average mini plot")
        self.ave_mini_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.ave_mini_label, 16, 0, 1, 2)
        self.ave_mini_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.ave_mini_axis_label, 17, 0)
        self.ave_mini_axis_color = QPushButton()
        self.ave_mini_axis_color.setObjectName("Ave mini plot axis")
        self.ave_mini_axis_color.clicked.connect(
            lambda checked: self.setColor(
                self.ave_mini_axis_color, "Ave mini plot", "axis"
            )
        )
        self.layout.addWidget(self.ave_mini_axis_color, 17, 1)

        self.ave_mini_acq_label = QLabel("Average mini", alignment=Qt.AlignRight)
        self.layout.addWidget(self.ave_mini_acq_label, 17, 2)
        self.ave_mini_acq_color = QPushButton()
        self.ave_mini_acq_color.setObjectName("Ave mini")
        self.ave_mini_acq_color.clicked.connect(
            lambda checked: self.setColor(
                self.ave_mini_acq_color, "Ave mini plot", "mini"
            )
        )
        self.layout.addWidget(self.ave_mini_axis_color, 17, 3)

        self.ave_mini_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.ave_mini_bgd_label, 18, 0)
        self.ave_mini_bgd_color = QPushButton()
        self.ave_mini_bgd_color.setObjectName("Ave mini plot background")
        self.ave_mini_bgd_color.clicked.connect(
            lambda checked: self.setColor(
                self.ave_mini_bgd_color, "Ave mini plot", "background"
            )
        )
        self.layout.addWidget(self.ave_mini_bgd_color, 18, 1)

        self.ave_mini_tau_label = QLabel("Tau (fit)", alignment=Qt.AlignRight)
        self.layout.addWidget(self.ave_mini_tau_label, 18, 2)
        self.ave_mini_tau_color = QPushButton()
        self.ave_mini_tau_color.setObjectName("Ave mini tau")
        self.ave_mini_tau_color.clicked.connect(
            lambda checked: self.setColor(
                self.ave_mini_tau_color, "Ave mini plot", "tau"
            )
        )
        self.layout.addWidget(self.ave_mini_tau_color, 18, 3)

        self.color_dict = {
            "Template plot axis": "#ffffff",
            "Template plot background": "#000000",
            "Template plot line": "#ffffff",
            "Scroll plot axis": "#ffffff",
            "Scroll plot background": "#000000",
            "Scroll plot acq": "#ffffff",
            "Scroll plot mini_s": "#ff00ff",
            "Scroll plot mini_u": "#00ff00",
            "Inspection plot axis": "#ffffff",
            "Inspection plot background": "#000000",
            "Inspection plot acq": "#ffffff",
            "Inspection plot mini_s": "#ff00ff",
            "Inspection plot mini_u": "#00ff00",
            "Mini plot axis": "#ffffff",
            "Mini plot background": "#000000",
            "Mini acq": "#ffffff",
            "Mini baseline": "#00ff00",
            "Mini peak": "#ff00ff",
            "Mini est tau": "#0000ff",
            "Mini fit tau": "#0000ff",
            "Ave mini plot axis": "#ffffff",
            "Ave mini plot background": "#000000",
            "Ave mini": "#ffffff",
            "Ave mini tau": "#ff00ff",
        }

        self.set_button_color()
        self.set_width()

    def setColor(self, push_button, name, part):
        color = QColorDialog.getColor(
            QtGui.QColor(self.color_dict[push_button.objectName()])
        )
        if color.isValid():
            push_button.setStyleSheet(
                f"background-color : {color.name()};"
                "border :1px solid;"
                "border-color: black"
            )
            self.color_dict[push_button.objectName()] = color.name()
            app = QApplication.instance()
            plot = [i for i in app.allWidgets() if i.objectName() == name][0]
            if part == "background":
                plot.setBackground(self.color_dict.get(push_button.objectName()))
            elif part == "axis":
                plot.getAxis("left").setPen(
                    self.color_dict.get(push_button.objectName())
                )
                plot.getAxis("left").setTextPen(
                    self.color_dict.get(push_button.objectName())
                )
                plot.getAxis("bottom").setPen(
                    self.color_dict.get(push_button.objectName())
                )
                plot.getAxis("bottom").setTextPen(
                    self.color_dict.get(push_button.objectName())
                )
            else:
                pass
        else:
            pass

    def set_button_color(self):
        buttons = self.findChildren(QPushButton)
        for i in buttons:
            color = self.color_dict.get(i.objectName())
            i.setStyleSheet(
                f"background-color : {color};"
                "border :1px solid;"
                "border-color: black"
            )

    def set_width(self):
        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMaximumWidth(30)


class OESPCAnalysisSettings(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 0)
        self.setLayout(self.layout)
        self.setObjectName("oEPSC analysis settings")

        self.oEPSC_label = QLabel("oEPSC plot")
        self.oEPSC_label.setStyleSheet("font-weight: bold")
        self.layout.addWidget(self.oEPSC_label, 0, 0, 1, 2)
        self.oEPSC_axis_label = QLabel("Axis", alignment=Qt.AlignRight)
        self.layout.addWidget(self.oEPSC_axis_label, 1, 0)
        self.oEPSC_axis_color = QPushButton()
        self.oEPSC_axis_color.setObjectName("oEPSC plot axis")
        self.oEPSC_axis_color.clicked.connect(
            lambda checked: self.setColor(self.oEPSC_axis_color, "oEPSC plot", "axis")
        )
        self.layout.addWidget(self.oEPSC_axis_color, 1, 1)

        self.oEPSC_bgd_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.oEPSC_bgd_label, 1, 2)
        self.oEPSC_bgd_color = QPushButton()
        self.oEPSC_bgd_color.setObjectName("oEPSC plot background")
        self.oEPSC_bgd_color.clicked.connect(
            lambda checked: self.setColor(
                self.oEPSC_bgd_color, "oEPSC plot", "background"
            )
        )
        self.layout.addWidget(self.oEPSC_bgd_color, 1, 3)

        self.oEPSC_acq_label = QLabel("Background", alignment=Qt.AlignRight)
        self.layout.addWidget(self.oEPSC_acq_label, 1, 2)
        self.oEPSC_acq_color = QPushButton()
        self.oEPSC_acq_color.setObjectName("oEPSC plot background")
        self.oEPSC_acq_color.clicked.connect(
            lambda checked: self.setColor(
                self.oEPSC_acq_color, "oEPSC plot", "background"
            )
        )
        self.layout.addWidget(self.oEPSC_acq_color, 1, 3)


if __name__ == "__main__":
    PreferencesWidget()
    MiniAnalysisSettings()
    OESPCAnalysisSettings()
