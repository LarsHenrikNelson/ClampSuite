from typing import Any, ClassVar, NamedTuple, Protocol, runtime_checkable

from ..loader.acquisition_data import AcquisitionData
from .base import (
    BaseAcquisitionAnalysis,
    BaseAcquisitionConfig,
    BaseConfig,
    BaseEpochAnalysis,
)


class AnalysisRegistry:
    """Analysis registry of acquisitions and epoch, and their respective config classes."""

    _acquisition: ClassVar[dict[str, type[BaseAcquisitionAnalysis]]] = {}
    _epoch: ClassVar[dict[str, type[BaseEpochAnalysis]]] = {}
    _epoch_config: ClassVar[dict[str, type[BaseConfig]]] = {}
    _acq_config: ClassVar[dict[str, type[BaseAcquisitionConfig]]] = {}

    @classmethod
    def register_acquisition(cls, param_type: type[BaseAcquisitionAnalysis]):
        cls._acquisition[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def register_epoch(cls, param_type: type[BaseEpochAnalysis]):
        cls._epoch[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def register_epoch_config(cls, param_type: type[BaseConfig]):
        cls._epoch_config[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def register_acq_config(cls, param_type: type[BaseAcquisitionConfig]):
        cls._acq_config[param_type.analysis_key()] = param_type
        return param_type

    @classmethod
    def get_acquisition(cls, param_type: str) -> type[BaseAcquisitionAnalysis]:
        if param_type in cls._acquisition:
            return cls._acquisition[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def get_epoch(cls, param_type: str) -> type[BaseEpochAnalysis]:
        if param_type in cls._epoch:
            return cls._epoch[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def get_acq_config(cls, param_type: str) -> type[BaseAcquisitionConfig]:
        if param_type in cls._acq_config:
            return cls._acq_config[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def get_epoch_config(cls, param_type: str) -> type[BaseConfig]:
        if param_type in cls._epoch_config:
            return cls._epoch_config[param_type]
        else:
            raise ValueError(f"{param_type} not in registered analyses.")

    @classmethod
    def list_available(cls) -> dict[str, list]:
        """List all registered analyses."""
        return {
            "acquisitions": list(cls._acquisition.keys()),
            "epochs": list(cls._epoch.keys()),
        }


def register_acquisition(param_type: type[BaseAcquisitionAnalysis]):
    return AnalysisRegistry.register_acquisition(param_type)


def register_epoch(param_type: type[BaseEpochAnalysis]):
    return AnalysisRegistry.register_epoch(param_type)


def register_epoch_config(param_type: type[BaseConfig]):
    return AnalysisRegistry.register_epoch_config(param_type)


def register_acq_config(param_type: type[BaseAcquisitionConfig]):
    return AnalysisRegistry.register_acq_config(param_type)
