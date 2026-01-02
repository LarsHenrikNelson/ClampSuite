from typing import Dict, Type, List, Any, Protocol, runtime_checkable, NamedTuple

from ..loader.acquisition_data import AcquisitionData


@runtime_checkable
class Parameters(Protocol):
    def analysis_key() -> str: ...
    def acquisition() -> dict: ...
    def final() -> dict: ...


@runtime_checkable
class AcquisitionAnalysisProtocol(Protocol):
    def analyze(self, acq_data: AcquisitionData, **kwargs): ...

    def data(self) -> Dict: ...


@runtime_checkable
class FinalAnalysisProtocol(Protocol):
    def run(self, acquisition_results: list[Dict[str, Any]]): ...


class AnalysisRegistry:
    _acquisition: Dict[str, Type[AcquisitionAnalysisProtocol]] = {}
    _epoch: Dict[str, Type[FinalAnalysisProtocol]] = {}

    @classmethod
    def register_acquisition(cls, param_type: Type[Parameters]):
        def decorator(analysis_cls):
            cls._acquisition[param_type.analysis_key()] = analysis_cls
            return analysis_cls

        return decorator

    @classmethod
    def register_epoch(cls, param_type: Type[Parameters]):
        def decorator(analysis_cls):
            cls._epoch[param_type.analysis_key()] = analysis_cls
            return analysis_cls

        return decorator

    @classmethod
    def get_acquisition(cls, param_type: str) -> Type[Parameters] | None:
        return cls._acquisition.get(param_type)

    @classmethod
    def get_epoch(cls, param_type: str) -> Type[Parameters] | None:
        return cls._epoch.get(param_type)

    @classmethod
    def list_available(cls) -> tuple:
        """List all registered analyses."""
        return cls._acquisition, cls._epoch


def register_acquisition(param_type: Type[Parameters]):
    return AnalysisRegistry.register_acquisition(param_type)


def register_epoch(param_type: Type[Parameters]):
    return AnalysisRegistry.register_epoch(param_type)
