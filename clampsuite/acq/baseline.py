from typing import Literal

import numpy as np
from numpy.polynomial import Polynomial
from scipy import interpolate


class Baseline:
    def __init__(
        self,
        array: np.ndarray,
        offset: float,
        fs: float,
        start: float,
        stop: float,
        method: Literal["mean", "median", "polynomial", "spline"] = "polynomial",
        degree: int = 3,
    ):
        self.array = array
        self.offset = offset
        self.fs = fs
        self.start = start
        self.stop = stop
        self.method = method
        self.degree = degree

    def analyze(self):
        if self.method == "polynomial":
            self.baseline = self.polynomial()
        elif self.method == "mean":
            self.baseline = self.mean()
        elif self.method == "median":
            self.baseline = self.median()
        y = self.array - self.baseline
        return y

    def polynomial(self) -> np.ndarray:
        np.arange(self.array[self.start, self.stop].size)
        fit = Polynomial.fit(self.x, self.array[self.start, self.stop], deg=self.degree)
        baseline = fit(self.x)
        return baseline

    def mean(self):
        fit = np.mean(self.array[self.start, self.stop])
        return fit

    def median(self):
        fit = np.median(self.array[self.start, self.stop])
        return fit

    def spline(self):
        knots = np.linspace(
            0, self.array[self.start, self.stop].size, num=self.degree + 2, dtype=int
        )[1:-2]
        fit = interpolate.make_lsq_spline(
            self.x, self.array[self.start, self.stop], self.x[knots], k=3
        )
        baseline = fit(self.x)
        return baseline
