from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from ..preprocess.base import Preprocessor
from ..preprocess.detrend import Detrend
from ..preprocess.resample import Resample


@dataclass
class AcquisitionData:
    acq_number: int
    array: np.ndarray
    epoch: int
    name: str
    pulse_amp: float
    amp_start: float
    pulse_pattern: int
    rc_amp: float
    rc_check_pulse_end_index: int
    rc_check_pulse_start_index: int
    _fs: float = field(repr=False)
    _pulse_start_index: int = field(repr=False)
    _pulse_end_index: int = field(repr=False)
    time_stamp: str
    acq_type: Literal["step", "ramp", "other"] = "other"
    cycle: int = 0
    gain: float = 1.0
    units: str = "mV"

    _fs_multiplier: float = field(default=1.0, repr=False)

    _preprocessors: list[Preprocessor] = field(default_factory=list)

    @property
    def fs(self):
        return self._fs * self._fs_multiplier

    @property
    def pulse_start_index(self):
        return int(self._pulse_start_index * self._fs_multiplier)

    @property
    def pulse_end_index(self):
        return int(self._pulse_end_index * self._fs_multiplier)

    @property
    def s_r_c(self):
        return self.fs / 1000

    @property
    def acquisition(self) -> np.ndarray:
        if self.rc_check_pulse_start_index != self.rc_check_pulse_end_index:
            data = self.array[: self.rc_check_pulse_start_index] * self.gain
        else:
            data = self.array * self.gain

        for preprocessor in self._preprocessors:
            data = preprocessor(data, self.fs)
            if isinstance(preprocessor, Resample):
                self._fs_multiplier = preprocessor.fs_multiplier
        return data

    def get_baseline(self, step: int | None = None) -> np.ndarray:
        if self.rc_check_pulse_start_index != self.rc_check_pulse_end_index:
            data = self.array[: self.rc_check_pulse_start_index] * self.gain
        else:
            data = self.array * self.gain

        if step is None:
            step = len(self._preprocessors)
        for i in np.arange(step):
            data = self._preprocessors[i](data, self.fs)
            if isinstance(self._preprocessors[i], Detrend):
                baseline = self._preprocessors[i].baseline_
            if not isinstance(baseline, np.ndarray):
                baseline = np.full(baseline, data)
        return baseline

    def clear_preprocessors(self) -> None:
        """Remove all preprocessing steps."""
        self._preprocessors.clear()

    def add_preprocessor(
        self, preprocessor: Preprocessor | list[Preprocessor]
    ) -> "AcquisitionData":
        """Add a preprocessing step. Returns self for chaining."""
        if isinstance(preprocessor, Preprocessor):
            self._preprocessors.append(preprocessor)
        else:
            self._preprocessors.extend(preprocessor)
        return self
