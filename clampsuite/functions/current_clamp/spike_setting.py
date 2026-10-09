import numpy as np


def dynamic_baseline_start(v: np.ndarray, start_index: int, peak_index: int) -> int:
    """
    Finds the start of the subthreshold charging phase between two spikes.
    Looks for the point where dV/dt recovers from negative repolarization (AHP)
    to positive values (dV/dt >= 0).
    """
    dv = np.gradient(v[start_index:peak_index])
    isi_dv = dv[start_index:peak_index]

    # Find where dV/dt crosses >= 0 after the AHP trough
    # (search backward from the current spike peak)
    neg_or_zero = np.where(isi_dv <= 0)[0]

    if len(neg_or_zero) > 0:
        # Start immediately after the last negative/zero dV/dt sample before the spike
        start_offset = neg_or_zero[-1] + 1
        start_idx = start_index + start_offset
    else:
        # Fallback for extreme high-frequency firing: use the last 25% of the ISI
        isi_len = peak_index - start_index
        start_idx = peak_index - int(isi_len * 0.33)

    return start_idx
