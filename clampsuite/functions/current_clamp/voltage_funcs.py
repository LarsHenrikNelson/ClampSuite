import numpy as np


def voltage_sag(
    array: np.array, pulse_start: int, pulse_end: int, proportion: float = 0.3
):
    output = {}
    length = pulse_end - pulse_start
    p50 = int(length * proportion) + pulse_start
    sag_loc = np.argmin(array[pulse_start:p50]) + pulse_start
    output["sag_index"] = sag_loc
    sag_v = array[sag_loc]
    injection_v = np.mean(array[p50:pulse_end])
    output["sag"] = sag_v - injection_v
    return output
