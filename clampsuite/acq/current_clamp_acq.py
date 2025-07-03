from typing import Literal, Union
from collections import defaultdict

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
    membrane_time_constant_deltav,
    membrane_time_constant_min,
)
from ..functions.general import baseline_stability, delta
from ..functions.utilities import map_keys
from ..loader.acquisition_data import AcquisitionData


class CurrentClampAcq:
    def __init__(self, acq_data: AcquisitionData):
        self.acq_data = acq_data

        self._analysis_variables = {}
        self._analysis_variables["baseline_mv"] = np.nan
        self._analysis_variables["delta_v_mv"] = np.nan
        self._analysis_variables["freq_hz"] = 0.0
        self._analysis_variables["iei_index"] = 0.0
        self._analysis_variables["spike_index"] = np.array([])
        self._analysis_variables["spike_mv"] = np.array([])
        self._analysis_variables["spike_number"] = np.array([])
        self._analysis_variables["mem_tau_min_index"] = np.nan
        self._analysis_variables["mem_tau_deltav_index"] = np.nan
        self._analysis_variables["sag_mv"] = np.nan
        self._analysis_variables["sag_index"] = np.nan
        self._analysis_variables["baseline_stability"] = np.nan
        self._analysis_variables["rebound_spike"] = 0
        self._analysis_variables["local_sfa"] = np.nan
        self._analysis_variables["divisor_sfa"] = np.nan
        self._analysis_variables["ai_sfa"] = np.nan
        self._analysis_variables["adaptation"] = np.nan
        self._analysis_variables["coefficient_of_variation"] = np.nan

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
        self._analysis_variables["baseline_mv"] = np.mean(
            self.acq_data.array[self.baseline_start : self.baseline_end]
        )
        spike_index, _ = signal.find_peaks(
            self.acq_data.array[self.pulse_start : self.pulse_end],
            height=self.min_spike_voltage,
            width=int(0.5 * self.acq_data.s_r_c()),
        )
        spike_index += self.pulse_start
        self._analysis_variables["spike_index"] = spike_index
        self._analysis_variables["spike_mv"] = self.acq_data.array[spike_index]
        self._analysis_variables["spike_number"] = np.arange(1, spike_index.size + 1)
        self._analysis_variables["freq_hz"] = len(spike_index) / (
            (self.pulse_end - self.pulse_start) / self.acq_data.fs
        )
        if len(spike_index) > 1:
            self._analysis_variables["iei_index"] = np.mean(np.diff(spike_index))
        if len(spike_index) > 0:
            self._analysis_variables.update(
                find_all_spk_thresholds(
                    self.acq_data.array,
                    spike_index,
                    self.pulse_start,
                    self.threshold_method,
                )
            )
            self._analysis_variables.update(
                find_all_ahps(self.acq_data.array, spike_index, self.pulse_end)
            )
            self._analysis_variables.update(
                find_all_spk_widths(
                    self.acq_data.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables.update(
                find_all_spk_auc(
                    self.acq_data.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables.update(
                find_all_spk_velocities(
                    self.acq_data.array,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables["local_sfa"] = local_sfa(spike_index)
            self._analysis_variables["divisor_sfa"] = divisor_sfa(spike_index)
            self._analysis_variables["ai_sfa"] = ai_sfa(spike_index)
            self._analysis_variables["adaptation"] = adaptation_index(spike_index)
            self._analysis_variables["coefficient_of_variation"] = (
                coefficient_of_variation(spike_index)
            )

        self._analysis_variables["delta_v_mv"] = self.get_delta_v(spike_index)

        if self.acq_data.pulse_amp < 0:
            self._analysis_variables.update(
                voltage_sag(self.acq_data.array, self.pulse_start, self.pulse_end)
            )
            self._analysis_variables["mem_tau_deltav_index"] = (
                membrane_time_constant_deltav(
                    self.acq_data.array,
                    self._analysis_variables["delta_v_mv"],
                    self.pulse_start,
                    self.baseline_start,
                    self.baseline_end,
                )
            )
            self._analysis_variables["mem_tau_min_index"] = membrane_time_constant_min(
                self.acq_data.array,
                self.pulse_start,
                self.baseline_start,
                self.baseline_end,
            )
        else:
            self._analysis_variables["sag_mv"] = None
            self._analysis_variables["sag_index"] = None

        self._analysis_variables["baseline_stability"] = baseline_stability(
            self.acq_data.array, self.pulse_start, self.pulse_end
        )

        rebound_spikes, _ = signal.find_peaks(
            self.acq_data.array[self.pulse_end :],
            height=self.min_spike_voltage,
            prominence=int(1 * self.acq_data.s_r_c()),
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
                self.acq_data.array,
                self.pulse_start,
                self.pulse_end,
                self.proportion,
                self.side,
            )
        else:
            index = self._analysis_variables["threshold_index"][0]
            delta_v = (
                self.acq_data.array[index] - self._analysis_variables["baseline_mv"]
            )
        # if self.ramp == "0":
        #     if len(self.spike_index) > 0:
        #         delta_v = delta(
        #             self.acq_data.array,
        #             self.pulse_start,
        #             self.pulse_end,
        #             self.proportion,
        #             self.side,
        #         )
        #     else:
        #         index = self._analysis_variables["threshold_index"][0]
        #         delta_v = self.acq_data.array[index] - self._analysis_variables["baseline_v"]
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
                    0, self.acq_data.pulse_amp, num=self.pulse_end - self.pulse_start
                )

                # Create an array of zeros where the ramp will be placed.
                ramp_array = np.zeros(len(self.acq_data.array))

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
                    self._analysis_variables["hw_left_index"],
                    self._analysis_variables["hw_right_index"],
                ]
            )
            / self.acq_data.s_r_c()
        )
        y = np.array(
            [self._analysis_variables["hw_mv"], self._analysis_variables["hw_mv"]]
        )
        return x, y

    def spike_widths(self):
        x = (
            np.array(
                [
                    self._analysis_variables["fw_left_index"],
                    self._analysis_variables["fw_right_index"],
                ]
            )
            / self.acq_data.s_r_c()
        )
        y = np.array(
            [self._analysis_variables["fw_mv"], self._analysis_variables["fw_mv"]]
        )
        return x, y

    def peaks(self):
        x = self._analysis_variables["spike_index"] / self.acq_data.s_r_c()
        y = self._analysis_variables["spike_mv"]
        return x, y

    def ahps(self):
        x = self._analysis_variables["ahp_index"]
        y = self._analysis_variables["ahp_voltages"]
        return x, y

    def thresholds(self):
        x = self._analysis_variables["threshold_index"] / self.acq_data.s_r_c()
        y = self.acq_data.array[self._analysis_variables["threshold_index"]]
        return x, y

    def min_velocity(self):
        return self._analysis_variables["min_velocity"], self._analysis_variables[
            "min_velocity_index"
        ] / self.acq_data.s_r_c()

    def max_velocity(self):
        return self._analysis_variables["max_velocity"], self._analysis_variables[
            "max_velocity_index"
        ] / self.acq_data.s_r_c()

    def acquisition(self):
        return np.arange(
            self.acq_data.array.size
        ) / self.acq_data.s_r_c(), self.acq_data.array

    def derivative(self):
        return np.arange(
            self.acq_data.array.size
        ) / self.acq_data.s_r_c(), -1 * np.gradient(self.acq_data.array)

    def data(self) -> dict:
        temp = self._analysis_variables.copy()
        acq_data = {}
        spk_data = {}
        for param in SPIKE_PARAMS:
            value = temp.pop(param)
            spk_data[param] = value
        spk_data["spike_index"] = temp.pop("spike_index")
        spk_data["spike_mv"] = temp.pop("spike_mv")
        spk_data["spike_number"] = temp.pop("spike_number")
        spk_data["epoch"] = [self.acq_data.epoch] * value.size
        spk_data["acq_number"] = [self.acq_data.acq_number] * value.size
        spk_data["cycle"] = [self.acq_data.cycle] * value.size
        spk_data["pulse_amp_pa"] = [self.acq_data.pulse_amp] * value.size

        for key, value in spk_data.items():
            if "index" in key:
                spk_data[key] = value / self.acq_data.s_r_c()

        for key2, value2 in temp.items():
            acq_data[key2] = value2
        acq_data["epoch"] = self.acq_data.epoch
        acq_data["acq_number"] = self.acq_data.acq_number
        acq_data["cycle"] = self.acq_data.cycle
        acq_data["pulse_amp_pa"] = self.acq_data.pulse_amp
        return acq_data, spk_data
