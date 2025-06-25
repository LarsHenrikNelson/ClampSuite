import numpy as np

VELOCITY_KEYS = [
    "min_velocity_index",
    "min_velocity",
    "max_velocity_index",
    "max_velocity",
]


def spk_velocity(dv: np.ndarray, start: int, end: int):
    min_pos = np.argmin(dv[start:end]) + start
    min_val = dv[min_pos]
    max_pos = np.argmax(dv[start:end]) + start
    max_val = dv[max_pos]
    return min_pos, min_val, max_pos, max_val


def find_all_spk_velocities(
    voltages: np.ndarray,
    spike_thresholds: np.ndarray,
    pulse_end: int,
):
    velocity_measures = {}
    for key in VELOCITY_KEYS:
        if "pos" in key:
            dtype = int
        else:
            dtype = float
        velocity_measures[key] = np.zeros(spike_thresholds.size, dtype=dtype)
    dv = np.diff(voltages)
    for index in range(spike_thresholds.size):
        if index < (len(spike_thresholds) - 1):
            end = spike_thresholds[index + 1]
        else:
            if index != 0:
                temp = (
                    int((spike_thresholds[index] - spike_thresholds[index - 1]) * 1.25)
                    + spike_thresholds[index]
                )
                end = min(temp, pulse_end)
            else:
                end = pulse_end
        output = spk_velocity(dv=dv, start=spike_thresholds[index], end=end)
        for key, value in zip(VELOCITY_KEYS, output):
            velocity_measures[key][index] = value
    return velocity_measures
