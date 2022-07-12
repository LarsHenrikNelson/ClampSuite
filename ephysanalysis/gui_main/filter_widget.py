#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 12:20:28 2022

@author: Lars
"""
from PyQt5.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QLabel,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QDoubleSpinBox,
)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QSize
import pyqtgraph as pg


from ..acq.acq import Acq
from ..gui_widgets.qtwidgets import LineEdit, ListView, ListModel


class filterWidget(QWidget):
    """
    This is how to subclass a widget.
    """

    def __init__(self):

        super().__init__()

        self.analysis_type = "filter"

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
        self.acq_model = ListModel()
        self.acq_model.setAnalysisType(self.analysis_type)
        # self.acq_model.layoutChanged.emit(self.set_acq_spinbox)
        self.load_widget.setModel(self.acq_model)
        self.filt_layout.addWidget(self.load_widget)

        self.del_sel_button = QPushButton("Delete selection")
        self.filt_layout.addRow(self.del_sel_button)
        self.del_sel_button.clicked.connect(self.del_selection)

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
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
        ]

        self.filter_selection = QComboBox(self)
        self.filter_selection.addItems(filters)
        self.filt_layout.addRow(self.filter_type_label, self.filter_selection)

        self.order_label = QLabel("Order")
        self.order_edit = LineEdit()
        self.order_edit.setValidator(QIntValidator())
        self.order_edit.setEnabled(True)
        self.filt_layout.addRow(self.order_label, self.order_edit)

        self.high_pass_label = QLabel("High-pass")
        self.high_pass_edit = LineEdit()
        self.high_pass_edit.setValidator(QIntValidator())
        self.high_pass_edit.setEnabled(True)
        self.filt_layout.addRow(self.high_pass_label, self.high_pass_edit)

        self.high_width_label = QLabel("High-width")
        self.high_width_edit = LineEdit()
        self.high_width_edit.setValidator(QIntValidator())
        self.high_width_edit.setEnabled(True)
        self.filt_layout.addRow(self.high_width_label, self.high_width_edit)

        self.low_pass_label = QLabel("Low-pass")
        self.low_pass_edit = LineEdit()
        self.low_pass_edit.setValidator(QIntValidator())
        self.low_pass_edit.setEnabled(True)
        self.filt_layout.addRow(self.low_pass_label, self.low_pass_edit)

        self.low_width_label = QLabel("Low-width")
        self.low_width_edit = LineEdit()
        self.low_width_edit.setValidator(QIntValidator())
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
            "exponential",
        ]
        self.window_edit = QComboBox(self)
        self.window_edit.addItems(windows)
        self.window_extra = QDoubleSpinBox()
        self.window_box = QWidget()
        self.window_box_layout = QVBoxLayout()
        self.window_box_layout.addWidget(self.window_edit)
        self.window_box_layout.addWidget(self.window_extra)
        self.window_box.setLayout(self.window_box_layout)
        self.filt_layout.addRow(self.window_label, self.window_box)

        self.polyorder_label = QLabel("Polyorder")
        self.polyorder_edit = LineEdit()
        self.polyorder_edit.setValidator(QIntValidator())
        self.polyorder_edit.setEnabled(True)
        self.filt_layout.addRow(self.polyorder_label, self.polyorder_edit)

        self.plot_filt = QPushButton("Plot acq")
        self.plot_filt.clicked.connect(self.plot_filt_button)
        # self.plot_filt.setMaximumSize(QSize(300,25))
        self.filt_layout.addRow(self.plot_filt)

        self.clear_plot = QPushButton("Clear plot")
        self.clear_plot.clicked.connect(self.clear_plot_button)
        self.clear_plot.setMaximumSize(QSize(300, 25))
        self.filt_layout.addRow(self.clear_plot)

        self.plot_list = {}
        self.pencil_list = []
        self.counter = 0
        self.filter_list = []
        self.need_to_save = False

    def set_acq_spinbox(self):
        x = len(self.acq_model.acq_dict)
        self.acq_number.setMaximum(x)
        self.acq_number.setMinimum(0)

    def del_selection(self):
        # Deletes the selected acquisitions from the list
        indexes = self.load_widget.selectedIndexes()
        if len(indexes) > 0:

            # Delete selections from model
            self.acq_model.deleteSelection(indexes)

            # Clear them from the view. Not sure if this is
            # actually needed sinced the view seems to change
            # without it.
            self.load_widget.clearSelection()
        self.set_acq_spinbox()

    def plot_filt_button(self):
        self.set_acq_spinbox()
        if (
            self.window_edit.currentText() == "gaussian"
            or self.window_edit.currentText() == "kaiser"
        ):
            window = self.window_edit.currentText()
        else:
            window = (self.window_edit.currentText(), self.window_extra.value())
        acq_components = self.acq_model.acq_list[self.acq_number.value()]
        h.analyze(
            sample_rate=self.sample_rate_edit.toInt(),
            baseline_start=self.b_start_edit.toInt(),
            baseline_end=self.b_end_edit.toInt(),
            filter_type=self.filter_selection.currentText(),
            order=self.order_edit.toInt(),
            high_pass=self.high_pass_edit.toInt(),
            high_width=self.high_width_edit.toInt(),
            low_pass=self.low_pass_edit.toInt(),
            low_width=self.low_width_edit.toInt(),
            window=window,
            polyorder=self.polyorder_edit.toInt(),
        )
        filter_dict = {
            "sample_rate": self.sample_rate_edit.toInt(),
            "baseline_start": self.b_start_edit.toInt(),
            "baseline_end": self.b_end_edit.toInt(),
            "filter_type": self.filter_selection.currentText(),
            "order": self.order_edit.toInt(),
            "high_pass": self.high_pass_edit.toInt(),
            "high_width": self.high_width_edit.toInt(),
            "low_pass": self.low_pass_edit.toInt(),
            "low_width": self.low_width_edit.toInt(),
            "window": self.window_edit.currentText(),
            "polyorder": self.polyorder_edit.toInt(),
        }
        self.filter_list += [filter_dict]
        if len(self.plot_list) == 0:
            pencil = pg.mkPen(color="w", alpha=int(0.75 * 255))
        else:
            pencil = pg.mkPen(color=pg.intColor(self.counter))
        plot_item = self.p1.plot(
            x=h.x_array,
            y=h.filtered_array,
            pen=pencil,
            name=(self.filter_selection.currentText() + "_" + str(self.counter)),
        )
        self.legend.addItem(
            plot_item, self.filter_selection.currentText() + "_" + str(self.counter)
        )
        self.plot_list[str(self.counter)] = h
        self.counter += 1
        self.pencil_list += [pencil]

    def spinbox(self, number):
        if len(self.plot_list.keys()) > 0:
            self.p1.clear()
            for i, j in zip(self.filter_list, self.pencil_list):
                print(i["sample_rate"])
                acq_components = self.acq_model.acq_list[number]
                h.analyze(
                    sample_rate=self.sample_rate_edit.toInt(),
                    baseline_start=self.b_start_edit.toInt(),
                    baseline_end=self.b_end_edit.toInt(),
                    filter_type=self.filter_selection.currentText(),
                    order=self.order_edit.toInt(),
                    high_pass=self.high_pass_edit.toInt(),
                    high_width=self.high_width_edit.toInt(),
                    low_pass=self.low_pass_edit.toInt(),
                    low_width=self.low_width_edit.toInt(),
                    window=window,
                    polyorder=self.polyorder_edit.toInt(),
                )
                self.p1.plot(x=h.x_array, y=h.filtered_array, pen=j)
        else:
            pass

    def clear_plot_button(self):
        self.p1.clear()
        self.legend.clear()
        self.counter = 0
        self.plot_list = {}
        self.pencil_list = []


if __name__ == "__main__":
    filterWidget()
