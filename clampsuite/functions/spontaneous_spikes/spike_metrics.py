import math
from dataclasses import dataclass
from scipy import stats, signal
import numpy as np


ANALYSIS_VARIABLES = ["width_index", "maximum_index", "maximum_pa", "minimum_pa"]


@dataclass
class Presence:
    presence_ratio: float
    reg_slope: float
    reg_pvalue: float
    modulation_index: float


def modulation_index(binned_data):
    normalized = binned_data / binned_data.sum()
    max_entropy = np.log(len(binned_data))
    mi = (max_entropy - (-np.sum(normalized * np.log(normalized)))) / max_entropy
    return mi


def presence(
    spike_times: np.ndarray,
    min_time: float | None = None,
    max_time: float | None = None,
    nbins: int = 10,
) -> Presence:
    """Modified version of AllenInstitutes spike presence. Runs a regression to test
    the slope since we want a slope close to zero.

    Args:
        spike_times: spike_times in ms.
        min_time: The minimum time in ms of the recording. Defaults is min(spike_times)
            if None.
        min_time: The maximum time in ms of the recording. Defaults is max(spike_times)
            if None.
        nbins: Number of bins for binning data. Defualts to 10.

    Returns:
        Presence: Dataclass containing the presence ratio, slope fit of binned data and
            the deviatio
    """
    if len(spike_times) == 0:
        return Presence(
            presence_ratio=np.nan,
            reg_slope=np.nan,
            reg_pvalue=np.nan,
            modulation_index=np.nan,
        )
    if min_time is None:
        min_time = min(spike_times)
    if max_time is None:
        max_time = min(spike_times)
    if nbins > 2:
        bins = np.linspace(min_time, max_time, num=nbins)
        h, _ = np.histogram(spike_times, bins=bins)
        reg_out = stats.linregress(np.arange(h.size), h)
        output = Presence(
            presence_ratio=np.sum(h > 0) / nbins,
            reg_slope=reg_out.slope,
            reg_pvalue=reg_out.pvalue,
            modulation_index=modulation_index(h),
        )
    else:
        output = Presence(
            presence_ratio=np.nan,
            reg_slope=np.nan,
            reg_pvalue=np.nan,
            modulation_index=np.nan,
        )
    return output


@dataclass
class WaveformFeatures:
    maximum_index: np.ndarray
    minimum_pa: np.ndarray
    maximum_pa: np.ndarray
    width_index: np.ndarray


def waveform_features(waveforms: np.ndarray) -> WaveformFeatures:
    amn = np.argmin(waveforms, axis=1)
    amx = np.argmax(waveforms, axis=1)
    rows = np.arange(amn.size)
    mn = waveforms[rows, amn]
    mx = waveforms[rows, amx]
    width = amx - amn
    return WaveformFeatures(amx, mn, mx, width)
