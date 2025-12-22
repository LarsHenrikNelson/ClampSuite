from dataclasses import dataclass
from typing import Dict, Literal, Union

import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseEpochAnalysis
from ..registry import register_epoch
from .acq import AcquisitionAnalysis
from ...functions.template_psc import TemplateParams
from ...functions.mspsc import (
    EventMethods,
    deconvolve_array,
    find_events,
    template_match,
    create_events,
)


@register_epoch
@dataclass
class PSCEpoch(BaseEpochAnalysis):
    # Acquisition parameters
    template_params: TemplateParams
    sensitivity: Union[int, float] = 4
    amp_threshold: Union[int, float] = 4
    mini_spacing: Union[int, float] = 2
    min_rise_time: Union[int, float] = 0.5
    max_rise_time: Union[int, float] = 4
    min_decay_time: Union[int, float] = 0.5
    event_length: Union[int, float] = 30
    decay_rise: bool = True
    invert: bool = False
    method: EventMethods = "weiner"
    est_decay: bool = False
    curve_fit_decay: Literal[0, 1, 2] = 0

    @staticmethod
    def analysis_key():
        return "psc"
