from typing import Literal

import numpy as np

from clampsuite.acq import (
    Acquisition,
    MiniAnalysisAcq,
)
from clampsuite.functions.template_psc import create_template
from .test_utils import white_noise_array


def create_event_array(
    sample_rate: int,
    length: int,
    event_length: int,
    direction: Literal["positive", "negative"] = "positive",
):
    # rng = default_rng(42)
    event_array = white_noise_array(length * sample_rate)

    # events = rng.integers(0, 10000 * 10, size=10)
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
    if direction == "negative":
        amplitudes *= -1
    for event_index, amp, tau, rise in zip(events, amplitudes, taus, rises):
        temp_event = create_template(amp, rise, tau, length=event_length)
        event_array[event_index : event_index + temp_event.size] += temp_event
    return event_array


def test_mini_acq():
    mini = Acquisition("mini")
    assert isinstance(mini, MiniAnalysisAcq)
