from typing import Literal, Union
import numpy as np
from scipy import optimize, signal
from scipy.stats import linregress

from ..functions.curve_fit import db_exp_decay, s_exp_decay


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
        y_array: Union[np.ndarray, list],
        event_length: int,
        sample_rate: int,
        curve_fit_decay: bool = False,
        curve_fit_type: Literal[
            "s_exp",
            "db_exp",
        ] = "dp_exp",
    ):
        self.acq_number = acq_number
        self.event_pos = int(event_pos)
        self.sample_rate = sample_rate
        self.s_r_c = sample_rate / 1000
        self.curve_fit_decay = curve_fit_decay
        self.curve_fit_type = curve_fit_type
        self.fit_tau = np.nan
        self.event_length = event_length
        self.create_event(y_array, event_length)
        self.find_peak()
        self.find_event_parameters(y_array)
        self.peak_align_value = self._event_peak_x - self.array_start

    def create_event(self, y_array: Union[np.ndarray, list], event_length: int):
        self.array_start = int(self.event_pos - (2 * self.s_r_c))
        self.adjust_pos = int(self.event_pos - self.array_start)
        end = int(self.event_pos + (event_length * self.s_r_c))
        if end > len(y_array) - 1:
            self.array_end = len(y_array) - 1
        else:
            self.array_end = end
        self.create_event_array(y_array)

    def create_event_array(self, y_array: Union[np.ndarray, list]):
        self.event_array = y_array[self.array_start : self.array_end]

    # Fix the find peak to scipy find peaks
    def find_peak(self):
        peaks_1, _ = signal.find_peaks(
            -1 * self.event_array,
            prominence=4,
            width=0.4 * self.s_r_c,
            distance=int(3 * self.s_r_c),
            # rel_height=1,
        )
        # peaks_1 = signal.argrelextrema(
        #     self.event_array, comparator=np.less, order=int(3 * self.s_r_c)
        # )[0]
        peaks_1 = peaks_1[peaks_1 > self.adjust_pos]
        if len(peaks_1) == 0:
            self.find_peak_alt()
        else:
            self.peak_corr(peaks_1[0])

    def peak_corr(self, peak_1: int):
        peaks_2 = signal.argrelextrema(
            self.event_array[:peak_1],
            comparator=np.less,
            order=int(0.4 * self.s_r_c),
        )[0]
        peaks_2 = peaks_2[peaks_2 > peak_1 - 4 * self.s_r_c]
        if len(peaks_2) == 0:
            final_peak = peak_1
        else:
            peaks_3 = peaks_2[
                self.event_array[peaks_2] < 0.85 * self.event_array[peak_1]
            ]
            if len(peaks_3) == 0:
                final_peak = peak_1
            else:
                final_peak = peaks_3[0]
        self._event_peak_x = self.x_array()[int(final_peak)]
        self.event_peak_y = self.event_array[int(final_peak)]

    def find_peak_alt(self):
        peaks_1 = signal.argrelextrema(
            self.event_array, comparator=np.less, order=int(3 * self.s_r_c)
        )[0]
        peaks_1 = peaks_1[peaks_1 > self.adjust_pos]
        if len(peaks_1) == 0:
            self._event_peak_x = np.nan
            self.event_peak_y = np.nan
        else:
            self.peak_corr(peaks_1[0])

    def find_alt_baseline(self):
        baselined_array = self.event_array - np.mean(
            self.event_array[: int(1 * self.s_r_c)]
        )
        masked_array = baselined_array.copy()
        mask = np.argwhere(baselined_array <= 0)
        masked_array[mask] = 0
        peaks = signal.argrelmax(
            masked_array[0 : int(self._event_peak_x - self.array_start)], order=2
        )
        if len(peaks[0]) > 0:
            self._event_start_x = self.x_array()[peaks[0][-1]]
            self.event_start_y = self.event_array[peaks[0][-1]]
        else:
            event_start = np.argmax(
                masked_array[0 : int(self._event_peak_x - self.array_start)]
            )
            self._event_start_x = self.x_array()[event_start]
            self.event_start_y = self.event_array[event_start]
        self.event_baseline = self.event_start_y

    def find_baseline(self):
        """
         This functions finds the baseline of an event. The biggest issue with
         most methods that find the baseline is that they assume the baseline
         does not deviate from zero, however this is often not true is real
         life. This methods combines a slope finding method with a peak
         finding method.

        Returns
        -------
        None.

        """
        # baselined_array = self.event_array - np.mean(
        #     self.event_array[: int(1 * self.s_r_c)]
        # )
        baselined_array = self.event_array - np.max(
            self.event_array[: self._event_peak_x]
        )
        peak = int(self._event_peak_x - self.array_start)
        # search_start = np.argwhere(
        #     baselined_array[:peak] > 0.5 * self.event_peak_y
        # ).flatten()
        search_start = np.argwhere(
            baselined_array[:peak] > 0.35 * self.event_peak_y
        ).flatten()
        if search_start.size > 0:
            slope = (self.event_array[search_start[-1]] - self.event_peak_y) / (
                peak - search_start[-1]
            )
            new_slope = slope + 1
            i = search_start[-1]
            while new_slope > slope:
                slope = (self.event_array[i] - self.event_peak_y) / (peak - i)
                i -= 1
                new_slope = (self.event_array[i] - self.event_peak_y) / (peak - i)
            baseline_start = signal.argrelmax(
                baselined_array[int(i - 1 * self.s_r_c) : i + 2], order=2
            )[0]
            if baseline_start.size > 0:
                temp = int(baseline_start[-1] + (i - 1 * self.s_r_c))
                self._event_start_x = self.x_array()[temp]
                self.event_start_y = self.event_array[temp]
            else:
                temp = int(baseline_start.size / 2 + (i - 1 * self.s_r_c))
                self._event_start_x = self.x_array()[temp]
                self.event_start_y = self.event_array[temp]
        else:
            self.find_alt_baseline()

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
        end = self._event_peak_x - self.array_start
        start = self._event_start_x - self.array_start
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
                    baselined_event[self._event_peak_x - self.array_start :]
                    >= (self.event_peak_y - self.event_start_y) * 0.25
                )
            )
            + (self._event_peak_x - self.array_start)
        )
        decay_y = self.event_array[
            self._event_peak_x - self.array_start : return_to_baseline
        ]
        if decay_y.size > 0:
            self.est_tau_y = (
                (self.event_peak_y - self.event_start_y) * (1 / np.exp(1))
            ) + self.event_start_y
            decay_x = self.x_array()[
                self._event_peak_x - self.array_start : return_to_baseline
            ]
            self._event_tau_x = np.interp(self.est_tau_y, decay_y, decay_x)
            self.final_tau_x = (self._event_tau_x - self._event_peak_x) / self.s_r_c
        else:
            self._event_tau_x = np.nan
            self.final_tau_x = np.nan
            self.est_tau_y = np.nan

    def find_decay_array(self) -> tuple[np.ndarray, np.ndarray]:
        decay_start = self._event_peak_x - self.array_start
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
            self.calc_event_amplitude()
            self.est_decay()
            self.calc_event_rise_time()
            self.peak_align_value = self._event_peak_x - self.array_start
            if self.curve_fit_decay:
                self.fit_decay(fit_type=self.curve_fit_type)

    def mini_x_comp(self) -> list:
        x = [
            self.event_start_x(),
            self.event_peak_x(),
            self.event_tau_x(),
        ]
        return x

    def mini_y_comp(self) -> list:
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
        return np.arange(self.array_start, self.array_end) / self.s_r_c

    def plot_event_y(self) -> np.ndarray:
        return self.event_array

    def x_array(self):
        return np.arange(self.array_start, self.array_end, 1)

    def change_amplitude(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._event_peak_x = x
        self.event_peak_y = y
        self.amplitude = abs(self.event_peak_y - self.event_start_y)
        self.calc_event_rise_time()
        self.est_decay()
        self.peak_align_value = self._event_peak_x - self.array_start
        if self.curve_fit_decay:
            self.fit_decay(fit_type=self.curve_fit_type)
        self.peak_align_value = self._event_peak_x - self.array_start

    def change_baseline(self, x: Union[int, float], y: Union[int, float]):
        x = int(x * self.s_r_c)
        self._event_start_x = x
        self.event_start_y = y
        int((self._event_start_x - self.array_start) - (0.5 * self.s_r_c))
        int(self._event_start_x - self.array_start)
        self.amplitude = abs(self.event_peak_y - self.event_start_y)
        self.calc_event_rise_time()
        self.est_decay()
        if self.curve_fit_decay:
            self.fit_decay(fit_type=self.curve_fit_type)
        self.peak_align_value = self._event_peak_x - self.array_start

    def load_mini(self, event_dict: dict, final_array: np.ndarray):
        self.sample_rate_correction = None

        for key, item in event_dict.items():
            if isinstance(item, list):
                value = np.array(item)
            else:
                value = item
            if key in {"event_tau_x", "event_peak_x", "event_start_x"}:
                key = "_" + key
            if key not in (
                "mini_plot_x",
                "mini_plot_y",
                "mini_comp_y",
                "mini_comp_x",
            ):
                setattr(self, key, value)

        if self.sample_rate_correction is not None:
            self.s_r_c = self.sample_rate_correction

        self.create_event_array(final_array)

        if "_event_tau_x" or "event_tau_x" not in event_dict.keys():
            self.est_decay()
