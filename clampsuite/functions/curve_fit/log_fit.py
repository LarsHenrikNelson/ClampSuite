from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit


class LogCurveFit(NamedTuple):
    vscale: float
    offset: float
    xshift: float


def log_func(x, vscale, offset=0, xshift=0):
    return vscale * np.log(x - xshift) + offset


def fit_log(x, y):
    try:
        xmin= np.min(x)
        xmax = np.max(x)
        divisor = max((xmax - xmin), 1)
        p0 = [np.max(y) - np.min(y) / max(np.log(divisor), 1), np.min(y), 0]
        ub = [np.inf, np.inf, xmin - 1e-6]
        lb = [-np.inf, -np.inf, -np.inf]
        p, _ = curve_fit(log_func, x, y, p0=p0, bounds=(lb, ub))

        output = LogCurveFit(
            vscale=p[0],
            offset=p[1],
            xshift=p[2],
        )
    except Exception:
        output = LogCurveFit(
            vscale=np.nan,
            offset=np.nan,
            xshift=np.nan,
        )
    return output
