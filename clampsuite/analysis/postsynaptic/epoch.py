from dataclasses import dataclass, field
from typing import Dict, Literal, Union

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
        return "current_clamp"


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
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = PostSynapticAcquisition(acq_data=value)
            self._acquisitions[key] = temp
    
        def analyze(self):
            for value in self._acquisitions.values():
                value.analyze(self.config.acquisition_config)
            self.create_raw_data()
            self.get_features()
        
        def create_raw_data(self):
            pass

        def get_features(self):
            pass