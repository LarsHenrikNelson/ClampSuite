import numpy as np


def membrane_time_constant_min(
    array: np.ndarray,
    pulse_start: int = 3000,
    baseline_start: int = 0,
    baseline_end: int = 3000,
):
    voltages = array - array[baseline_start:baseline_end]
    threshold1 = voltages.min() * 0.63
    min_val = voltages.argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold1)[0][0]
    return tau


def membrane_time_constant_deltav(
    array: np.ndarray,
    deltav: float,
    pulse_start: int = 3000,
    baseline_start: int = 0,
    baseline_end=3000,
):
    voltages = array - array[baseline_start:baseline_end]
    threshold2 = deltav * 0.63
    min_val = voltages.argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold2)[0][0]
    return tau
