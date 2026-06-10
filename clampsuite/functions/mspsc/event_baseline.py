import numpy as np
from scipy import signal


def find_alt_baseline(event_array: np.ndarray, peak_index: int, fs: float | int) -> int:
    s_r_c = fs / 1000
    baselined_array = event_array - np.mean(event_array[: int(1 * s_r_c)])
    masked_array = baselined_array.copy()
    mask = np.argwhere(baselined_array <= 0)
    masked_array[mask] = 0
    peaks = signal.argrelmax(masked_array[0 : int(peak_index)], order=2)
    if len(peaks[0]) > 0:
        event_baseline = int(peaks[0][-1])
    else:
        event_baseline = int(np.argmax(masked_array[0 : int(peak_index)]))
    return event_baseline


def find_baseline(event_array: np.ndarray, peak_index: int, fs: float) -> int:
    """
    This functions finds the baseline of an event. The biggest issue with
    most methods that find the baseline is that they assume the baseline
    does not deviate from zero, however this is often not true is real
    life. This methods combines a slope finding method with a peak
    finding method.
    """
    s_r_c = fs / 1000
    if event_array[peak_index] > 0:
        event_array = event_array * -1
    baselined_array = event_array - np.max(event_array[:peak_index])
    event_peak_y = event_array[peak_index]
    search_start = np.argwhere(
        baselined_array[:peak_index] > 0.35 * event_peak_y
    ).flatten()
    if search_start.size > 0:
        slope = (event_array[search_start[-1]] - event_peak_y) / (
            peak_index - search_start[-1]
        )
        new_slope = slope + 1
        i = search_start[-1]
        while new_slope > slope and i > 0:
            slope = (event_array[i] - event_peak_y) / (peak_index - i)
            i -= 1
            new_slope = (event_array[i] - event_peak_y) / (peak_index - i)
        baseline_start = signal.argrelmax(
            baselined_array[int(i - 1 * s_r_c) : i + 2], order=2
        )[0]
        if baseline_start.size > 0:
            event_baseline = int(baseline_start[-1] + (i - 1 * s_r_c))
            if event_baseline < 0:
                event_baseline = 0
        else:
            event_baseline = int(baseline_start.size / 2 + (i - 1 * s_r_c))
            if event_baseline < 0:
                event_baseline = 0
    else:
        event_baseline = find_alt_baseline(event_array, peak_index, fs=fs)
    return event_baseline
