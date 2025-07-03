from typing import Union, NamedTuple

from scipy.stats import linregress


class IVCurveOutput(NamedTuple):
    membrane_resistance: float
    slope: float
    intercept: float
    iv_x_start: float
    iv_x_end: float


def linear(x, slope, intercept):
    return slope * x + intercept


def fit_iv(
    current,
    voltage,
    start: int,
    end: Union[int, None],
) -> NamedTuple:
    if end is None:
        end = -1
    y = voltage[start - 1 : end]
    iv_x = current[start - 1 : end]
    reg = linregress(x=iv_x, y=y)
    mem_res = reg.slope * 1000
    return IVCurveOutput(mem_res, reg.slope, reg.intercept, iv_x[0], iv_x[-1])
