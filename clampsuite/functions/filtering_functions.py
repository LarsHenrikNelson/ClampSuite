from typing import Literal, Union, NamedTuple

import numpy as np
from scipy import signal


class FilterError(NamedTuple):
    passed: bool
    error_message: str

Windows = Literal[
    "hann",
    "hamming",
    "blackmanharris",
    "barthann",
    "nuttall",
    "blackman",
    "tukey",
    "kaiser",
    "gaussian",
    "parzen",
]

class MedianFilter(NamedTuple):
    filter_type: str = "median"
    order: int = 4

class EWMAFilter(NamedTuple):
    filter_type: Literal["ewma", "ewma_a"] = "ewma"
    window: int = 30
    sum_proportion: float = 0.5

class SavgolFilter(NamedTuple):
    filter_type = "savgol"
    order: int = 11
    polyorder: int = 3


class FIRFilter(NamedTuple):
    filter_type: Literal["fir", "fir_zero"] = "fir_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200
    window: Windows = "hann",
    beta_sigma: float = None

class RemezFilter(NamedTuple):
    filter_type: Literal["remez", "remez_zero"] = "remez_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200

class IIRFilter(NamedTuple):
    filter_type: Literal[
        "bessel",
        "butterworth",
        "bessel_zero",
        "butterworth_zero"
    ]
    order: int = 4
    high_pass: int | float | None = None
    low_pass: int | float | None = 500

def check_fir_filter_input(high_pass, high_width, low_pass, low_width, sample_rate):
    if high_pass is not None and high_width is not None:
        if high_pass < high_width:
            return FilterError(False, "High_pass must be large than high_width.")
        if high_pass < 0 or high_width < 0:
            return FilterError(False, "Filter settings cannot be less than 0.")
        if high_pass > (sample_rate / 2) or high_width > (sample_rate / 2):
            return FilterError(
                False, "Filter settings cannot be greater than the sample rate."
            )
    if low_pass is not None and low_width is not None:
        if (low_pass + low_width) >= (sample_rate / 2):
            return FilterError(
                False, "Low_pass + low_width must be less than sample_rate"
            )
        if low_pass < 0 or low_width < 0:
            return FilterError(False, "Filter settings cannot be less than 0.")
        if low_pass > (sample_rate / 2) or low_width > (sample_rate / 2):
            return FilterError(
                False,
                "Filter settings cannot be greater than the half the sample rate.",
            )
    if high_pass is not None and high_width is None:
        return FilterError(
            False, "High_width must be provided if high_pass is provided"
        )
    if low_pass is not None and low_width is None:
        return FilterError(False, "Low_width must be provided if low_pass is provided")
    if high_width is not None and high_pass is None:
        return FilterError(
            False, "High_pass must be provided if high_width is provided"
        )
    if low_width is not None and low_pass is None:
        return FilterError(False, "Low_pass must be provided if low_width is provided")
    if low_pass is not None and high_pass is not None:
        if low_pass < high_pass:
            return FilterError(False, "Low_pass must be greater than high_pass.")
    if low_pass is not None:
        if low_pass == 0:
            return FilterError(False, "Low_pass must be greater than 0.")
    if high_pass is not None:
        if high_pass > (sample_rate / 2):
            return FilterError(
                False, "High pass must be greater than half the sample_rate"
            )
        if high_pass == 0:
            return FilterError(False, "High_pass must be greater than 0")
    return FilterError(True, "")


def check_iir_filter_input(high_pass, low_pass, sample_rate):
    if high_pass is None and low_pass is None:
        return FilterError(False, "High_pass or low_pass or both must be provided.")
    if high_pass is not None:
        if high_pass > sample_rate:
            return FilterError(False, "High_pass must be less than sample_rate.")
    if low_pass is not None:
        if low_pass > sample_rate:
            return FilterError(False, "High_pass must be less than sample_rate.")
    if high_pass is not None and low_pass is not None:
        if low_pass < high_pass:
            return FilterError(False, "High_pass must be less than low_pass.")
    return FilterError(True, "")

def median_filter(array: Union[np.ndarray, list], filter_settings: MedianFilter):
    if isinstance(filter_settings.order, float):
        order = int(filter_settings.order)
    filt_array = signal.medfilt(array, order)
    return filt_array

def iir_filter(
    array: Union[np.ndarray, list],
    filter_settings: IIRFilter,
):
    if "bessel" in filter_settings.filter_type:
        filt_design = signal.bessel
    else:
        filt_design = signal.butter
    
    if "zero" in filter_settings.filter_type:
        filt_func = signal.sosfiltfilt
    else:
        filt_func = signal.sosfilt

    if filter_settings.high_pass is not None and filter_settings.low_pass is not None:
        sos = filt_design(
            filter_settings.order,
            Wn=[filter_settings.high_pass, filter_settings.low_pass],
            btype="bandpass",
            output="sos",
            fs=filter_settings.sample_rate,
        )
        filt_array = filt_func(sos, array)
        return filt_array
    elif filter_settings.high_pass is not None and filter_settings.low_pass is None:
        sos = filt_design(
            filter_settings.order, Wn=filter_settings.high_pass, btype="highpass", output="sos", fs=filter_settings.sample_rate
        )
        filt_array = filt_func(sos, array)
    elif filter_settings.high_pass is None and filter_settings.low_pass is not None:
        sos = filt_design(
            filter_settings.order, Wn=filter_settings.low_pass, btype="lowpass", output="sos", fs=filter_settings.sample_rate
        )
        filt_array = filt_func(sos, array)
    return filt_array

