import numpy as np

SAG_KEYS = ["sag_index", "peak_deflection_mv"]


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
    output["peak_deflection_mv"] = array[sag_loc] - array[:pulse_start].mean()
    return output
