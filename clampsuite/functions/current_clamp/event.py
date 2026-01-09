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
    ):
        self.array = array
        self.start_index = start_index
        self.end_index = end_index
        self._analysis_variables: dict[str, int | float] = dict(
            peak_index=peak_index, peak_mv=array[peak_index]
        )
        for i in SPIKE_PARAMS:
            self._analysis_variables[i] = np.nan

    def find_threshold(self, method: ThresholdType, threshold_value: float = 0.0):
        dv = np.gradient(self.array[self.start_index : self.end_index])
        ddv = np.gradient(dv)
        dddv = np.gradient(ddv)
        derivatives = {
            "v": self.array[self.start_index : self.end_index],
            "dv": dv,
            "ddv": ddv,
            "dddv": dddv,
        }
        try:
            if method == "allen_institute":
                threshold_index = ThresholdFunctions["allen_institute"](
                    derivatives, self.start_index, self.end_index, threshold_value
                )
            else:
                threshold_index = ThresholdFunctions[method](
                    derivatives, self.start_index, self.end_index
                )
        except IndexError:
            threshold_index = ThresholdFunctions["first_derivative"](
                derivatives, self.start_index, self.end_index
            )
        except IndexError:
            threshold_index = self.start_index
        threshold_index += self.start_index
        self._analysis_variables["threshold_index"] = threshold_index
        self._analysis_variables["threshold_mv"] = self.array[threshold_index]

    def find_ahp(self):
        peak = self._analysis_variables["peak_index"]
        ahp_index = int(np.argmin(self.array[peak : self.end_index]) + peak)
        self._analysis_variables["ahp_index"] = ahp_index
        self._analysis_variables["ahp_mv"] = self.array[ahp_index]

    def find_width(self):
        output = find_spk_width(
            self.array, int(self._analysis_variables["threshold_index"]), self.end_index
        )
        self._analysis_variables.update({key: o for key, o in zip(WIDTH_KEYS, output)})

    def find_auc(self):
        auc = find_spk_auc(
            self.array, int(self._analysis_variables["threshold_index"]), self.end_index
        )
        self._analysis_variables.update({key: a for key, a in zip(AUC_KEYS, auc)})

    def find_velocity(self):
        output = spk_velocity(
            np.gradient(self.array),
            int(self._analysis_variables["threshold_index"]),
            self.end_index,
        )
        self._analysis_variables.update(
            {key: a for key, a in zip(VELOCITY_KEYS, output)}
        )

    def set_end(self, end_index: int):
        self.end_index = end_index

    def analyze(self, method: ThresholdType, threshold_value: float = 0.0):
        self.find_threshold(method, threshold_value)
        self.find_auc()
        self.find_ahp()
        self.find_velocity()

    def data(self):
        return self._analysis_variables
