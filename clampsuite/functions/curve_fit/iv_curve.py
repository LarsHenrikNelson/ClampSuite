from typing import NamedTuple, Literal

from scipy.stats import linregress
import numpy as np


class IVCurveOutput(NamedTuple):
    membrane_resistance: float
    slope: float
    intercept: float


def linear(x, slope, intercept):
    return slope * x + intercept


def fit_iv(
    current,
    voltage,
    start: int | float | None = None,
    end: int | float | None = None,
    rectify: bool = False
) -> NamedTuple:
    if start is None:
        start = current.min()
    if end is None:
        end = current.max()
    indices = (current >= start) & (current <= end)
    current = current[indices]
    voltage = voltage[indices]
    if rectify:
        current = np.abs(current)
        voltage = np.abs(voltage)
    reg = linregress(x=current, y=voltage)
    mem_res = reg.slope * 1000
    return IVCurveOutput(mem_res, reg.slope, reg.intercept)
