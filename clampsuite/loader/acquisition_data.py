from dataclasses import dataclass, field
import numpy as np
from ..preprocess.base import Preprocessor


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
    gain: float = 1.0
    units: str = "mV"
    _preprocessors: list[Preprocessor] = field(default_factory=list)

    @property
    def s_r_c(self):
        return self.fs / 1000

    @property
    def acquisition(self) -> np.ndarray:
        data = self.array[: self.rc_check_pulse_start_index] * self.gain

        for preprocessor in self._preprocessors:
            data = preprocessor.process(data, self.fs)
        return data

    def clear_preprocessors(self) -> None:
        """Remove all preprocessing steps."""
        self._preprocessors.clear()

    def add_preprocessor(self, preprocessor: Preprocessor) -> "AcquisitionData":
        """Add a preprocessing step. Returns self for chaining."""
        self._preprocessors.append(preprocessor)
        return self
