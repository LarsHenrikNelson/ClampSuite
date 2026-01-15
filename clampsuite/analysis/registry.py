from typing import Dict, Type, List, Any, Protocol, runtime_checkable, NamedTuple

from ..loader.acquisition_data import AcquisitionData
from .base import BaseAcquisitionAnalysis, BaseEpochAnalysis


class AnalysisRegistry:
    _acquisition: Dict[str, Type[BaseAcquisitionAnalysis]] = {}
    _epoch: Dict[str, Type[BaseEpochAnalysis]] = {}

    @classmethod
    def register_acquisition(cls, param_type: Type[BaseAcquisitionAnalysis]):
        cls._acquisition[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def register_epoch(cls, param_type: Type[BaseEpochAnalysis]):
        cls._epoch[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def get_acquisition(cls, param_type: str) -> Type[BaseAcquisitionAnalysis]:
        if param_type in cls._acquisition:
            return cls._acquisition[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def get_epoch(cls, param_type: str) -> Type[BaseEpochAnalysis]:
        if param_type in cls._epoch:
            return cls._epoch[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def list_available(cls) -> tuple:
        """List all registered analyses."""
        return cls._acquisition, cls._epoch


def register_acquisition(param_type: Type[BaseAcquisitionAnalysis]):
    return AnalysisRegistry.register_acquisition(param_type)


def register_epoch(param_type: Type[BaseEpochAnalysis]):
    return AnalysisRegistry.register_epoch(param_type)
