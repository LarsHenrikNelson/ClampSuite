from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.polynomial import Polynomial as npPoly
from scipy import interpolate

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@register_preprocessor("detrend")
@dataclass
class Mean(Preprocessor):
    start: int = 0
    end: int = 0

    @property
    def name(self) -> str:
        return "mean"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[1]
        else:
            end = self.end
        return array - np.mean(array[self.start : end], axis=-1, keepdims=True)


@register_preprocessor("detrend")
@dataclass
class Median(Preprocessor):
    start: int = 0
    end: int = 0

    @property
    def name(self) -> str:
        return "median"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[1]
        else:
            end = self.end
        return array - np.median(array[self.start : end], axis=-1, keepdims=True)


@register_preprocessor("detrend")
@dataclass
class ExpDecay(Preprocessor):
    n_decays: Literal[1, 2] = 1

    @property
    def name(self) -> str:
        return "exp_decay"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        maximum = array.argmax()
        minimum = array.argmin()
        if np.abs(array[maximum]) > np.abs(array[minimum]):
            peak = maximum
        else:
            peak = minimum
        if self.n_decays == 1:
            fit_object = SExpDecay()
        else:
            fit_object = DExpDecay()
        y = array[peak:]
        x = np.arange(y.size) / fs
        fit_object.fit(x, y)
        y_fit = fit_object.predict(x)
        sub = np.zeros(array.size)
        sub[:peak] = y_fit
        return array - sub


@register_preprocessor("detrend")
@dataclass
class Polynomial(Preprocessor):
    degree: int = 3

    @property
    def name(self) -> str:
        return "polynomial"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        fit = npPoly.fit(x, array, deg=self.degree)
        baseline = fit(x)
        return array - baseline


@register_preprocessor("detrend")
@dataclass
class LSQSpline(Preprocessor):
    degree: int = 3

    @property
    def name(self) -> str:
        return "lsq_spline"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        knots = np.linspace(0, array.size, num=self.degree + 2, dtype=int)[1:-2]
        fit = interpolate.make_lsq_spline(x, array, x[knots], k=3)
        baseline = fit(x)
        return array - baseline
