from dataclasses import dataclass

from ...loader.acquisition_data import AcquisitionData
from ..base import BaseEpochAnalysis
from ..registry import register_epoch
from .acq import AcquisitionAnalysis


@register_epoch
@dataclass
class EvokedPSCEpoch(BaseEpochAnalysis):
    @staticmethod
    def analysis_key():
        return "evoked_psc"
