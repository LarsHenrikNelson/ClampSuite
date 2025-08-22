import numpy as np
from scipy import signal


def find_alt_baseline(event_array: np.ndarray, peak_x: int):
    baselined_array = event_array - np.mean(event_array[: int(1 * self.s_r_c)])
    masked_array = baselined_array.copy()
    mask = np.argwhere(baselined_array <= 0)
    masked_array[mask] = 0
    peaks = signal.argrelmax(masked_array[0 : int(peak_x - self._array_start)], order=2)
    if len(peaks[0]) > 0:
        baseline_x = peaks[0][-1]
    else:
        event_start = np.argmax(masked_array[0 : int(peak_x - self._array_start)])
        self._event_start_x = self.x_array()[event_start]
        self.event_start_y = event_array[event_start]
    self.event_baseline = self.event_start_y


def find_baseline(self):
    """
        This functions finds the baseline of an event. The biggest issue with
        most methods that find the baseline is that they assume the baseline
        does not deviate from zero, however this is often not true is real
        life. This methods combines a slope finding method with a peak
        finding method.

    Returns
    -------
    None.

    """
    # baselined_array = self.event_array - np.mean(
    #     self.event_array[: int(1 * self.s_r_c)]
    # )
    baselined_array = self.event_array - np.max(self.event_array[: self._event_peak_x])
    peak = int(self._event_peak_x - self._array_start)
    # search_start = np.argwhere(
    #     baselined_array[:peak] > 0.5 * self.event_peak_y
    # ).flatten()
    search_start = np.argwhere(
        baselined_array[:peak] > 0.35 * self.event_peak_y
    ).flatten()
    if search_start.size > 0:
        slope = (self.event_array[search_start[-1]] - self.event_peak_y) / (
            peak - search_start[-1]
        )
        new_slope = slope + 1
        i = search_start[-1]
        while new_slope > slope and i > 0:
            slope = (self.event_array[i] - self.event_peak_y) / (peak - i)
            i -= 1
            new_slope = (self.event_array[i] - self.event_peak_y) / (peak - i)
        baseline_start = signal.argrelmax(
            baselined_array[int(i - 1 * self.s_r_c) : i + 2], order=2
        )[0]
        if baseline_start.size > 0:
            temp = int(baseline_start[-1] + (i - 1 * self.s_r_c))
            if temp < 0:
                temp = 0
        else:
            temp = int(baseline_start.size / 2 + (i - 1 * self.s_r_c))
            if temp < 0:
                temp = 0
        self._event_start_x = self.x_array()[temp]
        self.event_start_y = self.event_array[temp]
    else:
        self.find_alt_baseline()
