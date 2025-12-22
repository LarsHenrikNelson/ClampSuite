from dataclasses import dataclass
from typing import Literal

import numpy as np

from ..functions.curve_fit import DExpDecay, SExpDecay
from .base import Preprocessor, register_preprocessor


@register_preprocessor("detrend")
@dataclass
class RemoveMean(Preprocessor):
    start: int = 0
    end: int = 0

    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        if self.end == 0:
            end = array.shape[1]
        else:
            end = self.end
        return array - np.mean(array[self.start : end], axis=-1, keepdims=True)


@register_preprocessor("detrend")
@dataclass
class RemoveExpDecay(Preprocessor):
    n_decays: Literal[1, 2] = 1

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
