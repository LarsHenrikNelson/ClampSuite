import math
from typing import Union, Literal

import numpy as np
from numpy.random import default_rng
from scipy import fft

from clampsuite.functions.template_psc import create_template


def round_sig(x, sig=2):
    if np.isnan(x):
        return np.nan
    elif x == 0:
        return 0
    elif x != 0 or not np.isnan(x):
        temp = math.floor(math.log10(abs(x)))
        if np.isnan(temp):
            return round(x, 0)
        else:
            return round(x, sig - int(temp) - 1)


def white_noise_array(N):
    rng = default_rng(42)
    X_white = fft.rfft(rng.standard_normal(N))
    S = fft.rfftfreq(N)
    # Normalize S
    S = S / np.sqrt(np.mean(S**2))
    X_shaped = X_white * S
    return fft.irfft(X_shaped)


def create_acq_data(
    array_len: int = 100000,
    acq_num: int = 1,
    acq_name: str = "AD0_1",
    epoch: int = 1,
    sample_rate: Union[float, int] = 10000,
    pulse_start: Union[int, float] = 0.0,
    pulse_end: Union[int, float] = 10000,
    timestamp: Union[int, float] = 10110010,
    pulse_amp: Union[float, int] = 0.0,
    ramp: int = "0",
    ai: str = "0",
    rc_amp: Union[float, int] = 0.0,
    rc_start: Union[float, int] = 0.0,
    rc_end: Union[float, int] = 0.0,
):
    data = {
        "name": acq_name,
        "acq_number": acq_num,
        "epoch": epoch,
        "array": white_noise_array(array_len),
        "sample_rate": sample_rate,
        "s_r_c": sample_rate / 1000,
        "pulse_start": pulse_start,
        "_pulse_start": int(pulse_start * (sample_rate / 1000)),
        "pulse_end": pulse_end,
        "_pulse_end": int(pulse_end * (sample_rate / 1000)),
        "ramp": ramp,
        "timestamp": timestamp,
        "pulse_amp": pulse_amp,
        "ai": ai,
        "rc_amp": rc_amp,
        "rc_start": rc_start,
        "_rc_start": int(rc_start * (sample_rate / 1000)),
        "rc_end": rc_end,
        "_rc_end": int(rc_end * (sample_rate / 1000)),
    }
    return data


def create_event_array(
    sample_rate: int,
    event_length: int = 300,
    num_events: int = 10,
    direction: Literal["positive", "negative"] = "positive",
):
    # rng = np.random.default_rng(42)
    event_array = white_noise_array(10 * sample_rate)

    # events = rng.integers(0, num_events, size=10)
    events = np.array(
        [77395, 65457, 43887, 43301, 85859, 8594, 69736, 20146, 9417, 52647]
    )

    # amplitudes = rng.lognormal(2.5, 0.5, 10)
    amplitudes = np.array(
        [
            11.50781387,
            8.00384268,
            8.06682032,
            16.86594321,
            17.6657385,
            15.98382277,
            8.73418945,
            13.681994,
            12.91439918,
            13.59013685,
        ]
    )

    # taus = rng.normal(5, 1.2, 10)
    taus = np.array(
        [
            4.6698293,
            6.79392957,
            3.96100266,
            6.16193403,
            2.98055627,
            4.59813796,
            5.19530368,
            5.7034668,
            5.8534719,
            5.95201668,
        ]
    )

    # rises = rng.normal(0.3, 0.05, 10)
    rises = np.array(
        [
            0.27863737,
            0.30792698,
            0.33127952,
            0.28453267,
            0.32283876,
            0.2669037,
            0.28184731,
            0.28091311,
            0.24020802,
            0.32434862,
        ]
    )
    s_r_c = 10000 / 1000
    if direction == "negative":
        amplitudes *= -1
    for event_index, amp, tau, rise in zip(events, amplitudes, taus, rises):
        temp_event = create_template(
            amp, rise, tau, length=event_length / s_r_c, sample_rate=sample_rate
        )
        if (event_index + temp_event.size) < event_array.size:
            event_array[event_index : event_index + temp_event.size] += temp_event
    return event_array
