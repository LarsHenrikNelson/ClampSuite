from dataclasses import dataclass
from typing import Literal, NamedTuple, TypeAlias

import numpy as np
from scipy import signal

from .base import Preprocessor, register_preprocessor

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


class FilterError(NamedTuple):
    passed: bool
    error_message: str


def check_fir_filter_input(high_pass, high_width, low_pass, low_width, fs):
    if high_pass is not None and high_width is not None:
        if high_pass < high_width:
            return FilterError(False, "High_pass must be large than high_width.")
        if high_pass < 0 or high_width < 0:
            return FilterError(False, "Filter settings cannot be less than 0.")
        if high_pass > (fs / 2) or high_width > (fs / 2):
            return FilterError(
                False, "Filter settings cannot be greater than the sample rate."
            )
    if low_pass is not None and low_width is not None:
        if (low_pass + low_width) >= (fs / 2):
            return FilterError(False, "Low_pass + low_width must be less than fs")
        if low_pass < 0 or low_width < 0:
            return FilterError(False, "Filter settings cannot be less than 0.")
        if low_pass > (fs / 2) or low_width > (fs / 2):
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
        if high_pass > (fs / 2):
            return FilterError(False, "High pass must be greater than half the fs")
        if high_pass == 0:
            return FilterError(False, "High_pass must be greater than 0")
    return FilterError(True, "")


def check_iir_filter_input(high_pass, low_pass, fs):
    if high_pass is None and low_pass is None:
        return FilterError(False, "High_pass or low_pass or both must be provided.")
    if high_pass is not None:
        if high_pass > fs:
            return FilterError(False, "High_pass must be less than fs.")
    if low_pass is not None:
        if low_pass > fs:
            return FilterError(False, "High_pass must be less than fs.")
    if high_pass is not None and low_pass is not None:
        if low_pass < high_pass:
            return FilterError(False, "High_pass must be less than low_pass.")
    return FilterError(True, "")


def zero_phase_convolve(b: np.ndarray, a: None, array: np.ndarray):
    output = np.convolve(array, b, mode="full")
    wlen = b.size // 2
    output = output[wlen : array.size + wlen]
    return output


@register_preprocessor("filter")
@dataclass
class MedianFilter(Preprocessor):
    filter_family: str = "median"
    filter_type: str = "median"
    order: int = 4

    def process(self, array: np.ndarray | list, fs: float | int):
        if isinstance(self.order, float):
            order = int(self.order)
        filt_array = signal.medfilt(array, order)
        return filt_array


@register_preprocessor("filter")
@dataclass
class NoFilter(Preprocessor):
    filter_family: str = "None"

    def process(self, array: np.ndarray, fs: float | int):
        return array


@register_preprocessor("filter")
@dataclass
class EWMAFilter(Preprocessor):
    filter_family: str = "ewma"
    filter_type: Literal["ewma", "ewma_a"] = "ewma"
    window: int = 30
    sum_proportion: float = 0.5

    def ewma_filter(self, array: np.ndarray | list, fs: float | int):
        alpha = 1 - np.exp(np.log(1 - self.sum_proportion) / self.window)
        if self.filter_type == "ewma_a":
            num = np.power(1.0 - alpha, np.arange(self.window + 1))
            b = num / np.sum(num)
        else:
            b = [alpha]
        a = 1
        filtered = signal.filtfilt(b, a, array)
        return filtered


@register_preprocessor("filter")
@dataclass
class SavgolFilter(Preprocessor):
    filter_family: str = "savgol"
    filter_type = "savgol"
    order: int = 11
    polyorder: int = 3

    def process(self, array: np.ndarray | list, fs: float | int):
        filtered_array = signal.savgol_filter(
            array, self.order, self.polyorder, mode="nearest"
        )
        return filtered_array


