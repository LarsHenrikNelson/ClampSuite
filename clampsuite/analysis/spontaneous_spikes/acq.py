from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from scipy import signal

from clampsuite.types import CurrentClamp

from ...functions.current_clamp import (
    adaptation_index,
    coefficient_of_variation,
    divisor_sfa,
    local_sfa,
)
from ...functions.spontaneous_spikes import (
    ANALYSIS_VARIABLES,
    find_spikes,
    presence,
    waveform_features,
)
from ...functions.utilities import map_keys
from ...loader import AcquisitionData
from ..base import BaseAcquisitionAnalysis, BaseAcquisitionConfig
from ..registry import register_acq_config, register_acquisition


@register_acq_config
@dataclass(frozen=True)
class SpontaneousSpkAcquisitionConfig(BaseAcquisitionConfig):
    """Configuration class for current clamp acquisition analysis.

    Attributes:
        min_spike_voltage: Minimum voltage a spike needs to reach
            to be considered a spike.
        threshold_method: Method used to find the spike threshold.
        min_spikes: The minimum number of spikes an acquisition must have to be
        considered a "spiking acquisition".
        velocity_threshold: The velocity in mV/ms a spike needs to achieve to be
        considered a spike.
        fit_sag_decay: An integer indicating what type of exponential decay to fit to
        the voltage sag decay. Use 0 if you do not want to fit a decay.
        fraction_window: A tuple containing the start and end of the pulse injection
        that you want to get the delta V from.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "spontaneous_spikes"

    threshold: float = 7.0
    prominence: float = 2.0
    start: float = 2.0
    end: float = 3.0


@register_acquisition
@dataclass
class SpontaneousSpkAcquisition(BaseAcquisitionAnalysis):
    """Spontaneous spiking acquisition analysis class

    Attributes:
        acq_data: Raw acquisition data and metadata (inherited from
            ``BaseAcquisitionAnalysis``), including pulse timing and
            sampling rate.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "spontaneous_spikes"

    def __post_init__(self):
        self._analysis_variables = {
            "spike_index": np.ndarray(0),
            "waveforms": np.ndarray(0),
        }

    def analyze(self, config: SpontaneousSpkAcquisitionConfig | None) -> None:
        """_summary_

        Args:
            config: Analysis configuration. Default parameters for the config if passed
                as ``None`` are threshold=7.0, prominence=2.0, start=2.0, end=3.0.
        """
        if config is None:
            config = SpontaneousSpkAcquisitionConfig()
        acquisition = self.acq_data.acquisition
        spikes, waveforms = find_spikes(acquisition, self.acq_data.fs, **asdict(config))
        self._analysis_variables["spike_index"] = spikes
        self._analysis_variables["waveforms"] = waveforms
        if len(spikes) > 0:
            features = waveform_features(waveforms)
            self._analysis_variables.update(asdict(features))

    def data(
        self, output_type: Literal["ms", "samples"] = "ms", format_keys: bool = False
    ):
        rec_length = self.acq_data.acquisition.size / self.acq_data.fs
        if output_type == "ms":
            ms = self.acq_data.fs / 1000
            spike_times = self._analysis_variables["spike_index"] / ms
        else:
            spike_times = self._analysis_variables["spike_index"]
            ms = 1
        iei = np.diff(spike_times)
        acq_data = {
            "frequency_hz": self._analysis_variables["spike_index"].size / rec_length,
            "n_spikes": self._analysis_variables["spike_index"].size,
            "iei": iei.mean() if len(iei) > 0 else np.nan,
            "exp(log(iei)": np.exp(np.mean(np.log(iei))) if len(iei) > 0 else np.nan,
            "cv": coefficient_of_variation(spike_times),
            "adaptation_index": adaptation_index(spike_times),
            "divisor_sfa": divisor_sfa(spike_times),
            "local_sfa": local_sfa(spike_times),
        }
        acq_data.update(
            asdict(
                presence(spike_times, 0, rec_length * 1000),
            )
        )
        for i in ANALYSIS_VARIABLES:
            if i in self._analysis_variables:
                if "index" in i:
                    key = i.replace("index", output_type)
                    acq_data[key] = self._analysis_variables[i].mean() / ms
                else:
                    acq_data[i] = self._analysis_variables[i].mean()
        spk_data = self._analysis_variables.copy()

        if output_type == "ms":
            for key, value in spk_data.items():
                if "index" in key:
                    spk_data[key] = value / self.acq_data.s_r_c

        if format_keys:
            key_mapper = map_keys(acq_data.keys())
            acq_data = {key_mapper[k]: v for k, v in acq_data.items()}
            key_mapper = map_keys(spk_data.keys())
            spk_data = {key_mapper[k]: v for k, v in spk_data.items()}

        return acq_data, spk_data
