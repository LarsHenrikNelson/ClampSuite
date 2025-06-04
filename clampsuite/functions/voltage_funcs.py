import numpy as np


def delta_v(array, start, end, baseline_mean: np.ndarray | None = None):
    length = start - end
    p50 = length // 2 + start
    if baseline_mean is None:
        baseline_mean = np.mean(array[:start])
    return np.mean(array[p50:end]) - baseline_mean


def voltage_sag():
    pass