def zero_phase_convolve(b: np.ndarray, a: None, array: np.ndarray):
    output = np.convolve(array, b, mode="full")
    wlen = b.size // 2
    output = output[wlen : array.size + wlen]
    return output

def fir_filter(array: np.ndarray, filter_settings: FIRFilter):
    if "zero" in filter_settings.filter_type:
        filt_func = signal.filtfilt
    else:
        filt_func = zero_phase_convolve
    if filter_settings.high_pass is not None and filter_settings.low_pass is not None:
        filt = signal.firwin2(
            filter_settings.order,
            freq=[
                0,
                filter_settings.high_pass - filter_settings.high_width,
                filter_settings.high_pass,
                filter_settings.low_pass,
                filter_settings.low_pass + filter_settings.low_width,
                filter_settings.sample_rate / 2,
            ],
            gain=[0, 0, 1, 1, 0, 0],
            window=filter_settings.window,
            fs=filter_settings.sample_rate,
        )
        filt_array = filt_func(filt, 1.0, array)
    elif filter_settings.high_pass is not None and filter_settings.low_pass is None:
        filt = signal.firwin2(
            filter_settings.order,
            freq=[0, filter_settings.high_pass - filter_settings.high_width, filter_settings.high_pass, filter_settings.sample_rate / 2],
            gain=[0, 0, 1, 1],
            window=filter_settings.window,
            fs=filter_settings.sample_rate,
        )
        filt_array = filt_func(filt, 1.0, array)
    elif filter_settings.high_pass is None and filter_settings.low_pass is not None:
        filt = signal.firwin2(
            filter_settings.order,
            freq=[0, filter_settings.low_pass, filter_settings.low_pass + filter_settings.low_width, filter_settings.sample_rate / 2],
            gain=[1, 1, 0, 0],
            window=filter_settings.window,
            fs=filter_settings.sample_rate,
        )
        filt_array = filt_func(filt, 1.0, array)
    return filt_array

def remez_filter(
    array: Union[np.ndarray, list],
    filter_settings: RemezFilter
):
    check_fir_filter_input(filter_settings.high_pass, filter_settings.high_width, filter_settings.low_pass, filter_settings.low_width, filter_settings.sample_rate)
    if filter_settings.high_pass is not None and filter_settings.low_pass is not None:
        filt = signal.remez(
            filter_settings.order,
            [
                0,
                filter_settings.high_pass - filter_settings.high_width,
                filter_settings.high_pass,
                filter_settings.low_pass,
                filter_settings.low_pass + filter_settings.low_width,
                filter_settings.sample_rate / 2,
            ],
            [0, 1, 0],
            fs=filter_settings.sample_rate,
        )
        filt_acq = signal.filtfilt(filt, 1.0, array)
    elif filter_settings.high_pass is not None and filter_settings.low_pass is None:
        hi = signal.remez(
            filter_settings.order,
            [0, filter_settings.high_pass - filter_settings.high_width, filter_settings.high_pass, filter_settings.sample_rate / 2],
            [0, 1],
            fs=filter_settings.sample_rate,
        )
        filt_acq = signal.filtfilt(hi, 1.0, array)
    elif filter_settings.high_pass is None and filter_settings.low_pass is not None:
        lo = signal.remez(
            filter_settings.order,
            [0, filter_settings.low_pass, filter_settings.low_pass + filter_settings.low_width, filter_settings.sample_rate / 2],
            [1, 0],
            fs=filter_settings.sample_rate,
        )
        filt_acq = signal.filtfilt(lo, 1.0, array)
    return filt_acq


def savgol_filter(array: Union[np.ndarray, list], filter_settings: SavgolFilter):
    if isinstance(filter_settings.polyorder, float):
        polyorder = int(filter_settings.polyorder)
    filtered_array = signal.savgol_filter(array,filter_settings.order, polyorder, mode="nearest")
    return filtered_array


def ewma_filter(array: Union[np.ndarray, list], filter_settings: EWMAFilter):
    alpha = 1 - np.exp(np.log(1 - filter_settings.sum_proportion) / filter_settings.window)
    if filter_settings.filter_type == "ewma_a":
        num = np.power(1.0 - alpha, np.arange(filter_settings.window + 1))
        b = num / np.sum(num)
    else:
        b = [alpha]
    a = 1
    filtered = signal.filtfilt(b, a, array)
    return filtered
