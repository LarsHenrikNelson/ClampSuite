from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit

from .curve_fit_base import CurveFitBase


class LogCurveFit(NamedTuple):
    vscale: float = np.nan
    offset: float = np.nan
    xshift: float = np.nan


class Log(CurveFitBase):
    @staticmethod
    def _fit_function(
        x: np.ndarray, vscale: float, offset: float = 0.0, xshift: float = 0.0
    ):
        return vscale * np.log(x - xshift) + offset

    def _get_bounds(self, x: np.ndarray, y: np.ndarray) -> tuple[list, list]:
        ub = [np.inf, np.inf, np.min(x) - 1e-6]
        lb = [-np.inf, -np.inf, -np.inf]
        return lb, ub

    def _get_initial_params(self, x: np.ndarray, y: np.ndarray) -> list:
        xmin = np.min(x)
        xmax = np.max(x)
        ymin = np.min(y)
        ymax = np.max(y)
        if np.abs(ymin) > np.abs(ymax):
            numerator = ymin - ymax
            offset_est = ymax
        else:
            offset_est = ymin
            numerator = ymax - ymin
        divisor = max(np.abs(xmax - xmin), 1)
        vscale_est = numerator / max(np.log(divisor), 1)
        p0 = [vscale_est, offset_est, 0]
        return p0

    def _create_nan_result(self):
        return LogCurveFit()

    def _create_result(self, popt: tuple):
        return LogCurveFit(*popt)
