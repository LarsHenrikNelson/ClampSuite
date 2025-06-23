from typing import Literal, Union

import numpy as np
from scipy import signal

from ..functions.current_clamp import (
    voltage_sag,
    find_all_spk_thresholds,
    find_all_ahps,
)
from ..functions.general import baseline_stability, delta
from . import filter_acq


class CurrentClampAcq(filter_acq.FilterAcq, analysis="current_clamp"):
    def analyze(
        self,
        threshold: Union[int, float] = -15,
        threshold_method: Literal[
            "third_derivative",
            "first_derivative",
            "second_derivative",
            "max_curvature",
            "legacy",
        ] = "third_derivative",
        min_spikes: int = 2,
        side: Literal["left", "right"] = "right",
        proportion: float = 0.5,
        debug=False,
    ):
        if self._pulse_start == 0:
            if self._baseline_end == self.array.size:
                self._pulse_start = 0
            else:
                self._pulse_start = self._baseline_end
                self.pulse_start = self.baseline_end
        self.threshold = threshold
        self.threshold_method = threshold_method
        self.min_spikes = min_spikes
        self.proportion = proportion
        self.side = side

        # Analysis functions
        self.baseline_mean = np.mean(
            self.array[self._baseline_start : self._baseline_end]
        )
        self.peaks, _ = signal.find_peaks(
            self.array[self._pulse_start : self._pulse_end],
            height=self.threshold,
            prominence=int(1 * self.s_r_c),
        )
        if len(self.peaks) > 0:
            self.spike_thresholds = find_all_spk_thresholds(
                self.array,
                self.peaks,
                self._pulse_start,
                self._pulse_end,
                self.threshold_method,
            )
            self.ahps = find_all_ahps()
        else:
            self.spike_thresholds = []
        self.delta_v = self.get_delta_v()

        if self.pulse_amp < 0:
            self.sag_loc, self.sag = voltage_sag(
                self.array, self._pulse_start, self._pulse_end
            )
        else:
            self.sag_loc, self.sag = np.nan, np.nan

        self.baseline_stability = baseline_stability(
            self.array, self._pulse_start, self._pulse_end
        )

        self.find_first_spike()
        self.spike_velocity()
        self.get_ramp_rheo()
        self.find_spike_width()
        self.find_AHP_peak()

    def get_delta_v(self):
        """This function finds the delta-v for a pulse. It simply takes the mean
        value from the pulse start to end for pulses without spikes. For
        pulses with spikes it takes the mode of the moving mean.
        """
        if self.ramp == "0":
            if len(self.peaks) > 0:
                delta_v = delta(
                    self.array,
                    self._pulse_start,
                    self._pulse_end,
                    self.proportion,
                    self.side,
                )
            else:
                delta_v = self.spike_thresholds[0]
        elif self.ramp == "1":
            delta_v = np.nan
        return delta_v

    def spike_velocity(self):
        if not np.isnan(self.first_ap[0]):
            # Differentiate the array to find the peak dv/dt.
            dv = np.gradient(self.first_ap)
            dt = np.gradient(self.spike_x_array())
            dv_dt = dv / dt

            self.max_velocity_x = np.argmax(dv_dt)
            self.max_velocity_y = dv[self.max_velocity_x]
            self.max_velocity_x += self.ap_index[0]

            self.min_velocity_x = np.argmin(dv_dt)
            self.min_velocity_y = dv[self.min_velocity_x]
            self.min_velocity_x += self.ap_index[0]
        else:
            self.max_velocity_x = np.nan
            self.max_velocity_y = np.nan

            self.min_velocity_x = np.nan
            self.min_velocity_y = np.nan

    def find_spike_width(self):
        # Create the masked array using the mask found earlier to find
        # The pulse half-width.
        if not np.isnan(self.peaks[0]):
            if self.ramp == "0":
                end = self._pulse_end
            else:
                end = self._pulse_end
            masked_array = self.array.copy()
            mask = np.array(self.array > self.spike_threshold)
            masked_array[~mask] = self.spike_threshold
            self.width_comp = signal.peak_widths(
                masked_array[:end], self.peaks, rel_height=0.5
            )
        else:
            self.width_comp = None

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
                    0, self.pulse_amp, num=self._pulse_end - self._pulse_start
                )

                # Create an array of zeros where the ramp will be placed.
                ramp_array = np.zeros(len(self.array))

                # Insert the ramp into the array of zeros.
                ramp_array[self._pulse_start : self._pulse_end] = ramp_values

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

    def hertz_exact(self) -> float:
        if self.ramp == "0":
            # Calculates the exact hertz by dividing the number peaks by
            # length of the pulse. If there is only one spike the hertz
            # returns an impossibly fast number is you take only divide by
            # the start of the spike_threshold to the end of the pulse.
            if not np.isnan(self.peaks[0]):
                return len(self.peaks) / (
                    (self._pulse_end - self._pulse_start) / self.sample_rate
                )
            else:
                return np.nan
        elif self.ramp == "1":
            if not np.isnan(self.peaks[0]):
                return len(self.peaks) / (
                    (self._pulse_end - self.rheo_x) / self.sample_rate
                )
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

    def spike_peaks_x(self) -> list:
        if not np.isnan(self.peaks[0]):
            return np.array(self.peaks) / self.s_r_c
        else:
            return []

    def spike_peaks_y(self) -> list:
        if not np.isnan(self.peaks[0]):
            return self.array[self.peaks]
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
                int(((self._pulse_end - self._pulse_start) / 2) + self._pulse_start)
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
        return self.peaks[0] / self.s_r_c

    def plot_acq_y(self) -> np.ndarray:
        return self.array

    def plot_acq_x(self) -> np.ndarray:
        return np.arange(0, len(self.array)) / self.s_r_c

    def acq_data(self) -> dict:
        """This create a dictionary of all the values created by the class. This
        makes it very easy to concentatenate the data from multiple
        acquisitions together.

        Returns:
            dict: dictionary of acquisition attributes
        """
        if np.isnan(self.peaks[0]):
            num_spks = np.nan
        else:
            num_spks = len(self.peaks)
        current_clamp_dict = {
            "Acquisition": self.acq_number,
            "Cycle": self.cycle,
            "Pulse pattern": self.pulse_pattern,
            "Pulse amp (pA)": self.pulse_amp,
            "Ramp": self.ramp,
            "Epoch": self.epoch,
            "Baseline mean (pA)": self.baseline_mean,
            "Pulse start (ms)": float(self._pulse_start) / self.s_r_c,
            "Delta V (mV)": self.delta_v,
            "Voltage sag (mV)": self.voltage_sag,
            "Spike threshold (mV)": self.spike_threshold,
            "Spike threshold (ms)": self.spike_threshold_x(),
            "Spike peak volt (mV)": self.peak_volt,
            "Spike time (ms)": self.first_peak_time(),
            "Hertz": self.hertz_exact(),
            "IEI": self.iei_mean,
            "Num spikes": num_spks,
            "Spike width (ms)": self.spike_width(),
            "Max AP vel (mV/ms)": self.max_velocity_y,
            "Max AP vel time (ms)": float(self.max_velocity_x) / self.s_r_c,
            "Min AP vel (mV/ms)": self.min_velocity_y,
            "Min AP vel time (ms)": float(self.min_velocity_x) / self.s_r_c,
            "Spike freq adapt": self.spike_adapt,
            "Local sfa": self.local_var,
            "Divisor sfa": self.sfa_divisor,
            "Peak AHP (mV)": self.ahp_y,
            "Peak AHP (ms)": self.ahp_x,
            "Ramp rheobase (pA)": self.ramp_rheo,
            "Baseline stability": self.baseline_stability,
        }
        return current_clamp_dict
