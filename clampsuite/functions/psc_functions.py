from typing import TypedDict

import numpy as np
from scipy import signal


class Event(TypedDict):
    peak_x: float
    amplitude: float
    start_x: float
    end_x: float


def find_peak_window(array, peak_direction, window_start, window_end):
    if peak_direction == "positive":
        peak_y = np.max(array[window_start:window_end])
        peak_x = np.argmax(array[window_start:window_end]) + window_start
    elif peak_direction == "negative":
        peak_y = np.min(array[window_start:window_end])
        peak_x = np.argmin(array[window_start:window_end]) + window_start
    return peak_y, peak_x


def find_multipeaks(array, height, prominence, distance):
    peaks, props = signal.find_peaks(
        array, height=height, prominence=prominence, distance=(distance)
    )
    events = []
    for i in np.arange(len(peaks)):
        if i < len(peaks) - 1:
            temp = Event(
                peak_x=peaks[i],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["left_bases"][i + 1],
            )
        else:
            temp = Event(
                peak_x=peaks[i],
                amplitude=np.abs(array[peaks[i]] - props["left_bases"][i]),
                start_x=props["left_bases"][i],
                end_x=props["right_bases"][i],
            )
        events.append(temp)
