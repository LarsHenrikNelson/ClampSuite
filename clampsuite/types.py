from typing import Literal, NamedTuple

import numpy as np

from .functions.current_clamp import ThresholdType


class CurrentClamp(NamedTuple):
    baseline_start: int
    baseline_end: int
    pulse_start: int
    pulse_end: int
    min_spike_voltage: float = 0
    threshold_method: ThresholdType = "third_derivative"
    min_spikes: int = 2
    side: Literal["left", "right"] = "left"
    proportion: float = 0.5
