from typing import Literal

import numpy as np


def delta(
    array: np.array,
    pulse_start: int,
    pulse_end: int,
    proportion: float,
    side: Literal["left", "right"] = "right",
    baseline_mean: np.ndarray | None = None,
):
    length = (pulse_start - pulse_end) * proportion
    if side == "left":
        end = pulse_start + length
        start = pulse_start
    else:
        end = pulse_end
        start = pulse_end - length
    if baseline_mean is None:
        baseline_mean = np.mean(array[:pulse_start])
    return np.mean(array[start:end]) - baseline_mean


def baseline_stability(array: np.array, pulse_start: int, pulse_end: int):
    if pulse_end != array.size:
        baseline_stability = np.abs(
            np.mean(array[:pulse_start]) - np.mean(array[pulse_end:])
        )
    else:
        baseline_stability = np.nan
    return baseline_stability
