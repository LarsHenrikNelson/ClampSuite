from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.curve_fit import Log, Sigmoid, fit_iv
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseConfig, BaseEpochAnalysis
from ..registry import register_epoch, register_epoch_config
from .acq import SpontaneousSpikeAcquisition, SpontaneousSpikeAcquisitionConfig


@register_epoch_config
@dataclass(frozen=True)
class SpontaneousSpikeConfig(BaseConfig):
    """Configuration for current clamp epoch and acquisition analysis.

    Serves as the single source of truth for current clamp analysis
    parameters. Instances are immutable and can be used for GUI
    generation and passed through ``ExpManager``.

    Attributes:
        acquisition_config: Parameters controlling per-acquisition
            spike detection and feature extraction.
        iv_start: Start time (s) of the window used to fit the I-V
            curve. If ``None``, the fit uses the full trace.
        iv_end: End time (s) of the window used to fit the I-V curve.
            If ``None``, the fit uses the full trace.
        rectify: Whether to fit the I-V curve as a rectifying
            (piecewise) relationship rather than a single line.
    """

    # Acquisition-level parameters
    acquisition_config: SpontaneousSpikeAcquisitionConfig = field(
        default_factory=SpontaneousSpikeAcquisitionConfig
    )

    @staticmethod
    def analysis_key() -> str:
        return "spontaneous_spikes"


@register_epoch
@dataclass
class SpontaneousSpikeEpoch(BaseEpochAnalysis[SpontaneousSpikeConfig]):
    """Aggregates current clamp acquisitions into epoch-level features.

    A ``SpontaneousSpikeEpoch`` represents one or many recordings (e.g. a family of
    current-step sweeps) and computes summary statistics across all
    acquisitions in that protocol, including rheobase, sag, f-I curve
    fits, and I-V curve fits.

    Attributes:
        config: Configuration for acquisition- and epoch-level
            analysis parameters.
    """

    config: SpontaneousSpikeConfig = field(default_factory=SpontaneousSpikeConfig)

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "spontaneous_spikes"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: dict[int, AcquisitionData]
    ):
        """Loads the acquisitions and creates ``SpontaneousSpikeAcquistion`` instances.

        Args:
            epoch_id (int): Epoch that the acquisitions belong to.
            acquisitions (dict[int, AcquisitionData]): Acquisitions used for the
            current clamp analysis.
        """
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = SpontaneousSpikeAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def features(self):
        spk_params = []
        acq_params = []
        for value in self._acquisitions.values():
            acq_data, spk_data = value.data()
            spk_params.append(pd.DataFrame(spk_data))
            acq_params.append(acq_data)

        spk_params = pd.DataFrame(spk_params)
        key_mapping = map_keys(spk_params.columns)
        spk_params = spk_params.rename(columns=key_mapping)

        acq_params = pd.DataFrame(acq_params)
        key_mapping = map_keys(acq_params.columns)
        acq_params = acq_params.rename(columns=key_mapping)

        self.df_dict["Acq Parameters"] = acq_params
        self.df_dict["Spike Parameters"] = spk_params
