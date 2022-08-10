#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 12:20:28 2022

@author: Lars
"""
import numpy as np
from PyQt5.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QLabel,
    QFormLayout,
    QSpinBox,
)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QSize
import pyqtgraph as pg

from ..functions.utilities import load_scanimage_file
from ..gui_widgets.qtwidgets import LineEdit, ListView, ListModel


class AcqInspectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        # self.path_layout = QHBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.filt_layout = QFormLayout()

        # Since the class is inheriting from QWdiget there is no need to set
        # or define a central widget like the mainwindow setCentralWidget
        self.setLayout(self.plot_layout)
        self.plot_layout.addLayout(self.filt_layout, 0)

        self.plot_widget = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Samples"}
        )
        pg.setConfigOptions(antialias=True)
        self.plot_widget.setMinimumWidth(500)
        self.plot_layout.addWidget(self.plot_widget)

        self.acq_number_label = QLabel("Acq number")
        self.acq_number = QSpinBox()
        self.acq_number.valueChanged.connect(self.spinbox)
        self.filt_layout.addRow(self.acq_number_label, self.acq_number)

        self.acq_dict = {}

    def setFileList(self, file_list):
        self.acq_dict = file_list
        self.acq_number.setMinimum(int(list(self.acq_dict.keys())[0]))
        self.acq_number.setMaximum(int(list(self.acq_dict.keys())[-1]))

    def spinbox(self, number):
        self.plot_widget.clear()
        if self.acq_dict.get(f"{number}"):
            self.plot_widget.plot(
                x=np.arange(len(self.acq_dict[str(number)].array)),
                y=self.acq_dict[str(number)].array,
            )
        else:
            pass


if __name__ == "__main__":
    AcqInspectionWidget()
