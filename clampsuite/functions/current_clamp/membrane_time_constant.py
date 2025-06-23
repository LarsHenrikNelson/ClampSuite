import numpy as np


def membrane_time_constant_min(
    acq, pulse_start=3000, pulse_end=10000, baseline_start=0, baseline_end=3000
):
    voltages = acq - acq[baseline_start:baseline_end]
    threshold1 = voltages.min() * 0.63
    min_val = voltages.argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold1)[0][0]
    return tau


def membrane_time_constant_deltav(
    acq, pulse_start=3000, pulse_end=10000, baseline_start=0, baseline_end=3000
):
    voltages = acq - acq[baseline_start:baseline_end]
    p50 = ((pulse_end - pulse_start) // 2) + pulse_start
    deltav = voltages[pulse_start:p50]
    threshold2 = deltav * 0.63
    min_val = voltages.argmin() + pulse_start
    tau = np.where(voltages[pulse_start:min_val] < threshold2)[0][0]
    return tau
