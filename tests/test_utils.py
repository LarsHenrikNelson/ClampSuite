from typing import Union

import numpy as np
from numpy.random import default_rng
from scipy import fft


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
        "acq_num": acq_num,
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
