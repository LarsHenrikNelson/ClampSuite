import numpy as np
from scipy import signal, stats


def find_spikes(
    acquisition: np.ndarray,
    fs: float,
    threshold: float = 7.0,
    height: float = 5,
    start: float = 2.0,
    end: float = 3.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Extracts spikes from loose-patch recordings.

    Args:
        acquisition: Acqusition data.
        threshold: Arbitrary threshold based off the median and median absolute
        deviation. Defualt threshold based off of experimental data. Defaults to 7.0.
        height: Minimum height of spikes. Defualt assumes data is in pA. Defaults to 5.
        start: Start relative to peak of spike in ms. Defaults to 2.0.
        end: End relative to peak of spike in ms. Defaults to 3.0.

    Returns:
        peaks, spikes: Returns the identified peaks of the spikes and their waveforms.
    """
    spikes = []
    new_peaks = []
    med: float = np.median(-acquisition)
    mad: float = stats.median_abs_deviation(-acquisition)
    peaks, _ = signal.find_peaks(-acquisition, height=mad * threshold + med, width=10)
    start = int(start * (fs / 1000))
    end = int(end * (fs / 1000))
    for i in peaks:
        if i > start and (i + end) < acquisition.size:
            spk = acquisition[i - start : i + end]
            mx, mn = np.argmax(spk), np.argmin(spk)
            if (
                mn < mx
                and (mx - mn) < (end + start)
                and (spk[mx] - spk[mn]) > height
                and mn > 0
                and mx < (start + end - 1)
            ):
                spikes.append(spk)
                new_peaks.append(i)
    if len(new_peaks) == 0:
        return np.empty(0), np.empty(0)
    return np.array(new_peaks), np.array(spikes)
