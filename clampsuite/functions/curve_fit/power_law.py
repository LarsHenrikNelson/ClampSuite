from typing import NamedTuple

import numpy as np
from scipy import optimize

from .curve_fit_base import CurveFitBase


class PowerLawFit(NamedTuple):
    amplitude: float = np.nan
    shift: float = np.nan
    alpha: float = np.nan
    offset: float = np.nan


class PowerLaw(CurveFitBase):
    @staticmethod
    def _fit_function(  # type: ignore[override]
        x: np.ndarray, amplitude: float, shift: float, alpha: float, offset: float = 0.0
    ) -> np.ndarray:
        y = amplitude * (x + shift) ** -alpha + offset
        return y

    def _get_bounds(self, x: np.ndarray, y: np.ndarray) -> tuple:
        if np.median(np.diff(y)) < 0:
            upper_bounds = [np.inf, np.max(x) / 2.0, 2.0, np.max(y)]
            lower_bounds = [0.0, 1e-5, 0.001, 0.0]
        else:
            upper_bounds = [0.0, np.max(x) / 2.0, 2.0, np.max(y)]
            lower_bounds = [-np.inf, 1e-5, 0.001, 0.0]
        return lower_bounds, upper_bounds

    def _get_initial_params(self, x: np.ndarray, y: np.ndarray) -> None | tuple | list:
        alpha = 0.3
        dt = np.median(np.diff(x))
        t0 = max(dt / 2.0, 1e-4)
        c = p0 = max(y[-1], 0.0)
        if np.mean(np.diff(y)) < 0:
            p0 = (max(y[0] - y[-1], -1e3), t0, alpha, c)
        else:
            p0 = (max(y[0] - y[-1], -1e3), t0, alpha, c)
        return p0

    def _create_nan_result(self):
        return PowerLawFit()

    def _create_result(self, popt: tuple):
        return PowerLawFit(*popt)
