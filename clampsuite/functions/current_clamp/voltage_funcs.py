import numpy as np


def voltage_sag(
    array: np.array, pulse_start: int, pulse_end: int, proportion: float = 0.3
):
    length = pulse_start - pulse_end
    p50 = int(length * proportion) + pulse_start
    sag_loc = np.argmin(array[pulse_start:p50]) + pulse_start
    sag_v = array[sag_loc]
    injection_v = np.mean(array[p50:pulse_end])
    sag = sag_v - injection_v
    return sag_loc, sag
