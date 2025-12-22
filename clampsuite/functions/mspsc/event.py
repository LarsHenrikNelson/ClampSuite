from typing import Literal, Union
import numpy as np
from scipy import optimize
from scipy.stats import linregress

from ...loader.acquisition_data import AcquisitionData
from ...functions.curve_fit import SExpDecay, DExpDecay, estimate_decay
from .event_peak import find_peak
from .event_baseline import find_baseline


class PostsynapticEvent:
    """
    This class is a base Mini class that contains all the functions
    needed to analyze a mini event.
    """

    def __init__(
        self,
        array: np.ndarray,
        fs: float | int,
        start_index: int,
        event_length: int | float,
        curve_fit_type: Literal[0, 1, 2] = 0,
    ):
        self.array = array
        self.event_length = event_length
        self.curve_fit_type = curve_fit_type
        self.s_r_c = fs / 1000
        self.fs = fs

        self._analysis_variables = {}
        self._analysis_variables["decay_fit"] = None
        self._analysis_variables["peak_index"] = np.nan
        self._analysis_variables["baseline_index"] = np.nan
        self._analysis_variables["start_index"] = start_index
        self._analysis_variables["end_index"] = start_index + int(
            event_length * self.s_r_c
        )
        self._analysis_variables["rise_time"] = np.nan
        self._analysis_variables["rise_rate"] = np.nan
        self._analysis_variables["rise_rate_10_90"] = np.nan
        self._analysis_variables["est_decay"] = np.nan
        self._analysis_variables["est_decay_y"] = np.nan

    def get_variable(self, variable: str) -> None | float | int:
        return self._analysis_variables[variable]

    def _event_array(self) -> np.ndarray:
        event_array = self.array[
            self._analysis_variables["start_index"] : self._analysis_variables[
                "end_index"
            ]
        ]
        return event_array

    def find_peak(self):
        peak = find_peak(
            self._event_array(),
            self.s_r_c,
            adjust_pos=10,
        )
        self._analysis_variables["peak_index"] = int(
            peak + self._analysis_variables["start_index"]
        )

    def find_baseline(self):
        peak = (
            self._analysis_variables["peak_index"]
            - self._analysis_variables["start_index"]
        )
        baseline = find_baseline(self._event_array(), int(peak), self.fs)
        self._analysis_variables["baseline_index"] = int(
            baseline + self._analysis_variables["start_index"]
        )

    def estimate_decay(self):
        peak = (
            self._analysis_variables["peak_index"]
            - self._analysis_variables["start_index"]
        )
        baseline = (
            self._analysis_variables["baseline_index"]
            - self._analysis_variables["start_index"]
        )
        est_tau_y, est_tau_index = estimate_decay(
            self._event_array(), baseline, int(peak)
        )
        self._analysis_variables["est_tau_y"] = est_tau_y
        self._analysis_variables["est_tau_index"] = (
            est_tau_index + self._analysis_variables["start_index"]
        )
        self._analysis_variables["est_tau"] = (est_tau_index - peak) / self.s_r_c

    def curve_fit_decay(self, curve_fit_type: Literal[1, 2], end_index: int | None):
        peak = self._analysis_variables["peak_index"]
        if end_index is None:
            end_index = self._analysis_variables["end_index"]
        y = self.array[peak:end_index]
        x = np.arange(y.size) / self.s_r_c
        if self.curve_fit_type > 0:
            if self.curve_fit_type == 1:
                temp_output = SExpDecay()
            else:
                temp_output = DExpDecay()
            temp_output.fit(x, y)
            self._analysis_variables["decay_fit"] = temp_output

    def decay(self) -> tuple[np.ndarray, np.ndarray]:
        if self._analysis_variables["decay_fit"] is not None:
            fit_object = self._analysis_variables["sag_fit"]
            tau = fit_object.params.tau
            end = tau * 5
            x = np.linspace(0, end, endpoint=False)
            y = fit_object.predict(x)
        else:
            x = np.array([])
            y = np.array([])
        return x, y

    def set_amplitude(self, x: Union[int, float], y: Union[int, float]):
        # x = int(x * self.s_r_c)
        self._event_peak_x = x
        self.event_peak_y = y
        self.amplitude = abs(self.event_peak_y - self.event_start_y)
        # self.calc_event_rise_time()
        # self.est_decay()
        # self.peak_align_value = self._event_peak_x - self._array_start
        # if self.curve_fit_decay:
        #     self.fit_decay(fit_type=self.curve_fit_type)
        # self.peak_align_value = self._event_peak_x - self._array_start

    def set_baseline(self, x: Union[int, float], y: Union[int, float]):
        # x = int(x * self.s_r_c)
        self._event_start_x = x
        self.event_start_y = y
        # int((self._event_start_x - self._array_start) - (0.5 * self.s_r_c))
        # int(self._event_start_x - self._array_start)
        # self.amplitude = abs(self.event_peak_y - self.event_start_y)
        # self.calc_event_rise_time()
        # self.est_decay()
        # if self.curve_fit_decay:
        #     self.fit_decay(fit_type=self.curve_fit_type)
        # self.peak_align_value = self._event_peak_x - self._array_start
