import numpy as np
from scipy import integrate
from scipy import signal

from .acquisition_base import AcquisitionBase
from ..functions.curve_fit import s_exp_decay, db_exp_decay


class oEPSCBase(AcquisitionBase):
    def peak_direction(self):
        if abs(max(self.filtered_array)) > abs(min(self.filtered_array)):
            self.peak_direction = "positive"
            self.peak_direction = "positive"
        else:
            self.peak_direction = "negative"

    def find_amplitude(self):
        if self.peak_direction == "positive":
            self.peak_y = np.max(
                self.filtered_array[self.p_window_start : self.p_window_end]
            )
            self.peak_x = (
                np.argmax(self.filtered_array[self.p_window_start : self.p_window_end])
                + self.p_window_start
            ) / self.s_r_c
        elif self.peak_direction == "negative":
            self.peak_y = np.min(
                self.filtered_array[self.n_window_start : self.n_window_end]
            )
            self.peak_x = (
                np.argmin(self.filtered_array[self.n_window_start : self.n_window_end])
                + self.n_window_start
            ) / self.s_r_c

    def find_charge_transfer(self):
        self.rms = np.sqrt(
            np.mean(
                np.square(self.filtered_array[self.baseline_start : self.baseline_end])
            )
        )
        try:
            index = np.argmax(
                abs(self.filtered_array[int(self.peak_x * self.s_r_c) :]) < 2 * self.rms
            ) + int(self.peak_x * self.s_r_c)
            self.charge_transfer = integrate.trapz(
                self.filtered_array[self.pulse_start : index],
                self.x_array[self.pulse_start : index],
            )
        except:
            self.charge_transfer = np.nan

    def analyze_oepsc(self):
        self.peak_direction()
        self.find_amplitude()
        self.find_charge_transfer()

    def change_peak(self, x, y):
        self.peak_x = x / self.s_r_c
        self.peak_y = y
        if self.peak_y < 0:
            self.peak_direction = "negative"
        else:
            self.peak_direction = "positive"

    def est_decay(self):
        baselined_event = self.event_array - self.event_start_y
        return_to_baseline = int(
            (
                np.argmax(
                    baselined_event[self.event_peak_x - self.array_start :]
                    >= (self.event_peak_y - self.event_start_y) * 0.25
                )
            )
            + (self.event_peak_x - self.array_start)
        )
        decay_y = self.event_array[
            self.event_peak_x - self.array_start : return_to_baseline
        ]
        if decay_y.size > 0:
            self.est_tau_y = (
                (self.event_peak_y - self.event_start_y) * (1 / np.exp(1))
            ) + self.event_start_y
            decay_x = self.x_array[
                self.event_peak_x - self.array_start : return_to_baseline
            ]
            self.est_tau_x = np.interp(self.est_tau_y, decay_y, decay_x)
            self.final_tau_x = (self.est_tau_x - self.event_peak_x) / self.s_r_c
        else:
            self.est_tau_x = np.nan
            self.final_tau_x = np.nan
            self.est_tau_y = np.nan

    def fit_decay(self, fit_type):
        try:
            baselined_event = self.event_array - self.event_start_y
            amp = self.event_peak_x - self.array_start
            decay_y = baselined_event[amp:]
            decay_x = np.arange(len(decay_y))
            if fit_type == "db_exp":
                upper_bounds = [0, np.inf, 0, np.inf]
                lower_bounds = [-np.inf, 0, -np.inf, 0]
                init_param = np.array([self.event_peak_y, self.final_tau_x, 0, 0])
                popt, pcov = signal.curve_fit(
                    db_exp_decay,
                    decay_x,
                    decay_y,
                    p0=init_param,
                    bounds=[lower_bounds, upper_bounds],
                )
                amp_1, self.fit_tau, amp_2, tau_2 = popt
                self.fit_decay_y = (
                    db_exp_decay(decay_x, amp_1, self.fit_tau, amp_2, tau_2)
                    + self.z_start_y
                )
            else:
                upper_bounds = [0, np.inf]
                lower_bounds = [-np.inf, 0]
                init_param = np.array([self.event_peak_y, self.final_tau_x])
                popt, pcov = signal.curve_fit(
                    s_exp_decay,
                    decay_x,
                    decay_y,
                    p0=init_param,
                    bounds=[lower_bounds, upper_bounds],
                )
                amp_1, self.fit_tau = popt
                self.fit_decay_y = (
                    s_exp_decay(decay_x, amp_1, self.fit_tau) + self.event_start_y
                )
            self.fit_decay_x = (decay_x + self.event_peak_x) / self.s_r_c
        except:
            self.fit_decay_x = np.nan
            self.fit_decay_y = np.nan
            self.fit_tau = np.nan

    def plot_y(self):
        return self.filtered_array[self.baseline_start :]

    def plot_x(self):
        return self.x_array[self.baseline_start :]

    def plot_peak_x(self):
        return [self.peak_x]

    def plot_peak_y(self):
        return [self.peak_y]

    def create_dict(self):
        oepsc_dict = {
            "Amplitude": abs(self.peak_y),
            "Charge_transfer": self.charge_transfer,
            "Epoch": self.epoch,
            "Acq number": self.acq_number,
            "Peak direction": self.peak_direction,
        }
        return oepsc_dict
