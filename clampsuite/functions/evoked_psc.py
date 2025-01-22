from typing import TypedDict, Literal

import numpy as np
from scipy import signal, optimize


class Event(TypedDict):
    peak_x: float
    peak_y: float
    amplitude: float
    baseline: float


def _detect_pos_neg(y):
    maximum = np.abs(y.max())
    minimum = np.abs(y.min())
    if maximum > minimum:
        return "positive"
    else:
        return "negative"


def find_peak_window(
    array,
    peak_direction,
    window_start,
    window_end,
    statistic: Literal["max", "mean", "median"] = "mean",
):
    if statistic == "max":
        if peak_direction == "positive":
            peak_y = np.max(array[window_start:window_end])
            peak_x = np.argmax(array[window_start:window_end]) + window_start
        elif peak_direction == "negative":
            peak_y = np.min(array[window_start:window_end])
            peak_x = np.argmin(array[window_start:window_end]) + window_start
    else:
        if statistic == "mean":
            peak_y = np.mean(array[window_start:window_end])
        elif statistic == "median":
            peak_y = np.median(array[window_start:window_end])
        else:
            raise ValueError("Statistic not recognized, must be max, mean or median")
        peak_x = (window_start + window_end) / 2
    return peak_x, peak_y


def _iterative_peak_window(
    y: np.ndarray,
    pulse_starts: np.ndarray,
    window_starts: np.ndarray,
    window_ends: np.ndarray,
    sample_rate: float | int,
    baseline_size: float = 10,
    statistic: Literal["max", "mean", "median"] = "mean",
    direction: Literal["positive", "negative"] | None = None,
) -> Event:
    """
    Iteratively finds the peak by taking the max, mean or median within a window of data.

    Args:
        y (np.ndarray): Acquisition data.
        pulse_starts (np.nadarray): Start of pulses in milliseconds.
        window_starts (np.ndarray): Start of windows in milliseconds.
        window_ends (np.ndarray): End of windows in milliseconds.
        sample_rate (float | int): Sample rate of data.
        baseline_size (float, optional): Size of the baseline before the peak. Defaults to 10.
        statistic (Literal[&quot;max&quot;, &quot;mean&quot;, &quot;median&quot;], optional): Statistic of the window. Defaults to "mean".

    Returns:
        Event: _description_
    """
    if direction is None:
        direction = _detect_pos_neg(y)
    peaks = []
    s_r_c = sample_rate / 1000
    baseline_size = int(baseline_size * s_r_c)
    for pstart, start, end in zip(pulse_starts, window_starts, window_ends):
        start = int(start * s_r_c)
        end = int(end * s_r_c)
        pstart = int(pstart * s_r_c)
        peak_x, peak_y = find_peak_window(y, direction, start, end, statistic)
        baseline = np.mean(y[pstart - baseline_size - 1 : pstart])
        amplitude = np.abs(peak_y - baseline)
        temp = Event(
            peak_x=peak_x,
            peak_y=peak_y,
            amplitude=amplitude,
        )
        peaks.append(temp)
    return peaks


def iterative_peak_window(
    y: np.ndarray,
    window_offset: float,
    window_size: float,
    pulse_starts: np.ndarray,
    sample_rate: float | int,
    baseline_size: float = 10,
    statistic: Literal["max", "mean", "median"] = "mean",
    direction: Literal["positive", "negative"] | None = None,
):
    window_starts = np.array(pulse_starts) + window_offset
    window_ends = np.array(window_starts) + window_size
    peaks = _iterative_peak_window(
        y,
        pulse_starts,
        window_starts,
        window_ends,
        sample_rate,
        baseline_size,
        statistic,
        direction,
    )

    s_r_c = sample_rate / 1000
    for i in peaks:
        i["peak_x"] /= s_r_c
    return peaks


def iterative_peak_prominence(
    y: np.ndarray,
    height: float,
    prominence: float,
    distance: int,
) -> Event:
    peaks, props = signal.find_peaks(
        y, height=height, prominence=prominence, distance=(distance)
    )
    # Need to rework this some more. Based on how scipy.find_peaks works this
    # will likely not yield the expected results.

    events = []
    for i in np.arange(len(peaks)):
        if i < (len(peaks) - 1):
            temp = Event(
                peak_x=peaks[i],
                peak_y=y[peaks[i]],
                amplitude=np.abs(y[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                rise_time=props["left_bases"][i],
                end_x=(peaks[i] - props["left_bases"][i + 1]),
            )
        else:
            temp = Event(
                peak_x=peaks[i],
                peak_y=y[peaks[i]],
                amplitude=np.abs(y[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["right_bases"][i],
                rise_time=(peaks[i] - props["left_bases"][i]),
            )
        events.append(temp)
    return events


class CurveFitDataSExp(TypedDict):
    amplitude: float
    rise_tau: float
    decay_tau: float
    rise_power: float


class CurveFitDataDExp(TypedDict):
    amplitude: float
    rise_tau: float
    decay_tau_fast: float
    decay_tau_slow: float
    rise_power: float


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


def psc_dexp(
    x: np.ndarray,
    amplitude: int | float = -20,
    rise_tau: int | float = 3,
    decay_tau_fast: int | float = 50,
    decay_tau_slow: int | float = 0,
    risepower: int | float = 0.5,
):

    y = amplitude * (
        (1 - (np.exp(-x / rise_tau))) ** risepower
        * (np.exp((-x / decay_tau_fast) + np.exp((-x / decay_tau_slow))))
    )
    return y


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


def iterative_curve_fit(
    y: np.ndarray,
    pulse_starts: np.ndarray,
    offset: float,
    sample_rate: float | int,
    direction: Literal["positive", "negative"] | None = None,
):
    """Data is an array that contains multiple events. Pulse starts note the beginning of each
    event.

    Args:
        y (np.ndarray): array of y
        pulse_starts (np.ndarray): pulse starts in milliseconds
        sample_rate (float, int): sample rate
    """
    y = y.copy()
    s_r_c = sample_rate / 1000
    pulse_ends = pulse_starts[1:]
    pulse_starts = np.array(pulse_starts) + offset
    m = np.max(np.diff(pulse_starts))
    pulse_ends = np.r_[pulse_ends, pulse_ends[-1] + m]
    fit_vals = []
    for start, end in zip(pulse_starts, pulse_ends):
        popt = _fit_psc(y, start, end, sample_rate, direction)
        size = y.size - int(start * s_r_c)
        x = np.arange(size) / s_r_c
        temp = psc_sexp(x, *popt)
        y[int(start * s_r_c) :] -= temp
        fit_vals.append(
            CurveFitDataSExp(
                amplitude=popt[0],
                rise_tau=popt[1],
                decay_tau=popt[2],
                rise_power=popt[3],
            )
        )
    return fit_vals


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


def _convert_psc_template_vars(
    data: list[CurveFitDataSExp], pulse_starts: list[float], offset: float
):
    vals = []
    for i, j in zip(data, pulse_starts):
        vals.extend(
            [
                i["amplitude"],
                i["rise_tau"] + offset,
                i["decay_tau"] + offset,
                i["rise_power"],
                j + offset,
            ]
        )
    return vals


class EvokedPSC:

    def __init__(
        self,
        data: np.ndarray,
        sample_rate: float | int,
        pulse_starts: list[float],
        start: float | None = None,
        end: float | None = None,
    ):
        self.data = data
        self.sample_rate = sample_rate
        self.pulse_starts = pulse_starts
        self.start = start
        self.end = end

    def analyze():
        pass
