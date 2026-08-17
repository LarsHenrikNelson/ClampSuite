import logging
from collections import namedtuple

import pyqtgraph as pg
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)

from ...functions.utilities import round_sig
from ..qtwidgets import AnalysisWidget

logger = logging.getLogger(__name__)

XAxisCoord = namedtuple("XAxisCoord", ["x_min", "x_max"])


class EvokedPSCAnalysisWidget(AnalysisWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.exp_manager = None

        self.setObjectName("evoked_psc_analysis")

        self.psc_layout = QHBoxLayout()
        self.setLayout(self.psc_layout)

        self.psc_properties = QFormLayout()
        self.psc_layout.addLayout(self.psc_properties)

        self.acquisition_number.valueChanged.connect(self.acqSpinbox)
        self.acquisition_number.setEnabled(True)
        self.psc_properties.addRow("Acq Number", self.acquisition_number)

        self.epoch_number = QLineEdit()
        self.epoch_number.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch_number.text())
        )
        self.epoch_number.setMaximumWidth(70)
        self.psc_properties.addRow("Epoch", self.epoch_number)

        self.oepsc_amp_edit = QLineEdit()
        self.oepsc_amp_edit.setReadOnly(True)
        self.psc_properties.addRow("Amplitude", self.oepsc_amp_edit)

        self.oepsc_charge_edit = QLineEdit()
        self.oepsc_charge_edit.setReadOnly(True)
        self.psc_properties.addRow("Charge transfer", self.oepsc_charge_edit)

        self.oepsc_edecay_edit = QLineEdit()
        self.oepsc_edecay_edit.setReadOnly(True)
        self.psc_properties.addRow("Est decay (ms)", self.oepsc_edecay_edit)

        self.oepsc_fdecay_edit = QLineEdit()
        self.oepsc_fdecay_edit.setReadOnly(True)
        self.psc_properties.addRow("Fit decay (ms)", self.oepsc_fdecay_edit)

        self.set_peak_button = QPushButton("Set point as peak")
        self.set_peak_button.clicked.connect(self.setPSCPeak)
        self.set_peak_button.setEnabled(True)
        self.psc_properties.addRow(self.set_peak_button)

        self.delete_oepsc_button = QPushButton("Delete oEPSC")
        self.delete_oepsc_button.clicked.connect(self.deletePSC)
        self.delete_oepsc_button.setEnabled(True)
        self.psc_properties.addRow(self.delete_oepsc_button)

        self.set_peak_action = QAction("Set point as peak")
        self.set_peak_action.triggered.connect(self.setPSCPeak)

        self.delete_oepsc_action = QAction("Delete oEPSC")
        self.delete_oepsc_action.triggered.connect(self.deletePSC)

        self.final_analysis_button = QPushButton("Final analysis")
        self.psc_properties.addRow(self.final_analysis_button)
        self.final_analysis_button.clicked.connect(self.runFinalAnalysis)
        self.final_analysis_button.setEnabled(True)

        self.psc_plot = pg.PlotWidget(
            labels={"left": "Amplitude (mV)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.psc_plot.setObjectName("Evoked PSC plot")
        self.psc_plot.setMinimumWidth(500)
        self.psc_plot.setAutoVisible(y=True)
        self.psc_plot.sigXRangeChanged.connect(self.getXRange)
        self.psc_layout.addWidget(self.psc_plot)

        o_vb = self.psc_plot.getViewBox()
        o_vb.menu.addSeparator()
        o_vb.menu.addAction(self.set_peak_action)
        o_vb.menu.addSeparator()
        o_vb.menu.addAction(self.delete_oepsc_action)

        self.on_x_set = False
        self.op_x_set = False
        self.last_oepsc_point_clicked = []

    def getXRange(self):
        h = self.acquisition_number.value()
        x = self.psc.viewRange()[0]
        if self.exp_manager.acq_exists("lfp", h):
            self.setLFPPlotX(x)

    def setOPlotX(self, x):
        peak_dir = self.exp_manager.exp_dict["oepsc"][
            self.acquisition_number.value()
        ].peak_direction
        if peak_dir == "positive":
            self.op_x_axis = XAxisCoord(x[0], x[1])
            self.op_x_set = True
        else:
            self.on_x_axis = XAxisCoord(x[0], x[1])
            self.on_x_set = True

    def setOEPSCLimits(self, oepsc_object):
        if not self.on_x_set:
            self.on_x_axis = XAxisCoord(
                oepsc_object.pulse_start - 100,
                oepsc_object.pulse_start + 450,
            )
            self.on_x_set = True
        if not self.op_x_set:
            self.op_x_axis = XAxisCoord(
                oepsc_object.pulse_start - 100,
                oepsc_object.x_array[-1],
            )
            self.op_x_set = True

    def acqSpinbox(self, acq_number):
        self.signals.acq.emit(acq_number)
        self.psc_plot.clear()
        oepsc_object = None
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("No acquisitions analyzed, acquisition not set.")
            self.fileDoesNotExist()
            return None
        self.exp_manager.need_to_save = True
        self.acquisition_number.setDisabled(True)
        self.last_oepsc_point_clicked = []
        if self.exp_manager.acq_exists("oepsc", acq_number):
            logger.info(f"Plotting oEPSC {acq_number}.")
            oepsc_object = self.exp_manager.exp_dict["oepsc"][acq_number]
            self.setOEPSCLimits(oepsc_object)
            self.oepsc_acq_plot = pg.PlotDataItem(
                x=oepsc_object.plot_acq_x(),
                y=oepsc_object.plot_acq_y(),
                name=str("oepsc_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.oepsc_peak_plot = pg.PlotDataItem(
                x=oepsc_object.plot_x_comps(),
                y=oepsc_object.plot_y_comps(),
                symbol="o",
                symbolSize=8,
                symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
                pen=None,
            )
            self.oepsc_acq_plot.sigPointsClicked.connect(self.oEPSCPlotClicked)
            self.psc_plot.addItem(self.oepsc_acq_plot)
            self.psc_plot.addItem(self.oepsc_peak_plot)
            if oepsc_object.peak_direction == "negative":
                self.psc_plot.setXRange(
                    self.on_x_axis.x_min, self.on_x_axis.x_max, padding=0
                )
            else:
                self.psc_plot.setXRange(
                    self.op_x_axis.x_min, self.op_x_axis.x_max, padding=0
                )
            self.psc_plot.enableAutoRange(axis="y")
            self.psc_plot.setAutoVisible(y=True)
            self.oepsc_amp_edit.setText(str(round_sig(oepsc_object.peak_y)))
            if oepsc_object.find_ct:
                self.oepsc_charge_edit.setText(
                    str(round_sig((oepsc_object.charge_transfer)))
                )
            if oepsc_object.find_edecay:
                self.oepsc_edecay_edit.setText(
                    str(round_sig((oepsc_object.est_decay())))
                )
            logger.info(f"oEPSC acquisition {acq_number} plotted.")
        else:
            logger.info(f"No oEPSC acquisition {acq_number}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.psc_plot.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.psc_plot.addItem(text)
        if oepsc_object is not None:
            self.epoch_number.setText(oepsc_object.epoch)
        self.acquisition_number.setEnabled(True)

    def oEPSCPlotClicked(self, item, points):
        logger.info(
            f"oEPSC acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_oepsc_point_clicked:
            self.last_oepsc_point_clicked.resetPen()
            self.last_oepsc_point_clicked.resetBrush()
            self.last_oepsc_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_oepsc_point_clicked = points[0]
        logger.info(
            f"Point {self.last_oepsc_point_clicked.pos()[0]}"
            "set as PSC point clicked."
        )

    def setPSCPeak(self):
        """Sets the peak on the PSC acquisition.

        Returns:
        -------
        None.
        """
        if not self.exp_manager.acq_exists("oepsc", self.acquisition_number.value()):
            logger.info(
                "oEPSC peak was not set, acquisition"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "oEPSC peak was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_oepsc_point_clicked is None:
            logger.info("No oEPSC point was selected, peak not set.")
            self.fileDoesNotExist("No oEPSC point was selected, peak not set.")
            return None

        logger.info(f"Setting peak on oEPSC {self.acquisition_number.value()}.")
        acq = self.exp_manager.exp_dict["oepsc"][self.acquisition_number.value()]
        self.need_to_save = True
        x = self.last_oepsc_point_clicked.pos()[0]
        y = self.last_oepsc_point_clicked.pos()[1]
        acq.set_peak(x, y)
        self.oepsc_peak_plot.setData(
            x=acq.plot_x_comps(),
            y=acq.plot_y_comps(),
            symbol="o",
            symbolSize=8,
            symbolBrush=[pg.mkBrush("g"), pg.mkBrush("m")],
            pen=None,
        )
        self.oepsc_amp_edit.setText(str(round_sig(acq.peak_y)))
        self.last_oepsc_point_clicked.resetPen()
        self.last_oepsc_point_clicked.resetBrush()
        self.last_oepsc_point_clicked = None
        logger.info(f"Peak setzs on oEPSC {self.acquisition_number.value()}.")

    def deletePSC(self):
        if not self.exp_manager.acqs_exist("oepsc"):
            logger.info(
                "No acquisition deleted, oepsc acquisition"
                f" {self.acquisition_number.values()} does not exist."
            )
            self.fileDoesNotExist(
                "No acquisition deleted, oepsc acquisition\n"
                f"{self.acquisition_number.values()} does not exist."
            )
        else:
            self.need_to_save = True
            self.psc_plot.clear()
            self.exp_manager.delete_acq("oepsc", self.acquisition_number.value())
            logger.info(f"oEPSC Aquisition {self.acquisition_number.value()} deleted.")

    def reset(self):
        logger.info("Reseting PSC UI.")
        self.psc_plot.clear()
        logger.info("PSC UI reset.")

    def setAcquisition(self):
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)
        self.acqSpinbox(self.exp_manager.start_acq)

    def runFinalAnalysis(self, checked: bool):
        self.signals.clicked.emit(checked)
