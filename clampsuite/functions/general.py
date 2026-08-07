from typing import Literal

import numpy as np
from scipy import integrate, stats


def delta(
    array: np.ndarray,
    pulse_start: int,
    pulse_end: int,
    proportion: float,
    side: Literal["left", "right"] = "right",
    baseline_mean: np.ndarray | None = None,
) -> tuple[int, float]:
    length = int((pulse_end - pulse_start) * proportion)
    if side == "left":
        end = pulse_start + length
        start = pulse_start
        index = pulse_start + length // 2
    else:
        end = pulse_end
        start = pulse_end - length
        index = start + length // 2
    if baseline_mean is None:
        baseline_mean = np.mean(array[:pulse_start])
    return index, np.mean(array[start:end]) - baseline_mean


def baseline_stability(array: np.ndarray, pulse_start: int, pulse_end: int):
    if pulse_end != array.size:
        baseline_stability = np.abs(
            np.mean(array[:pulse_start]) - np.mean(array[pulse_end:])
        )
    else:
        baseline_stability = np.nan
    return baseline_stability


def charge_transfer(x, y, method: Literal["trapezoid", "simpson"] = "simpson"):
    if method == "trapezoid":
        charge_transfer = integrate.trapezoid(y, x)
    elif method == "simpson":
        charge_transfer = integrate.simpson(y, x)
    else:
        raise ValueError("Method not recognized")
    return charge_transfer


def regress_subset(
    array, start: float = 0.1, stop: float = 0.9, fs: float | None = None
):
    length = len(array)
    ten = int(length * start)
    ninety = int(length * stop)
    y = array[ten:ninety]
    if fs is not None:
        x = np.arange(y.size) / fs
    else:
        x = np.arange(y.size)
    reg = stats.linregress(x, y)
    return reg.slope
