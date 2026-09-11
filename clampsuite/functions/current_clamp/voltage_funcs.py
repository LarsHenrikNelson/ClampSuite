import numpy as np

SAG_KEYS = ["sag_index", "sag_mv"]


def voltage_sag(
    array: np.ndarray,
    pulse_start: int,
    pulse_end: int,
):
    output = {}
    length = pulse_end - pulse_start
    p50 = int(length * 0.5) + pulse_start
    sag_loc = np.argmin(array[pulse_start:p50]) + pulse_start
    output["sag_index"] = sag_loc
    sag_v = array[sag_loc]
    injection_v = np.mean(array[p50:pulse_end])
    output["sag_mv"] = sag_v - injection_v
    return output
