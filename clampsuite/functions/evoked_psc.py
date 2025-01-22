from typing import TypedDict, Literal

import numpy as np
from scipy import signal, optimize


class Event(TypedDict):
    peak_x: float
    peak_y: float
    amplitude: float
    start_x: float
    end_x: float
    rise_time: float


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
    return peak_y, peak_x


def _iterative_peak_window(
    y: np.ndarray,
    window_starts: float,
    window_ends: float,
    sample_rate: float | int,
    baseline_size: float = 10,
    statistic: Literal["max", "mean", "median"] = "mean",
) -> Event:
    """
    Iteratively finds the peak by taking the max, mean or median within a window of data.

    Args:
        y (np.ndarray): Acquisition data.
        window_starts (float): Start of window in milliseconds.
        window_ends (float): End of window in milliseconds.
        sample_rate (float | int): Sample rate of data.
        baseline_size (float, optional): Size of the baseline before the peak. Defaults to 10.
        statistic (Literal[&quot;max&quot;, &quot;mean&quot;, &quot;median&quot;], optional): Statistic of the window. Defaults to "mean".

    Returns:
        Event: _description_
    """
    direction = _detect_pos_neg(y)
    peaks = []
    s_r_c = sample_rate / 1000
    baseline_size = int(baseline_size * s_r_c)
    for start, end in zip(window_starts, window_ends):
        start = start * s_r_c
        end = end * s_r_c
        peak_x, peak_y = find_peak_window(y, direction, start, end, statistic)
        amplitude = np.abs(peak_y - y[start - baseline_size - 1 : start])
        temp = Event(
            peak_x=peak_x,
            peak_y=peak_y,
            amplitude=amplitude,
            start_x=start,
            end_x=end,
            rise_time=peak_x - start,
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
):
    window_starts = pulse_starts + window_offset
    window_ends = window_starts + window_size
    peaks = _iterative_peak_window(
        y, window_starts, window_ends, sample_rate, baseline_size, statistic
    )

    s_r_c = sample_rate / 1000
    for i in peaks:
        i["peak_x"] *= s_r_c
        i["start_x"] *= s_r_c
        i["end_x"] *= s_r_c
        i["rise_time"] *= s_r_c
    return peaks


def iterative_peak_prominence(
    array: np.ndarray,
    height: float,
    prominence: float,
    distance: int,
) -> Event:
    peaks, props = signal.find_peaks(
        array, height=height, prominence=prominence, distance=(distance)
    )
    # Need to rework this some more. Based on how scipy.find_peaks works this
    # will likely not yield the expected results.

    events = []
    for i in np.arange(len(peaks)):
        if i < (len(peaks) - 1):
            temp = Event(
                peak_x=peaks[i],
                peak_y=array[peaks[i]],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                rise_time=props["left_bases"][i],
                end_x=(peaks[i] - props["left_bases"][i + 1]),
            )
        else:
            temp = Event(
                peak_x=peaks[i],
                peak_y=array[peaks[i]],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["right_bases"][i],
                rise_time=(peaks[i] - props["left_bases"][i]),
            )
        events.append(temp)
    return events


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


def _fit_psc(y: np.ndarray, start: float, end: float, sample_rate: float | int):
    s_r_c = sample_rate / 1000
    temp = y[int(start * s_r_c) : int(end * s_r_c)]
    x = np.arange(temp.size) / s_r_c

    # Detect whether acquisition is positive or negative
    direction = _detect_pos_neg(y)

    # Must provide bounds otherwise curve_fit throws an error
    if direction == "positive":
        lower_bounds = (0.0, 0.0, 0.0, 0.0)
        peak_point = y.argmax()
        upper_bounds = (
            y[peak_point] * 2,
            peak_point / s_r_c,
            float(y.size / s_r_c),
            np.inf,
        )
    else:
        peak_point = y.argmin()
        lower_bounds = (y[peak_point] * 2, 0.0, 0.0, 0.0)
        upper_bounds = (
            0.0,
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
    s_r_c = sample_rate / 1000
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
    return fit_vals


def psc_template(
    x,
    *args,
):
    amplitude = np.array(args[0::5])
    tau1 = np.array(args[1::5])
    tau2 = np.array(args[2::5])
    rp = np.array(args[3::5])
    spacer = np.array(args[4::5])
    output = np.zeros((amplitude.size, x.size))
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
    template = x.copy()
    length = template.size - spacer
    t_length = np.arange(0, length, dtype=float)
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
    data: list[CurveFitData], pulse_starts: list[float], sample_rate
):
    vals = []
    src = sample_rate / 1000
    for i, j in zip(data, pulse_starts):
        vals.extend(
            [
                i["amplitude"],
                i["rise_tau"] * src,
                i["decay_tau"] * src,
                i["rise_power"],
                j * src,
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
