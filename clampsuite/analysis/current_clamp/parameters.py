from typing import NamedTuple, Union, Literal

from ...functions.current_clamp import ThresholdType
from ..registry import register_params


@register_params
class CurrentClampParameters(NamedTuple):
    min_spike_voltage: Union[int, float] = 0
    threshold_method: ThresholdType = "third_derivative"
    min_spikes: int = 1
    side: Literal["left", "right"] = "right"
    proportion: float = 0.5
    iv_start: float | None = None
    iv_end: float | None = None

    @staticmethod
    def analysis_key() -> str:
        return "current_clamp"

    def acquisition(self):
        return {
            "min_spike_voltage": self.min_spike_voltage,
            "threshold_method": self.threshold_method,
            "min_spikes": self.min_spikes,
            "side": self.side,
            "proportion": self.proportion,
        }

    def final(self):
        return {
            "iv_start": self.iv_start,
            "iv_end": self.iv_end,
        }
