import numpy as np


def calc_rs(acquisition, pulse_start, rc_duration, pulse_amp):
    rc_baseline = np.mean(acquisition[:pulse_start])
    if pulse_amp < 0:
        peak = (
            np.argmin(acquisition[pulse_start : pulse_start + rc_duration])
            + pulse_start
        )
    else:
        peak = (
            np.argmax(acquisition[pulse_start : pulse_start + rc_duration])
            + pulse_start
        )
    amp = acquisition[peak] - rc_baseline
    return np.abs(pulse_amp / amp * 1000)
