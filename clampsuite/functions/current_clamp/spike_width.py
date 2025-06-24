import numpy as np
from scipy import signal

KEYS = ["hw_left", "hw_right", "hw_y", "fw_left", "fw_right", "fw_y"]


def find_spk_width(voltages: np.array, start: int, end: int):
    volts = np.asarray(voltages[int(start) : int(end)])
    spike_threshold = voltages[start]
    masked_array = volts.copy()
    mask = np.array(volts > spike_threshold)
    peak_x = np.argmax(volts)
    masked_array[~mask] = spike_threshold
    hw = signal.peak_widths(masked_array, [peak_x], rel_height=0.5)
    fw = signal.peak_widths(masked_array, [peak_x], rel_height=1)
    return (
        hw[2][0] + start,
        hw[3][0] + start,
        hw[1][0],
        fw[2][0] + start,
        fw[3][0] + start,
        fw[1][0],
    )


def find_all_spk_widths(
    voltages: np.ndarray,
    spike_thresholds: np.ndarray,
    pulse_end: int,
    offset: int = 2000,
):
    width = {key: np.zeros(len(spike_thresholds)) for key in KEYS}
    for index in range(len(spike_thresholds)):
        if index < (len(spike_thresholds) - 1):
            end = spike_thresholds[index + 1]
        else:
            # Adding 2000 samples (or 200 ms) to the end helps with spikes that occur just before the end of the acquisition
            if (pulse_end - spike_thresholds[index]) < offset:
                end = spike_thresholds[index] + offset
            else:
                end = pulse_end
        output = find_spk_width(
            voltages,
            spike_thresholds[index],
            end,
        )
        for key, value in zip(KEYS, output):
            width[key][index] = value
    return width
