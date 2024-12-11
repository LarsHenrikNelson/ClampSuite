from typing import TypedDict

import numpy as np
from scipy import signal, optimize


class Event(TypedDict):
    peak_x: float
    amplitude: float
    start_x: float
    end_x: float


def find_peak_window(array, peak_direction, window_start, window_end):
    if peak_direction == "positive":
        peak_y = np.max(array[window_start:window_end])
        peak_x = np.argmax(array[window_start:window_end]) + window_start
    elif peak_direction == "negative":
        peak_y = np.min(array[window_start:window_end])
        peak_x = np.argmin(array[window_start:window_end]) + window_start
    return peak_y, peak_x


def find_multipeaks(array, height, prominence, distance):
    peaks, props = signal.find_peaks(
        array, height=height, prominence=prominence, distance=(distance)
    )
    events = []
    for i in np.arange(len(peaks)):
        if i < len(peaks) - 1:
            temp = Event(
                peak_x=peaks[i],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["left_bases"][i + 1],
            )
        else:
            temp = Event(
                peak_x=peaks[i],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["right_bases"][i],
            )
        events.append(temp)


class CurveFitData(TypedDict):
    amplitude: float
    rise_tau: float
    decay_tau: float
    rise_power: float


def psc(
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


def _detect_pos_neg(y):
    maximum = np.abs(y.max())
    minimum = np.abs(y.min())
    if maximum > minimum:
        return "positive"
    else:
        return "negative"


def _fit_psc(y: np.ndarray, start: float, end: float, sample_rate: float | int):
    s_r_c = int(sample_rate / 1000)
    temp = y[int(start * s_r_c) : int(end * s_r_c)]
    x = np.arange(temp.size) / s_r_c

    # Detect whether acquisition is positive or negative
    direction = _detect_pos_neg(y)

    # Must provide bounds otherwise curve_fit throws an error
    if direction == "positive":
        lower_bounds = (0.001, 0.0001, 0.0001, 0.0001)
        peak_point = y.argmax()
        upper_bounds = (
            y[peak_point] * 1.2,
            peak_point / s_r_c,
            float(y.size / s_r_c),
            np.inf,
        )
    else:
        peak_point = y.argmin()
        lower_bounds = (y[peak_point] * 1.2, 0.0001, 0.0001, 0.0001)
        upper_bounds = (
            0.001,
            peak_point / s_r_c,
            float(y.size / s_r_c),
            np.inf,
        )

    popt, _ = optimize.curve_fit(
        psc,
        x,
        temp,
        bounds=[lower_bounds, upper_bounds],
        ftol=0.0002,
    )
    return popt


def iterative_curve_fit(
    data: np.ndarray, pulse_starts: np.ndarray, sample_rate: float | int
):
    """Data is an array that contains multiple events. Pulse starts note the beginning of each
    event.

    Args:
        data (np.ndarray): array of data
        pulse_starts (np.ndarray): pulse starts in milliseconds
        sample_rate (float, int): sample rate
    """
    y = data.copy()
    s_r_c = int(sample_rate / 1000)
    pulse_ends = pulse_starts[1:]
    pulse_ends = np.r_[pulse_ends, data.size / s_r_c]
    fit_vals = []
    for start, end in zip(pulse_starts, pulse_ends):
        popt = _fit_psc(y, start, end, sample_rate)
        size = data.size - int(start * s_r_c)
        x = np.arange(size) / s_r_c
        temp = psc(x, *popt)
        y[int(start * s_r_c) :] -= temp
        fit_vals.append(
            CurveFitData(
                amplitude=popt[0],
                rise_tau=popt[1],
                decay_tau=popt[2],
                rise_power=popt[3],
            )
        )
    return fit_vals, y
