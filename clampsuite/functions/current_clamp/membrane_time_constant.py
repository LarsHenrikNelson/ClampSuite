import numpy as np


def membrane_time_constant_min(
    array: np.ndarray,
    pulse_start: int = 3000,
):
    voltages = array - array[:pulse_start].mean()
    threshold1 = voltages[pulse_start:].min() * (1-1 / np.exp(1))
    min_val = voltages[pulse_start:].argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold1)[0][0]
    return tau


def membrane_time_constant_deltav(
    array: np.ndarray,
    deltav: float,
    pulse_start: int = 3000,
):
    voltages = array - array[:pulse_start].mean()
    threshold2 = deltav * (1-1 / np.exp(1))
    min_val = voltages[pulse_start:].argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold2)[0][0]
    return tau
