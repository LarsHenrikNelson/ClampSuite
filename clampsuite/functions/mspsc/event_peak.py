import numpy as np
from scipy import signal


def find_peak(event_array: np.ndarray, fs: float, adjust_pos: int) -> int | float:
    s_r_c = fs / 1000
    peaks_1, _ = signal.find_peaks(
        -1 * event_array,
        prominence=4,
        width=0.4 * s_r_c,
        distance=int(3 * s_r_c),
    )
    peaks_1 = peaks_1[peaks_1 > adjust_pos]
    if len(peaks_1) == 0:
        peak_x = find_peak_alt(event_array, s_r_c, adjust_pos)
    else:
        peak_x = peak_corr(event_array, peaks_1[0], s_r_c)
    return peak_x


def peak_corr(event_array: np.ndarray, peak_1: int, s_r_c) -> int:
    peaks_2 = signal.argrelextrema(
        event_array[:peak_1],
        comparator=np.less,
        order=int(0.4 * s_r_c),
    )[0]
    peaks_2 = peaks_2[peaks_2 > peak_1 - 4 * s_r_c]
    if len(peaks_2) == 0:
        final_peak = peak_1
    else:
        peaks_3 = peaks_2[event_array[peaks_2] < 0.85 * event_array[peak_1]]
        if len(peaks_3) == 0:
            final_peak = peak_1
        else:
            final_peak = peaks_3[0]
    peak_x = final_peak
    return peak_x


def find_peak_alt(
    event_array: np.ndarray, s_r_c: int | float, adjust_pos: int
) -> int | float:
    peaks_1 = signal.argrelextrema(
        event_array, comparator=np.less, order=int(3 * s_r_c)
    )[0]
    peaks_1 = peaks_1[peaks_1 > adjust_pos]
    if len(peaks_1) == 0:
        peak_x = -1
    else:
        peak_x = peak_corr(event_array, peaks_1[0], s_r_c)
    return peak_x
