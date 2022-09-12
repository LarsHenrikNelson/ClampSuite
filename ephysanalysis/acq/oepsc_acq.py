import numpy as np
from scipy import integrate, optimize
from scipy import signal

from . import filter_acq
from ..functions.curve_fit import s_exp_decay, db_exp_decay


class oEPSCAcq(filter_acq.FilterAcq, analysis="oepsc"):
    def analyze(
        self,
        sample_rate=10000,
        baseline_start=800,
        baseline_end=1000,
        filter_type="None",
        order=None,
        high_pass=None,
        high_width=None,
        low_pass=None,
        low_width=None,
        window=None,
        polyorder=None,
        pulse_start=1000,
        n_window_start=1001,
        n_window_end=1050,
        p_window_start=1045,
        p_window_end=1055,
        find_ct=False,
        find_est_decay=False,
        curve_fit_decay=False,
        curve_fit_type="s_exp",
    ):
        # Set all the attributes
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
        self.pulse_start = int(pulse_start * self.s_r_c)
        self.pulse_start = int(pulse_start * self.s_r_c)
        self.n_window_start = int(n_window_start * self.s_r_c)
        self.n_window_end = int(n_window_end * self.s_r_c)
        self.p_window_start = int(p_window_start * self.s_r_c)
        self.p_window_end = int(p_window_end * self.s_r_c)
        self.find_ct = find_ct
        self.find_edecay = find_est_decay
        self.find_fdecay = curve_fit_decay
        self.curve_fit_type = curve_fit_type

        # Analysis functions
        self.filter_array()
        self.baseline_mean = np.mean(
            self.filtered_array[self.baseline_start : self.baseline_end]
        )
        self.find_peak_dir()
        self.find_amplitude()
        self.zero_crossing()
        if self.find_ct:
            self.find_charge_transfer()
        if self.find_edecay:
            self.find_est_decay()
        if self.find_fdecay:
            self.find_fit_decay()

    def find_peak_dir(self):
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

    def zero_crossing(self):
        if self.peak_direction == "negative":
            index = np.where(
                self.filtered_array[int(self.peak_x * self.s_r_c) :]
                > self.baseline_mean
            )[0]
        else:
            index = np.where(
                self.filtered_array[int(self.peak_x * self.s_r_c) :]
                < self.baseline_mean
            )[0]
        if index.shape[0] > 0:
            self.index = index[0] + int(self.peak_x * self.s_r_c)
        else:
            self.index = len(self.filtered_array)

    def find_charge_transfer(self):
        self.charge_transfer = integrate.trapz(
            self.filtered_array[self.pulse_start : self.index],
            self.x_array[self.pulse_start : self.index],
        )

    def find_est_decay(self):
        self.decay_y = self.filtered_array[int(self.peak_x * self.s_r_c) : self.index]
        if self.decay_y.size > 0:
            self.est_tau_y = self.peak_y * (1 / np.exp(1))

        if self.peak_direction == "positive":
            y = -self.est_tau_y
            decay_y = -self.decay_y
        else:
            y = self.est_tau_y
            decay_y = self.decay_y

        if self.decay_y.size > 0:
            self.decay_x = self.x_array[int(self.peak_x * self.s_r_c) : self.index]
            self.est_tau_x = np.interp(y, decay_y, self.decay_x)

        else:
            self.est_tau_x = np.nan
            self.est_tau_y = np.nan

    def find_fit_decay(self):
        if self.peak_direction == "positive":
            upper_bounds = [np.inf, np.inf, np.inf, np.inf]
            lower_bounds = [0, 0, 0, 0]
        else:
            upper_bounds = [0, np.inf, 0, np.inf]
            lower_bounds = [-np.inf, 0, -np.inf, 0]
        if self.curve_fit_type == "db_exp":
            init_param = np.array([self.peak_y, self.final_tau_x, 0, 0])
            popt, pcov = optimize.curve_fit(
                db_exp_decay,
                self.decay_x,
                self.decay_y,
                p0=init_param,
                bounds=[lower_bounds, upper_bounds],
            )
            amp_1, self.fit_tau, amp_2, tau_2 = popt
            self.fit_decay_y = (
                db_exp_decay(decay_x, amp_1, self.fit_tau, amp_2, tau_2)
                + self.z_start_y
            )
        elif self.curve_fit_type == "s_exp":
            init_param = np.array([self.peak_y, self.final_tau_x])
            popt, pcov = optimize.curve_fit(
                f=s_exp_decay,
                xdata=self.decay_x,
                ydata=self.decay_y,
                p0=init_param,
                bounds=[lower_bounds[:2], upper_bounds[:2]],
            )
            amp_1, self.fit_tau = popt
            self.fit_decay_y = s_exp_decay(self.decay_x, amp_1, self.fit_tau)

    def change_peak(self, x, y):
        self.peak_x = x / self.s_r_c
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
    def est_decay(self):
        return self.est_tau_x - self.peak_x

    def plot_est_decay(self):
        return [self.est_tau_x]

    def plot_fit_decay(self):
        return

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
            "Epoch": self.epoch,
            "Acq number": self.acq_number,
            "Peak direction": self.peak_direction,
            "Amplitude": abs(self.peak_y),
        }
        if self.find_ct:
            oepsc_dict["Charge_transfer"] = self.charge_transfer
        if self.find_edecay:
            oepsc_dict["Est_decay"] = self.est_decay()
        if self.find_fdecay:
            oepsc_dict["Curve_fit_tau"] = self.fit_tau
        return oepsc_dict
