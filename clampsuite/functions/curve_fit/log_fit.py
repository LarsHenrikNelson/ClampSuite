from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit


class LogCurveFit(NamedTuple):
    vscale: float
    offset: float


def log_func(x, vscale, offset=0, xshift=0):
    return vscale * np.log(x - xshift) + offset


def fit_log(x, y):
    try:
        p0 = [np.max(y) - np.min(y) / np.log(x[-1] - x[0]), np.min(y), 0]
        ub = [np.inf, np.inf, np.min(x) - 1e-6]
        lb = [-np.inf, -np.inf, -np.inf]
        p, _ = curve_fit(log_func, x, y, p0=p0, bounds=(lb, ub))

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
