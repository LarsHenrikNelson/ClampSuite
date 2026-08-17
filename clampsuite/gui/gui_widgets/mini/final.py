import logging

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PySide6.QtWidgets import (
    QComboBox,
    QTabWidget,
)

from ....functions.kde import create_kde

logger = logging.getLogger(__name__)


class FinalMiniAnalysis(DockArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.table_dock = Dock("Data (table)")
        self.ave_event_dock = Dock("Average Event")
        self.data_dock = Dock("Data (visualization)")
        self.addDock(self.table_dock, position="left")
        self.addDock(self.ave_event_dock, position="right")
        self.addDock(self.data_dock, position="bottom")
        self.ave_event_plot = pg.PlotWidget(
            labels={"left": "Amplitude (pA)", "bottom": "Time (ms)"}, useOpenGL=True
        )
        self.ave_event_plot.setLabel(
            "bottom",
            text="Time (ms)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_plot.setLabel(
            "left",
            text="Amplitude (pA)",
            **{"color": "#C9CDD0", "font-size": "10pt"},
        )
        self.ave_event_dock.addWidget(self.ave_event_plot)
        self.ave_event_plot.setObjectName("Ave event plot")
        self.final_tab_widget = QTabWidget()
        self.final_tab_widget.setMinimumHeight(300)
        self.table_dock.addWidget(self.final_tab_widget)
        self.stem_plot = pg.PlotWidget(labels={"bottom": "Time (ms)"}, useOpenGL=True)
        self.amp_dist = pg.PlotWidget(useOpenGL=True)
        self.plot_selector = QComboBox()
        self.plot_selector.setMaximumWidth(100)
        self.plot_selector.currentTextChanged.connect(self.plotRawData)
        self.data_dock.addWidget(self.plot_selector, 0, 0)
        self.data_dock.addWidget(self.stem_plot, 0, 1)
        self.data_dock.addWidget(self.amp_dist, 0, 2)

    def runFinalAnalysis(self):
        fa = self.exp_manager.final_analysis
        self.plotAveEvent(
            fa.average_event_x(),
            fa.average_event_y(),
            fa.fit_decay_x(),
            fa.fit_decay_y(),
        )
        logger.info("Plotted mini average event")
        for key, df in fa.df_dict.items():
            data_table = pg.TableWidget(sortable=False)
            self.table_dict[key] = data_table
            data_table.setData(df.T.to_dict("dict"))
            self.final_tab_widget.addTab(data_table, key)
        logger.info("Set final data into tables.")
        plots = [
            "Amplitude (pA)",
            "Est tau (ms)",
            "Rise time (ms)",
            "Rise rate (pA/ms)",
            "IEI (ms)",
        ]
        self.plot_selector.clear()
        self.plot_selector.addItems(plots)
        self.plot_selector.setMinimumContentsLength(len(max(plots, key=len)))
        if self.plot_selector.currentText() != "IEI (ms)":
            self.plotRawData(self.plot_selector.currentText())

    def plotAveEvent(self, x, y, decay_x, decay_y):
        self.ave_event_plot.clear()
        self.ave_event_plot.plot(x=x, y=y, pen=pg.mkPen(width=3))
        self.ave_event_plot.plot(
            x=decay_x, y=decay_y, pen=pg.mkPen({"color": "#34E44B", "width": 2})
        )

    def plotRawData(self, y: str):
        if self.exp_manager.final_analysis is not None and y != "":
            if y != "IEI (ms)":
                self.plotStemData(y)
            else:
                self.stem_plot.clear()
            self.plotAmpDist(y)

    def plotStemData(self, column: str):
        self.stem_plot.clear()
        fa = self.exp_manager.final_analysis
        x_values = fa.timestamp_array()
        y_values = fa.get_raw_data(column)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(x_values, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        head_item = pg.PlotDataItem(
            x=x_values,
            y=y_values,
            pen=None,
            symbol="o",
            symbolSize=2,
            symbolPen=None,
            symbolBrush="w",
        )
        self.stem_plot.addItem(stem_item)
        self.stem_plot.addItem(head_item)
        self.stem_plot.setLabel(axis="left", text=f"{column}")

    def plotAmpDist(self, column: str):
        self.amp_dist.clear()
        fa = self.exp_manager.final_analysis
        log_y, x = create_kde(
            fa.df_dict["Raw data"],
            self.plot_selector.currentText(),
        )
        y = fa.get_raw_data(self.plot_selector.currentText())
        dist_item = pg.PlotDataItem(
            x=x,
            y=log_y,
            fillLevel=0,
            fillOutline=True,
            fillBrush=pg.mkBrush("#bf00bf50"),
        )
        self.amp_dist.addItem(dist_item)
        self.amp_dist.setXRange(np.nanmin(y), np.nanmax(y))
        y_values = np.full(y.shape, max(log_y) * 0.05)
        y_stems = np.insert(y_values, np.arange(y_values.size), 0)
        x_stems = np.repeat(y, 2)
        stem_item = pg.PlotDataItem(x=x_stems, y=y_stems, connect="pairs")
        self.amp_dist.addItem(stem_item)

    def clearTables(self):
        if self.table_dict:
            for i in self.table_dict.values():
                i.clear()
                i.hide()
                i.deleteLater()
            self.table_dict = {}
