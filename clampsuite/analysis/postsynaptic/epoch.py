from dataclasses import dataclass, field
from typing import Any, Literal, Union

import numpy as np
import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.mspsc import (
    EventMethods,
    create_events,
    deconvolve_array,
    find_events,
    template_match,
)
from ...functions.template_psc import TemplateParams
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseConfig, BaseEpochAnalysis
from ..registry import register_epoch, register_epoch_config
from .acq import PostSynapticAcquisition, PostSynapticAcquisitionConfig


@register_epoch_config
@dataclass(frozen=True)
class PostSynapticConfig(BaseConfig):
    """Configuration for postsynaptic epoch and acquisition analysis.

    Serves as the single source of truth for postynaptic analysis
    parameters. Instances are immutable and can be used for GUI
    generation and passed through ``ExpManager``.

    Attributes:
        acquisition_config: Parameters controlling per-acquisition
            spike detection and feature extraction.
        curve_fit_decay (0, 1, 2, optional): Exponential curve fit type to use for
        fitting PSC decays.
    """

    # Acquisition-level parameters
    acquisition_config: PostSynapticAcquisitionConfig = field(
        default_factory=PostSynapticAcquisitionConfig
    )

    # Epoch-level parameters
    curve_fit_decay: Literal[0, 1, 2] = 0

    @staticmethod
    def analysis_key() -> str:
        return "psc"


@register_epoch
@dataclass
class PostSynapticEpoch(BaseEpochAnalysis):
    """Aggregates PSC acquisitions into epoch-level features.

    A ``PostSynapticEpoch`` represents one long or many small recordings and computes
    summary statistics across all aquisitions.

    Attributes:
        config: Configuration for acquisition- and epoch-level
            analysis parameters.
    """

    config: PostSynapticConfig = field(default_factory=PostSynapticConfig)

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "psc"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: dict[int, AcquisitionData]
    ):
        """Loads the acquisitions and creates ``PostSynapticAcquistion`` instances.

        Args:
            epoch_id (int): Epoch that the acquisitions belong to.
            acquisitions (dict[int, AcquisitionData]): Acquisitions used for the
            current clamp analysis.
        """
        self._acquisitions: dict[int, PostSynapticAcquisition] = {}
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = PostSynapticAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def analyze(self):
        """Analyzes the acquistions in an epoch."""
        for value in self._acquisitions.values():
            value.analyze(self.config.acquisition_config)

    def features(self):
        self.create_raw_data()
        self.get_features()

    def create_raw_data(self):
        """Generates the ``Event Parameters`` and ``Acq Parameters`` dataframes from
        the raw acquisitions
        """
        event_params = []
        acq_params = []
        for value in self._acquisitions.values():
            acq_data, event_data = value.data()
            event_params.append(pd.DataFrame(event_data))
            acq_params.append(acq_data)

        acq_params = pd.DataFrame(acq_params)
        key_mapping = map_keys(acq_params.columns)
        acq_params = acq_params.rename(columns=key_mapping)

        event_params = pd.concat(event_params)
        key_mapping = map_keys(event_params.columns)
        event_params = event_params.rename(columns=key_mapping)

        self.df_dict["Event Parameters"] = event_params
        self.df_dict["Acq Parameters"] = acq_params

    def events(self) -> tuple[np.ndarray, np.ndarray]:
        """Compiles all events in each acquisition.

        Returns:
            tuple[np.ndarray, np.ndarray]: PSC events
        """
        x = []
        y = []
        for value in self._acquisitions.values():
            x_, y_ = value.events()
            x.append(x_)
            y.append(y_)
        x = np.concat(x)
        y = np.concat(y)
        return x, y

    def avg_event(self, scale: bool = False) -> np.ndarray:
        """Creates an average PSC event.

        Args:
            scale (bool, optional): _description_. Defaults to False.

        Returns:
            np.ndarray: Average PSC event
        """
        _, y = self.events()
        if scale:
            ymin = y[:, :150].min(axis=1, keepdims=True)
            ymax = y[:, :150].max(axis=1, keepdims=True)
            y = (y - ymin) / (ymax - ymin)
        y = y.mean(axis=0)
        return y

    def get_features(self):
        """Creates the ``Epoch Parameters`` dataframe"""
        event_params = self.df_dict["Event Parameters"]
        acq_params = self.df_dict["Acq Parameters"]
        ep_data = event_params.mean().to_frame().T
        ep_data = ep_data.drop(columns=["Acq Number"])
        iei = event_params.groupby("Acq Number")["Peak (ms)"].diff().values
        iei = iei[~np.isnan(iei)]
        ep_data["IEI (ms)"] = np.mean(iei)
        ep_data["exp(log(IEI (ms)))"] = np.exp(np.mean(np.log(iei)))
        ep_data["Freq (Hz)"] = np.mean(acq_params["Freq (Hz)"])
        self.df_dict["Epoch Parameters"] = ep_data
