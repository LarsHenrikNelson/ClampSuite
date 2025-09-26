import numpy as np
import scipy.integrate as sci

AUC_KEYS = ["auc", "auc_left", "auc_right"]


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
        sci.trapezoid(yinterp[indices[:-1]], dx=x[1] / 10 - x[0] / 10),
        sci.trapezoid(yinterp[indices[0] : peak + 1], dx=x[1] / 10 - x[0] / 10),
        sci.trapezoid(yinterp[peak : indices[-1] + 1], dx=x[1] / 10 - x[0] / 10),
    )
    return auc


def find_all_spk_auc(
    voltages: np.ndarray,
    spike_thresholds: np.ndarray,
    pulse_end: int,
):
    auc = {key: np.zeros(len(spike_thresholds)) for key in AUC_KEYS}
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
        output = find_spk_auc(
            voltages,
            spike_thresholds[index],
            end,
        )
        for key, value in zip(AUC_KEYS, output):
            auc[key][index] = value
    return auc
