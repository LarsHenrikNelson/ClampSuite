from dataclasses import dataclass, field
from typing import Dict, Literal, Union

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
    """Single source of truth for current clamp analysis parameters.

    This class can be used for GUI generation and passed through ExpManager.
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
    config: PostSynapticConfig = field(default_factory=PostSynapticConfig)

    @staticmethod
    def analysis_key():
        return "psc"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: Dict[int, AcquisitionData]
    ):
        self._acquisitions: dict[int, PostSynapticAcquisition] = {}
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = PostSynapticAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def analyze(self):
        for value in self._acquisitions.values():
            value.analyze(self.config.acquisition_config)
        self.create_raw_data()
        # self.get_features()

    def create_raw_data(self):
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


    def events(self):
        x = []
        y = []
        for key, value in self._acquisitions.items():
            x_, y_ = value.events()
            x.append(x_)
            y.append(y_)
        x = np.concat(x)
        y = np.concat(y)
        return x, y

    def avg_event(self, scale: bool = False) -> np.ndarray:
        _, y = self.events()
        if scale:
            ymin = y[:, :150].min(axis=1, keepdims=True)
            ymax = y[:, :150].max(axis=1, keepdims=True)
            y = (y - ymin) / (ymax - ymin)
        y = y.mean(axis=0)
        return y
        

    def get_features(self):
        pass
