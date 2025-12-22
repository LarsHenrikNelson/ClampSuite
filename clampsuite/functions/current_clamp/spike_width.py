import numpy as np
from scipy import signal

WIDTH_KEYS = [
    "hw_left_index",
    "hw_right_index",
    "hw_mv",
    "fw_left_index",
    "fw_right_index",
    "fw_mv",
]


def find_spk_width(voltages: np.ndarray, start: int, end: int):
    start = int(start)
    end = int(end)
    volts = np.asarray(voltages[start:end])
    xvals = np.linspace(start, end, num=int((end - start) * 10))
    x = np.linspace(start, end, num=int(end - start))
    volts = np.interp(xvals, x, volts)
    spike_threshold = voltages[start]
    masked_array = volts.copy()
    mask = np.array(volts > spike_threshold)
    peak_x = np.argmax(volts)
    masked_array[~mask] = spike_threshold
    hw = signal.peak_widths(masked_array, [peak_x], rel_height=0.5)
    fw = signal.peak_widths(masked_array, [peak_x], rel_height=1)
    return (
        hw[2][0] / 10 + start,
        hw[3][0] / 10 + start,
        hw[1][0],
        fw[2][0] / 10 + start,
        fw[3][0] / 10 + start,
        fw[1][0],
    )


def find_all_spk_widths(
    voltages: np.ndarray,
    spike_thresholds: np.ndarray,
    pulse_end: int,
):
    width = {key: np.zeros(len(spike_thresholds)) for key in WIDTH_KEYS}
    for index in range(len(spike_thresholds)):
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
        output = find_spk_width(voltages, spike_thresholds[index], end)
        for key, value in zip(WIDTH_KEYS, output):
            width[key][index] = value
    return width
