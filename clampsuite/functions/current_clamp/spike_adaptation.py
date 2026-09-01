import numpy as np


def local_sfa(event_times):
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

    if len(event_times) < 3:
        local_var = np.nan
    else:
        iei = np.diff(event_times)
        isi_shift = iei[1:]
        isi_cut = iei[:-1]
        n_minus_1 = len(isi_cut)
        divisor = (isi_cut + isi_shift) ** 2
        has_zeros = np.any(divisor == 0)
        if not has_zeros:
            local_var = np.sum((3 * (isi_cut - isi_shift) ** 2) / divisor) / n_minus_1
        else:
            local_var = np.nan
    return local_var


def divisor_sfa(event_times):
    """
    The idea for the function was initially inspired by a program called
    Easy Electropysiology (https://github.com/easy-electrophysiology).
    """
    if len(event_times) > 2:
        iei = np.diff(event_times)
        sfa_divisor = iei[0] / iei[-1]
    else:
        sfa_divisor = np.nan
    return sfa_divisor


def ai_sfa(event_times):
    """
    This function calculates the spike frequency adaptation. A positive
    number means that the spikes are speeding up and a negative number
    means that spikes are slowing down. This function was inspired by the
    Allen Brain Institutes IPFX analysis program
    https://github.com/AllenInstitute/ipfx/tree/
    db47e379f7f9bfac455cf2301def0319291ad361
    """

    if len(event_times) < 3:
        spike_adapt = np.nan
    else:
        iei = np.diff(event_times)
        if np.allclose((iei[1:] + iei[:-1]), 0.0):
            spike_adapt = np.nan
        else:
            norm_diffs = (iei[1:] - iei[:-1]) / (iei[1:] + iei[:-1])
            norm_diffs[(iei[1:] == 0) & (iei[:-1] == 0)] = 0.0
            spike_adapt = np.nanmean(norm_diffs)
    return spike_adapt


def adaptation_index(event_times):
    if len(event_times) > 2:
        adapt = event_times[0] / event_times[1]
    else:
        adapt = np.nan
    return adapt


def coefficient_of_variation(event_times):
    if len(event_times) > 2:
        iei = np.diff(event_times)
        adapt = np.std(iei) / np.mean(iei)
    else:
        adapt = np.nan
    return adapt
