from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.curve_fit import Log, Sigmoid, fit_iv
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseConfig, BaseEpochAnalysis
from ..registry import register_epoch, register_epoch_config
from .acq import ChirpAcquisition, ChirpAcquisitionConfig


@register_epoch_config
@dataclass(frozen=True)
class ChirpConfig(BaseConfig):
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
    acquisition_config: ChirpAcquisitionConfig

    @staticmethod
    def analysis_key() -> str:
        return "chirp"


@register_epoch
@dataclass
class CurrentClampEpoch(BaseEpochAnalysis[ChirpConfig]):
    """Aggregates current clamp acquisitions into epoch-level features.

    A ``CurrentClampEpoch`` represents one current-clamp stimulation
    protocol (e.g. a family of current-step sweeps) and computes
    summary statistics across all acquisitions in that protocol,
    including rheobase, sag, f-I curve fits, and I-V curve fits.

    Attributes:
        config: Configuration for acquisition- and epoch-level
            analysis parameters.
    """

    config: ChirpConfig

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "chirp"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: dict[int, AcquisitionData]
    ):
        """Loads the acquisitions and creates ``CurrentClampAcquistion`` instances.

        Args:
            epoch_id (int): Epoch that the acquisitions belong to.
            acquisitions (dict[int, AcquisitionData]): Acquisitions used for the
            current clamp analysis.
        """
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = ChirpAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def features(self):
        acq_params = []
        frequency_params = []
        for value in self._acquisitions.values():
            acq_data, frequency_data = value.data()
            acq_params.append(acq_data)
            frequency_params.append(frequency_data)
        self.df_dict["Acq Parameters"] = pd.DataFrame(acq_params)
        self.df_dict["Frequency"] = pd.DataFrame(frequency_params)
        self.df_dict["Epoch Parameteres"] = self.df_dict["Acq Parameters"].mean()
