from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit

from .curve_fit_base import CurveFitBase


class SigmoidCurveFit(NamedTuple):
    max_value: float = np.nan
    midpoint: float = np.nan
    slope: float = np.nan
    offset: float = np.nan


class Sigmoid(CurveFitBase):
    @staticmethod
    def _fit_function(  # type: ignore[override]
        x: np.ndarray, max_value: float, midpoint: float, slope: float, offset: float
    ) -> np.ndarray:
        return 1 / (1 + np.exp((x - midpoint) / -slope)) * max_value + offset

    def _get_bounds(self, x: np.ndarray, y: np.ndarray) -> tuple[list, list]:
        lb = [-np.inf, -np.inf, 1e-6, 0]
        ub = [np.inf, np.inf, np.inf, np.inf]
        return lb, ub

    def _get_initial_params(self, x: np.ndarray, y: np.ndarray) -> list:
        return [np.max(y), np.mean(x), 30, 0]

    def _create_nan_result(self):
        return SigmoidCurveFit()

    def _create_result(self, popt: tuple):
        return SigmoidCurveFit(*popt)
