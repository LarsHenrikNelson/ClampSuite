from typing import Literal, Union
import numpy as np
from scipy import optimize
from scipy.stats import linregress

from ...functions.curve_fit import SExpDecay, DExpDecay, estimate_decay
from ...functions.general import regress_subset
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
        y = self.array[
            self._analysis_variables["start_index"] : self._analysis_variables[
                "end_index"
            ]
        ]
        return y

    def find_peak(self):
        peak = find_peak(
            self._event_array(),
            self.fs,
            adjust_pos=10,
        )
        if peak > -1:
            self["peak_index"] = int(peak + int(self["start_index"]))

    def find_baseline(self):
        peak = self["peak_index"] - self["start_index"]
        baseline = find_baseline(self._event_array(), int(peak), self.fs)
        self["baseline_index"] = int(baseline + self["start_index"])

    def estimate_decay(self):
        event_array = self.array[self["peak_index"] : self["end_index"]]
        baseline = self.array[self["baseline_index"]]
        event_array = event_array - baseline
        est_tau_y, est_tau_index = estimate_decay(event_array)
        self["est_tau_y"] = est_tau_y + baseline
        self["est_tau_index"] = est_tau_index + self["peak_index"]

    def curve_fit_decay(self, curve_fit_type: Literal[0, 1, 2], end_index: int | None):
        peak = self["peak_index"]
        est_tau = self.est_tau()
        if np.isnan(est_tau):
            if end_index is not None:
                end_index = min(self["end_index"], end_index)
            else:
                end_index = self["end_index"]
        elif end_index is not None:
            event_end = int((est_tau * 5) * self.s_r_c) + self["start_index"]
            if event_end < end_index:
                end_index = event_end
        else:
            event_end = int((est_tau * 5) * self.s_r_c) + self["start_index"]
            end_index = min(self["end_index"], event_end)

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
        self.find_peak()
        if self["peak_index"] > 0:
            self.find_baseline()
            self.estimate_decay()

    def amplitude(self) -> float:
        return np.abs(
            self.array[self["peak_index"]] - self.array[self["baseline_index"]]
        )

    def peak(self) -> tuple[float, float]:
        return self["peak_index"] / self.s_r_c, self.array[self["peak_index"]]

    def baseline(self) -> tuple[float, float]:
        return self["baseline_index"] / self.s_r_c, self.array[self["baseline_index"]]

    def decay_fit(self) -> tuple[np.ndarray, np.ndarray]:
        if self._decay_fit is None:
            return np.array([]), np.array([])
        else:
            x = np.arange(self["peak_index"], self["end_index"]) / self.s_r_c
            y = self._decay_fit.predict(x - x[0])
            return x, y

    def rise_time(
        self,
        output_type: Literal["ms", "samples"] = "ms",
    ) -> float | int:
        if output_type == "ms":
            return (self["peak_index"] - self["baseline_index"]) / (self.fs / 1000)
        else:
            return self["peak_index"] - self["baseline_index"]

    def rise_rate_regress(
        self,
        start: float = 0.1,
        stop: float = 0.9,
        output_type: Literal["ms", "samples"] = "ms",
    ):
        slope = regress_subset(
            self.array[self["baseline_index"] : self["peak_index"]], start, stop
        )
        if output_type == "ms":
            return slope * (self.fs / 1000)
        else:
            return np.abs(slope)

    def est_tau(
        self,
        output_type: Literal["ms", "samples"] = "ms",
    ) -> float:
        if output_type == "ms":
            return (self["est_tau_index"] - self["baseline_index"]) / (self.fs / 1000)
        else:
            return self["est_tau_index"] - self["baseline_index"]

    def rise_rate(self, output_type: Literal["ms", "samples"] = "ms"):
        return self.amplitude() / self.rise_time(output_type=output_type)

    def data(
        self,
        output_type: Literal["ms", "samples"] = "ms",
    ) -> dict:
        output = {}
        output["est_tau_ms"] = self.est_tau(output_type=output_type)
        output["rise_time_ms"] = self.rise_time(output_type=output_type)
        output["rise_rate_pa/ms_regress"] = self.rise_rate_regress(
            output_type=output_type
        )
        output["amplitude_pa"] = self.amplitude()
        output["rise_rate_pa/ms"] = self.rise_rate()
        output["peak_ms"] = self._analysis_variables["peak_index"] / (self.fs / 1000)
        if self._decay_fit:
            fit_values = self._decay_fit.params._asdict()
            output.update({f"fit_{key}": value for key, value in fit_values.items()})
        return output

    def event(self) -> tuple[np.ndarray, np.ndarray]:
        y = self._event_array()
        x = np.arange(
            self._analysis_variables["start_index"],
            self._analysis_variables["end_index"],
        ) / (self.fs / 1000)
        return x, y
