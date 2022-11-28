from typing import Union

import numpy as np
from scipy.stats import linregress
from scipy import signal

from . import filter_acq


class LFPAcq(filter_acq.FilterAcq, analysis="lfp"):
    """
    This class creates a LFP acquisition. This class subclasses the
    Acquisition class and takes input specific for LFP analysis.
    """

    def analyze(
        self,
        sample_rate: Union[int, float] = 10000,
        baseline_start: Union[int, float] = 0,
        baseline_end: Union[int, float] = 800,
        filter_type: str = "remez_2",
        order: Union[int, float] = 301,
        high_pass: Union[int, float, None] = None,
        high_width: Union[int, float, None] = None,
        low_pass: Union[int, float] = 300,
        low_width: Union[int, float] = 100,
        window: Union[int, None] = None,
        polyorder: Union[int, None] = None,
        pulse_start: Union[int, float] = 1000,
    ):
        """
        This function runs all the other functions in one place. This makes
        it easy to troubleshoot.
        """
        # Set all the attributes for analysis.
        self.sample_rate = sample_rate
        self.s_r_c = sample_rate / 1000
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.x_array = np.arange(len(self.array)) / (sample_rate / 1000)
        self.baseline_start = int(baseline_start * (sample_rate / 1000))
        self.baseline_end = int(baseline_end * (sample_rate / 1000))
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self._pulse_start = int(pulse_start * self.s_r_c)
        self._fp_x = np.nan
        self.fp_y = np.nan
        self._fv_x = np.nan
        self.fv_y = np.nan
        self.max_x = np.nan
        self.max_y = np.nan
        self.slope_y = np.nan
        self._slope_x = [np.nan]
        self.b = np.nan
        self._slope = np.nan
        self.regression_line = np.nan

        # Run the analysis
        self.filter_array()
        self.field_potential()
        if np.isnan(self._fp_x):
            self.plot_lfp = False
        else:
            self.find_fiber_volley()
            self.find_slope_start()
            self.find_slope_array()
            self.regression()
            self.plot_lfp = True

    def field_potential(self):
        """
        This function finds the field potential based on the largest value in
        the array.

        Returns
        -------
        None.

        """
        # The end value was chosed based on experimental data.
        w_end = self._pulse_start + 200

        # The start value was chosen based on experimental data.
        w_start = self._pulse_start + 44

        if abs(np.max(self.filtered_array[w_start:w_end])) < abs(
            np.min(self.filtered_array[w_start:w_end])
        ):
            self.fp_y = np.min(self.filtered_array[w_start:w_end])
            self._fp_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start
        else:
            self.fp_y = np.nan
            self._fp_x = np.nan

    def find_fiber_volley(self):
        if np.isnan(self._fp_x) or self._fp_x is None:
            self.fv_y = np.nan
            self._fv_x = np.nan
        else:
            peaks, _ = signal.find_peaks(
                -1 * self.filtered_array[self._pulse_start : self._fp_x],
                width=int(0.5 * self.s_r_c),
            )
        if len(peaks) > 0:
            self._fv_x = int(peaks[0] + self._pulse_start)
            self.fv_y = self.filtered_array[self._fv_x]
        else:
            self.fv_y, self._fv_x = self.fiber_volley_sec()

    def fiber_volley_sec(self):
        """
        This function finds the fiber volley based on the position of the
        field potential. The window for finding the fiber volley is based on
        experimental data.

        Returns
        -------
        None.

        """
        w_start = self._pulse_start + int(0.9 * self.s_r_c)
        if self._fp_x < (self._pulse_start + 74):
            w_end = self._fp_x - int(2 * self.s_r_c)
        else:
            w_end = self._fp_x - int(4 * self.s_r_c)
            if w_end > (self._pulse_start + int(49 * self.s_r_c)):
                w_end = self._pulse_start + int(49 * self.s_r_c)
        fv_y = np.min(self.filtered_array[w_start:w_end])
        fv_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start
        return fv_y, fv_x

    def find_slope_array_sec(self, w_end):
        """
        This function returns the array for slope of the field potential onset
        based upon the 10-90% values of the field potential rise. The field
        potential x coordinate needs to be passed to this function.

        Returns
        -------
        None.

        """
        start = self._pulse_start
        x_values = np.arange(0, len(self.filtered_array) - 1)
        if w_end is not np.nan:
            w_end = int(w_end)
            if w_end < (start + int(7.4 * self.s_r_c)):
                x = w_end - int(1.9 * self.s_r_c)
            else:
                x = w_end - int(3.9 * self.s_r_c)
                if x > (start + int(4.9 * self.s_r_c)):
                    x = start + int(4.9 * self.s_r_c)
            w_start = np.argmin(
                self.filtered_array[(start + int(0.9 * self.s_r_c)) : x]
            ) + (start + int(0.9 * self.s_r_c))
            if w_end < w_start:
                self.slope_y = [np.nan]
                self._slope_x = [np.nan]
                self.max_x = [np.nan]
                self.max_y = [np.nan]
            else:
                self.max_x = np.argmax(self.filtered_array[w_start:w_end]) + w_start
                self.max_y = np.max(self.filtered_array[w_start:w_end])
                y_array_subset = self.filtered_array[self.max_x : w_end]
                x_array_subset = x_values[self.max_x : w_end]
                self.slope_y = y_array_subset[
                    int(len(y_array_subset) * 0.1) : int(len(y_array_subset) * 0.9)
                ]
                self._slope_x = x_array_subset[
                    int(len(x_array_subset) * 0.1) : int(len(x_array_subset) * 0.9)
                ]
        else:
            self.max_x = [np.nan]
            self.max_y = [np.nan]
            self.slope_y = [np.nan]
            self._slope_x = [np.nan]

    def find_slope_start(self):
        peaks, _ = signal.find_peaks(
            self.filtered_array[self._fv_x : self._fp_x], width=int(0.5 * self.s_r_c)
        )
        if len(peaks) > 0:
            indices = peaks + self._fv_x
            temp = np.argmax(self.filtered_array[indices])
            self.max_x = indices[temp]
        else:
            self.max_x = self._fv_x + int(1 * self.s_r_c)
        self.max_y = self.filtered_array[self.max_x]

    def find_slope_array(self):
        x_array_subset = np.arange(self.max_x, self._fp_x + 1)
        y_array_subset = self.filtered_array[self.max_x : self._fp_x + 1]
        self.slope_y = y_array_subset[
            int(len(y_array_subset) * 0.1) : int(len(y_array_subset) * 0.9)
        ]
        self._slope_x = x_array_subset[
            int(len(x_array_subset) * 0.1) : int(len(x_array_subset) * 0.9)
        ]

    def regression(self):
        """
        This function runs a regression on the slope array created by the
        find_slop_array function.

        Returns
        -------
        None.

        """
        if len(self.slope_y) > 5:
            reg = linregress(self._slope_x, self.slope_y)
            self._slope = reg[0]
            self.reg_line = [(self._slope * i) + reg[1] for i in self._slope_x]
        else:
            self.b = np.nan
            self._slope = np.nan
            self.reg_line = np.nan

    def change_fv(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._fv_x = x
        self.fv_y = y
        self.find_slope_start()
        self.find_slope_array()
        self.regression()

    def change_fp(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._fp_x = x
        self.fp_y = y
        self.find_slope_array()
        self.regression()

    def change_slope_start(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self.max_x = x
        self.max_y = y
        self.find_slope_array()
        self.regression()

    def plot_elements_x(self) -> list:
        return [self.fv_x(), self.fp_x()]

    def plot_elements_y(self) -> list:
        return [self.fv_y, self.fp_y]

    def slope_x(self) -> Union[float, int]:
        if not np.isnan(self._slope):
            return self._slope_x / self.s_r_c
        else:
            return self._slope_x

    def fp_x(self) -> Union[float, int]:
        if not np.isnan(self._fp_x):
            return self._fp_x / self.s_r_c
        else:
            return self._fp_x

    def fv_x(self) -> float:
        if not np.isnan(self._fv_x):
            return self._fv_x / self.s_r_c
        else:
            return self._fv_x

    def pulse_start(self) -> Union[int, float]:
        return self._pulse_start / self.s_r_c

    def slope(self) -> float:
        if not np.isnan(self._slope):
            return self._slope * self.s_r_c
        else:
            return self._slope

    def plot_acq_x(self) -> np.ndarray:
        return np.arange(0, len(self.filtered_array)) / self.s_r_c

    def plot_acq_y(self) -> np.ndarray:
        return self.filtered_array

    def create_dict(self) -> dict:
        """
        This function returns a dictionary of all the values you will need to
        analyze the lfp. The dictionary is not an attribute of the class to
        keep the size of the created object small.

        Returns
        -------
        lfp_dict : TYPE
            DESCRIPTION.

        """
        if not np.isnan(self._fp_x):
            lfp_dict = {
                "FV amp": self.fv_y,
                "FV time (ms)": self.fv_x(),
                "FP amp": self.fp_y,
                "FP_time (ms)": self.fp_x(),
                "FP_slope (mV/ms)": self.slope(),
                "Epoch": self.epoch,
                "Acq number": self.acq_number,
                "LFP Pulse start (ms)": self.pulse_start(),
            }
        else:
            lfp_dict = {
                "FV amp (mV)": np.nan,
                "FV time (ms)": np.nan,
                "FP amp (mV)": np.nan,
                "FP time (ms)": np.nan,
                "FP slope (mV/ms)": np.nan,
                "Epoch": self.epoch,
                "Acq number": self.acq_number,
                "LFP Pulse start (ms)": self.pulse_start(),
            }
        return lfp_dict
