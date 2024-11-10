import logging
from collections import namedtuple

import numpy as np
import pyqtgraph as pg
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QFormLayout,
    QSpinBox,
    QLineEdit,
    QPushButton,
)

from ...functions.utilities import round_sig
from ..qtwidgets import WorkerSignals

logger = logging.getLogger(__name__)

XAxisCoord = namedtuple("XAxisCoord", ["x_min", "x_max"])


class LFPAnalysisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.exp_manager = None

        self.signals = WorkerSignals()

        self.lfp_plot_layout = QHBoxLayout()
        self.setLayout(self.lfp_plot_layout)

        self.lfp_plot = pg.PlotWidget(
            labels={"left": "Amplitude (mV)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.lfp_plot.setObjectName("LFP plot")
        self.lfp_plot.setMinimumWidth(500)
        self.lfp_plot.setAutoVisible(y=True)
        self.lfp_plot.sigXRangeChanged.connect(self.getXRange)

        self.lfp_properties = QFormLayout()
        self.lfp_plot_layout.addLayout(self.lfp_properties)

        self.acquisition_number = QSpinBox()
        self.acquisition_number.setMaximumWidth(70)
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)
        self.acquisition_number.valueChanged.connect(self.acqSpinbox)
        self.acquisition_number.setEnabled(True)
        self.lfp_properties.addRow("Acq Number", self.acquisition_number)

        self.epoch_number = QLineEdit()
        self.epoch_number.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch_number.text())
        )
        self.epoch_number.setMaximumWidth(70)
        self.lfp_properties.addRow("Epoch", self.epoch_number)

        self.final_analysis_button = QPushButton("Final analysis")
        self.lfp_properties.addRow(self.final_analysis_button)
        self.final_analysis_button.clicked.connect(self.runFinalAnalysis)
        self.final_analysis_button.setEnabled(True)

    def getXRange(self):
        h = self.acquisition_number.value()
        x = self.lfp_plot.viewRange()[0]
        if self.exp_manager.acq_exists("lfp", h):
            self.setLFPPlotX(x)

    def setLFPPlotX(self, x):
        self.lfp_x_axis = XAxisCoord(x[0], x[1])

    def acqSpinbox(self, h):
        self.lfp_plot.clear()
        lfp_object = None
        if not self.exp_manager.acqs_exist("oepsc") and not self.exp_manager.acqs_exist(
            "lfp"
        ):
            logger.info("No acquisitions analyzed, acquisition not set.")
            self.fileDoesNotExist()
            return None
        self.exp_manager.need_to_save = True
        self.acquisition_number.setDisabled(True)
        self.last_lfp_point_clicked = []
        if self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(f"Plotting LFP {self.acquisition_number.value()}.")
            lfp_object = self.exp_manager.exp_dict["lfp"][
                self.acquisition_number.value()
            ]
            self.lfp_acq_plot = pg.PlotDataItem(
                x=lfp_object.plot_acq_x(),
                y=lfp_object.plot_acq_y(),
                name=str("lfp_" + self.acquisition_number.text()),
                symbol="o",
                symbolSize=10,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )
            self.lfp_plot.addItem(self.lfp_acq_plot)
            if lfp_object.plot_lfp:
                self.lfp_points = pg.PlotDataItem(
                    x=lfp_object.plot_elements_x(),
                    y=lfp_object.plot_elements_y(),
                    symbol="o",
                    symbolSize=8,
                    symbolBrush=[pg.mkBrush("m"), pg.mkBrush("b")],
                    pen=None,
                )
                if lfp_object.reg_line is not np.nan:
                    self.lfp_reg = pg.PlotDataItem(
                        x=lfp_object.slope_x(),
                        y=lfp_object.reg_line,
                        pen=pg.mkPen(color="g", width=4),
                        name="reg_line",
                    )
                self.lfp_plot.addItem(self.lfp_points)
                self.lfp_plot.addItem(self.lfp_reg)
                self.lfp_fv_edit.setText(str(round_sig(lfp_object.fv_y)))
                self.lfp_fp_edit.setText(str(round_sig(lfp_object.fp_y)))
                self.lfp_fp_slope_edit.setText(str(round_sig(lfp_object.slope())))

            self.lfp_acq_plot.sigPointsClicked.connect(self.LFPPlotClicked)
            self.lfp_plot.setXRange(
                self.lfp_x_axis.x_min, self.lfp_x_axis.x_max, padding=0
            )
            self.lfp_plot.enableAutoRange(axis="y")
            self.lfp_plot.setAutoVisible(y=True)
            logger.info(f"LFP acquisition {self.acquisition_number.value()} plotted.")
        else:
            logger.info(f"No LFP acquisition {self.acquisition_number.value()}.")
            text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            text.setFont(QFont("Helvetica", 20))
            self.lfp_plot.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.lfp_plot.addItem(text)
        if lfp_object is not None:
            self.epoch_number.setText(lfp_object.epoch)
        self.acquisition_number.setEnabled(True)

    def LFPPlotClicked(self, item, points):
        logger.info(
            f"oEPSC acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_lfp_point_clicked:
            self.last_lfp_point_clicked.resetPen()
            self.last_lfp_point_clicked.resetBrush()
            self.last_lfp_point_clicked.setSize(size=3)
        points[0].setPen("g", width=2)
        points[0].setBrush("w")
        points[0].setSize(size=8)
        self.last_lfp_point_clicked = points[0]
        logger.info(
            f"Point {self.last_lfp_point_clicked.pos()[0]} set as LFP point clicked."
        )

    def setPointAsFV(self):
        """
        This will set the LFP fiber volley as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Fiber volley was not set,"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Fiber volley was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, fiber volley not set.")
            self.fileDoesNotExist("No LFP point was selected, fiber volley not set.")
            return None

        logger.info(f"Setting fiber volley on LFP {self.acquisition_number.value()}.")

        self.need_to_save = True

        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]

        acq.set_fv(x, y)

        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq.slope() is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )

        self.lfp_fv_edit.setText(str(round_sig(acq.fv_y)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None

        logger.info(f"Fiber volley set on LFP {self.acquisition_number.value()}.")

    def setPointAsSlopeStart(self):
        """
        This will set the LFP fiber volley as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Slope start was not set,"
                f" {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Slope start was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, slope start not set.")
            self.fileDoesNotExist("No LFP point was selected, slope start not set.")
            return None

        logger.info(f"Setting slope start on LFP {self.acquisition_number.value()}.")

        self.need_to_save = True

        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]

        acq.set_slope_start(x, y)

        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq.slope is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fv_edit.setText(str(round_sig(acq.fv_y)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None
        logger.info(f"Slope start set on LFP {self.acquisition_number.value()}.")

    def setPointAsFP(self):
        """
        This will set the LFP field potential as the point selected on the
        lfp plot and update the other two acquisition plots.

        Returns
        -------
        None.

        """
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.value()):
            logger.info(
                "Field potential was not set,"
                f" acquisition {self.acquisition_number.value()} does not exist."
            )
            self.fileDoesNotExist(
                "Field potential was not set, acquisition\n"
                f"{self.acquisition_number.value()} does not exist."
            )
            return None

        if self.last_lfp_point_clicked is None:
            logger.info("No LFP point was selected, field potential not set.")
            self.fileDoesNotExist("No LFP point was selected, field potential not set.")
            return None

        logger.info(f"Setting slope start on LFP {self.acquisition_number.value()}.")
        x = self.last_lfp_point_clicked.pos()[0]
        y = self.last_lfp_point_clicked.pos()[1]

        acq = self.exp_manager.exp_dict["lfp"][self.acquisition_number.value()]
        acq.set_fp(x, y)
        self.lfp_points.setData(
            x=acq.plot_elements_x(),
            y=acq.plot_elements_y(),
            symbol="o",
            symbolSize=8,
            symbolBrush="m",
            pen=None,
        )
        if acq is not np.nan:
            self.lfp_reg.setData(
                x=acq.slope_x(),
                y=acq.reg_line,
                pen=pg.mkPen(color="g", width=4),
                name="reg_line",
            )
        self.lfp_fp_edit.setText(str(round_sig(acq.fp_y)))
        self.lfp_fp_slope_edit.setText(str(round_sig(acq.slope)))
        self.last_lfp_point_clicked.resetPen()
        self.last_lfp_point_clicked.resetBrush()
        self.last_lfp_point_clicked = None
        logger.info(f"Field potential set on LFP {self.acquisition_number.value()}.")

    def deleteLFP(self):
        if not self.exp_manager.acq_exists("lfp", self.acquisition_number.values()):
            logger.info(
                "No acquisition deleted, lfp acquisition"
                f"{self.acquisition_number.values()} does not exist."
            )
            self.fileDoesNotExist(
                "No acquisition deleted, lfp acquisition\n"
                f"{self.acquisition_number.values()} does not exist."
            )
        else:
            self.need_to_save = True
            self.lfp_plot.clear()
            self.exp_manager.delete_acq("lfp", self.acquisition_number.value())
            logger.info(f"LFP Aquisition {self.acquisition_number.value()} deleted.")

    def reset(self):
        logger.info("Reseting LFP UI.")
        self.lfp_plot.clear()
        logger.info("LFP UI reset.")

    def editAttr(self, line_edit, value):
        for i in self.exp_manager.exp_dict.values():
            setattr(
                i[self.acquisition_number.value()],
                line_edit,
                value,
            )
        return True
