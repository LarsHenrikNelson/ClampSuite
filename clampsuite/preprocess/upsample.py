from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import interpolate, signal

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@register_preprocessor("upsample")
@dataclass
class BSpline(Preprocessor):
    k: int = 3
    order: int = 4

    def fs_multiplier(self):
        return self.order

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size) / fs
        x_new = np.linspace(x[0], x[-1], num=array.size * self.order)
        bspline = interpolate.make_interp_spline(x, array, k=self.k)
        return bspline(x_new)


@register_preprocessor("upsample")
@dataclass
class Pchip(Preprocessor):
    k: int = 3
    order: int = 4

    @property
    def fs_multiplier(self):
        return self.order

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        x = np.arange(array.size) / fs
        x_new = np.linspace(x[0], x[-1], num=array.size * self.order)
        bspline = interpolate.make_interp_spline(x, array, k=self.k)
        return bspline(x_new)


@register_preprocessor("upsample")
@dataclass
class Polyphase(Preprocessor):
    up: int = 8
    down: int = 2

    @property
    def fs_multiplier(self):
        return self.up / self.down

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        y_up = signal.resample_poly(array - array[0], 8, 2) + array[0]
        return y_up
