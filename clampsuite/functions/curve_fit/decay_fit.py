import numpy as np
from typing import NamedTuple
from scipy import optimize
from .utilities import _detect_pos_neg


class SExpDecayFit(NamedTuple):
    amplitude: float
    tau: float
    offset: float


def s_exp_decay(x: np.ndarray, amplitude: float, tau: float, offset: float = 0.0):
    y = amplitude * np.exp(-x / tau) + offset
    return y


class DExpDecayFit(NamedTuple):
    amplitude_fast: float
    amplitude_slow: float
    tau_slow: float
    multiplier: float
    offset: float


def db_exp_decay(
    x: np.ndarray,
    amplitude_fast: float,
    amplitude_slow: float,
    tau_slow: float,
    multiplier: float,
    offset: float = 0.0,
):
    tau_fast = tau_slow * multiplier
    y = (
        offset
        + (amplitude_fast * np.exp(-x / tau_fast))
        + (amplitude_slow * np.exp(-x / tau_slow))
    )
    return y


CURVE_FIT_OUTPUT = {1: SExpDecayFit, 2: DExpDecayFit}
DECAY_FUNCS = {1: s_exp_decay, 2: db_exp_decay}


def _curve_fit_bounds(amplitude: float, length: float, num_decays: int):
    if amplitude > 0:
        if num_decays == 1:
            upper_bounds = [amplitude * 2, length, np.inf]
            lower_bounds = [0.0, 0.0, -np.inf]
        else:
            upper_bounds = [amplitude * 2, amplitude * 2, length, 1.0, np.inf]
            lower_bounds = [0.0, 0.0, 0.0, 0.0, -np.inf]
    else:
        if num_decays == 1:
            upper_bounds = [0.0, length, np.inf]
            lower_bounds = [amplitude * 2, 0.0, -np.inf]
        else:
            upper_bounds = [0.0, 0.0, length, 1, np.inf]
            lower_bounds = [amplitude * 2, amplitude * 2, 0.0, 0.0, -np.inf]
    return lower_bounds, upper_bounds


def fit_decay(x: np.ndarray, y: np.ndarray, num_decays: int):
    amplitude = y[0] - y[-1]
    lower_bounds, upper_bounds = _curve_fit_bounds(amplitude, x[-1], num_decays)

    popt, _ = optimize.curve_fit(
        DECAY_FUNCS[num_decays],
        x,
        y,
        bounds=[lower_bounds, upper_bounds],
    )

    output = CURVE_FIT_OUTPUT[num_decays](*popt)
    return output

def fit(x, params):
    if isinstance(params, SExpDecayFit):
        return s_exp_decay(x, *params)
    else:
        return db_exp_decay(x, *params)

def est_decay(
    event_array,
    array_start,
    event_peak_y,
    event_peak_x,
    event_start_y,
):
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
