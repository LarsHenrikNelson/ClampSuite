from typing import Literal

import numpy as np
from scipy import optimize

from .utilities import _detect_pos_neg


def psc_sexp(
    x: np.ndarray,
    amplitude: int | float = -20,
    rise_tau: int | float = 3,
    decay_tau: int | float = 50,
    risepower: int | float = 0.5,
):
    Aprime = (decay_tau / rise_tau) ** (rise_tau / (rise_tau - decay_tau))
    y = (
        amplitude
        / Aprime
        * ((1 - (np.exp(-x / rise_tau))) ** risepower * np.exp((-x / decay_tau)))
    )
    return y


def template(
    x: np.ndarray,
    amplitude: int | float = -20,
    rise_tau: int | float = 3,
    decay_tau: int | float = 50,
    risepower: int | float = 0.5,
    spacer: int | float = 15,
    sample_rate: float = 10000,
) -> np.ndarray:
    """Creates a template based on several factors. X, taus and spacer must
    be in samples and not milliseconds or seconds.

    Args:
        amplitude (float): Amplitude of template
        tau_1 (float): Rise tau (ms) of template
        tau_2 (float): Decay tau (ms) of template
        risepower (float): Risepower of template
        length (float): Length of time (ms) for template
        spacer (int, optional): Delay (ms) until template starts. Defaults to 1.5.

    Returns:
        np.array: Numpy array of the template.
    """
    s_r_c = sample_rate / 1000
    template = x.copy()
    spacer = int(spacer * s_r_c)
    length = template.size - spacer
    t_length = np.arange(0, length, dtype=float) / s_r_c
    Aprime = (decay_tau / rise_tau) ** (rise_tau / (rise_tau - decay_tau))
    y = (
        amplitude
        / Aprime
        * (
            (1 - (np.exp(-t_length / rise_tau))) ** risepower
            * np.exp((-t_length / decay_tau))
        )
    )
    template[int(spacer) :] = y
    return template


def psc_template(
    x,
    *args,
):
    amplitude = args[0::5]
    tau1 = args[1::5]
    tau2 = args[2::5]
    rp = args[3::5]
    spacer = args[4::5]
    output = np.zeros((len(amplitude), len(x)))
    i = 0
    for a, t1, t2, r, s in zip(amplitude, tau1, tau2, rp, spacer):
        output[int(i)] = template(output[i], a, t1, t2, r, s)
        i += 1
    return output.sum(axis=0)


def _fit_psc(
    y: np.ndarray,
    start: float,
    end: float,
    sample_rate: float | int,
    direction: Literal["positive", "negative"] | None = None,
):
    s_r_c = sample_rate / 1000
    temp = y[int(start * s_r_c) : int(end * s_r_c)]
    x = np.arange(temp.size) / s_r_c

    # Detect whether acquisition is positive or negative
    if direction is None:
        direction = _detect_pos_neg(y)

    # Must provide bounds otherwise curve_fit throws an error
    if direction == "positive":
        lower_bounds = (0.0, 0.0, 0.0, 0.0)
        peak_point = y.argmax()
        upper_bounds = (
            y[peak_point] * 2,
            peak_point / s_r_c,
            float(temp.size / s_r_c),
            np.inf,
        )
    else:
        peak_point = y.argmin()
        lower_bounds = (y[peak_point] * 2, 0.0, 0.0, 0.0)
        upper_bounds = (
            0.0,
            peak_point / s_r_c,
            float(temp.size / s_r_c),
            np.inf,
        )

    popt, _ = optimize.curve_fit(
        psc_sexp,
        x,
        temp,
        bounds=[lower_bounds, upper_bounds],
        ftol=0.0002,
    )
    return popt
