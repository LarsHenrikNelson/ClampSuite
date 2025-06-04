import numpy as np


def local_sfa(peaks):
    """
    The idea for the function was initially inspired by a program called
    Easy Electropysiology (https://github.com/easy-electrophysiology).

    This function calculates the local variance in spike frequency
    accomadation that was drawn from the paper:
    Shinomoto, Shima and Tanji. (2003). Differences in Spiking Patterns
    Among Cortical Neurons. Neural Computation, 15, 2823-2842.

    Returns
    -------
    None.

    """

    if len(peaks) < 2:
        local_var = np.nan
    else:
        iei = np.diff(peaks)
        isi_shift = iei[1:]
        isi_cut = iei[:-1]
        n_minus_1 = len(isi_cut)
        local_var = (
            np.sum((3 * (isi_cut - isi_shift) ** 2) / (isi_cut + isi_shift) ** 2)
            / n_minus_1
        )
    return local_var


def divisor_sfa(peaks):
    """
    The idea for the function was initially inspired by a program called
    Easy Electropysiology (https://github.com/easy-electrophysiology).
    """
    if len(peaks) > 2:
        iei = np.diff(peaks)
        sfa_divisor = iei[0] / iei[-1]
    else:
        sfa_divisor = np.nan
    return sfa_divisor


def ai_sfa(peaks):
    """
    This function calculates the spike frequency adaptation. A positive
    number means that the spikes are speeding up and a negative number
    means that spikes are slowing down. This function was inspired by the
    Allen Brain Institutes IPFX analysis program
    https://github.com/AllenInstitute/ipfx/tree/
    db47e379f7f9bfac455cf2301def0319291ad361
    """

    if len(peaks) > 1:
        spike_adapt = np.nan
    else:
        iei = np.diff(peaks)
        if np.allclose((iei[1:] + iei[:-1]), 0.0):
            spike_adapt = np.nan
        norm_diffs = (iei[1:] - iei[:-1]) / (iei[1:] + iei[:-1])
        norm_diffs[(iei[1:] == 0) & (iei[:-1] == 0)] = 0.0
        spike_adapt = np.nanmean(norm_diffs)
    return spike_adapt


def adaptation_index(peaks):
    if len(peaks) > 2:
        adapt = peaks[0] / peaks[1]
    else:
        adapt = np.nan
    return adapt
