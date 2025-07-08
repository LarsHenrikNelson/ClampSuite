from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit


class LogCurveFit(NamedTuple):
    vscale: float
    offset: float


def log_func(x, vscale, offset=0):
    return vscale * np.log(x) + offset


def fit_log(x, y):
    try:
        p, _ = curve_fit(log_func, x, y)

        output = LogCurveFit(
            vscale=p[0],
            offset=p[1],
        )
    except Exception:
        output = LogCurveFit(
            vscale=np.nan,
            offset=np.nan,
        )
    return output
