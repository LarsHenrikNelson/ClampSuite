from ...loader.acquisition_data import AcquisitionData
from ..base import BaseAcquisitionAnalysis
from ..registry import register_acquisition


@register_acquisition
class AcquisitionAnalysis(BaseAcquisitionAnalysis):
    @staticmethod
    def analysis_key():
        return "evoked_psc"
