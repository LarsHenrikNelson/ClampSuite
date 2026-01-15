from typing import Literal, TypeAlias, Callable

import numpy as np
from scipy import signal

THRESHOLD_KEYS = ["threshold_index", "threshold_mv"]


def third_derivative(derivatives: dict[str, np.ndarray], start: int, end: int):
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


def max_curvature(derivatives: dict[str, np.ndarray], start: int, end: int):
    dv = derivatives["dv"][start:end]
    v = derivatives["v"][start:end]
    peak = np.argmax(-1 * (dv / v))
    peak = peak - 2 + start
    return peak


def method_vii(derivatives: dict[str, np.ndarray], start: int, end: int):
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["ddv"][start:end]
    method_vii = ddv * (1 + dv**2) ** (-3 / 2)
    peak = method_vii.argmax() + start
    return peak


def method_ii(derivatives: dict[str, np.ndarray], start: int, end: int):
    dddv = derivatives["dddv"][start:end]
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["dv"][start:end]
    temp = (dddv * dv - ddv**2) / (np.ma.array(dv**3, mask=dv != 0))
    peak = temp.data.argmax() + start
    return peak


def first_derivative(derivatives: dict[str, np.ndarray], start: int, end: int):
    dv = derivatives["dv"][start:end]
    min_index = derivatives["v"][start:end].argmin()
    base = dv.argmax()
    index = base - 1
    val = dv[base] - dv[index]
    mm = dv[base] / 10
    while val >= min_index or dv[base] > mm:
        index -= 1
        base -= 1
        val = dv[base] - dv[index]
    base = np.where(dv > np.max(dv[:base]))[0][0]
    peak = base + start
    return peak


def second_derivative(derivatives: dict[str, np.ndarray], start: int, end: int):
    ddv = derivatives["ddv"][start:end]
    min_index = derivatives["v"][start:end].argmin()
    base = ddv.argmax()
    index = base - 1
    val = ddv[base] - ddv[index]
    while val > min_index:
        index -= 1
        base -= 1
        val = ddv[base] - ddv[index]
    peak = start + base
    return peak


def legacy(derivatives: dict[str, np.ndarray], start: int, end: int):
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


def derivative_threshold(
    derivatives: dict[str, np.ndarray], start: int, end: int, threshold: float = 5.0
):
    dv = derivatives["dv"][start:end]
    peak = np.argwhere(dv > threshold)[0] + start
    return peak


ThresholdFunctions: dict[str, Callable] = {
    "third_derivative": third_derivative,
    "max_curvature": max_curvature,
    "method_vii": method_vii,
    "method_ii": method_ii,
    "first_derivative": first_derivative,
    "second_derivative": second_derivative,
    "legacy": legacy,
    "allen_institute": derivative_threshold,
}

ThresholdType: TypeAlias = Literal[
    "third_derivative",
    "max_curvature",
    "method_vii",
    "method_ii",
    "first_derivative",
    "second_derivative",
    "legacy",
    "allen_institute",
]


def find_all_spk_thresholds(
    voltages: np.ndarray,
    peaks: np.ndarray,
    pulse_start: int = 0,
    threshold_method: ThresholdType = "third_derivative",
):
    output = np.zeros(len(peaks), dtype=int)
    dv = np.gradient(voltages)
    ddv = np.gradient(dv)
    dddv = np.gradient(ddv)
    derivatives = {"v": voltages, "dv": dv, "ddv": ddv, "dddv": dddv}
    if threshold_method == "allen_institute":
        threshold: list[float] = []
        for index, peak in enumerate(peaks):
            if index == 0:
                threshold.append(np.max(dv[pulse_start:peak]))
            else:
                threshold.append(np.max(dv[peaks[index - 1], peak]))
            threshold_value = float(np.mean(threshold))
    thresh_func = ThresholdFunctions[threshold_method]
    for index in range(len(peaks)):
        end_index = peaks[index]
        if index > 0:
            start_index = (
                voltages[peaks[index - 1] : peaks[index]].argmin() + peaks[index - 1]
            )
        else:
            start_index = int((peaks[index] - pulse_start) * 0.1) + pulse_start
        try:
            if threshold_method == "allen_institute":
                output[index] = derivative_threshold(
                    derivatives, start_index, end_index, threshold_value
                )
            else:
                output[index] = thresh_func(derivatives, start_index, end_index)
        except IndexError:
            output[index] = ThresholdFunctions["first_derivative"](
                derivatives, start_index, end_index
            )
        except IndexError:
            output[index] = start_index
    return {"threshold_index": output, "threshold_mv": voltages[output]}
