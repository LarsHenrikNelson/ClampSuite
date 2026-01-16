from dataclasses import dataclass
from typing import Literal, ClassVar

import numpy as np
from numpy.polynomial import Polynomial as npPoly
from scipy import interpolate

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@dataclass
class Detrend(Preprocessor):
    module: ClassVar[str] = "detrend"


@register_preprocessor
@dataclass
class Mean(Detrend):
    start: int = 0
    end: int = 0

    name: ClassVar[str] = "mean"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[1]
        else:
            end = self.end
        return array - np.mean(array[self.start : end], axis=-1, keepdims=True)


@register_preprocessor
@dataclass
class Median(Detrend):
    start: int = 0
    end: int = 0

    name: ClassVar[str] = "median"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[1]
        else:
            end = self.end
        return array - np.median(array[self.start : end], axis=-1, keepdims=True)


@register_preprocessor
@dataclass
class ExpDecay(Detrend):
    n_decays: Literal[1, 2] = 1

    name: ClassVar[str] = "exp_decay"

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


@register_preprocessor
@dataclass
class Polynomial(Detrend):
    degree: int = 3

    name: ClassVar[str] = "polynomial"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        fit = npPoly.fit(x, array, deg=self.degree)
        baseline = fit(x)
        return array - baseline


@register_preprocessor
@dataclass
class LSQSpline(Detrend):
    degree: int = 3

    name: ClassVar[str] = "lsq_spline"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        knots = np.linspace(0, array.size, num=self.degree + 2, dtype=int)[1:-2]
        fit = interpolate.make_lsq_spline(x, array, x[knots], k=3)
        baseline = fit(x)
        return array - baseline
