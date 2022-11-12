from PyQt5.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QLabel,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import QSize
import pyqtgraph as pg


from ..gui_widgets.qtwidgets import LineEdit, ListView


class filterWidget(QWidget):
    """
    This is how to subclass a widget.
    """

    def __init__(self):

        super().__init__()

        self.analysis_type = "filter"
        self.initUI()

    def initUI(self):
        # pg.setConfigOptions(antialias=True)

        # self.path_layout = QHBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.filt_layout = QFormLayout()

        # Since the class is inheriting from QWdiget there is no need to set
        # or define a central widget like the mainwindow setCentralWidget
        self.setLayout(self.plot_layout)
        self.plot_layout.addLayout(self.filt_layout, 0)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.p1 = self.plot_widget.addPlot(row=0, col=0)
        pg.setConfigOptions(antialias=True)
        self.plot_layout.addWidget(self.plot_widget, 1)
        self.p1.setMinimumWidth(500)

        self.v1 = self.plot_widget.addViewBox(row=0, col=1)
        self.v1.setMaximumWidth(100)
        self.v1.setMinimumWidth(100)

        self.legend = pg.LegendItem()
        self.v1.addItem(self.legend)
        self.legend.setParentItem(self.v1)
        self.legend.anchor((0, 0), (0, 0))

        # Setup for the drag and drop load layout
        self.load_acq_label = QLabel("Acquisition(s)")
        self.filt_layout.addWidget(self.load_acq_label)
        self.load_widget = ListView()
        self.load_widget.setAnalysisType(self.analysis_type)
        self.filt_layout.addWidget(self.load_widget)

        self.del_sel_button = QPushButton("Delete selection")
        self.filt_layout.addRow(self.del_sel_button)
        self.del_sel_button.clicked.connect(self.delSelection)

        self.acq_number_label = QLabel("Acquisition")
        self.acq_number = QSpinBox()
        self.acq_number.setValue(0)
        self.acq_number.valueChanged.connect(self.spinbox)
        self.filt_layout.addRow(self.acq_number_label, self.acq_number)

        self.b_start_label = QLabel("Baseline start")
        self.b_start_edit = LineEdit()
        self.b_start_edit.setEnabled(True)
        self.b_start_edit.setText("0")
        self.filt_layout.addRow(self.b_start_label, self.b_start_edit)

        self.b_end_label = QLabel("Baseline end")
        self.b_end_edit = LineEdit()
        self.b_end_edit.setEnabled(True)
        self.b_end_edit.setText("80")
        self.filt_layout.addRow(self.b_end_label, self.b_end_edit)

        self.sample_rate_label = QLabel("Sample rate")
        self.sample_rate_edit = LineEdit()
        self.sample_rate_edit.setEnabled(True)
        self.sample_rate_edit.setText("10000")
        self.filt_layout.addRow(self.sample_rate_label, self.sample_rate_edit)

        self.filter_type_label = QLabel("Filter Type")

        filters = [
            "None",
            "remez_2",
            "remez_1",
            "fir_zero_2",
            "fir_zero_1",
            "savgol",
            "ewma",
            "ewma_a",
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
        ]
        self.filter_selection = QComboBox(self)
        self.filter_selection.setMinimumContentsLength(len(max(filters, key=len)))
        self.filter_selection.addItems(filters)
        self.filt_layout.addRow(self.filter_type_label, self.filter_selection)
        self.filter_selection.currentTextChanged.connect(self.setFiltProp)

        self.order_label = QLabel("Order")
        self.order_edit = LineEdit()
        self.order_edit.setValidator(QIntValidator())
        self.order_edit.setEnabled(True)
        self.filt_layout.addRow(self.order_label, self.order_edit)

        self.high_pass_label = QLabel("High-pass")
        self.high_pass_edit = LineEdit()
        self.high_pass_edit.setValidator(QDoubleValidator())
        self.high_pass_edit.setEnabled(True)
        self.filt_layout.addRow(self.high_pass_label, self.high_pass_edit)

        self.high_width_label = QLabel("High-width")
        self.high_width_edit = LineEdit()
        self.high_width_edit.setValidator(QDoubleValidator())
        self.high_width_edit.setEnabled(True)
        self.filt_layout.addRow(self.high_width_label, self.high_width_edit)

        self.low_pass_label = QLabel("Low-pass")
        self.low_pass_edit = LineEdit()
        self.low_pass_edit.setValidator(QDoubleValidator())
        self.low_pass_edit.setEnabled(True)
        self.filt_layout.addRow(self.low_pass_label, self.low_pass_edit)

        self.low_width_label = QLabel("Low-width")
        self.low_width_edit = LineEdit()
        self.low_width_edit.setValidator(QDoubleValidator())
        self.low_width_edit.setEnabled(True)
        self.filt_layout.addRow(self.low_width_label, self.low_width_edit)

        self.window_label = QLabel("Window type")
        windows = [
            "hann",
            "hamming",
            "blackmmaharris",
            "barthann",
            "nuttall",
            "blackman",
            "tukey",
            "kaiser",
            "gaussian",
            "parzen",
        ]
        self.window_edit = QComboBox(self)
        self.window_edit.addItems(windows)
        self.window_edit.setMinimumContentsLength(len(max(windows, key=len)))
        self.window_edit.currentTextChanged.connect(self.windowChanged)
        self.filt_layout.addRow(self.window_label, self.window_edit)

        self.beta_sigma_label = QLabel("Beta")
        self.beta_sigma = QDoubleSpinBox()
        self.beta_sigma.setObjectName("beta_sigma")
        self.filt_layout.addRow(self.beta_sigma_label, self.beta_sigma)

        self.polyorder_label = QLabel("Polyorder")
        self.polyorder_edit = LineEdit()
        self.polyorder_edit.setValidator(QDoubleValidator())
        self.polyorder_edit.setEnabled(True)
        self.filt_layout.addRow(self.polyorder_label, self.polyorder_edit)

        self.plot_filt = QPushButton("Plot acq")
        self.plot_filt.clicked.connect(self.plotFiltButton)
        # self.plot_filt.setMaximumSize(QSize(300,25))
        self.filt_layout.addRow(self.plot_filt)

        self.clear_plot = QPushButton("Clear plot")
        self.clear_plot.clicked.connect(self.clearPlotButton)
        self.clear_plot.setMaximumSize(QSize(300, 25))
        self.filt_layout.addRow(self.clear_plot)

        self.plot_list = 0
        self.pencil_list = []
        self.counter = 0
        self.filter_list = []
        self.need_to_save = False
        self.acq_number.setMinimum(1)

    def windowChanged(self, text):
        if text == "Gaussian":
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

    def setAcqSpinbox(self):
        x = len(self.load_widget.model().acq_dict)
        self.acq_number.setMaximum(x)

    def delSelection(self):
        # Deletes the selected acquisitions from the list
        indexes = self.load_widget.selectedIndexes()
        if len(indexes) > 0:

            # Delete selections from model
            self.load_widget.deleteSelection(indexes)
            self.load_widget.clearSelection()

            # Clear them from the view. Not sure if this is
            # actually needed sinced the view seems to change
            # without it.
            self.load_widget.clearSelection()

        if len(self.load_widget.model().acq_dict) == 0:
            self.plot_list = 0
            self.pencil_list = []
            self.p1.clear()
        self.setAcqSpinbox()

    def plotFiltButton(self):
        self.setAcqSpinbox()
        if (
            self.window_edit.currentText() == "gaussian"
            or self.window_edit.currentText() == "kaiser"
        ):
            window = (self.window_edit.currentText(), self.beta_sigma.value())
        else:
            window = self.window_edit.currentText()
        key = list(self.load_widget.model().acq_dict.keys())[
            self.acq_number.value() - 1
        ]
        h = self.load_widget.model().acq_dict[key].deep_copy()
        h.analyze(
            sample_rate=self.sample_rate_edit.toInt(),
            baseline_start=self.b_start_edit.toInt(),
            baseline_end=self.b_end_edit.toInt(),
            filter_type=self.filter_selection.currentText(),
            order=self.order_edit.toInt(),
            high_pass=self.high_pass_edit.toFloat(),
            high_width=self.high_width_edit.toFloat(),
            low_pass=self.low_pass_edit.toFloat(),
            low_width=self.low_width_edit.toFloat(),
            window=window,
            polyorder=self.polyorder_edit.toFloat(),
        )
        filter_dict = {
            "sample_rate": self.sample_rate_edit.toInt(),
            "baseline_start": self.b_start_edit.toInt(),
            "baseline_end": self.b_end_edit.toInt(),
            "filter_type": self.filter_selection.currentText(),
            "order": self.order_edit.toInt(),
            "high_pass": self.high_pass_edit.toFloat(),
            "high_width": self.high_width_edit.toFloat(),
            "low_pass": self.low_pass_edit.toFloat(),
            "low_width": self.low_width_edit.toFloat(),
            "window": self.window_edit.currentText(),
            "polyorder": self.polyorder_edit.toFloat(),
        }
        self.filter_list += [filter_dict]
        pencil = pg.mkPen(color=pg.intColor(self.counter))
        plot_item = self.p1.plot(
            x=h.plot_x_array(),
            y=h.filtered_array,
            pen=pencil,
            name=(self.filter_selection.currentText() + "_" + str(self.counter)),
        )
        self.legend.addItem(
            plot_item, self.filter_selection.currentText() + "_" + str(self.counter)
        )
        self.plot_list += 1
        self.counter += 1
        self.pencil_list += [pencil]

    def spinbox(self, number):
        if self.plot_list > 0:
            self.p1.clear()
            for i, j in zip(self.filter_list, self.pencil_list):
                key = list(self.load_widget.model().acq_dict.keys())[number - 1]
                h = self.load_widget.model().acq_dict[int(key)]
                h.analyze(
                    sample_rate=i["sample_rate"],
                    baseline_start=i["baseline_start"],
                    baseline_end=i["baseline_end"],
                    filter_type=i["filter_type"],
                    order=i["order"],
                    high_pass=i["high_pass"],
                    high_width=i["high_width"],
                    low_pass=i["low_pass"],
                    low_width=i["low_width"],
                    window=i["window"],
                    polyorder=i["polyorder"],
                )
                self.p1.plot(x=h.plot_x_array(), y=h.filtered_array, pen=j)
        else:
            pass

    def clearPlotButton(self):
        self.p1.clear()
        self.legend.clear()
        self.counter = 0
        self.plot_list = 0
        self.filter_list = []
        self.pencil_list = []

    def removeLastPlotted(self):
        pass


if __name__ == "__main__":
    filterWidget()
