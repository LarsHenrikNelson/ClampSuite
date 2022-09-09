import numpy as np
from scipy import signal

from ..functions.filtering_functions import (
    median_filter,
    remez_1,
    remez_2,
    fir_zero_1,
    fir_zero_2,
    bessel,
    butterworth,
    elliptic,
    bessel_zero,
    butterworth_zero,
    elliptic_zero,
)

from . import base_acq


class FilterAcq(base_acq.BaseAcq, analysis="filter"):

    """
    This is the base class for acquisitions. It returns the array from a
    matfile and filters the array.

    To remove DC from the signal, signal is baselined to the mean of the
    chosen baseline of the array. A highpass filter is usually not needed to
    for offline analysis because the signal can baselined using the mean.
    """

    def analyze(
        self,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=800,
        filter_type="None",
        order=None,
        high_pass=None,
        high_width=None,
        low_pass=None,
        low_width=None,
        window=None,
        polyorder=None,
    ):
        self.sample_rate = sample_rate
        self.baseline_start = baseline_start
        self.baseline_end = baseline_end
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self.filter_array()
        self.s_r_c = sample_rate / 1000

    def filter_array(self):
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

        if self.filter_type == "median":
            self.filtered_array = median_filter(self.baselined_array, self.order)
        elif self.filter_type == "bessel":
            self.filtered_array = bessel(
                self.baselined_array,
                self.order,
                self.sample_rate,
                self.high_pass,
                self.low_pass,
            )
        elif self.filter_type == "bessel_zero":
            self.filtered_array = bessel_zero(
                self.baselined_array,
                self.order,
                self.sample_rate,
                self.high_pass,
                self.low_pass,
            )
        elif self.filter_type == "butterworth":
            self.filtered_array = butterworth(
                self.baselined_array,
                self.order,
                self.sample_rate,
                self.high_pass,
                self.low_pass,
            )
        elif self.filter_type == "butterworth_zero":
            self.filtered_array = butterworth_zero(
                self.baselined_array,
                self.order,
                self.sample_rate,
                self.high_pass,
                self.low_pass,
            )
        elif self.filter_type == "fir_zero_1":
            self.filtered_array = fir_zero_1(
                self.baselined_array,
                self.sample_rate,
                self.order,
                self.high_pass,
                self.high_width,
                self.low_pass,
                self.low_width,
                self.window,
            )
        elif self.filter_type == "fir_zero_2":
            self.filtered_array = fir_zero_2(
                self.baselined_array,
                self.sample_rate,
                self.order,
                self.high_pass,
                self.high_width,
                self.low_pass,
                self.low_width,
                self.window,
            )
        elif self.filter_type == "remez_1":
            self.filtered_array = remez_1(
                self.baselined_array,
                self.sample_rate,
                self.order,
                self.high_pass,
                self.high_width,
                self.low_pass,
                self.low_width,
            )
        elif self.filter_type == "remez_2":
            self.filtered_array = remez_2(
                self.baselined_array,
                self.sample_rate,
                self.order,
                self.high_pass,
                self.high_width,
                self.low_pass,
                self.low_width,
            )
        elif self.filter_type == "savgol":
            self.filtered_array = signal.savgol_filter(
                self.baselined_array, self.order, self.polyorder, mode="nearest"
            )
        elif self.filter_type == "None":
            self.filtered_array = self.baselined_array.copy()

        elif self.filter_type == "subtractive":
            array = fir_zero_2(
                self.baselined_array,
                self.sample_rate,
                self.order,
                self.high_pass,
                self.high_width,
                self.low_pass,
                self.low_width,
                self.window,
            )
            self.filtered_array = self.baselined_array - array

        elif self.filter_type == "ewma":
            alpha = 1 - np.exp(np.log(1 - self.polyorder) / self.order)
            b = [alpha]
            a = [1, alpha - 1]
            self.fitered_array = signal.filtfilt(b, a, array)

    def x_array(self):
        return np.arange(len(self.filtered_array)) / self.s_r_c
