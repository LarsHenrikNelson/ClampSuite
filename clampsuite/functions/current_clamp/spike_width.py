import numpy as np
from scipy import signal


def spk_half_width(
    voltages: np.array, peak_x: int, spike_threshold: float, start: int, end: int
):
    volts = np.asarray(voltages[int(start) : int(end)])
    masked_array = volts.copy()
    mask = np.array(volts > spike_threshold)
    masked_array[~mask] = spike_threshold
    width = signal.peak_widths(masked_array, [int(peak_x - start)], rel_height=0.5)
    width[2][0] += start
    width[3][0] += start
    width = np.array([width[2][0], width[3][0], width[1][0]])
    return width


def spk_width(voltages: np.array, spike_threshold: float, start: int, end: int):
    volts = np.asarray(voltages[int(start) : int(end)])
    x = np.arange(len(volts))
    xvals = np.linspace(x[0], x[-1], num=x.size * 10)
    yinterp = np.interp(xvals, x, volts)
    indices = np.where(yinterp > spike_threshold)[0]
    splits = np.where(np.diff(indices) > 1)[0]
    if len(splits) > 0:
        indices = indices[: splits[0]]
    adj_indices = indices / 10
    width = np.array(
        [
            adj_indices[0] + start,
            adj_indices[-1] + start,
            yinterp[indices[0]],
            yinterp[indices[-1]],
        ]
    )
    return width


def spk_auc(voltages: np.array, spike_threshold: float, start: int, end: int):
    volts = np.asarray(voltages[int(start) : int(end)])
    x = np.arange(len(volts))
    xvals = np.linspace(x[0], x[-1], num=x.size * 10)
    yinterp = np.interp(xvals, x, volts)
    indices = np.where(yinterp > spike_threshold)[0]
    splits = np.where(np.diff(indices) > 1)[0]
    if len(splits) > 0:
        indices = indices[: splits[0]]
    yinterp = yinterp - yinterp[indices[0]]
    peak = np.argmax(yinterp)
    auc = np.array(
        [
            np.trapezoid(yinterp[indices[:-1]], dx=x[1] / 10 - x[0] / 10),
            np.trapezoid(yinterp[indices[0] : peak], dx=x[1] / 10 - x[0] / 10),
            np.trapezoid(yinterp[peak : indices[-1]], dx=x[1] / 10 - x[0] / 10),
        ]
    )
    return auc


def find_all_spk_widths(
    voltages: np.ndarray,
    peaks: np.ndarray,
    spike_thresholds: np.ndarray,
    pulse_end: int,
    end_offset: int = 2000,
):
    hws = np.zeros((len(peaks), 3))
    fws = np.zeros((len(peaks), 4))
    auc = np.zeros((len(peaks), 3))
    for index in range(len(peaks)):
        if index < (len(peaks) - 1):
            end = spike_thresholds[index + 1, 0]
        else:
            # Adding end_offset samples (or 2 ms) to the end helps with spikes that occur just before the end of the acquisition
            if (pulse_end - spike_thresholds[index, 0]) < end_offset:
                end = spike_thresholds[index, 0] + end_offset
            else:
                end = pulse_end
        hws[index] = spk_half_width(
            voltages,
            peaks[index],
            spike_thresholds[index, 1],
            spike_thresholds[index, 0],
            end,
        )
        fws[index] = spk_width(
            voltages,
            spike_thresholds[index, 1],
            spike_thresholds[index, 0],
            end,
        )
        auc[index] = spk_auc(
            voltages,
            spike_thresholds[index, 1],
            spike_thresholds[index, 0],
            end,
        )
    return hws, fws, auc
