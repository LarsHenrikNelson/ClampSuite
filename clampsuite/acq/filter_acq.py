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

from ..types import Filter


class FilterAcq:
    def __init__(self, filter: Filter):
        self.filter = filter

    def analyze(self, array) -> None:
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
        if self.window == "gaussian" or self.window == "kaiser":
            window = (self.window, self.beta_sigma)
        else:
            window = self.window

        if self.filter_type == "median":
            output = median_filter(array=array, order=self.order)
        elif self.filter_type == "bessel":
            output = bessel(
                array=array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "bessel_zero":
            output = bessel_zero(
                array=array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "butterworth":
            output = butterworth(
                array=array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "butterworth_zero":
            output = butterworth_zero(
                array=array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                low_pass=self.low_pass,
            )
        elif self.filter_type == "fir_zero_1":
            output = fir_zero_1(
                array=array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=window,
            )
        elif self.filter_type == "fir_zero_2":
            output = fir_zero_2(
                array=array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=window,
            )
        elif self.filter_type == "remez_1":
            output = remez_1(
                array=array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
            )
        elif self.filter_type == "remez_2":
            output = remez_2(
                array=array,
                sample_rate=self.sample_rate,
                order=self.order,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
            )
        elif self.filter_type == "savgol":
            output = savgol_filt(
                array=array, order=self.order, polyorder=self.polyorder
            )

        elif self.filter_type == "None":
            output = array.copy()

        elif self.filter_type == "subtractive":
            array = fir_zero_2(
                array,
                order=self.order,
                sample_rate=self.sample_rate,
                high_pass=self.high_pass,
                high_width=self.high_width,
                low_pass=self.low_pass,
                low_width=self.low_width,
                window=window,
            )
            output = array - array

        elif self.filter_type == "ewma":
            output = ewma_filt(
                array=array, window=self.order, sum_proportion=self.polyorder
            )
        elif self.filter_type == "ewma_a":
            output = ewma_afilt(
                array=array, window=self.order, sum_proportion=self.polyorder
            )
        return output
