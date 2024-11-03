import logging

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QHBoxLayout,
    QWidget,
)

from ...functions.utilities import round_sig
from ..qtwidgets import WorkerSignals, LineEdit

logger = logging.getLogger(__name__)


class AnalysisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.exp_manager = None

        self.signals = WorkerSignals()

        self.h_layout = QHBoxLayout()
        self.setLayout(self.h_layout)
        self.plot_layout = QHBoxLayout()
        self.analysis_buttons = QFormLayout()
        self.h_layout.addLayout(self.plot_layout, 1)
        self.plot_layout.addLayout(self.analysis_buttons, 0)

        self.acquisition_number_label = QLabel("Acq number")
        self.acquisition_number = QSpinBox()
        self.acquisition_number.setKeyboardTracking(False)
        self.acquisition_number.setMinimumWidth(70)
        self.acquisition_number.valueChanged.connect(self.spinbox)
        self.analysis_buttons.addRow(
            self.acquisition_number_label, self.acquisition_number
        )

        self.epoch_number = LineEdit()
        self.analysis_buttons.addRow("Epoch", self.epoch_number)
        self.epoch_number.editingFinished.connect(
            lambda: self.editAttr("epoch", self.epoch_number.toText())
        )

        self.pulse_amp_num = LineEdit()
        self.analysis_buttons.addRow("Pulse amp", self.pulse_amp_num)
        self.pulse_amp_num.editingFinished.connect(
            lambda: self.editAttr("pulse_amp", self.pulse_amp_num.toFloat())
        )

        self.pulse_pattern = QLineEdit()
        self.pulse_pattern.editingFinished.connect(
            lambda: self.editAttr("pulse_pattern", self.pulse_pattern.text())
        )
        self.analysis_buttons.addRow("Pulse pattern", self.pulse_pattern)

        self.cycle = LineEdit()
        self.cycle.editingFinished.connect(
            lambda: self.editAttr("cycle", self.cycle.toInt())
        )
        self.analysis_buttons.addRow("Cycle", self.cycle)

        self.baseline_mean_edit = QLineEdit()
        self.analysis_buttons.addRow("Baseline mean (mV)", self.baseline_mean_edit)

        self.delta_v_edit = QLineEdit()
        self.analysis_buttons.addRow("Delta V (mV)", self.delta_v_edit)

        self.voltage_sag_edit = QLineEdit()
        self.analysis_buttons.addRow("Voltage sag (mV)", self.voltage_sag_edit)

        self.spike_threshold_edit = QLineEdit()
        self.analysis_buttons.addRow("Spike threshold (mV)", self.spike_threshold_edit)

        self.half_width_edit = QLineEdit()
        self.analysis_buttons.addRow("Half-width (ms)", self.half_width_edit)

        self.spike_rate_label = QLabel("Spike rate")
        self.spike_rate_edit = QLineEdit()
        self.analysis_buttons.addRow(self.spike_rate_label, self.spike_rate_edit)

        self.ahp_label = QLabel("AHP (mv)")
        self.ahp_edit = QLineEdit()
        self.analysis_buttons.addRow(self.ahp_label, self.ahp_edit)

        self.baseline_stability_label = QLabel("Baseline stability")
        self.baseline_stability_edit = QLineEdit()
        self.analysis_buttons.addRow(
            self.baseline_stability_label, self.baseline_stability_edit
        )

        self.set_spike_threshold = QPushButton("Set spike threshold")
        self.set_spike_threshold.clicked.connect(self.setSpikeThreshold)
        self.analysis_buttons.addRow(self.set_spike_threshold)

        self.delete_event_button = QPushButton("Delete acquisition")
        self.delete_event_button.clicked.connect(self.deleteAcq)
        self.analysis_buttons.addRow(self.delete_event_button)

        self.reset_recent_reject_button = QPushButton(
            "Reset recent rejected acquisition"
        )
        self.reset_recent_reject_button.clicked.connect(self.resetRecentRejectAcq)
        self.analysis_buttons.addRow(self.reset_recent_reject_button)

        self.reset_rejected_acqs_button = QPushButton("Reset rejected acquistions")
        self.reset_rejected_acqs_button.clicked.connect(self.resetRejectedAcqs)
        self.analysis_buttons.addRow(self.reset_rejected_acqs_button)

        self.calculate_params_2 = QPushButton("Final analysis")
        self.calculate_params_2.setObjectName("calculate_params_2")
        self.analysis_buttons.addRow(self.calculate_params_2)
        self.calculate_params_2.clicked.connect(self.runFinalAnalysis)

        self.tab2_dock = DockArea()
        self.plot_layout.addWidget(self.tab2_dock, 1)
        self.d1 = Dock("Acquisition")
        self.d2 = Dock("First spike")
        self.tab2_dock.addDock(self.d1, "left")
        self.tab2_dock.addDock(self.d2, "right")

        self.plot_widget = pg.PlotWidget(useOpenGL=True)
        self.plot_widget.setMinimumWidth(300)
        self.d1.addWidget(self.plot_widget)

        self.delete_acq_action = QAction("Delete acq")
        self.delete_acq_action.triggered.connect(self.deleteAcq)

        self.reset_recent_acq_action = QAction("Reset recent del acq")
        self.reset_recent_acq_action.triggered.connect(self.resetRecentRejectAcq)

        self.reset_acq_action = QAction("Reset del acq(s)")
        self.reset_acq_action.triggered.connect(self.resetRejectedAcqs)

        self.spike_plot = pg.PlotWidget(useOpenGL=True)
        self.spike_plot.setMinimumWidth(300)
        self.d2.addWidget(self.spike_plot)

        vb = self.plot_widget.getViewBox()
        vb.menu.addSeparator()
        vb.menu.addAction(self.delete_acq_action)
        vb.menu.addAction(self.reset_recent_acq_action)
        vb.menu.addAction(self.reset_acq_action)

        self.last_acq_point_clicked = None

        self.createPlotItems()

    def createPlotItems(self):
        self.acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 0, 0, 0),
            symbolPen=(0, 0, 0, 0),
        )

        self.acq_plot.sigPointsClicked.connect(self.plotClicked)
        self.plot_widget.addItem(self.acq_plot)

        self.delta_v_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen="r",
        )
        self.plot_widget.addItem(self.delta_v_data)

        self.vsag_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen="#fcbb2f",
        )
        self.plot_widget.addItem(self.vsag_data)

        self.spike_peaks_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="y",
        )
        self.plot_widget.addItem(self.spike_peaks_data)

        self.ahp_acq_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="#E867E8",
        )
        self.plot_widget.addItem(self.ahp_acq_data)

        self.ahp_spike_data = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="m",
        )
        self.spike_plot.addItem(self.ahp_spike_data)

        self.st_data_spk_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.spike_plot.addItem(self.st_data_spk_plot)

        self.st_data_acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.plot_widget.addItem(self.st_data_acq_plot)

        self.spk_width_acq_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=pg.mkPen("g", width=4),
        )
        self.plot_widget.addItem(self.spk_width_acq_plot)

        self.spk_width_spk_plot = pg.PlotDataItem(
            x=[],
            y=[],
            pen=pg.mkPen("g", width=4),
        )
        self.spike_plot.addItem(self.spk_width_spk_plot)

        self.clickable_spike_data = pg.PlotDataItem(
            x=[],
            y=[],
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 0, 0, 0),
            symbolPen=(0, 0, 0, 0),
        )
        self.clickable_spike_data.sigPointsClicked.connect(self.plotClicked)
        self.spike_plot.addItem(self.clickable_spike_data)

        self.text = None

    def editAttr(self, line_edit, value):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return False
        else:
            logger.info(
                f"Editing aquisition attribute {self.acquisition_number.value()}."
            )
            acq = self.exp_manager.exp_dict["current_clamp"][
                self.acquisition_number.value()
            ]
            setattr(acq, line_edit, value)
            logger.info(
                f"Set {value} for {line_edit} on aquisition\
                    {self.acquisition_number.value()}."
            )
            return True

    def setAcquisition(self):
        logger.info("Analysis finished.")
        self.acquisition_number.setMaximum(self.exp_manager.end_acq)
        self.acquisition_number.setMinimum(self.exp_manager.start_acq)
        self.acquisition_number.setValue(self.exp_manager.start_acq)
        self.spinbox(self.exp_manager.start_acq)
        self.analyze_acq_button.setEnabled(True)
        self.main_widget.setCurrentIndex(1)
        self.pbar.setFormat("Analysis finished")
        logger.info("Firsts acquisition set.")

    def clearAcqPlots(self, clear_main: bool = False, clear_spikes: bool = False):
        if clear_main:
            self.acq_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("w"),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.delta_v_data.setData(
                x=[],
                y=[],
                pen=pg.mkPen(color="r", width=2),
            )
            self.vsag_data.setData(
                x=[],
                y=[],
                pen=pg.mkPen(color="m", width=2),
            )
        if clear_spikes:
            self.spike_peaks_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="y",
            )
            self.spk_width_acq_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("g", width=4),
            )

            self.st_data_acq_plot.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="b",
            )

            self.ahp_acq_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="m",
            )

            self.clickable_spike_data.setData(
                x=[],
                y=[],
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.spk_width_spk_plot.setData(
                x=[],
                y=[],
                pen=pg.mkPen("g", width=4),
            )

            self.st_data_spk_plot.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="b",
            )

            self.ahp_spike_data.setData(
                x=[],
                y=[],
                pen=None,
                symbol="o",
                symbolBrush="m",
            )
            if self.text is not None:
                self.plot_widget.removeItem(self.text)
                self.text = None
        self.last_acq_point_clicked = None

    def reset(self):
        logger.info("Resetting UI.")
        self.load_widget.clearData()
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.calc_param_clicked = False
        self.clearAcqPlots(clear_main=True, clear_spikes=True)
        self.load_widget.setData(self.exp_manager)
        self.pbar.setValue(0)
        self.pbar.setFormat("Ready to analyze")
        logger.info("UI Reset. Ready to analyze.")

    def spinbox(self, _):
        if not self.exp_manager.analyzed:
            logger.info(
                "No acquisitions analyzed,"
                f" acquisition {self.acquisition_number.value()} not set."
            )
            self.errorDialog(
                "No acquisitions analyzed,\n"
                f"acquisition {self.acquisition_number.value()} not set."
            )
            return None

        logger.info("Preparing UI for plotting.")
        self.acquisition_number.setEnabled(False)
        if self.last_acq_point_clicked:
            self.plot_widget.removeItem(self.last_acq_point_clicked[0])
            self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        self.need_to_save = True
        self.plot_widget.enableAutoRange()
        self.spike_plot.enableAutoRange()
        if (
            self.acquisition_number.value()
            in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"Plotting acquisition {self.acquisition_number.value()}.")
            acq_object = self.exp_manager.exp_dict["current_clamp"][
                self.acquisition_number.value()
            ]
            self.epoch_number.setText(acq_object.epoch)
            self.pulse_amp_num.setText(str(acq_object.pulse_amp))
            self.pulse_pattern.setText(acq_object.pulse_pattern)
            self.cycle.setText(str(acq_object.cycle))
            self.baseline_mean_edit.setText(
                str(round_sig(acq_object.baseline_mean, sig=4))
            )
            self.delta_v_edit.setText(str(round_sig(acq_object.delta_v, sig=4)))
            self.voltage_sag_edit.setText(str(round_sig(acq_object.voltage_sag, sig=4)))
            self.spike_threshold_edit.setText(
                str(round_sig(acq_object.spike_threshold, sig=4))
            )
            self.spike_rate_edit.setText(
                str(round_sig(acq_object.hertz_exact(), sig=4))
            )
            self.half_width_edit.setText(str(round_sig(acq_object.spike_width())))
            self.ahp_edit.setText(str(round_sig(acq_object.ahp_y, sig=4)))
            self.baseline_stability_edit.setText(
                str(round_sig(acq_object.baseline_stability, sig=4))
            )
            self.acq_plot.setData(
                x=acq_object.plot_acq_x(),
                y=acq_object.plot_acq_y(),
                pen=pg.mkPen("w"),
                symbol="o",
                symbolSize=8,
                symbolBrush=(0, 0, 0, 0),
                symbolPen=(0, 0, 0, 0),
            )

            self.delta_v_data.setData(
                x=acq_object.plot_deltav_x(),
                y=acq_object.plot_deltav_y(),
                pen=pg.mkPen(color="r", width=2),
            )

            self.vsag_data.setData(
                x=acq_object.plot_voltage_sag_x(),
                y=acq_object.plot_voltage_sag_y(),
                pen=pg.mkPen(color="m", width=2),
            )
            if not np.isnan(acq_object.peaks[0]):
                self.spike_peaks_data.setData(
                    x=acq_object.spike_peaks_x(),
                    y=acq_object.spike_peaks_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="y",
                )
                self.spk_width_acq_plot.setData(
                    x=acq_object.spike_width_x(),
                    y=acq_object.spike_width_y(),
                    pen=pg.mkPen("g", width=4),
                )

                self.st_data_acq_plot.setData(
                    x=acq_object.plot_st_x(),
                    y=acq_object.plot_st_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="b",
                )

                self.ahp_acq_data.setData(
                    x=acq_object.plot_ahp_x(),
                    y=acq_object.plot_ahp_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="m",
                )

                self.clickable_spike_data.setData(
                    x=acq_object.spike_x_array(),
                    y=acq_object.first_ap,
                    symbol="o",
                    symbolSize=8,
                    symbolBrush=(0, 0, 0, 0),
                    symbolPen=(0, 0, 0, 0),
                )

                self.spk_width_spk_plot.setData(
                    x=acq_object.spike_width_x(),
                    y=acq_object.spike_width_y(),
                    pen=pg.mkPen("g", width=4),
                )

                self.st_data_spk_plot.setData(
                    x=acq_object.plot_st_x(),
                    y=acq_object.plot_st_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="b",
                )

                self.ahp_spike_data.setData(
                    x=acq_object.plot_ahp_x(),
                    y=acq_object.plot_ahp_y(),
                    pen=None,
                    symbol="o",
                    symbolBrush="m",
                )
            else:
                self.clearAcqPlots(clear_spikes=True)
        else:
            self.clearAcqPlots(clear_main=True, clear_spikes=True)
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.text = pg.TextItem(text="No acquisition", anchor=(0.5, 0.5))
            self.text.setFont(QFont("Helvetica", 20))
            self.plot_widget.setRange(xRange=(-30, 30), yRange=(-30, 30))
            self.plot_widget.addItem(self.text)
        self.acquisition_number.setEnabled(True)

    def plotClicked(self, item, points):
        logger.info(
            f"Current clamp acquisition {self.acquisition_number.value()} point clicked."
        )
        if self.last_acq_point_clicked:
            self.plot_widget.removeItem(self.last_acq_point_clicked[0])
            self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        acq_point_clicked = pg.PlotDataItem(
            x=[points[0].pos()[0]],
            y=[points[0].pos()[1]],
            pen=None,
            symbol="o",
            symbolPen=pg.mkPen("#E867E8", width=3),
        )
        self.plot_widget.addItem(acq_point_clicked)
        self.last_acq_point_clicked = (acq_point_clicked, points[0].pos())

        spike_point_clicked = pg.PlotDataItem(
            x=[points[0].pos()[0]],
            y=[points[0].pos()[1]],
            pen=None,
            symbol="o",
            symbolPen=pg.mkPen("#E867E8", width=3),
        )
        self.spike_plot.addItem(spike_point_clicked)
        self.last_spike_point_clicked = (spike_point_clicked, points[0].pos())

        logger.info(f"Point {self.last_spike_point_clicked[1][0]} clicked.")

    def setSpikeThreshold(self):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return None

        if self.last_acq_point_clicked is None:
            logger.info("No point was selected, peak not set.")
            self.errorDialog("No point was selected, peak not set.")
            return None

        acq = self.exp_manager.exp_dict["current_clamp"][
            self.acquisition_number.value()
        ]
        self.need_to_save = True
        x = self.last_acq_point_clicked[1][0]
        y = self.last_acq_point_clicked[1][1]
        acq.set_spike_threshold(x, y)

        self.plot_widget.removeItem(self.last_acq_point_clicked[0])
        self.spike_plot.removeItem(self.last_spike_point_clicked[0])

        self.st_data_spk_plot.setData(
            x=acq.plot_st_x(),
            y=acq.plot_st_y(),
            pen=None,
            symbol="o",
            symbolBrush="b",
        )
        self.st_data_acq_plot.setData(
            x=acq.plot_st_x(),
            y=acq.plot_st_y(),
            pen=None,
            symbol="o",
            symbolBrush="b",
        )

        self.spk_width_acq_plot.setData(
            x=acq.spike_width_x(),
            y=acq.spike_width_y(),
            pen=pg.mkPen("g", width=4),
        )

        self.spk_width_spk_plot.setData(
            x=acq.spike_width_x(),
            y=acq.spike_width_y(),
            pen=pg.mkPen("g", width=4),
        )

        logger.info(f"Spike threshold set {self.acquisition_number.value()}.")

    def deleteAcq(self):
        if (
            not self.exp_manager.acqs_exist("current_clamp")
            or self.acquisition_number.value()
            not in self.exp_manager.exp_dict["current_clamp"]
        ):
            logger.info(f"No acquisition {self.acquisition_number.value()}.")
            self.errorDialog(f"No acquisition {self.acquisition_number.value()}.")
            return None

        logger.info(f"Deleting acquisition {self.acquisition_number.value()}.")
        self.need_to_save = False
        self.exp_manager.delete_acq("current_clamp", self.acquisition_number.value())

        # Clear plots
        self.plot_widget.clear()
        logger.info(f"Deleted acquisition {self.acquisition_number.value()}.")

    def resetRejectedAcqs(self):
        if not self.exp_manager.acqs_exist("current_clamp"):
            logger.info("Did not reset acquistions, no acquisitions exist.")
            self.errorDialog("Did not reset acquistions, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting deleted acquisitions.")
            self.exp_manager.reset_deleted_acqs("current_clamp")
            logger.info("Deleted acquisitions reset.")
            self.pbar.setFormat("Reset deleted acquisitions.")

    def resetRecentRejectAcq(self):
        if not self.exp_manager.acqs_exist("current_clamp"):
            logger.info("Did not reset recent acquistion, no acquisitions exist.")
            self.errorDialog("Did not reset recent acquistion, no acquisitions exist.")
        else:
            self.need_to_save = True
            logger.info("Resetting most recent deleted acquisition.")
            number = self.exp_manager.reset_recent_deleted_acq("current_clamp")
            if number != 0:
                self.acquisition_number.setValue(number)
                logger.info(f"Acquisition {number} reset.")
                self.pbar.setFormat(f"Reset acquisition {number}.")
            else:
                logger.info("No acquisition to reset.")
                self.pbar.setFormat("No acquisition to reset.")

    def errorDialog(self, text):
        self.signals.error.emit(text)
