from dataclasses import dataclass, field

import numpy as np

from .spike_ahp import AHP_KEYS
from .spike_auc import AUC_KEYS, find_spk_auc
from .spike_threshold import THRESHOLD_KEYS, ThresholdFunctions, ThresholdType
from .spike_velocity import VELOCITY_KEYS, spk_velocity
from .spike_width import WIDTH_KEYS, find_spk_width

SPIKE_PARAMS = THRESHOLD_KEYS + WIDTH_KEYS + AUC_KEYS + VELOCITY_KEYS + AHP_KEYS


class Spike:
    def __init__(
        self,
        array: np.ndarray,
        start_index: int,
        end_index: int,
        peak_index: int,
        fs: float,
    ):
        self._array = array
        start_index = self._dynamic_baseline_start(
            array, start_index, end_index, peak_index
        )
        self._analysis_variables: dict[str, int | float] = {
            "peak_index": peak_index,
            "peak_mv": array[peak_index],
            "start_index": start_index,
            "end_index": end_index,
        }
        self.fs = fs
        for i in SPIKE_PARAMS:
            self._analysis_variables[i] = np.nan

    def _dynamic_baseline_start(
        self, v: np.ndarray, start_index: int, end_index: int, peak_index: int
    ) -> int:
        """
        Finds the start of the subthreshold charging phase between two spikes.
        Looks for the point where dV/dt recovers from negative repolarization (AHP)
        to positive values (dV/dt >= 0).
        """
        dv = np.gradient(v[start_index:end_index])
        isi_dv = dv[start_index:end_index]

        # Find where dV/dt crosses >= 0 after the AHP trough
        # (search backward from the current spike peak)
        neg_or_zero = np.where(isi_dv <= 0)[0]

        if len(neg_or_zero) > 0:
            # Start immediately after the last negative/zero dV/dt sample before the spike
            start_offset = neg_or_zero[-1] + 1
            start_idx = start_index + start_offset
        else:
            # Fallback for extreme high-frequency firing: use the last 25% of the ISI
            isi_len = peak_index - start_index
            start_idx = peak_index - int(isi_len * 0.25)

        return start_idx

    def find_threshold(self, method: ThresholdType, threshold_value: float = 0.0):
        peak_index = self._analysis_variables["peak_index"]
        dv = np.gradient(self._array[self["start_index"] : peak_index])
        ddv = np.gradient(dv)
        dddv = np.gradient(ddv)
        derivatives = {
            "v": self._array[self["start_index"] : peak_index],
            "dv": dv,
            "ddv": ddv,
            "dddv": dddv,
        }
        try:
            threshold_index = ThresholdFunctions[method](
                derivatives,
                0,
                peak_index - self["start_index"],
                threshold_value=threshold_value,
                fs=self.fs,
            )
        except IndexError:
            threshold_index = ThresholdFunctions["first_derivative"](
                derivatives, 0, peak_index - self["start_index"], fs=self.fs
            )
        except IndexError:
            threshold_index = self["start_index"]
        threshold_index += self["start_index"]
        self["threshold_index"] = int(threshold_index)
        self["threshold_mv"] = self._array[int(threshold_index)]

    def find_ahp(self):
        peak = self["peak_index"]
        ahp_index = int(np.argmin(self._array[peak : self["end_index"]]) + peak)
        self["ahp_index"] = ahp_index
        self["ahp_mv"] = self._array[ahp_index]

    def find_width(self):
        output = find_spk_width(
            self._array, int(self["threshold_index"]), self["end_index"]
        )
        self._analysis_variables.update({key: o for key, o in zip(WIDTH_KEYS, output)})

    def find_auc(self):
        auc = find_spk_auc(self._array, int(self["threshold_index"]), self["end_index"])
        self._analysis_variables.update({key: a for key, a in zip(AUC_KEYS, auc)})

    def find_velocity(self):
        output = spk_velocity(
            np.gradient(self._array),
            int(self["threshold_index"]),
            self["end_index"],
            self.fs,
        )
        self._analysis_variables.update(
            {key: a for key, a in zip(VELOCITY_KEYS, output)}
        )

    def set_end_index(self, end_index: int):
        self["end_index"] = end_index

    def analyze(self, method: ThresholdType, threshold_value: float = 0.0):
        self.find_threshold(method, threshold_value)
        self.find_width()
        self.find_auc()
        self.find_ahp()
        self.find_velocity()

    def __getitem__(self, index):
        return self._analysis_variables[index]

    def __setitem__(self, index, value):
        if index in self._analysis_variables:
            self._analysis_variables[index] = value
        else:
            raise ValueError("Index not in Spike.")

    def data(self) -> dict:
        return self._analysis_variables

    def event(self) -> tuple[np.ndarray, np.ndarray]:
        if not np.isnan(self["threshold_index"]):
            alt = int(self["threshold_index"] - 0.002 * self.fs)
            start_index = max(self["start_index"], alt)
        else:
            start_index = self["start_index"]
        x = np.arange(start_index, self["end_index"]) / self.fs
        return x, self._array[start_index : self["end_index"]]
