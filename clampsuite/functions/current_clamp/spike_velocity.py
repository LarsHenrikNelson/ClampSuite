import numpy as np

VELOCITY_KEYS = ["min_velocity_pos", "min_velocity", "max_velocity_pos", "max_velocity"]


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
    end_offset: int = 2000,
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
            # Adding end_offset samples (or 2 ms) to the end helps with spikes that occur just before the end of the acquisition
            if (pulse_end - spike_thresholds[index]) < end_offset:
                end = spike_thresholds[index] + end_offset
            else:
                end = pulse_end
        output = spk_velocity(dv=dv, start=spike_thresholds[index], end=end)
        for key, value in zip(VELOCITY_KEYS, output):
            velocity_measures[key][index] = value
    return velocity_measures
