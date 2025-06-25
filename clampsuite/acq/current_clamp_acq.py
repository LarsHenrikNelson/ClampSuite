from typing import Literal, Union

import numpy as np
from scipy import signal

from ..functions.current_clamp import (
    SPIKE_PARAMS,
    ThresholdType,
    adaptation_index,
    ai_sfa,
    coefficient_of_variation,
    divisor_sfa,
    find_all_ahps,
    find_all_spk_auc,
    find_all_spk_thresholds,
    find_all_spk_velocities,
    find_all_spk_widths,
    local_sfa,
    voltage_sag,
)
from ..functions.general import baseline_stability, delta


class CurrentClampAcq:
    def __init__(self, array: np.ndarray, fs: float, pulse_amp: float, epoch: int = 0):
        self.array = array
        self.fs = fs
        self.s_r_c = fs / 1000
        self.pulse_amp = pulse_amp

        self._analysis_variables = {}
        self._analysis_variables["baseline_v"] = np.nan
        self._analysis_variables["delta_v"] = np.nan
        self._analysis_variables["hertz"] = 0.0
        self._analysis_variables["iei"] = 0.0
        self._analysis_variables["peak_index"] = np.array([])
        self._analysis_variables["peak_voltages"] = np.array([])
        self._analysis_variables["spike_number"] = np.array([])
        self._analysis_variables["mem_tau_est"] = np.nan
        self._analysis_variables["sag"] = np.nan
        self._analysis_variables["sag_index"] = np.nan
        self._analysis_variables["baseline_stability"] = np.nan
        self._analysis_variables["rebound_spike"] = 0
        self._analysis_variables["local_sfa"] = np.nan
        self._analysis_variables["divisor_sfa"] = np.nan
        self._analysis_variables["ai_sfa"] = np.nan
        self._analysis_variables["adaptation"] = np.nan
        self._analysis_variables["coefficient_of_variation"] = np.nan
        self._analysis_variables["epoch"] = epoch

        for i in SPIKE_PARAMS:
            self._analysis_variables[i] = np.array([])

    def analyze(
        self,
        baseline_start: int = 0,
        baseline_end: int = 3000,
        pulse_start: int = 3000,
        pulse_end: int = 10000,
        min_spike_voltage: Union[int, float] = 0,
        threshold_method: ThresholdType = "third_derivative",
        min_spikes: int = 2,
        side: Literal["left", "right"] = "right",
        proportion: float = 0.5,
    ):
        if pulse_end < pulse_start:
            raise ValueError("pulse_end must be greater than pulse_start")
        if baseline_end < baseline_start:
            raise ValueError("baseline_end must be greater than baseline_start")
        self.min_spike_voltage = min_spike_voltage
        self.threshold_method = threshold_method
        self.min_spikes = min_spikes
        self.proportion = proportion
        self.side = side
        self.baseline_start = baseline_start
        self.baseline_end = baseline_end
        self.pulse_end = pulse_end
        self.pulse_start = pulse_start

        # Analysis functions
        self._analysis_variables["baseline_v"] = np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        peak_index, _ = signal.find_peaks(
            self.array[self.pulse_start : self.pulse_end],
            height=self.min_spike_voltage,
            width=int(0.5 * self.s_r_c),
        )
        peak_index += self.pulse_start
        self._analysis_variables["peak_index"] = peak_index
        self._analysis_variables["peak_voltages"] = self.array[peak_index]
        self._analysis_variables["spike_number"] = np.arange(1, peak_index.size + 1)
        self._analysis_variables["hertz"] = len(peak_index) / (
            (self.pulse_end - self.pulse_start) / self.fs
        )
        if len(peak_index) > 1:
            self._analysis_variables["iei"] = np.mean(np.diff(peak_index / self.fs))
        if len(peak_index) > 0:
            self._analysis_variables.update(
                find_all_spk_thresholds(
                    self.array,
                    peak_index,
                    self.pulse_start,
                    self.threshold_method,
                )
            )
            self._analysis_variables.update(
                find_all_ahps(self.array, peak_index, self.pulse_end)
            )
            self._analysis_variables.update(
                find_all_spk_widths(
                    self.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables.update(
                find_all_spk_auc(
                    self.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables.update(
                find_all_spk_velocities(
                    self.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables["local_sfa"] = local_sfa(peak_index)
            self._analysis_variables["divisor_sfa"] = divisor_sfa(peak_index)
            self._analysis_variables["ai_sfa"] = ai_sfa(peak_index)
            self._analysis_variables["adaptation"] = adaptation_index(peak_index)
            self._analysis_variables["cv"] = coefficient_of_variation(peak_index)

        self._analysis_variables["delta_v"] = self.get_delta_v(peak_index)

        if self.pulse_amp < 0:
            self._analysis_variables.update(
                voltage_sag(self.array, self.pulse_start, self.pulse_end)
            )
        else:
            self._analysis_variables["sag"] = None
            self._analysis_variables["sag_index"] = None

        self._analysis_variables["baseline_stability"] = baseline_stability(
            self.array, self.pulse_start, self.pulse_end
        )

        rebound_spikes, _ = signal.find_peaks(
            self.array[self.pulse_end :],
            height=self.min_spike_voltage,
            prominence=int(1 * self.s_r_c),
        )
        if len(rebound_spikes) > 0:
            self._analysis_variables["rebound_spike"] = len(rebound_spikes)

    def get_delta_v(self, peaks):
        """This function finds the delta-v for a pulse. It simply takes the mean
        value from the pulse start to end for pulses without spikes. For
        pulses with spikes it takes the mode of the moving mean.
        """

        if len(peaks) == 0:
            delta_v = delta(
                self.array,
                self.pulse_start,
                self.pulse_end,
                self.proportion,
                self.side,
            )
        else:
            index = self._analysis_variables["threshold_index"][0]
            delta_v = self.array[index] - self._analysis_variables["baseline_v"]
        # if self.ramp == "0":
        #     if len(self.peak_index) > 0:
        #         delta_v = delta(
        #             self.array,
        #             self.pulse_start,
        #             self.pulse_end,
        #             self.proportion,
        #             self.side,
        #         )
        #     else:
        #         index = self._analysis_variables["threshold_index"][0]
        #         delta_v = self.array[index] - self._analysis_variables["baseline_v"]
        # elif self.ramp == "1":
        #     delta_v = np.nan
        return delta_v

    def get_ramp_rheo(self):
        """
        This function gets the ramp rheobase. The ramp pulse is recreated
        based on the values in the matfile and then the current is extracted.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if self.ramp == "1":
            if self.rheo_x is np.nan:
                self.ramp_rheo = np.nan
            else:
                # Create the ramp current values.
                ramp_values = np.linspace(
                    0, self.pulse_amp, num=self.pulse_end - self.pulse_start
                )

                # Create an array of zeros where the ramp will be placed.
                ramp_array = np.zeros(len(self.array))

                # Insert the ramp into the array of zeros.
                ramp_array[self.pulse_start : self.pulse_end] = ramp_values

                # Extract the ramp rheobase.
                self.ramp_rheo = ramp_array[self.rheo_x]
        else:
            self.ramp_rheo = np.nan

    def spike_half_widths(self):
        x = (
            np.array(
                [
                    self._analysis_variables["hw_left"],
                    self._analysis_variables["hw_right"],
                ]
            )
            / self.s_r_c
        ).T
        y = np.array(
            [self._analysis_variables["hw_y"], self._analysis_variables["hw_y"]]
        ).T
        return x, y

    def spike_widths(self):
        x = (
            np.array(
                [
                    self._analysis_variables["fw_left"],
                    self._analysis_variables["fw_right"],
                ]
            )
            / self.s_r_c
        ).T
        y = np.array(
            [self._analysis_variables["fw_y"], self._analysis_variables["fw_y"]]
        ).T
        return x, y

    def peaks(self):
        x = self._analysis_variables["peak_index"] / self.s_r_c
        y = self._analysis_variables["peak_voltages"]
        return x, y

    def ahps(self):
        x = self._analysis_variables["ahp_index"]
        y = self._analysis_variables["ahp_voltages"]
        return x, y

    def thresholds(self):
        x = self._analysis_variables["threshold_index"] / self.s_r_c
        y = self.array[self._analysis_variables["threshold_index"]]
        return x, y

    def min_velocity(self):
        return self._analysis_variables["min_velocity"], self._analysis_variables[
            "min_velocity_index"
        ] / self.s_r_c

    def max_velocity(self):
        return self._analysis_variables["max_velocity"], self._analysis_variables[
            "max_velocity_index"
        ] / self.s_r_c

    def acquisition(self):
        return np.arange(self.array.size) / self.s_r_c, self.array

    def derivative(self):
        return np.arange(self.array.size) / self.s_r_c, -1 * np.gradient(self.array)

    def acq_data(self) -> dict:
        return self._analysis_variables.copy()
