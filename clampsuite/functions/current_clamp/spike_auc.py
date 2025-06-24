import numpy as np

KEYS = ["auc", "left_auc", "right_auc"]


def find_spk_auc(voltages: np.array, start: int, end: int):
    volts = np.asarray(voltages[int(start) : int(end)])
    spike_threshold = voltages[start]
    x = np.arange(len(volts))
    xvals = np.linspace(x[0], x[-1], num=x.size * 10)
    yinterp = np.interp(xvals, x, volts)
    peak = np.argmax(yinterp)
    indices = np.where(yinterp > spike_threshold)[0]
    splits = np.where(np.diff(indices) > 1)[0]
    if len(splits) > 0:
        indices = indices[: splits[0]]
    yinterp = yinterp - yinterp[indices[0]]
    auc = (
        np.trapezoid(yinterp[indices[:-1]], dx=x[1] / 10 - x[0] / 10),
        np.trapezoid(yinterp[indices[0] : peak], dx=x[1] / 10 - x[0] / 10),
        np.trapezoid(yinterp[peak : indices[-1]], dx=x[1] / 10 - x[0] / 10),
    )
    return auc


def find_all_spk_auc(voltages, spike_thresholds, pulse_end):
    auc = {key: np.zeros(len(spike_thresholds)) for key in KEYS}
    for index in range(len(spike_thresholds)):
        if index < (len(spike_thresholds) - 1):
            end = spike_thresholds[index + 1]
        else:
            # Adding 2000 samples (or 2 ms) to the end helps with spikes that occur just before the end of the acquisition
            if (pulse_end - spike_thresholds[index]) < 2000:
                end = spike_thresholds[index] + 2000
            else:
                end = pulse_end
        output = find_spk_auc(
            voltages,
            spike_thresholds[index],
            end,
        )
        for key, value in zip(KEYS, output):
            auc[key][index] = value
    return auc
