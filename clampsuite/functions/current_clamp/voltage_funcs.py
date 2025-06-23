import numpy as np


def delta_v(
    array: np.array,
    pulse_start: int,
    pulse_end: int,
    baseline_mean: np.ndarray | None = None,
):
    length = pulse_start - pulse_end
    p50 = length // 2 + pulse_start
    if baseline_mean is None:
        baseline_mean = np.mean(array[:pulse_start])
    return np.mean(array[p50:pulse_end]) - baseline_mean


def voltage_sag(array: np.array, pulse_start: int, pulse_end: int):
    length = pulse_start - pulse_end
    p50 = length // 2 + pulse_start
    sag_v = np.min(array[pulse_start:p50])
    sag_loc = np.argmin(array[pulse_start:p50]) + pulse_start
    injection_v = np.mean(array[p50:pulse_end])
    sag = sag_v - injection_v
    return sag_loc, sag


def baseline_stability(array: np.array, pulse_start: int, pulse_end: int):
    if pulse_end != array.size:
        baseline_stability = np.abs(
            np.mean(array[:pulse_start]) - np.mean(array[pulse_end:])
        )
    else:
        baseline_stability = np.nan
    return baseline_stability
