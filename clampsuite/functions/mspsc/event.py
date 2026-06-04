from typing import Literal, Union
import numpy as np
from scipy import optimize
from scipy.stats import linregress

from ...functions.curve_fit import SExpDecay, DExpDecay, estimate_decay
from .event_peak import find_peak
from .event_baseline import find_baseline


class PostsynapticEvent:
    """
    This class is a base Mini class that contains all the functions
    needed to analyze a mini event.
    """

    def __getitem__(self, index):
        return self._analysis_variables[index]

    def __setitem__(self, index, value):
        if index in self._analysis_variables:
            self._analysis_variables[index] = value
        else:
            raise ValueError("Index not in PostsynapticEvent.")

    def __init__(
        self,
        array: np.ndarray,
        fs: float | int,
        start_index: int,
        event_length: int | float,
    ):
        self.array = array
        self.event_length = event_length
        self.s_r_c = fs / 1000
        self.fs = fs

        self._analysis_variables: dict[str, int | float] = {}
        self._analysis_variables["peak_index"] = -1
        self._analysis_variables["baseline_index"] = -1
        self._analysis_variables["start_index"] = start_index
        self._analysis_variables["end_index"] = start_index + int(
            event_length * self.s_r_c
        )
        self._analysis_variables["rise_rate_10_90"] = np.nan
        self._analysis_variables["est_tau_index"] = -1
        self._analysis_variables["est_tau_y"] = np.nan
        self._decay_fit = None

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
            self.fs,
            adjust_pos=10,
        )
        self._analysis_variables["peak_index"] = int(
            peak + int(self._analysis_variables["start_index"])
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
        peak = self["peak_index"] - self["start_index"]
        baseline = int(self["baseline_index"] - self["start_index"])
        est_tau_y, est_tau_index = estimate_decay(
            self._event_array(), baseline, int(peak)
        )
        self["est_tau_y"] = est_tau_y
        self["est_tau_index"] = est_tau_index + self["start_index"]

    def curve_fit_decay(self, curve_fit_type: Literal[0, 1, 2], end_index: int | None):
        peak = self["peak_index"]
        if end_index is None:
            end_index = int(self["end_index"])
        y = self.array[peak:end_index]
        x = np.arange(y.size) / self.s_r_c
        if curve_fit_type > 0:
            if curve_fit_type == 1:
                self._decay_fit = SExpDecay()
            else:
                self._decay_fit = DExpDecay()
            self._decay_fit.fit(x, y)

    def decay(self) -> tuple[np.ndarray, np.ndarray]:
        if self._decay_fit is not None:
            fit_object = self._decay_fit
            tau = fit_object.params.tau
            end = tau * 5
            x = np.linspace(0, end, endpoint=False)
            y = fit_object.predict(x)
        else:
            x = np.array([])
            y = np.array([])
        return x, y

    def analyze(self):
        self.find_baseline()
        self.estimate_decay()

    def amplitude(self) -> float:
        return np.abs(
            self.array[self["peak_index"]] - self.array[self["baseline_index"]]
        )

    def rise_time(self) -> float:
        return (self["peak_index"] - self["baseline_index"]) / (self.fs / 1000)

    def est_tau(self) -> float:
        return (self["est_tau_index"] - self["baseline_index"]) / (self.fs / 1000)

    def data(self) -> dict:
        return self._analysis_variables
