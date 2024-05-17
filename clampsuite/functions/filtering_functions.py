from typing import Literal, Union, NamedTuple

import numpy as np
from scipy import signal


class FilterError(NamedTuple):
    passed: bool
    error_message: str


Filters = Literal[
    "remez_2",
    "remez_1",
    "fir_zero_2",
    "fir_zero_1",
    "savgol",
    "ewma",
    "ewma_a",
    "median",
    "bessel",
    "butterworth",
    "bessel_zero",
    "butterworth_zero",
    "None",
]

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


def median_filter(array: Union[np.ndarray, list], order: int):
    if isinstance(order, float):
        order = int(order)
    filt_array = signal.medfilt(array, order)
    return filt_array


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
        if high_pass < (sample_rate / 2):
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


def bessel(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.bessel(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.bessel(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.bessel(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def bessel_zero(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.bessel(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.bessel(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.bessel(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def butterworth(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.butter(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.butter(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.butter(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def butterworth_zero(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.butter(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.butter(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.butter(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def elliptic(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.ellip(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.ellip(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.ellip(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def elliptic_zero(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
):
    if high_pass is not None and low_pass is not None:
        sos = signal.ellip(
            order,
            Wn=[high_pass, low_pass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif high_pass is not None and low_pass is None:
        sos = signal.ellip(
            order, Wn=high_pass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif high_pass is None and low_pass is not None:
        sos = signal.ellip(
            order, Wn=low_pass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def fir_zero_1(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    high_width: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
    low_width: Union[int, float, None] = None,
    window: str = "hann",
):
    check_fir_filter_input(high_pass, high_width, low_pass, low_width, sample_rate)
    if high_pass is not None and low_pass is not None:
        filt = signal.firwin2(
            order,
            freq=[
                0,
                high_pass - high_width,
                high_pass,
                low_pass,
                low_pass + low_width,
                sample_rate / 2,
            ],
            gain=[0, 0, 1, 1, 0, 0],
            window=window,
            fs=sample_rate,
        )
        filt_array = signal.filtfilt(filt, 1.0, array)
    elif high_pass is not None and low_pass is None:
        filt = signal.firwin2(
            order,
            freq=[0, high_pass - high_width, high_pass, sample_rate / 2],
            gain=[0, 0, 1, 1],
            window=window,
            fs=sample_rate,
        )
        filt_array = signal.filtfilt(filt, 1.0, array)
    elif high_pass is None and low_pass is not None:
        filt = signal.firwin2(
            order,
            freq=[0, low_pass, low_pass + low_width, sample_rate / 2],
            gain=[1, 1, 0, 0],
            window=window,
            fs=sample_rate,
        )
        filt_array = signal.filtfilt(filt, 1.0, array)
    return filt_array


def fir_zero_2(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    high_width: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
    low_width: Union[int, float, None] = None,
    window: str = "hann",
):
    check_fir_filter_input(high_pass, high_width, low_pass, low_width, sample_rate)
    grp_delay = int(0.5 * (order - 1))
    if high_pass is not None and low_pass is not None:
        filt = signal.firwin2(
            order,
            freq=[
                0,
                high_pass - high_width,
                high_pass,
                low_pass,
                low_pass + low_width,
                sample_rate / 2,
            ],
            gain=[0, 0, 1, 1, 0, 0],
            window=window,
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(filt, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    elif high_pass is not None and low_pass is None:
        hi = signal.firwin2(
            order,
            [0, high_pass - high_width, high_pass, sample_rate / 2],
            gain=[0, 0, 1, 1],
            window=window,
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(hi, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    elif high_pass is None and low_pass is not None:
        lo = signal.firwin2(
            order,
            [0, low_pass, low_pass + low_width, sample_rate / 2],
            gain=[1, 1, 0, 0],
            window=window,
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(lo, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    return filt_array


def remez_1(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    high_width: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
    low_width: Union[int, float, None] = None,
):
    check_fir_filter_input(high_pass, high_width, low_pass, low_width, sample_rate)
    if high_pass is not None and low_pass is not None:
        filt = signal.remez(
            order,
            [
                0,
                high_pass - high_width,
                high_pass,
                low_pass,
                low_pass + low_width,
                sample_rate / 2,
            ],
            [0, 1, 0],
            fs=sample_rate,
        )
        filt_acq = signal.filtfilt(filt, 1.0, array)
    elif high_pass is not None and low_pass is None:
        hi = signal.remez(
            order,
            [0, high_pass - high_width, high_pass, sample_rate / 2],
            [0, 1],
            fs=sample_rate,
        )
        filt_acq = signal.filtfilt(hi, 1.0, array)
    elif high_pass is None and low_pass is not None:
        lo = signal.remez(
            order,
            [0, low_pass, low_pass + low_width, sample_rate / 2],
            [1, 0],
            fs=sample_rate,
        )
        filt_acq = signal.filtfilt(lo, 1.0, array)
    return filt_acq


def remez_2(
    array: Union[np.ndarray, list],
    order: int,
    sample_rate: Union[int, float],
    high_pass: Union[int, float, None] = None,
    high_width: Union[int, float, None] = None,
    low_pass: Union[int, float, None] = None,
    low_width: Union[int, float, None] = None,
):
    check_fir_filter_input(high_pass, high_width, low_pass, low_width, sample_rate)
    grp_delay = int(0.5 * (order - 1))
    if high_pass is not None and low_pass is not None:
        filt = signal.remez(
            numtaps=order,
            bands=[
                0,
                high_pass - high_width,
                high_pass,
                low_pass,
                low_pass + low_width,
                sample_rate / 2,
            ],
            desired=[0, 1, 0],
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(filt, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    elif high_pass is not None and low_pass is None:
        hi = signal.remez(
            order,
            [0, high_pass - high_width, high_pass, sample_rate / 2],
            [0, 1],
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(hi, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    elif high_pass is None and low_pass is not None:
        lo = signal.remez(
            order,
            [0, low_pass, low_pass + low_width, sample_rate / 2],
            [1, 0],
            fs=sample_rate,
        )
        acq1 = np.hstack((array, np.zeros(grp_delay)))
        filt_acq = signal.lfilter(lo, 1.0, acq1)
        filt_array = filt_acq[grp_delay:]
    return filt_array


def savgol_filt(array: Union[np.ndarray, list], order: int, polyorder: int):
    if isinstance(polyorder, float):
        polyorder = int(polyorder)
    filtered_array = signal.savgol_filter(array, order, polyorder, mode="nearest")
    return filtered_array


def ewma_filt(array: Union[np.ndarray, list], window: int, sum_proportion: float):
    alpha = 1 - np.exp(np.log(1 - sum_proportion) / window)
    b = [alpha]
    a = [1, alpha - 1]
    filtered = signal.filtfilt(b, a, array)
    return filtered


def ewma_afilt(array: Union[np.ndarray, list], window: int, sum_proportion: float):
    alpha = 1 - np.exp(np.log(1 - sum_proportion) / window)
    num = np.power(1.0 - alpha, np.arange(window + 1))
    b = num / np.sum(num)
    a = 1
    filtered = signal.filtfilt(b, a, array)
    return filtered
