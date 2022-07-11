# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 09:21:26 2021

Last updated on Wed Feb 16 12:33:00 2021 

@author: LarsNelson
"""
from glob import glob
from math import log10, floor, isnan, nan

import json
import numpy as np
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFormLayout,
    QSpinBox,
    QTabWidget,
    QProgressBar,
    QMessageBox,
    QScrollArea,
)
from PyQt5.QtCore import QThreadPool
import pyqtgraph as pg

from ..acq.acq import Acq
from ..final_analysis.final_current_clamp import FinalCurrentClampAnalysis
from ..gui_widgets.qtwidgets import (
    LineEdit,
    SaveWorker,
    YamlWorker,
    ListView,
    ListModel,
    DragDropScrollArea,
)
from ..load_analysis.load_classes import LoadCurrentClampData
from ..main_acq.current_clamp import CurrentClampAnalysis


class currentClampWidget(QWidget):
    """
    This the currentClampAnalysis widget. The primary functions are carried
    out by the CurrentClamp class. The final analysis and output is done by
    functions contained within the currentClampAnalysis widget.
    """

    def __init__(self):
        super().__init__()

        self.main_widget = QScrollArea()
        self.main_layout = QHBoxLayout()
        self.input_layout = QFormLayout()
        self.v_layout = QVBoxLayout()
        self.analysis_layout = QVBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.analysis_buttons = QFormLayout()

        self.setLayout(self.main_layout)
        self.v_layout.addLayout(self.input_layout, 0)
        self.main_layout.addLayout(self.v_layout, 0)
        self.main_layout.addLayout(self.analysis_layout, 0)
        self.analysis_layout.addLayout(self.plot_layout, 1)
        self.plot_layout.addLayout(self.analysis_buttons, 1)

        # Analysis layout setup
        self.acquisition_number_label = QLabel("Acq number")
        self.acquisition_number = QSpinBox()
        self.acquisition_number.valueChanged.connect(self.spinbox)
        self.analysis_buttons.addRow(
            self.acquisition_number_label, self.acquisition_number
        )

        self.epoch_label = QLabel("Epoch")
        self.epoch_number = QLineEdit()
        self.analysis_buttons.addRow(self.epoch_label, self.epoch_number)

        self.baseline_mean_label = QLabel("Baseline mean (mV)")
        self.baseline_mean_edit = QLineEdit()
        self.analysis_buttons.addRow(self.baseline_mean_label, self.baseline_mean_edit)

        self.delta_v_label = QLabel("Delta V (mV)")
        self.delta_v_edit = QLineEdit()
        self.analysis_buttons.addRow(self.delta_v_label, self.delta_v_edit)

        self.spike_threshold_label = QLabel("Spike threshold (mV)")
        self.spike_threshold_edit = QLineEdit()
        self.analysis_buttons.addRow(
            self.spike_threshold_label, self.spike_threshold_edit
        )

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

        self.delete_event_button = QPushButton("Delete acquisition")
        self.delete_event_button.clicked.connect(self.delete_acq)
        self.analysis_buttons.addRow(self.delete_event_button)

        self.reset_recent_reject_button = QPushButton(
            "Reset recent rejected acquisition"
        )
        self.reset_recent_reject_button.clicked.connect(self.reset_recent_reject_acq)
        self.analysis_buttons.addRow(self.reset_recent_reject_button)

        self.reset_rejected_acqs_button = QPushButton("Reset rejected acquistions")
        self.reset_rejected_acqs_button.clicked.connect(self.reset_rejected_acqs)
        self.analysis_buttons.addRow(self.reset_rejected_acqs_button)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMinimumWidth(300)
        self.plot_layout.addWidget(self.plot_widget)

        self.spike_plot = pg.PlotWidget()
        self.spike_plot.setMinimumWidth(300)
        self.plot_layout.addWidget(self.spike_plot)

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.analysis_layout.addWidget(self.tabs, 1)

        self.tabs.setStyleSheet("""QTabWidget::tab-bar {alignment: left;}""")

        # Final data widgets
        self.raw_data_table = pg.TableWidget(sortable=False)
        self.final_data_table = pg.TableWidget(sortable=False)
        self.pulse_aps = pg.TableWidget(sortable=False)
        self.ramp_aps = pg.TableWidget(sortable=False)
        self.deltav = pg.TableWidget(sortable=False)
        self.tabs.addTab(self.raw_data_table, "Raw data")
        self.tabs.addTab(self.final_data_table, "Final data")
        self.tabs.addTab(self.pulse_aps, "First APs-Pulse")
        self.tabs.addTab(self.ramp_aps, "First APs-Ramp")
        self.tabs.addTab(self.deltav, "Delta V")

        self.iv_curve_plot = pg.PlotWidget()
        self.tabs.addTab(self.iv_curve_plot, "IV curve")

        self.spike_curve_plot = pg.PlotWidget()
        self.tabs.addTab(self.spike_curve_plot, "Spike curve")

        self.pulse_ap_plot = pg.PlotWidget()
        self.tabs.addTab(self.pulse_ap_plot, "Pulse AP")

        self.ramp_ap_plot = pg.PlotWidget()
        self.tabs.addTab(self.ramp_ap_plot, "Ramp AP")

        # Input widgets and labels
        self.load_acq_label = QLabel("Acquisition(s)")
        self.input_layout.addRow(self.load_acq_label)
        self.acq_view = ListView()
        self.acq_model = ListModel()
        self.analysis_type = "current clamp"
        self.acq_model.setAnalysisType(self.analysis_type)
        self.acq_view.setModel(self.acq_model)
        self.input_layout.addRow(self.acq_view)

        self.del_selection_button = QPushButton("Delete selection")
        self.input_layout.addRow(self.del_selection_button)

        self.b_start_label = QLabel("Baseline start (ms)")
        self.b_start_edit = LineEdit()
        self.b_start_edit.setObjectName("b_start_edit")
        self.b_start_edit.setEnabled(True)
        self.b_start_edit.setText("0")
        self.input_layout.addRow(self.b_start_label, self.b_start_edit)

        self.b_end_label = QLabel("Baseline end (ms)")
        self.b_end_edit = LineEdit()
        self.b_end_edit.setObjectName("b_end_edit")
        self.b_end_edit.setEnabled(True)
        self.b_end_edit.setText("300")
        self.input_layout.addRow(self.b_end_label, self.b_end_edit)

        self.sample_rate_label = QLabel("Sample rate (Hz)")
        self.sample_rate_edit = LineEdit()
        self.sample_rate_edit.setObjectName("sample_rate_edit")
        self.sample_rate_edit.setEnabled(True)
        self.sample_rate_edit.setText("10000")
        self.input_layout.addRow(self.sample_rate_label, self.sample_rate_edit)

        self.pulse_start_label = QLabel("Pulse start(ms)")
        self.pulse_start_edit = LineEdit()
        self.pulse_start_edit.setObjectName("pulse_start_edit")
        self.pulse_start_edit.setEnabled(True)
        self.pulse_start_edit.setText("300")
        self.input_layout.addRow(self.pulse_start_label, self.pulse_start_edit)

        self.pulse_end_label = QLabel("Pulse end (ms)")
        self.pulse_end_edit = LineEdit()
        self.pulse_end_edit.setObjectName("pulse_end_edit")
        self.pulse_end_edit.setEnabled(True)
        self.pulse_end_edit.setText("1002")
        self.input_layout.addRow(self.pulse_end_label, self.pulse_end_edit)

        self.ramp_start_label = QLabel("Ramp start (ms)")
        self.ramp_start_edit = LineEdit()
        self.ramp_start_edit.setObjectName("ramp_start_edit")
        self.ramp_start_edit.setEnabled(True)
        self.ramp_start_edit.setText("300")
        self.input_layout.addRow(self.ramp_start_label, self.ramp_start_edit)

        self.ramp_end_label = QLabel("Ramp end (ms)")
        self.ramp_end_edit = LineEdit()
        self.ramp_end_edit.setObjectName("ramp_end_edit")
        self.ramp_end_edit.setEnabled(True)
        self.ramp_end_edit.setText("4000")
        self.input_layout.addRow(self.ramp_end_label, self.ramp_end_edit)

        self.min_spike_threshold_label = QLabel("Min spike threshold (mV)")
        self.min_spike_threshold_edit = LineEdit()
        self.min_spike_threshold_edit.setObjectName("min_spike_threshold")
        self.min_spike_threshold_edit.setEnabled(True)
        self.min_spike_threshold_edit.setText("-15")
        self.input_layout.addRow(
            self.min_spike_threshold_label, self.min_spike_threshold_edit
        )

        self.iv_start_label = QLabel("IV curve start")
        self.iv_start_edit = LineEdit()
        self.iv_start_edit.setObjectName("iv_start_edit")
        self.iv_start_edit.setText("1")
        self.input_layout.addRow(self.iv_start_label, self.iv_start_edit)

        self.iv_end_label = QLabel("IV curve end")
        self.iv_end_edit = LineEdit()
        self.iv_end_edit.setObjectName("iv_end_edit")
        self.iv_end_edit.setText("6")
        self.input_layout.addRow(self.iv_end_label, self.iv_end_edit)

        self.analyze_acq_button = QPushButton("Analyze acquisitions")
        self.analyze_acq_button.setObjectName("analyze_acq_button")
        self.input_layout.addRow(self.analyze_acq_button)
        self.analyze_acq_button.clicked.connect(self.analyze)

        self.calculate_parameters = QPushButton("Calculate parameters")
        self.calculate_parameters.setObjectName("calculate_parameters")
        self.input_layout.addRow(self.calculate_parameters)
        self.calculate_parameters.clicked.connect(self.final_analysis_button)

        self.reset_button = QPushButton("Reset Analysis")
        self.input_layout.addRow(self.reset_button)
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setObjectName("reset_button")

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.v_layout.addWidget(self.pbar, 0)

        self.threadpool = QThreadPool()

        self.set_width()

        self.acq_dict = {}
        self.analysis_list = []
        self.file_list = []
        self.raw_list = []
        self.iv_line = []
        self.iv_plot_x = []
        self.hertz_x = []
        self.hertz_y = []
        self.deleted_acqs = {}
        self.pref_dict = {}
        self.recent_reject_acq = {}
        self.calc_param_clicked = False
        self.need_to_save = False

    def set_width(self):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            i.setMinimumWidth(70)

        push_buttons = self.findChildren(QPushButton)
        for i in push_buttons:
            i.setMinimumWidth(100)

    def del_selection(self):
        self.need_to_save = True
        indexes = self.acq_view.selectedIndexes()
        if len(indexes) > 0:
            for index in sorted(indexes, reverse=True):
                del self.acq_model.acq_list[index.row()]
                del self.acq_model.fname_list[index.row()]
            self.acq_model.layoutChanged.emit()
            self.acq_view.clearSelection()

    def analyze(self):
        self.need_to_save = True
        self.analyze_acq_button.setEnabled(False)
        if len(self.acq_model.acq_list) == 0:
            self.file_does_not_exist()
            self.analyze_acq_button.setEnabled(True)
        else:
            self.pbar.setFormat("Analyzing...")
            self.pbar.setValue(0)
            self.acq_dict = self.acq_model.acq_dict
            for count, acq in enumerate(self.acq_dict.items()):
                acq.analyze(
                    sample_rate=self.sample_rate_edit.toInt(),
                    baseline_start=self.b_start_edit.toInt(),
                    baseline_end=self.b_end_edit.toInt(),
                    filter_type="None",
                    pulse_start=self.pulse_start_edit.toInt(),
                    pulse_end=self.pulse_end_edit.toInt(),
                    ramp_start=self.ramp_start_edit.toInt(),
                    ramp_end=self.ramp_end_edit.toInt(),
                    threshold=self.min_spike_threshold_edit.toInt(),
                )
                self.pbar.setValue(
                    int(((count + 1) / len(self.acq_model.acq_list)) * 100)
                )
            self.analysis_list = [int(i) for i in self.acq_dict]
            self.acquisition_number.setMaximum(self.analysis_list[-1])
            self.acquisition_number.setMinimum(self.analysis_list[0])
            self.acquisition_number.setValue(self.analysis_list[0])
            self.spinbox(int(self.analysis_list[0]))
            self.analyze_acq_button.setEnabled(False)
            self.pbar.setFormat("Analysis finished")

    def reset(self):
        self.need_to_save = False
        self.plot_widget.clear()
        self.spike_plot.clear()
        self.acq_dict = {}
        self.analysis_list = []
        self.acq_model.acq_list = []
        self.acq_model.fname_list = []
        self.analyze_acq_button.setEnabled(True)
        self.calculate_parameters.setEnabled(True)
        self.raw_data_table.clear()
        self.final_data_table.clear()
        self.iv_curve_plot.clear()
        self.spike_curve_plot.clear()
        self.pulse_aps.clear()
        self.ramp_aps.clear()
        self.pulse_ap_plot.clear()
        self.ramp_ap_plot.clear()
        self.iv_line = []
        self.iv_plot_x = []
        self.hertz_x = []
        self.hertz_y = []
        self.deleted_acqs = {}
        self.recent_reject_acq = {}
        self.pref_dict = {}
        self.calc_param_clicked = False
        self.need_to_save = False
        self.pbar.setValue(0)
        self.pbar.setFormat("")

    def spinbox(self, h):
        self.need_to_save = True
        self.plot_widget.clear()
        self.spike_plot.clear()
        if self.acq_dict.get(str(self.acquisition_number.text())):
            acq_object = self.acq_dict[str(self.acquisition_number.text())]
            self.epoch_number.setText(acq_object.epoch)
            self.baseline_mean_edit.setText(
                str(self.round_sig(acq_object.baseline_mean, sig=4))
            )
            self.delta_v_edit.setText(str(self.round_sig(acq_object.delta_v, sig=4)))
            self.spike_threshold_edit.setText(
                str(self.round_sig(acq_object.spike_threshold, sig=4))
            )
            self.spike_rate_edit.setText(
                str(self.round_sig(acq_object.hertz_exact, sig=4))
            )
            self.ahp_edit.setText(str(self.round_sig(acq_object.ahp_y, sig=4)))
            self.baseline_stability_edit.setText(
                str(self.round_sig(acq_object.baseline_stability_ratio, sig=4))
            )
            if acq_object.ramp == "0":
                self.plot_widget.plot(x=acq_object.x_array, y=acq_object.array)
                self.plot_widget.plot(x=acq_object.plot_x, y=acq_object.plot_y, pen="r")
                if acq_object.peaks[0] is not np.nan:
                    self.plot_widget.plot(
                        x=acq_object.spike_peaks_x(),
                        y=acq_object.spike_peaks_y(),
                        pen=None,
                        symbol="o",
                        symbolBrush="y",
                    )
                    self.plot_widget.plot(
                        x=acq_object.plot_rheo_x(),
                        y=[acq_object.spike_threshold],
                        pen=None,
                        symbol="o",
                        symbolBrush="b",
                    )

                    self.spike_plot.plot(
                        x=acq_object.spike_x_array(), y=acq_object.first_ap,
                    )
                    self.spike_plot.plot(
                        x=acq_object.spike_width_x(),
                        y=acq_object.spike_width_y(),
                        pen=pg.mkPen("g", width=4),
                    )
                    self.spike_plot.plot(
                        x=acq_object.plot_rheo_x(),
                        y=[acq_object.spike_threshold],
                        pen=None,
                        symbol="o",
                        symbolBrush="b",
                    )
                    self.spike_plot.plot(
                        x=acq_object.plot_ahp_x(),
                        y=[acq_object.ahp_y],
                        pen=None,
                        symbol="o",
                        symbolBrush="m",
                    )
            elif acq_object.ramp == "1":
                self.plot_widget.plot(x=acq_object.x_array, y=acq_object.array)
                if len(acq_object.peaks) > 0:
                    self.plot_widget.plot(
                        x=acq_object.spike_peaks_x(),
                        y=acq_object.spike_peaks_y(),
                        pen=None,
                        symbol="o",
                        symbolBrush="y",
                    )
                    self.plot_widget.plot(
                        x=acq_object.plot_rheo_x(),
                        y=[acq_object.spike_threshold],
                        pen=None,
                        symbol="o",
                        symbolBrush="b",
                    )
                    self.spike_plot.plot(
                        x=acq_object.spike_x_array(), y=acq_object.first_ap,
                    )
                    self.spike_plot.plot(
                        x=acq_object.spike_width_x(),
                        y=acq_object.spike_width_y(),
                        pen=pg.mkPen("g", width=4),
                    )
                    self.spike_plot.plot(
                        x=acq_object.plot_rheo_x(),
                        y=[acq_object.spike_threshold],
                        pen=None,
                        symbol="o",
                        symbolBrush="b",
                    )
                    self.spike_plot.plot(
                        x=acq_object.plot_ahp_x(),
                        y=[acq_object.ahp_y],
                        pen=None,
                        symbol="o",
                        symbolBrush="m",
                    )
        else:
            pass

    def round_sig(self, x, sig=2):
        if isnan(x):
            return np.nan
        elif x == 0:
            return 0
        elif x != 0 or x is not np.nan or nan:
            return round(x, sig - int(floor(log10(abs(x)))) - 1)

    def delete_acq(self):
        self.need_to_save = False
        self.recent_reject_acq = {}
        self.deleted_acqs[str(self.acquisition_number.text())] = self.acq_dict[
            str(self.acquisition_number.text())
        ]
        self.recent_reject_acq[str(self.acquisition_number.text())] = self.acq_dict[
            str(self.acquisition_number.text())
        ]
        del self.acq_dict[str(self.acquisition_number.text())]
        self.plot_widget.clear()
        self.analysis_list.remove(int(self.acquisition_number.text()))

    def reset_rejected_acqs(self):
        self.need_to_save = False
        self.acq_dict.update(self.deleted_acqs)
        self.analysis_list += [int(i) for i in self.deleted_acqs.keys()]
        self.deleted_acqs = {}
        self.recent_reject_acq = {}

    def reset_recent_reject_acq(self):
        self.need_to_save = False
        self.acq_dict.update(self.recent_reject_acq)
        self.analysis_list += [int(i) for i in self.recent_reject_acq.keys()]

    def final_analysis_button(self):
        self.need_to_save = True
        self.calculate_parameters.setEnabled(False)
        self.calc_param_clicked = True
        self.final_obj = FinalCurrentClampAnalysis(self.acq_dict)
        self.raw_data_table.setData(self.final_obj.raw_df.T.to_dict())
        self.final_data_table.setData(self.final_obj.final_df.T.to_dict())
        self.pulse_aps.setData(self.final_obj.pulse_df.T.to_dict())
        self.ramp_aps.setData(self.final_obj.ramp_df.T.to_dict())
        self.deltav.setData(self.final_obj.deltav_df.T.to_dict())
        self.plot_iv_curve()
        self.plot_spike_frequency(self.final_obj.final_df)
        if not self.final_obj.pulse_df.empty:
            self.plot_pulse_ap(self.final_obj.pulse_df)
        if not self.final_obj.ramp_df.empty:
            self.plot_ramp_ap(self.final_obj.ramp_df)

    def plot_iv_curve(self):
        deltav_df = self.final_obj.deltav_df
        iv_df = self.final_obj.iv_df
        if len(self.final_obj.plot_epochs) == 1:
            self.iv_curve_plot.plot(
                iv_df["iv_plot_x"], iv_df[self.final_obj.plot_epochs[0]]
            )
            self.iv_curve_plot.plot(
                deltav_df["deltav_x"],
                deltav_df[self.final_obj.plot_epochs[0]],
                pen=None,
                symbol="o",
                symbolBrush="y",
            )
        else:
            self.iv_curve_plot.addLegend()
            for i in self.final_obj.plot_epochs:
                if iv_df[i].isna().all():
                    pass
                else:
                    pencil = pg.mkPen(color=pg.intColor(i))
                    brush = pg.mkBrush(color=pg.intColor(i))
                    self.iv_curve_plot.plot(iv_df["iv_plot_x"], iv_df[i], pen=pencil)
                    self.iv_curve_plot.plot(
                        deltav_df["deltav_x"],
                        deltav_df[i],
                        pen=None,
                        symbol="o",
                        symbolPen=pencil,
                        symbolBrush=brush,
                        name=f"Epoch {i}",
                    )

    def plot_spike_frequency(self, df):
        df1 = df[df["Ramp", ""] == 0].copy()
        if df1.empty == True or "Hertz" not in df1.columns.levels[0].tolist():
            pass
        else:
            plot_epochs = df1["Epoch"].to_list()
            df2 = df1["Hertz"].copy()
            df2.dropna(axis=0, how="all", inplace=True)
            self.hertz_x = np.array(df2.T.index.map(int))
            self.hertz_y = df2.to_numpy()
            if len(self.hertz_y) == 1:
                self.spike_curve_plot.plot(
                    self.hertz_x,
                    self.hertz_y[0],
                    symbol="o",
                    name=f"Epoch {plot_epochs[0]}",
                )
            else:
                self.spike_curve_plot.addLegend()
                for i in range(len(self.hertz_y)):
                    if np.isnan(self.hertz_y).all():
                        pass
                    else:
                        pencil = pg.mkPen(color=pg.intColor(i))
                        brush = pg.mkBrush(color=pg.intColor(i))
                        self.spike_curve_plot.plot(
                            self.hertz_x,
                            self.hertz_y[i],
                            symbol="o",
                            pen=pencil,
                            name=f"Epoch {plot_epochs[i]}",
                            symbolPen=pencil,
                            symbolBrush=brush,
                        )

    def plot_pulse_ap(self, df):
        if len(df.columns) > 1:
            for i in df.columns:
                self.pulse_ap_plot.addLegend()
                array = df[i].to_numpy()
                pencil = pg.mkPen(color=pg.intColor(i))
                self.pulse_ap_plot.plot(
                    np.arange(len(array)) / 10, array, pen=pencil, name=f"Epoch {i}"
                )
        else:
            i = df.columns[0]
            array = df[i]
            self.pulse_ap_plot.plot(
                np.arange(len(array)) / 10, array, name=f"Epoch {i}"
            )

    def plot_ramp_ap(self, df):
        if len(df.columns) > 1:
            for i in df.columns:
                self.ramp_ap_plot.addLegend()
                array = df[i].to_numpy()
                pencil = pg.mkPen(color=pg.intColor(i))
                self.ramp_ap_plot.plot(
                    np.arange(len(array)) / 10, array, pen=pencil, name=f"Epoch {i}"
                )
        else:
            i = df.columns[0]
            array = df[i]
            self.ramp_ap_plot.plot(np.arange(len(array)) / 10, array, name=f"Epoch {i}")

    def open_files(self, directory):
        self.analyze_acq_button.setEnabled(False)
        self.calculate_parameters.setEnabled(False)
        load_dict = YamlWorker.load_yaml(directory)
        self.pbar.setFormat("Loading...")
        file_list = glob(f"{directory}/*.json")
        if not file_list:
            self.file_list = None
        else:
            for i in range(len(file_list)):
                with open(file_list[i]) as file:
                    data = json.load(file)
                    x = LoadCurrentClamp(data)
                    self.acq_dict[str(x.acq_number)] = x
                    self.pbar.setValue(int(((i) / len(file_list)) * 100))
            excel_file = glob(f"{directory}/*.xlsx")[0]
            self.final_obj = LoadCurrentClampData(excel_file)
            self.plot_spike_frequency(self.final_obj.final_df)
            self.plot_iv_curve(self.final_obj.iv_df)
            self.pbar.setFormat("Loaded")
            self.acquisition_number.setMaximum(int(list(self.acq_dict.keys())[-1]))
            self.acquisition_number.setMinimum(int(list(self.acq_dict.keys())[0]))
            self.analysis_list = np.arange(
                int(list(self.acq_dict.keys())[0]),
                int(list(self.acq_dict.keys())[-1]) + 1,
            ).tolist()
            self.acquisition_number.setValue(int(list(self.acq_dict.keys())[0]))
            self.raw_list = [
                self.acq_dict[i].current_clamp_dict for i in self.acq_dict.keys()
            ]
            self.spinbox(self.analysis_list[0])

    def set_preferences(self, pref_dict):
        line_edits = self.findChildren(QLineEdit)
        for i in line_edits:
            if i.objectName() != "":
                i.setText(pref_dict["line_edits"][i.objectName()])

        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                i.setEnabled(pref_dict["buttons"][i.objectName()])

    def create_pref_dict(self):
        line_edits = self.findChildren(QLineEdit)
        line_edit_dict = {}
        for i in line_edits:
            if i.objectName() != "":
                line_edit_dict[i.objectName()] = i.text()
        self.pref_dict["line_edits"] = line_edit_dict

        buttons_dict = {}
        buttons = self.findChildren(QPushButton)
        for i in buttons:
            if i.objectName() != "":
                buttons_dict[i.objectName()] = i.isEnabled()
        self.pref_dict["buttons"] = buttons_dict

    def file_does_not_exist(self):
        self.dlg = QMessageBox(self)
        self.dlg.setWindowTitle("Error")
        self.dlg.setText("File does not exist")
        self.dlg.exec()

    def save_as(self, save_filename):
        self.need_to_save = False
        self.pbar.setValue(0)
        self.pbar.setFormat("Saving...")
        self.create_pref_dict()
        self.pref_dict["Final Analysis"] = self.calc_param_clicked
        self.pref_dict["Acq_number"] = self.acquisition_number.value()
        self.pref_dict["Deleted Acqs"] = list(self.deleted_acqs.keys())
        YamlWorker.save_yaml(self.pref_dict, save_filename)
        if self.pref_dict["Final Analysis"]:
            self.final_obj.save_data(save_filename)
        self.worker = SaveWorker(save_filename, self.acq_dict)
        self.worker.signals.progress.connect(self.update_save_progress)
        self.worker.signals.finished.connect(self.progress_finished)
        self.threadpool.start(self.worker)

    def load_preferences(self, file_name):
        self.need_to_save = True
        load_dict = YamlWorker.load_yaml(file_name)
        self.set_preferences(load_dict)

    def save_preferences(self, save_filename):
        self.create_pref_dict()
        if self.pref_dict:
            YamlWorker.save_yaml(self.pref_dict, save_filename)
        else:
            pass

    def update_save_progress(self, progress):
        self.pbar.setValue(progress)

    def progress_finished(self, finished):
        self.pbar.setFormat(finished)


if __name__ == "__main__":
    currentClampWidget()
