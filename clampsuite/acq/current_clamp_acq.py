from typing import Literal, Union

import numpy as np
from scipy import signal

from ..functions.current_clamp import (
    ThresholdType,
    find_all_ahps,
    find_all_spk_auc,
    find_all_spk_thresholds,
    find_all_spk_widths,
    voltage_sag,
)
from ..functions.general import baseline_stability, delta


class CurrentClampAcq:
    def __init__(self, array: np.ndarray, fs: float, pulse_amp):
        self.array = array
        self.fs = fs
        self.s_r_c = fs / 1000
        self.pulse_amp = pulse_amp

        self.analysis_variables = {}
        self.analysis_variables["baseline_v"] = None
        self.analysis_variables["delta_v"] = None
        self.analysis_variables["hertz"] = 0.0
        self.analysis_variables["peak_index"] = None
        self.analysis_variables["threshold_index"] = None
        self.analysis_variables["hw_left"] = None
        self.analysis_variables["hw_right"] = None
        self.analysis_variables["hw_y"] = None
        self.analysis_variables["fw_left"] = None
        self.analysis_variables["fw_right"] = None
        self.analysis_variables["fw_y"] = None
        self.analysis_variables["auc"] = None
        self.analysis_variables["auc_left"] = None
        self.analysis_variables["auc_right"] = None
        self.analysis_variables["ahp_index"] = None
        self.analysis_variables["velocity"] = None
        self.analysis_variables["mem_tau_est"] = None
        self.analysis_variables["sag"] = None
        self.analysis_variables["sag_loc"] = None
        self.analysis_variables["baseline_stability"] = None

    def analyze(
        self,
        baseline_start: int = 0,
        baseline_end: int = 3000,
        pulse_start: int = 3000,
        pulse_end: int = 10000,
        min_spike_voltage: Union[int, float] = -15,
        threshold_method: ThresholdType = "third_derivative",
        min_spikes: int = 2,
        side: Literal["left", "right"] = "right",
        proportion: float = 0.5,
        offset: float = 200.0,
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
        self.offset = int(offset * self.s_r_c)

        # Analysis functions
        self.analysis_variables["baseline_v"] = np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        peak_index, _ = signal.find_peaks(
            self.array[self.pulse_start : self.pulse_end],
            height=self.min_spike_voltage,
            prominence=int(1 * self.s_r_c),
        )
        peak_index += self.pulse_start
        self.analysis_variables["peak_index"] = peak_index
        if peak_index is not None:
            self.analysis_variables.update(
                find_all_spk_thresholds(
                    self.array,
                    peak_index,
                    self.pulse_start,
                    self.pulse_end,
                    self.threshold_method,
                )
            )
            self.analysis_variables.update(
                find_all_ahps(self.array, peak_index, self.pulse_end)
            )
            self.analysis_variables.update(
                find_all_spk_widths(
                    self.array,
                    self.analysis_variables["threshold_index"],
                    self.pulse_end,
                    self.offset,
                )
            )
            self.analysis_variables.update(
                find_all_spk_auc(
                    self.array,
                    self.analysis_variables["threshold_index"],
                    self.pulse_end,
                    self.offset,
                )
            )

        self.analysis_variables["delta_v"] = self.get_delta_v(peak_index)

        if self.pulse_amp < 0:
            self.analysis_variables.update(
                voltage_sag(self.array, self.pulse_start, self.pulse_end)
            )
        else:
            self.analysis_variables["sag"] = None
            self.analysis_variables["sag_loc"] = None

        self.analysis_variables["baseline_stability"] = baseline_stability(
            self.array, self.pulse_start, self.pulse_end
        )

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
            index = self.analysis_variables["threshold_index"][0]
            delta_v = self.array[index] - self.analysis_variables["baseline_v"]
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
        #         index = self.analysis_variables["threshold_index"][0]
        #         delta_v = self.array[index] - self.analysis_variables["baseline_v"]
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

    # Helper functions that correct x-values for plotting

    def set_spike_threshold(self, x: Union[float, int], y: Union[float, int]):
        self.rheo_x = int(self.s_r_c * x)
        self.spike_threshold = y
        self.find_spike_width()
        self.find_first_spike()

    def spike_width(self) -> Union[int, float]:
        if self.width_comp is not None:
            return self.width_comp[0][0] / self.s_r_c
        else:
            return np.nan

    def spike_width_y(self) -> list:
        if self.width_comp is not None:
            return [self.width_comp[1][0], self.width_comp[1][0]]

    def spike_width_x(self) -> list:
        return [
            self.width_comp[2][0] / self.s_r_c,
            self.width_comp[3][0] / self.s_r_c,
        ]

    def spike_threshold_x(self) -> Union[int, float]:
        if not np.isnan(self.rheo_x):
            return self.rheo_x / self.s_r_c
        else:
            return self.rheo_x

    def spike_x_array(self) -> list:
        return self.plot_acq_x()[self.ap_index[0] : self.ap_index[1]]

    def spike_peak_index_x(self) -> list:
        if not np.isnan(self.peak_index[0]):
            return np.array(self.peak_index) / self.s_r_c
        else:
            return []

    def spike_peak_index_y(self) -> list:
        if not np.isnan(self.peak_index[0]):
            return self.array[self.peak_index]
        else:
            return []

    def plot_st_x(self) -> list:
        return [self.rheo_x / self.s_r_c]

    def plot_st_y(self) -> list:
        return [self.spike_threshold]

    def plot_ahp_y(self) -> list:
        return [self.ahp_y]

    def plot_deltav_x(self) -> list:
        """
        This function creates the elements to plot the delta-v as a vertical
        line in the middle of the pulse. The elements are corrected so that
        they will plot in milliseconds.
        """
        if self.ramp == "0":
            x = (
                int(((self.pulse_end - self.pulse_start) / 2) + self.pulse_start)
                / self.s_r_c
            )
            plot_x = [x, x]
        elif self.ramp == "1":
            plot_x = [np.nan]
        return plot_x

    def plot_deltav_y(self) -> list:
        if self.ramp == "0":
            voltage_response = self.delta_v + self.baseline_mean
            plot_y = [self.baseline_mean, voltage_response]
        elif self.ramp == "1":
            plot_y = [np.nan]
        return plot_y

    def plot_voltage_sag_y(self) -> list:
        if not np.isnan(self.voltage_sag):
            voltage_response = self.voltage_sag + self.array[self._voltage_sag_x]
            return [voltage_response, self.array[self._voltage_sag_x]]
        else:
            return [np.nan]

    def plot_voltage_sag_x(self) -> list:
        if not np.isnan(self._voltage_sag_x):
            return [self._voltage_sag_x / self.s_r_c, self._voltage_sag_x / self.s_r_c]
        else:
            return [np.nan]

    def plot_ahp_x(self) -> list:
        return [self.ahp_x]

    def first_peak_time(self) -> list:
        return self.peak_index[0] / self.s_r_c

    def acq_y(self) -> np.ndarray:
        return self.array

    def acq_x(self) -> np.ndarray:
        return np.arange(0, len(self.array)) / self.s_r_c

    def acq_data(self) -> dict:
        pass