@register_preprocessor("filter")
@dataclass
class FIRFilter(Preprocessor):
    filter_family: str = "fir"
    filter_type: Literal["fir", "fir_zero"] = "fir_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200
    window: Windows = "hann"
    beta_sigma: float | None = None

    def process(self, array: np.ndarray, fs: float | int):
        check = check_fir_filter_input(
            self.high_pass,
            self.high_width,
            self.low_pass,
            self.low_width,
            fs,
        )
        if not check.passed:
            return check
        if "zero" in self.filter_type:
            filt_func = signal.filtfilt
        else:
            filt_func = zero_phase_convolve
        if self.beta_sigma is not None and self.filter_type == "kaiser":
            window = (self.filter_type, self.beta_sigma)
        elif self.beta_sigma is None and self.filter_type == "kaiser":
            window = ("kaiser", signal.kaiser_beta(-60))
        else:
            window = self.window
        if self.high_pass is not None and self.low_pass is not None:
            filt = signal.firwin2(
                self.order,
                freq=[
                    0,
                    self.high_pass - self.high_width,
                    self.high_pass,
                    self.low_pass,
                    self.low_pass + self.low_width,
                    fs / 2,
                ],
                gain=[0, 0, 1, 1, 0, 0],
                window=window,
                fs=fs,
            )
            filt_array = filt_func(filt, 1.0, array)
        elif self.high_pass is not None and self.low_pass is None:
            filt = signal.firwin2(
                self.order,
                freq=[
                    0,
                    self.high_pass - self.high_width,
                    self.high_pass,
                    fs / 2,
                ],
                gain=[0, 0, 1, 1],
                window=window,
                fs=fs,
            )
            filt_array = filt_func(filt, 1.0, array)
        elif self.high_pass is None and self.low_pass is not None:
            filt = signal.firwin2(
                self.order,
                freq=[
                    0,
                    self.low_pass,
                    self.low_pass + self.low_width,
                    fs / 2,
                ],
                gain=[1, 1, 0, 0],
                window=window,
                fs=fs,
            )
            filt_array = filt_func(filt, 1.0, array)
        return filt_array


@register_preprocessor("filter")
@dataclass
class RemezFilter(Preprocessor):
    filter_family: str = "remez"
    filter_type: Literal["remez", "remez_zero"] = "remez_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200

    def process(self, array: np.ndarray | list, fs: float | int):
        check = check_fir_filter_input(
            self.high_pass,
            self.high_width,
            self.low_pass,
            self.low_width,
            fs,
        )
        if not check.passed:
            return check
        if self.high_pass is not None and self.low_pass is not None:
            filt = signal.remez(
                self.order,
                [
                    0,
                    self.high_pass - self.high_width,
                    self.high_pass,
                    self.low_pass,
                    self.low_pass + self.low_width,
                    fs / 2,
                ],
                [0, 1, 0],
                fs=fs,
            )
            filt_acq = signal.filtfilt(filt, 1.0, array)
        elif self.high_pass is not None and self.low_pass is None:
            hi = signal.remez(
                self.order,
                [
                    0,
                    self.high_pass - self.high_width,
                    self.high_pass,
                    fs / 2,
                ],
                [0, 1],
                fs=fs,
            )
            filt_acq = signal.filtfilt(hi, 1.0, array)
        elif self.high_pass is None and self.low_pass is not None:
            lo = signal.remez(
                self.order,
                [
                    0,
                    self.low_pass,
                    self.low_pass + self.low_width,
                    fs / 2,
                ],
                [1, 0],
                fs=fs,
            )
            filt_acq = signal.filtfilt(lo, 1.0, array)
        return filt_acq


@register_preprocessor("filter")
@dataclass
class IIRFilter(Preprocessor):
    filter_family: str = "iir"
    filter_type: Literal["bessel", "butterworth", "bessel_zero", "butterworth_zero"] = (
        "butterworth_zero"
    )
    order: int = 4
    high_pass: int | float | None = None
    low_pass: int | float | None = 500

    def process(self, array: np.ndarray | list, fs: float | int):
        check = check_iir_filter_input(
            self.high_pass,
            self.low_pass,
            fs,
        )
        if not check.passed:
            return check
        if "bessel" in self.filter_type:
            filt_design = signal.bessel
        else:
            filt_design = signal.butter

        if "zero" in self.filter_type:
            filt_func = signal.sosfiltfilt
        else:
            filt_func = signal.sosfilt

        if self.high_pass is not None and self.low_pass is not None:
            sos = filt_design(
                self.order,
                Wn=[self.high_pass, self.low_pass],
                btype="bandpass",
                output="sos",
                fs=fs,
            )
            filt_array = filt_func(sos, array)
            return filt_array
        elif self.high_pass is not None and self.low_pass is None:
            sos = filt_design(
                self.order,
                Wn=self.high_pass,
                btype="highpass",
                output="sos",
                fs=fs,
            )
            filt_array = filt_func(sos, array)
        elif self.high_pass is None and self.low_pass is not None:
            sos = filt_design(
                self.order,
                Wn=self.low_pass,
                btype="lowpass",
                output="sos",
                fs=fs,
            )
            filt_array = filt_func(sos, array)
        return filt_array


Filters: TypeAlias = (
    MedianFilter
    | EWMAFilter
    | SavgolFilter
    | FIRFilter
    | IIRFilter
    | RemezFilter
    | NoFilter
)
