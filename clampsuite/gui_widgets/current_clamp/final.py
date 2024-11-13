import logging

import numpy as np
import pandas as pd
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
import pyqtgraph as pg
from PySide6.QtWidgets import QTabWidget


logger = logging.getLogger(__name__)


class FinalCurrentClampAnalysis(DockArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.df_dock = Dock("Data")
        self.addDock(self.df_dock, "left")
        self.df_tabs = QTabWidget()
        self.df_tabs.setUsesScrollButtons(True)
        self.df_dock.addWidget(self.df_tabs)
        self.plot_dock = Dock("Plots")
        self.addDock(self.plot_dock, "right")
        self.plot_tabs = QTabWidget()
        self.plot_tabs.setUsesScrollButtons(True)
        self.plot_dock.addWidget(self.plot_tabs)
        self.plot_tabs.setStyleSheet("""QTabWidget::tab-bar {alignment: left;}""")
        self.df_tabs.setUsesScrollButtons(True)

    def runFinalAnalysis(self):
        fi_an = self.exp_manager.final_analysis
        for key, value in fi_an.df_dict.items():
            table = pg.TableWidget(sortable=False)
            table.setData(value.T.to_dict())
            self.table_dict["key"] = table
            self.df_tabs.addTab(table, key)
        logger.info("Set final data into tables.")
        self.plotIVCurve("Delta V (mV)")
        self.plotIVCurve("Voltage sag (mV)")
        if fi_an.hertz:
            self.plotSpikeFrequency(fi_an.df_dict["Hertz"].copy())
        if fi_an.pulse_ap:
            self.plotAP(fi_an.df_dict["Pulse APs"].copy(), "Pulse")
        if fi_an.ramp_ap:
            self.plotAP(fi_an.df_dict["Ramp APs"].copy(), "Ramp")

    def plotIVCurve(self, column: str):
        iv_curve_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict[f"{column} iv_curve_plot"] = iv_curve_plot
        self.plot_tabs.addTab(iv_curve_plot, f"{column} IV curve")
        fa = self.exp_manager.final_analysis
        deltav_df = fa.df_dict[column]
        iv_x = fa.df_dict[f"{column} IV x"]
        iv_y = fa.df_dict[f"{column} IV lines"]
        iv_curve_plot.addLegend()
        epochs = iv_y.columns.to_list()
        for i in epochs:
            if iv_x[i].isna().all():
                pass
            else:
                pencil = pg.mkPen(color=pg.Color(int(i)))
                brush = pg.mkBrush(color=pg.intColor(int(i)))
                iv_curve_plot.plot(iv_x[i].to_numpy(), iv_y[i].to_numpy(), pen=pencil)
                iv_curve_plot.plot(
                    deltav_df["Pulse amp (pA)"].to_numpy(),
                    deltav_df[i].to_numpy(),
                    pen=None,
                    symbol="o",
                    symbolPen=pencil,
                    symbolBrush=brush,
                    name=f"Epoch {i}",
                )

    def plotSpikeFrequency(self, hertz):
        spike_curve_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict["spike_curve_plot"] = spike_curve_plot
        self.plot_tabs.addTab(spike_curve_plot, "Spike curve")
        pulse_amp = hertz.pop("Pulse amp (pA)").to_numpy()
        plot_epochs = hertz.columns.to_list()
        spike_curve_plot.addLegend()
        for i in plot_epochs:
            pencil = pg.mkPen(color=pg.intColor(i))
            brush = pg.mkBrush(color=pg.intColor(i))
            spike_curve_plot.plot(
                pulse_amp,
                hertz[i].to_numpy(),
                symbol="o",
                pen=pencil,
                name=f"Epoch {i}",
                symbolPen=pencil,
                symbolBrush=brush,
            )

    def plotAP(self, df: pd.DataFrame, ap_type: str):
        pulse_ap_plot = pg.PlotWidget(useOpenGL=True)
        self.plot_dict[f"{ap_type}_ap_plot"] = pulse_ap_plot
        self.plot_tabs.addTab(pulse_ap_plot, f"{ap_type} AP")
        pulse_ap_plot.addLegend()
        if len(df.columns) > 1:
            for i in df.columns:
                array = df[i].to_numpy()
                pencil = pg.mkPen(color=pg.intColor(i))
                pulse_ap_plot.plot(
                    np.arange(len(array)) / 10, array, pen=pencil, name=f"Epoch {i}"
                )
        else:
            i = df.columns[0]
            array = df[i]
            pulse_ap_plot.plot(np.arange(len(array)) / 10, array, name=f"Epoch {i}")
