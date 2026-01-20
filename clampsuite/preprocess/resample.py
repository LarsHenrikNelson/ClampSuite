from dataclasses import dataclass
from typing import ClassVar, Literal

import numpy as np
from scipy import interpolate, signal
from scipy.signal import decimate

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@dataclass
class Resample(Preprocessor):
    module: ClassVar[str] = "resample"


@register_preprocessor
@dataclass
class BSpline(Resample):
    k: int = 3
    order: int = 4

    name: ClassVar[str] = "b_spline"

    def fs_multiplier(self):
        return self.order

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size) / fs
        x_new = np.arange(array.size * self.order) / (fs * self.order)
        bspline = interpolate.make_interp_spline(x, array, k=self.k)
        return bspline(x_new)


@register_preprocessor
@dataclass
class Pchip(Resample):
    k: int = 3
    order: int = 4

    name: ClassVar[str] = "pchip_spline"

    @property
    def fs_multiplier(self):
        return self.order

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size) / fs
        x_new = np.arange(array.size * self.order) / (fs * self.order)
        bspline = interpolate.make_interp_spline(x, array, k=self.k)
        return bspline(x_new)


@register_preprocessor
@dataclass
class Polyphase(Resample):
    up: int = 8
    down: int = 2

    name: ClassVar[str] = "polyphase"

    @property
    def fs_multiplier(self):
        return self.up / self.down

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        y_up = signal.resample_poly(array - array[0], 8, 2) + array[0]
        return y_up


@register_preprocessor
@dataclass
class Decimate(Resample):
    q: int = 4

    name: ClassVar[str] = "decimate"

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        return signal.decimate(array, self.q)
