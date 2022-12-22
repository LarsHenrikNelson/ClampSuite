from typing import Literal, Union

import numpy as np

from ..functions.filtering_functions import (
    bessel,
    bessel_zero,
    butterworth,
    butterworth_zero,
    ewma_afilt,
    ewma_filt,
    fir_zero_1,
    fir_zero_2,
    median_filter,
    remez_1,
    remez_2,
    savgol_filt,
)

from . import acquisition


class FilterAcq(acquisition.Acquisition, analysis="filter"):

    """
    This is the base class for acquisitions. It returns the array from a
    matfile and filters the array.

    To remove DC from the signal, signal is baselined to the mean of the
    chosen baseline of the array. A highpass filter is usually not needed to
    for offline analysis because the signal can baselined using the mean.
    """

    def analyze(
        self,
        baseline_start: Union[int, float] = 0,
        baseline_end: Union[int, float] = 800,
        filter_type: Literal[
            "remez_2",
            "remez_1",
            "fir_zero_2",
            "fir_zero_1",
            "ewma",
            "ewma_a",
            "savgol",
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
            "None",
        ] = "fir_zero_2",
        order: Union[None, int] = None,
        high_pass: Union[int, float, None] = None,
        high_width: Union[int, float, None] = None,
        low_pass: Union[int, float, None] = None,
        low_width: Union[int, float, None] = None,
        window: Literal[
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
            "exponential",
        ] = "hann",
        polyorder: Union[int, None] = None,
    ):
        self.baseline_start = int(baseline_start * (self.sample_rate / 1000))
        self.baseline_end = int(baseline_end * (self.sample_rate / 1000))
        self.filter_type = filter_type
        order = self.order = order
        high_pass = self.high_pass = high_pass
        high_width = self.high_width = high_width
        low_pass = self.low_pass = low_pass
        low_width = self.low_width = low_width
        window = self.window = window
        self.polyorder = polyorder
        self.filter_array(self.array)

    def filter_array(self, array):
        """
        This funtion filters the array of data, with several different types
        of filters.

        median: is a filter that return the median for a specified window
        size. Needs an odd numbered window.

        bessel: modeled after the traditional analog minimum phase filter.
        Needs to have order, sample rate, high pass and low pass settings.

        fir_zero_1: zero phase phase filter that filter backwards and forwards
        to achieve zero phase. The magnitude of the filter is sqaured due to
        the backwards and forwards filtering. Needs sample rate, order, high
        pass, width of the cutoff region, low pass, width of the low pass
        region and the type of window. Windows that are currently supported
        are hann, hamming, nutall, flattop, blackman. Currently does not
        support a kaiser filter.

        fir_zero_2: An almost zero phase filter that filters only in the
        forward direction. The zero phase filtering only holds true for odd
        numbered orders. The zero phase filtering is achieved by adding a set
        amount of values ((order-1)/2 = 5) equal to the last value of the array to the
        ending of the array. After the signal has been filtered, the same
        same number of values are removed from the beginning of the array thus
        yielding a zero phase filter.

        remez_1: A zero phase FIR filter that does not rely on windowing. The
        magnitude of the filter is squared since it filters forward and
        backwards. Uses the same arguments as fir_zero_1/2, but does not need
        a window type.

        remez_2: An almost zero phase filter similar fir_zero_2 except that
        it does not need a window type.

        savgol: This a windowed polynomial filter called the Savitsky-Golay
        filter. It fits a polynomial of specified number to a specified
        window. Please note the order needs to be larger than the polyorder.

        none: No filtering other than baselining the array.

        subtractive: This filter is more experimental. Essentially you filter
        the array to create an array of frequency that you do not want then
        subtract that from the unfiltered array to create a filtered array
        based on subtraction. Pretty esoteric and is more for learning
        purposes.
        """
        baselined_array = array - np.mean(
            array[self.baseline_start : self.baseline_end]
        )
        if self.filter_type == "median":
            self.filtered_array = median_filter(array=baselined_array, order=self.order)
        elif self.filter_type == "bessel":
            self.filtered_array = bessel(
                array=baselined_array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "bessel_zero":
            self.filtered_array = bessel_zero(
                array=baselined_array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "butterworth":
            self.filtered_array = butterworth(
                array=baselined_array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "butterworth_zero":
            self.filtered_array = butterworth_zero(
                array=baselined_array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "fir_zero_1":
            self.filtered_array = fir_zero_1(
                array=baselined_array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=self.window,
            )
        elif self.filter_type == "fir_zero_2":
            self.filtered_array = fir_zero_2(
                array=baselined_array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=self.window,
            )
        elif self.filter_type == "remez_1":
            self.filtered_array = remez_1(
                array=baselined_array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
            )
        elif self.filter_type == "remez_2":
            self.filtered_array = remez_2(
                array=baselined_array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
            )
        elif self.filter_type == "savgol":
            self.filtered_array = savgol_filt(
                array=baselined_array, order=self.order, polyorder=self.polyorder
            )

        elif self.filter_type == "None":
            self.filtered_array = baselined_array.copy()

        elif self.filter_type == "subtractive":
            array = fir_zero_2(
                baselined_array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=self.window,
            )
            self.filtered_array = baselined_array - array

        elif self.filter_type == "ewma":
            self.filtered_array = ewma_filt(
                array=baselined_array, window=self.order, sum_proportion=self.polyorder
            )
        elif self.filter_type == "ewma_a":
            self.filtered_array = ewma_afilt(
                array=baselined_array, window=self.order, sum_proportion=self.polyorder
            )

    def plot_acq_x(self) -> np.ndarray:
        return np.arange(len(self.filtered_array)) / self.s_r_c

    def plot_acq_y(self) -> np.ndarray:
        return self.filtered_array
