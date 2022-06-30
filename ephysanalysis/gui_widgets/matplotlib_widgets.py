from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from PyQt5.QtWidgets import (
    QWidget,
    QSizePolicy,
    QVBoxLayout,
)
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV


class StemPlotCanvas(FigureCanvasQTAgg):
    """
    Creating a matplotlib window this way 
    """

    def __init__(
        self,
        parent=None,
        width=3,
        height=2,
        dpi=300,
        facecolor="black",
        axis_color="white",
        point_color="white",
    ):

        self.facecolor = facecolor
        self.axis_color = axis_color
        self.point_color = point_color

        fig = Figure(figsize=(width, height), dpi=dpi, facecolor=self.facecolor)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor(self.facecolor)
        self.axis.tick_params(axis="both", color=self.axis_color)
        self.axis.xaxis.label.set_color(self.axis_color)
        self.axis.yaxis.label.set_color(self.axis_color)
        self.axis.spines[["top", "left", "right", "bottom"]].set_color(self.axis_color)

        FigureCanvasQTAgg.__init__(self, fig)
        self.setParent(parent)

        FigureCanvasQTAgg.setSizePolicy(
            self, QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        FigureCanvasQTAgg.updateGeometry(self)

    def plot(self, x, y, df):
        self.axes.stemplot(x, y)
        self.axes.set_title(f"{y} over time".format(y))
        self.draw()

    def set_style(self, facecolor, axis_color, point_color):
        self.facecolor = facecolor
        self.axis_color = axis_color
        self.point_color = point_color


class MplWidget(QWidget):
    def __init__(
        self,
        parent=None,
        width=3,
        height=2,
        dpi=300,
        facecolor="black",
        axis_color="white",
        point_color="white",
    ):
        QWidget.__init__(self, parent)

        self.facecolor = facecolor
        self.axis_color = axis_color
        self.point_color = point_color

        self.fig = Figure(facecolor=self.facecolor)
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.set_facecolor(self.facecolor)
        self.canvas.axes.tick_params(axis="both", colors=self.axis_color, labelsize=12)
        self.canvas.axes.xaxis.label.set_color(self.axis_color)
        self.canvas.axes.yaxis.label.set_color(self.axis_color)
        self.canvas.axes.spines[["top", "left", "right", "bottom"]].set_color(
            self.axis_color
        )

        self.setLayout(self.vertical_layout)

    def plot(self, x, y, df):
        self.canvas.axes.cla()
        self.canvas.draw()
        self.canvas.axes.set_title(f"{y} over time", color=self.point_color)
        stem, marker, base = self.canvas.axes.stem(df[x], df[y])
        stem.set(color=self.point_color, alpha=0.5)
        marker.set(color=self.point_color)
        self.canvas.draw()

    def clear(self):
        self.canvas.axes.cla()
        self.canvas.draw()


class DistributionPlot(QWidget):
    def __init__(
        self, facecolor="black", axis_color="white", point_color="white", parent=None
    ):

        QWidget.__init__(self, parent)

        self.facecolor = facecolor
        self.axis_color = axis_color
        self.point_color = point_color

        self.fig = Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.setLayout(self.vertical_layout)

    def plot(self, df, column):
        self.canvas.axes.cla()
        self.canvas.draw()
        self.canvas.axes.set_title("{} distribution".format(column))
        y = df[column].dropna().to_numpy()[:, np.newaxis]
        x = np.arange(y.shape[0])[:, np.newaxis]
        kde = KernelDensity(kernel="gaussian")
        bandwidth = np.logspace(-1, 1, 20)
        grid = GridSearchCV(kde, {"bandwidth": bandwidth})
        grid.fit(y)
        kde = grid.best_estimator_
        logprob = kde.score_samples(x)

        self.canvas.axes.fill_between(np.arange(y.size), 0, np.exp(logprob), alpha=0.5)
        self.canvas.axes.set_xlim(min(y)[0], max(y)[0])
        self.canvas.axes.plot(x[:, 0], np.exp(logprob))
        self.canvas.axes.plot(
            df[column].dropna().to_numpy(),
            np.zeros(y.shape[0]),
            "|",
            color="black",
            alpha=0.15,
        )
        self.canvas.draw()

    def clear(self):
        self.canvas.axes.cla()
        self.canvas.draw()
