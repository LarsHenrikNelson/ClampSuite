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
        ymin = np.min(y)
        ymax = np.max(y)
        if np.abs(ymin) > np.abs(ymax):
            numerator = ymin-ymax
            offset_est = ymax
        else:
            offset_est = ymin
            numerator = ymax-ymin
        divisor = max(np.abs(xmax - xmin), 1)
        vscale_est = numerator / max(np.log(divisor), 1)
        p0 = [vscale_est, offset_est, 0]
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
