from dataclasses import dataclass, field
from typing import Literal, ClassVar

import numpy as np
from numpy.polynomial import Polynomial as npPoly
from scipy import interpolate

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@dataclass
class Detrend(Preprocessor):
    module: ClassVar[str] = "detrend"
    baseline_: np.ndarray | None = field(default=None, repr=False, init=False)


@register_preprocessor
@dataclass
class Mean(Detrend):
    start: float = 0
    end: float = 0

    name: ClassVar[str] = "mean"

    def __call__(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[-1]
        else:
            end = self.end
        start = int(self.start * fs / 1000)
        end = int(end * fs / 1000)
        self.baseline_ = np.mean(array[start:end], axis=-1, keepdims=True)
        return array - self.baseline_


@register_preprocessor
@dataclass
class Median(Detrend):
    start: float = 0
    end: float = 0

    name: ClassVar[str] = "median"

    def __call__(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[-1]
        else:
            end = self.end
        start = int(self.start * fs / 1000)
        end = int(end * fs / 1000)
        self.baseline_ = np.median(array[start:end], axis=-1, keepdims=True)
        return array - self.baseline_


@register_preprocessor
@dataclass
class ExpDecay(Detrend):
    n_decays: Literal[1, 2] = 1

    name: ClassVar[str] = "exp_decay"

    def __call__(self, array: np.ndarray, fs: float | int) -> np.ndarray:
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
        self.baseline_ = np.zeros(array.size)
        self.baseline_[:peak] = y_fit
        return array - self.baseline_


@register_preprocessor
@dataclass
class Polynomial(Detrend):
    degree: int = 3

    name: ClassVar[str] = "polynomial"

    def __call__(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        fit = npPoly.fit(x, array, deg=self.degree)
        self.baseline_ = fit(x)
        return array - self.baseline_


@register_preprocessor
@dataclass
class LSQSpline(Detrend):
    degree: int = 3
    n_knots: int = 5

    name: ClassVar[str] = "lsq_spline"

    def __call__(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size)
        internal_knots = np.linspace(0, array.size, num=self.n_knots + 2, dtype=int)[
            1:-1
        ]
        t = np.r_[
            [x[0]] * (self.degree + 1), internal_knots, [x[-1]] * (self.degree + 1)
        ]
        fit = interpolate.make_lsq_spline(x, array, t, k=self.degree)
        self.baseline_ = fit(x)
        return array - self.baseline_
