import numpy as np
from typing import NamedTuple
from scipy import optimize
from .epsc_functions import _detect_pos_neg


class SExpDecayFit(NamedTuple):
    amplitude: float
    tau: float
    rise_power: float


def s_exp_decay(x, amplitude, tau):
    y = amplitude * np.exp(-x / tau)
    return y


class SExpDecayOffsetFit(NamedTuple):
    amplitude: float
    tau: float
    rise_power: float
    offset: float


def s_exp_decay_offset(x, amplitude, tau, offset):
    y = amplitude * np.exp((-x + offset) / tau)
    return y


class DExpDecayFit(NamedTuple):
    amplitude_fast: float
    tau_fast: float
    amplitude_slow: float
    tau_slow: float
    rise_power: float


def db_exp_decay(x, amplitude_fast, tau_fast, amplitude_slow, tau_slow):
    y = (amplitude_fast * np.exp((-x) / tau_fast)) + (
        amplitude_slow * np.exp((-x) / tau_slow)
    )
    return y


class TExpDecayFit(NamedTuple):
    amplitude_fast: float
    tau_fast: float
    amplitude_medium: float
    tau_medium: float
    amplitude_slow: float
    tau_slow: float
    rise_power: float


def t_exp_decay(
    x,
    amplitude_fast,
    tau_fast,
    amplitude_medium,
    tau_medium,
    amplitude_slow,
    tau_slow,
):
    y = (
        (amplitude_fast * np.exp((-x) / tau_fast))
        + (amplitude_medium * np.exp((-x) / tau_medium))
        + (amplitude_slow * np.exp((-x) / tau_slow))
    )
    return y


CURVE_FIT_OUTPUT = {"0": SExpDecayFit, "1": DExpDecayFit, "2": TExpDecayFit}
DECAY_FUNCS = {"0": s_exp_decay, "1": db_exp_decay, "2": t_exp_decay}


def _curve_fit_bounds(amplitude: float, length: float, num_decays: int, direction):
    if "positive":
        upper_bounds = [amplitude * 2, length] * num_decays
        lower_bounds = [0.0, 0.0] * num_decays
    else:
        upper_bounds = [0.0, length] * num_decays
        lower_bounds = [amplitude * 2, 0.0] * num_decays
    return lower_bounds, upper_bounds


def fit_decay(y, sample_rate, num_decays):
    direction = _detect_pos_neg(y)
    s_r_c = sample_rate / 1000
    x = np.arange(y.size) / s_r_c
    lower_bounds, upper_bounds = _curve_fit_bounds(y, x[-1], num_decays, direction)

    popt, _ = optimize.curve_fit(
        DECAY_FUNCS[str(num_decays)],
        x,
        y,
        bounds=[lower_bounds, upper_bounds],
    )

    # Maybe not so great usage of NamedTuple but decreases the amount of code.
    output = CURVE_FIT_OUTPUT[str(num_decays)](*popt)
    output = {j: output[index] for index, j in enumerate(output._fields)}
    return output


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


if __name__ == "__main__":
    s_exp_decay()
    db_exp_decay()
    t_exp_decay()
    est_decay()
