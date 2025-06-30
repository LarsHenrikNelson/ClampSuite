from dataclasses import dataclass
import numpy as np


@dataclass
class AcquisitionData:
    acq_number: int
    array: np.ndarray
    epoch: int
    name: str
    pulse_amp: float
    pulse_end_index: int
    pulse_pattern: int
    pulse_start_index: int
    rc_amp: float
    rc_check_pulse_end_index: int
    rc_check_pulse_start_index: int
    fs: float
    time_stamp: str
    ramp: int = 0
    cycle: int = 0

    def s_r_c(self):
        return self.fs / 1000
