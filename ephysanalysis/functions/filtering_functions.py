#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 14:09:32 2022

@author: Lars
"""

import numpy as np
from scipy import signal
import patsy
from sklearn.linear_model import LinearRegression


def median_filter(array, order):
    filt_array = signal.medfilt(array, order)
    return filt_array


def bessel(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.bessel(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.bessel(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.bessel(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def bessel_zero(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.bessel(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.bessel(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.bessel(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def butterworth(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.butter(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.butter(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.butter(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def butterworth_zero(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.butter(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.butter(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.butter(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def elliptic(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.ellip(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.ellip(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.ellip(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfilt(sos, array)
    return filt_array


def elliptic_zero(array, order, sample_rate, highpass=None, lowpass=None):
    if highpass is not None and lowpass is not None:
        sos = signal.ellip(
            order,
            Wn=[highpass, lowpass],
            btype="bandpass",
            output="sos",
            fs=sample_rate,
        )
        filt_array = signal.sosfiltfilt(sos, array)
        return filt_array
    elif highpass is not None and lowpass is None:
        sos = signal.ellip(
            order, Wn=highpass, btype="highpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    elif highpass is None and lowpass is not None:
        sos = signal.ellip(
            order, Wn=lowpass, btype="lowpass", output="sos", fs=sample_rate
        )
        filt_array = signal.sosfiltfilt(sos, array)
    return filt_array


def fir_zero_1(
    array,
    sample_rate,
    order,
    high_pass=None,
    high_width=None,
    low_pass=None,
    low_width=None,
    window="hann",
):
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
    array,
    sample_rate,
    order,
    high_pass=None,
    high_width=None,
    low_pass=None,
    low_width=None,
    window="flattop",
):
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
    array,
    sample_rate,
    order,
    high_pass=None,
    high_width=None,
    low_pass=None,
    low_width=None,
):
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
    array,
    sample_rate,
    order,
    high_pass=None,
    high_width=None,
    low_pass=None,
    low_width=None,
):
    grp_delay = int(0.5 * (order - 1))
    if high_pass is not None and low_pass is not None:
        print("used")
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


def nat_spline_filt(array, order):
    # Good for finding baselines, but not great for filtering large arrays.
    x_array = np.arange(len(array))
    x_basis = patsy.cr(x_array, df=order, constraints="center")
    model = LinearRegression().fit(x_basis, array)
    y_hat = model.predict(x_basis)
    return y_hat


if __name__ == "__main__":
    fir_zero_2()
    fir_zero_1()
    bessel()
    median_filter()
    nat_spline_filt()
    remez_2()
    remez_1()
    bessel_zero()
    butterworth()
    butterworth_zero()
    elliptic()
    elliptic_zero()
