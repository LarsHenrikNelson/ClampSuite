import numpy as np


class RCCheck:
    def __init__(
        self,
        array: np.ndarray,
        fs: float,
        start: float,
        end: float,
        pulse_start: float,
        pulse_end: float,
        pulse_amplitude: float,
    ):
        self.array = array
        self.start = start
        self.end = end
        self.fs = fs
        self.pulse_start = pulse_start
        self.pulse_end = pulse_end
        self._pulse_start = int(pulse_start * fs / 1000)
        self._pulse_end = int(pulse_end * fs / 1000)
        self.pulse_amplitude = pulse_amplitude

    def calc_rs(self):
        rc_baseline = np.mean(self.array[: self._pulse_start])
        if self.pulse_amplitude < 0:
            peak = (
                np.argmin(self.array[self._pulse_start : self.pulse_end])
                + self._pulse_start
            )
        else:
            peak = (
                np.argmax(self.array[self._pulse_start : self.pulse_end])
                + self._pulse_start
            )
        amp = self.array[peak] - rc_baseline
        return peak
        self.access_resistance = np.abs(self.pulse_amplitude / amp * 1000)

    def calc_membrane_time_constant(self):
        pass

    def calc_membrane_resistance(self):
        pass

    def calc_membrane_capacitance(self):
        pass
