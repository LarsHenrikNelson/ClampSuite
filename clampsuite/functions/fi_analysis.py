from typing import TypedDict

import numpy as np
from scipy.optimize import curve_fit


class SigmoidCurveFit(TypedDict):
    max_value: float
    midpoint: float
    slope: float
    offset: float
    max_gain: float
    max_current: float


def sigmoid(x, max_value, midpoint, slope, offset):
    return 1 / (1 + np.exp((x - midpoint) / slope)) * max_value + offset


def curve_fit_sigmoid(current, firing_rate):
    p, _ = curve_fit(sigmoid, current, firing_rate)
    upsampled_current = np.linspace(current.min(), current.max(), 1000)
    sigmoid_curve = sigmoid(upsampled_current, *p)
    diff = np.gradient(sigmoid_curve)
    max_gain = diff.argmax()
    max_gain = diff[max_gain]
    max_current = upsampled_current[max_gain]

    output = SigmoidCurveFit(
        max_value=p[0],
        midpoint=p[1],
        slope=p[2],
        offset=p[3],
        max_gain=max_gain,
        max_current=max_current,
    )

    return output
