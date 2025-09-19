from typing import Literal, Union
import numpy as np
from scipy import optimize
from scipy.stats import linregress

from ..functions.curve_fit.decay_fit import db_exp_decay, s_exp_decay


class MiniEvent:
    """
    This class is a base Mini class that contains all the functions
    needed to analyze a mini event.
    """

    def __repr__(self):
        return f"{self.mini_class}"

    def __init__(self):
        self.mini_class = "Mini"

    def analyze(
        self,
        acq_number: int,
        event_pos: int,
        array: Union[np.ndarray, list],
        event_length: float,
        sample_rate: int,
        curve_fit_type: Literal[
            "none",
            "s_exp",
            "d_exp",
        ] = "s_exp",
    ):
        self.acq_number = acq_number
        self.event_pos = event_pos
        self.sample_rate = sample_rate
        self.curve_fit_type = curve_fit_type
        self.s_r_c = sample_rate / 1000
        self.event_length = int(event_length * self.s_r_c)
        self.array = array
        self.event_start, self.event_end = self.find_event_limits(
            self.array, 2 * self.s_r_c
        )
        self.find_peak()
        self.find_event_parameters(array)
        self.adjust_pos = int(self.event_pos - self.event_start)

    def find_event_limits(self, array: Union[np.ndarray, list], offset: int = 20):
        event_start = int(self.event_pos - offset)
        end = int(self.event_pos + self.event_length)
        if end > len(array) - 1:
            event_end = len(array) - 1
        else:
            event_end = end
        return event_start, event_end


    def calc_event_amplitude(self):
        self.amplitude = abs(self.event_peak_y - self.event_start_y)

    def calc_event_rise_time(self):
        """
        This function calculates the rise rate (10-90%) and the rise time
        (end of baseline to peak).

        Returns
        -------
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.

        """
        end = self._event_peak_x - self._array_start
        start = self._event_start_x - self._array_start
        rise_array = self.event_array[start:end]
        rise_y = rise_array[int(len(rise_array) * 0.1) : int(len(rise_array) * 0.9)]
        rise_x = (
            np.arange(int(len(rise_array) * 0.1), int(len(rise_array) * 0.9))
            + self._event_start_x
        ) / self.s_r_c
        self.rise_time = (self._event_peak_x - self._event_start_x) / self.s_r_c
        if len(rise_y) > 3:
            self.rise_rate = abs(linregress(rise_x, rise_y)[0])
        else:
            self.rise_rate = np.nan

    def est_decay(self):
        baselined_event = self.event_array - self.event_start_y
        return_to_baseline = int(
            (
                np.argmax(
                    baselined_event[self._event_peak_x - self._array_start :]
                    >= (self.event_peak_y - self.event_start_y) * 0.25
                )
            )
            + (self._event_peak_x - self._array_start)
        )
        decay_y = self.event_array[
            self._event_peak_x - self._array_start : return_to_baseline
        ]
        if decay_y.size > 0:
            self.est_tau_y = (
                (self.event_peak_y - self.event_start_y) * (1 / np.exp(1))
            ) + self.event_start_y
            decay_x = self.x_array()[
                self._event_peak_x - self._array_start : return_to_baseline
            ]
            self._event_tau_x = np.interp(self.est_tau_y, decay_y, decay_x)
            self.final_tau_x = (self._event_tau_x - self._event_peak_x) / self.s_r_c
        else:
            self._event_tau_x = np.nan
            self.final_tau_x = np.nan
            self.est_tau_y = np.nan

    def find_decay_array(self) -> tuple[np.ndarray, np.ndarray]:
        decay_start = self._event_peak_x - self._array_start
        decay_temp = self.event_array[decay_start:]
        decay_end_temp = np.where(decay_temp > self.event_start_y)[0]
        if len(decay_end_temp) > 0:
            decay_end = decay_end_temp[0]
        else:
            decay_end = np.argmax(decay_temp)
        decay_y = decay_temp[:decay_end]
        decay_x = np.arange(len(decay_y))
        return decay_y, np.asarray(decay_x, dtype=np.float64)

    def fit_decay(self, fit_type):
        try:
            decay_y, decay_x = self.find_decay_array()
            est_tau = self._event_tau_x - self._event_peak_x
            if fit_type == "db_exp":
                upper_bounds = [0, np.inf, 0, np.inf]
                lower_bounds = [-np.inf, 0, -np.inf, 0]
                init_param = np.array([self.event_peak_y, est_tau, 0, 0])
                popt, _ = optimize.curve_fit(
                    db_exp_decay,
                    decay_x,
                    decay_y,
                    p0=init_param,
                    bounds=[lower_bounds, upper_bounds],
                )
                amp_1, self.fit_tau, amp_2, tau_2 = popt
                self.fit_decay_y = (
                    db_exp_decay(decay_x, amp_1, self.fit_tau, amp_2, tau_2)
                    + self.event_start_y
                )
            else:
                upper_bounds = [0, np.inf]
                lower_bounds = [-np.inf, 0]
                init_param = np.array([self.event_peak_y, est_tau])
                popt, _ = optimize.curve_fit(
                    s_exp_decay,
                    decay_x,
                    decay_y,
                    p0=init_param,
                    bounds=[lower_bounds, upper_bounds],
                )
                amp_1, self.fit_tau = popt
                self.fit_decay_y = s_exp_decay(decay_x, amp_1, self.fit_tau)
            self.fit_decay_x = (decay_x + self._event_peak_x) / self.s_r_c
        except (RuntimeError, ValueError):
            self.fit_decay_x = np.nan
            self.fit_decay_y = np.nan
            self.fit_tau = np.nan

    def find_event_parameters(self, y_array: Union[np.ndarray, list]):
        if self._event_peak_x is np.nan:
            pass
        else:
            self.find_baseline()
            self._event_pos = self._event_start_x
            self.create_event(y_array, offset=5)
            self.calc_event_amplitude()
            self.est_decay()
            self.calc_event_rise_time()
            self.peak_align_value = self._event_peak_x - self._array_start
            if self.curve_fit_decay:
                self.fit_decay(fit_type=self.curve_fit_type)

    def event_x_comp(self) -> list:
        x = [
            self.event_start_x(),
            self.event_peak_x(),
            self.event_tau_x(),
        ]
        return x

    def event_y_comp(self) -> list:
        y = [self.event_start_y, self.event_peak_y, self.est_tau_y]
        return y

    def event_tau_x(self) -> float:
        if not np.isnan(self._event_tau_x):
            return self._event_tau_x / self.s_r_c
        else:
            return self._event_tau_x

    def event_start_x(self) -> Union[int, float]:
        if not np.isnan(self._event_start_x):
            return self._event_start_x / self.s_r_c
        else:
            return self._event_start_x

    def event_peak_x(self) -> Union[int, float]:
        if not np.isnan(self._event_peak_x):
            return self._event_peak_x / self.s_r_c
        else:
            return self._event_peak_x

    def plot_event_x(self) -> np.ndarray:
        return np.arange(self._array_start, self._array_end) / self.s_r_c

    def plot_event_y(self) -> np.ndarray:
        return self.event_array

    def x_array(self):
        return np.arange(self._array_start, self._array_end, 1)

    def set_amplitude(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._event_peak_x = x
        self.event_peak_y = y
        self.amplitude = abs(self.event_peak_y - self.event_start_y)
        self.calc_event_rise_time()
        self.est_decay()
        self.peak_align_value = self._event_peak_x - self._array_start
        if self.curve_fit_decay:
            self.fit_decay(fit_type=self.curve_fit_type)
        self.peak_align_value = self._event_peak_x - self._array_start

    def set_baseline(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._event_start_x = x
        self.event_start_y = y
        int((self._event_start_x - self._array_start) - (0.5 * self.s_r_c))
        int(self._event_start_x - self._array_start)
        self.amplitude = abs(self.event_peak_y - self.event_start_y)
        self.calc_event_rise_time()
        self.est_decay()
        if self.curve_fit_decay:
            self.fit_decay(fit_type=self.curve_fit_type)
        self.peak_align_value = self._event_peak_x - self._array_start

    def load_event(self, event_dict: dict, final_array: np.ndarray):
        self.sample_rate_correction = None

        for key, item in event_dict.items():
            if isinstance(item, list):
                value = np.array(item)
            else:
                value = item
            if key not in (
                "mini_plot_x",
                "mini_plot_y",
                "mini_comp_y",
                "mini_comp_x",
                "x_array",
            ):
                setattr(self, key, value)

        if self.sample_rate_correction is not None:
            self.s_r_c = self.sample_rate_correction

        self.create_event_array(final_array)

        if "_event_tau_x" or "event_tau_x" not in event_dict.keys():
            self.est_decay()
