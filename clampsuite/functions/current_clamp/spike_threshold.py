from typing import Literal, TypeAlias

import numpy as np
from scipy import signal


def third_derivative(derivatives, start, end):
    dddv = derivatives["dddv"][start:end]
    base = dddv.argmin()
    index = base - 1
    val = dddv[base] - dddv[index]
    while val < 0:
        index -= 1
        base -= 1
        val = dddv[base] - dddv[index]
    peak = start + index
    return peak


def max_curvature(derivatives, start, end):
    dv = derivatives["dv"][start:end]
    v = derivatives["v"][start:end]
    peak = np.argmax(-1 * (dv / v))
    peak = peak - 2 + start
    return peak


def method_vii(derivatives, start, end):
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["ddv"][start:end]
    method_vii = ddv * (1 + dv**2) ** (-3 / 2)
    peak = method_vii.argmax() + start
    return peak


def method_ii(derivatives, start, end):
    dddv = derivatives["dddv"][start:end]
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["dv"][start:end]
    temp = (dddv * dv - ddv**2) / (np.ma.array(dv**3, mask=dv != 0))
    peak = temp.data.argmax() + start
    return peak


def first_derivative(derivatives, start, end):
    dv = derivatives["dv"][start:end]
    base = dv.argmax()
    index = base - 1
    val = dv[base] - dv[index]
    mm = dv[base] / 10
    while val > 0 or dv[base] > mm:
        index -= 1
        base -= 1
        val = dv[base] - dv[index]
    base = np.where(dv > np.max(dv[:base]))[0][0]
    peak = base + start + 1
    return peak


def second_derivative(derivatives, start, end):
    ddv = derivatives["ddv"][start:end]
    base = ddv.argmax()
    index = base - 1
    val = ddv[base] - ddv[index]
    while val > 0:
        index -= 1
        base -= 1
        val = ddv[base] - ddv[index]
    peak = start + base
    return peak


def legacy(derivatives, start, end):
    # While many papers use a single threshold to find the threshold
    # potential this does not work if you want to analyze both
    # interneurons and other neuron types. I have created a shifting
    # threshold based on where the maximum velocity occurs of the first
    # spike occurs.
    dv = derivatives["dv"][start:end]
    peak_dv, _ = signal.find_peaks(dv, height=6)
    try:
        peak = (np.argwhere(np.gradient(dv[: peak_dv[0]]) < (0.3))[0] + start)[-1]
    except IndexError:
        peak = np.argmin(dv[: peak_dv[0]]) + start
    finally:
        peak = np.nan
    return peak


ThresholdFunctions = {
    "third_derivative": third_derivative,
    "max_curvature": max_curvature,
    "method_vii": method_vii,
    "method_ii": method_ii,
    "first_derivative": first_derivative,
    "second_derivative": second_derivative,
    "legacy": legacy,
}

ThresholdType: TypeAlias = Literal[
    "third_derivative",
    "max_curvature",
    "method_vii",
    "method_ii",
    "first_derivative",
    "second_derivative",
    "legacy",
]


def find_all_spk_thresholds(
    voltages: np.ndarray,
    peaks: np.ndarray,
    pulse_start: int = 0,
    pulse_end: int = -1,
    threshold_method: ThresholdType = "third_derivative",
):
    output = np.zeros(len(peaks))
    start_index = pulse_start
    dv = np.gradient(voltages)
    ddv = np.gradient(dv)
    dddv = np.gradient(ddv)
    derivatives = {"v": voltages, "dv": dv, "ddv": ddv, "dddv": dddv}
    thresh_func = ThresholdFunctions[threshold_method]
    for index in range(len(peaks)):
        if index < (len(peaks) - 1):
            end_index = peaks[index]
        else:
            end_index = pulse_end
        try:
            output[index] = thresh_func(derivatives, start_index, end_index)
        except IndexError:
            output[index] = np.nan
        start_index = peaks[index]
    return output
