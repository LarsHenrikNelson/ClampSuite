import numpy as np
from typing import NamedTuple
from scipy import optimize
from .utilities import _detect_pos_neg

from .curve_fit_base import CurveFitBase


class SExpDecayFit(NamedTuple):
    amplitude: float = np.nan
    tau: float = np.nan
    offset: float = np.nan


class DExpDecayFit(NamedTuple):
    amplitude_fast: float = np.nan
    amplitude_slow: float = np.nan
    tau_slow: float = np.nan
    multiplier: float = np.nan
    offset: float = np.nan


class SExpDecay(CurveFitBase):
    @staticmethod
    def _fit_function(
        x: np.ndarray, amplitude: float, tau: float, offset: float = 0.0
    ) -> np.ndarray:
        y = amplitude * np.exp(-x / tau) + offset
        return y

    def _get_bounds(self, x: np.ndarray, y: np.ndarray):
        amplitude = y[0] - y[-1]
        if amplitude > 0:
            upper_bounds = [amplitude * 2, x[-1], np.inf]
            lower_bounds = [0.0, 0.0, -np.inf]
        else:
            upper_bounds = [0.0, x[-1], np.inf]
            lower_bounds = [amplitude * 2, 0.0, -np.inf]
        return lower_bounds, upper_bounds

    def _create_nan_result(self):
        return SExpDecayFit()

    def _create_result(self, popt: tuple):
        return SExpDecayFit(*popt)


class DExpDecay(CurveFitBase):
    @staticmethod
    def _fit_function(
        x: np.ndarray,
        amplitude_fast: float,
        amplitude_slow: float,
        tau_slow: float,
        multiplier: float,
        offset: float = 0.0,
    ) -> np.ndarray:
        tau_fast = tau_slow * multiplier
        y = (
            offset
            + (amplitude_fast * np.exp(-x / tau_fast))
            + (amplitude_slow * np.exp(-x / tau_slow))
        )
        return y

    def _get_bounds(self, x: np.ndarray, y: np.ndarray):
        amplitude = y[0] - y[-1]
        if amplitude > 0:
            upper_bounds = [amplitude * 2, amplitude * 2, x[-1], 1.0, np.inf]
            lower_bounds = [0.0, 0.0, 0.0, 0.0, -np.inf]
        else:
            upper_bounds = [0.0, 0.0, x[-1], 1, np.inf]
            lower_bounds = [amplitude * 2, amplitude * 2, 0.0, 0.0, -np.inf]
        return lower_bounds, upper_bounds

    def _create_nan_result(self):
        return DExpDecayFit()

    def _create_result(self, popt: tuple):
        return DExpDecayFit(*popt)


def est_decay(
    event_array: np.ndarray,
    array_start: int,
    event_peak_y: float,
    event_peak_x: int,
    event_start_y: float,
) -> tuple[float, float]:
    event_array
    return_to_baseline = int(
        (np.argmax(event_array[event_peak_x:] >= event_peak_y * 0.25)) + event_peak_x
    )
    decay_y = event_array[event_peak_x:return_to_baseline]
    x = np.arange(event_array)
    if decay_y.size > 0:
        est_tau_y = ((event_peak_y - event_start_y) * (1 / np.exp(1))) + event_start_y
        decay_x = x[event_peak_x - array_start : return_to_baseline]
        est_tau_x = np.interp(est_tau_y, decay_y, decay_x)
    else:
        est_tau_x = np.nan
        est_tau_y = np.nan
    return est_tau_y, est_tau_x
