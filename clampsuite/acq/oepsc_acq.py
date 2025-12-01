from typing import Union

import numpy as np
from scipy import integrate, optimize

from ..functions.curve_fit import SExpDecay, DExpDecay
from ..functions.evoked_psc import _detect_pos_neg
from . import filter_acq


class oEPSCAcq(filter_acq.FilterAcq):
    def analyze(
        self,
        pulse_start: Union[int, float] = 1000,
        n_window_start: Union[int, float] = 1001,
        n_window_end: Union[int, float] = 1050,
        p_window_start: Union[int, float] = 1045,
        p_window_end: Union[int, float] = 1055,
        multiple_peaks: bool = False,
        find_ct: bool = False,
        find_est_decay: bool = False,
        curve_fit_decay: bool = False,
        curve_fit_type: str = "s_exp",
    ):
        # Set all the attributes
        self.pulse_start = pulse_start
        self._pulse_start = int(pulse_start * self.s_r_c)
        self.x_array = np.arange(len(self.array)) / (self.sample_rate / 1000)
        self._n_window_start = int(n_window_start * self.s_r_c)
        self.n_window_start = n_window_start
        self._n_window_end = int(n_window_end * self.s_r_c)
        self.n_window_end = n_window_end
        self._p_window_start = int(p_window_start * self.s_r_c)
        self.p_window_start = p_window_start
        self._p_window_end = int(p_window_end * self.s_r_c)
        self.p_window_end = p_window_end
        self.find_ct = find_ct
        self.find_edecay = find_est_decay
        self.find_fdecay = curve_fit_decay
        self.curve_fit_type = curve_fit_type
        self.multiple_peaks = multiple_peaks

        self.run_analysis()

    def run_analysis(self):
        self.filter_array(self.array)
        self.baseline_mean = np.mean(
            self.filtered_array[self._baseline_start : self._baseline_end]
        )
        self.peak_direction = _detect_pos_neg(self.filtered_array)
        self.find_amplitude()
        self.zero_crossing()
        if self.find_ct:
            self.find_charge_transfer()
        if self.find_edecay:
            self.find_est_decay()
        else:
            self.est_tau_x = np.nan
        if self.find_fdecay:
            self.find_fit_decay()

    def find_amplitude(self):
        if self.peak_direction == "positive":
            self.peak_y = np.max(
                self.filtered_array[self._p_window_start : self._p_window_end]
            )
            self._peak_x = (
                np.argmax(
                    self.filtered_array[self._p_window_start : self._p_window_end]
                )
                + self._p_window_start
            )
        elif self.peak_direction == "negative":
            self.peak_y = np.min(
                self.filtered_array[self._n_window_start : self._n_window_end]
            )
            self._peak_x = (
                np.argmin(
                    self.filtered_array[self._n_window_start : self._n_window_end]
                )
                + self._n_window_start
            )

    def zero_crossing(self):
        if self.peak_direction == "negative":
            index = np.where(self.filtered_array[self._peak_x :] > self.baseline_mean)[
                0
            ]
        else:
            index = np.where(self.filtered_array[self._peak_x :] < self.baseline_mean)[
                0
            ]
        if index.shape[0] > 0:
            self._index = index[0] + self._peak_x
        else:
            self._index = len(self.filtered_array)

    def find_charge_transfer(self):
        self.charge_transfer = integrate.trapz(
            self.filtered_array[self._pulse_start : self._index],
            self.x_array[self._pulse_start : self._index],
        )

    def find_est_decay(self):
        self.decay_y = self.filtered_array[self._peak_x : self._index]
        if self.decay_y.size > 0:
            self.est_tau_y = self.peak_y * (1 / np.exp(1))

        if self.peak_direction == "positive":
            y = -self.est_tau_y
            decay_y = -self.decay_y
        else:
            y = self.est_tau_y
            decay_y = self.decay_y

        if self.decay_y.size > 0:
            self.decay_x = self.x_array[self._peak_x : self._index]
            self.est_tau_x = np.interp(y, decay_y, self.decay_x)

        else:
            self.est_tau_x = np.nan
            self.est_tau_y = np.nan

    def find_fit_decay(self):
        if self.curve_fit_type == "db_exp":
            fit_object = DExpDecay()
        else:
            fit_object = SExpDecay()
        fit_object.curve_fit(self.decay_x, self.decay_y)

    def set_peak(self, x: Union[float, int], y: Union[float, int]):
        x = int(x * self.s_r_c)
        self._peak_x = x
        self.peak_y = y
        if self.peak_y < 0:
            self.peak_direction = "negative"
        else:
            self.peak_direction = "positive"
        self.zero_crossing()
        if self.find_ct:
            self.find_charge_transfer()
        if self.find_edecay:
            self.find_est_decay()
        if self.find_fdecay:
            self.find_fit_decay()

    # Helper functions for plottings x in the correct units
    def peak_x(self) -> Union[float, int]:
        return self._peak_x / self.s_r_c

    def est_decay(self) -> Union[float, int]:
        if np.isnan(self.est_tau_x):
            return np.nan
        else:
            return self.est_tau_x - self.peak_x()

    def plot_x_comps(self) -> list:
        if self.find_edecay:
            return [
                self.peak_x(),
                self.est_tau_x,
            ]
        else:
            return [self.peak_x(), self.est_tau_x]

    def plot_y_comps(self) -> list:
        if self.find_edecay:
            return [
                self.peak_y,
                self.filtered_array[int(self.est_tau_x * self.s_r_c)],
            ]
        else:
            return [self.peak_y, self.est_tau_x]

    def plot_acq_x(self) -> np.ndarray:
        return np.arange(0, len(self.filtered_array)) / self.s_r_c

    def plot_acq_y(self) -> np.ndarray:
        return self.filtered_array

    def acq_data(self) -> dict:
        oepsc_dict = {
            "Epoch": self.epoch,
            "Acquisition": self.acq_number,
            "Peak direction": self.peak_direction,
            "Amplitude": abs(self.peak_y),
            "Peak time (ms)": self.peak_x(),
            "oEPSC Pulse start (ms)": self.pulse_start,
        }
        if self.find_ct:
            oepsc_dict["Charge_transfer"] = self.charge_transfer
        if self.find_edecay:
            oepsc_dict["Est_decay (ms)"] = self.est_decay()
        if self.find_fdecay:
            oepsc_dict["Curve_fit_tau (ms)"] = self.fit_tau
        return oepsc_dict
