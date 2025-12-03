from typing import Literal, Union
import numpy as np
from scipy import optimize
from scipy.stats import linregress

from ..loader.acquisition_data import AcquisitionData
from ..functions.curve_fit import SExpDecay, DExpDecay


class MiniEvent:
    """
    This class is a base Mini class that contains all the functions
    needed to analyze a mini event.
    """

    def __repr__(self):
        return f"{self.mini_class}"

    def __init__(self):
        self.mini_class = "Mini"

        self._analysis_variables = {
            "decay_fit": None,
            "peak_index": np.nan,
            "baseline_index": np.nan
        }

    def analyze(
        self,
        acq_data: AcquisitionData,
        start_index: int,
        event_length: int,
        array: Union[np.ndarray, list],
        curve_fit_type: Literal[
            "none",
            "s_exp",
            "d_exp",
        ] = "s_exp",
    ):
        self.event_pos = start_index
        self.curve_fit_type = curve_fit_type

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

