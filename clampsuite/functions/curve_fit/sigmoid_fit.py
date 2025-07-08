from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit


class SigmoidCurveFit(NamedTuple):
    max_value: float
    midpoint: float
    slope: float
    offset: float
    max_gain: float
    max_current: float


def sigmoid(x, max_value, midpoint, slope, offset):
    return 1 / (1 + np.exp((x - midpoint) / -slope)) * max_value + offset


def fit_sigmoid(current, firing_rate):
    lb = [-np.inf, -np.inf, 1e-6, 0]
    ub = [np.inf, np.inf, np.inf, np.inf]
    p0 = [np.max(firing_rate), np.mean(current), 30, 0]
    try:
        p, _ = curve_fit(sigmoid, current, firing_rate, p0=p0, bounds=(lb, ub))
        upsampled_current = np.linspace(current.min(), current.max(), 1000)

        sigmoid_curve = sigmoid(upsampled_current, *p)
        diff = np.gradient(sigmoid_curve)
        max_gain_index = diff.argmax()
        max_gain = diff[max_gain_index]
        max_current = upsampled_current[max_gain_index]

        output = SigmoidCurveFit(
            max_value=p[0],
            midpoint=p[1],
            slope=p[2],
            offset=p[3],
            max_gain=max_gain,
            max_current=max_current,
        )
    except Exception:
        output = SigmoidCurveFit(
            max_value=np.nan,
            midpoint=np.nan,
            slope=np.nan,
            offset=np.nan,
            max_gain=np.nan,
            max_current=np.nan,
        )
    return output
