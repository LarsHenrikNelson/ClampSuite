#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 12:20:28 2022

@author: Lars
"""
import numpy as np
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

import pyqtgraph as pg


class AcqInspectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        # self.path_layout = QHBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.props_layout = QFormLayout()
        self.acq_dict = {}

        # Since the class is inheriting from QWdiget there is no need to set
        # or define a central widget like the mainwindow setCentralWidget
        self.setLayout(self.plot_layout)
        self.plot_layout.addLayout(self.props_layout, 0)

        self.plot_widget = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Samples"}
        )
        pg.setConfigOptions(antialias=True)
        self.plot_widget.setMinimumWidth(500)
        self.plot_layout.addWidget(self.plot_widget)

        self.acq_number = QSpinBox()
        self.acq_number.valueChanged.connect(self.spinbox)
        self.props_layout.addRow("Acq number", self.acq_number)

        self.epoch = QLineEdit()
        self.epoch.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch.text())
        )
        self.props_layout.addRow("Epoch", self.epoch)

        self.pulse_amp = QLineEdit()
        self.pulse_amp.editingFinished.connect(
            lambda: self.editAttr("pulse_amp", self.pulse_amp.text())
        )
        self.props_layout.addRow("Pulse amp", self.pulse_amp)

        self.ramp = QLineEdit()
        self.ramp.editingFinished.connect(
            lambda: self.editAttr("ramp", self.ramp.text())
        )
        self.props_layout.addRow("Ramp", self.ramp)

        self.acq_dict = {}

    def setData(self, analysis, exp_manager):
        self.acq_dict = exp_manager.exp_dict[analysis]
        sorted_list = sorted(self.acq_dict.keys(), key=lambda x: int(x))
        self.acq_number.setMinimum(sorted_list[0])
        self.acq_number.setMaximum(sorted_list[-1])

    def removeFileList(self):
        self.acq_dict = {}

    def editAttr(self, line_edit, value):
        setattr(self.acq_dict[self.acq_number.value()], line_edit, value)
        return True

    def spinbox(self, number):
        self.plot_widget.clear()
        if self.acq_dict.get(number):
            self.plot_widget.plot(
                x=np.arange(len(self.acq_dict[number].array)),
                y=self.acq_dict[number].array,
            )
            self.ramp.setText(self.acq_dict[number].ramp)
            self.pulse_amp.setText(self.acq_dict[number].pulse_amp)
            self.epoch.setText(self.acq_dict[number].epoch)

        else:
            pass

    def clearData(self):
        self.acq_dict = {}
