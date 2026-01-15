from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass, field

import pandas as pd

from ..loader import AcquisitionData


@dataclass
class BaseAcquisitionAnalysis(ABC):
    """Base class for per-acquisition analysis."""

    acq_data: AcquisitionData
    _analysis_variables: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    @abstractmethod
    def analysis_key() -> str: ...

    @abstractmethod
    def analyze(self, *args, **kwargs) -> None:
        """Run analysis on a single acquisition."""
        pass

    @abstractmethod
    def data(self) -> tuple[dict, dict]:
        """Return the data for this acquisition."""
        pass

    def __getitem__(self, index):
        return self._analysis_variables[index]

    def __setitem__(self, index, value):
        if index in self._analysis_variables:
            self._analysis_variables[index] = value
        else:
            raise KeyError(f"Key {index} not found in analysis variables.")

    def update(self, dictionary: dict):
        for key, value in dictionary:
            self[key] = value


@dataclass
class BaseEpochAnalysis(ABC):
    def __post_init__(self):
        self._acquisitions: Dict[str | int, BaseAcquisitionAnalysis] = {}
        self.epoch_id: int = 0
        self.df_dict: Dict[str, pd.DataFrame] = {}

    @staticmethod
    @abstractmethod
    def analysis_key() -> str: ...

    @abstractmethod
    def analyze(self) -> None:
        """Analyze acquisitions."""
        pass

    @abstractmethod
    def load_acquisitions(
        self, epoch_id: int, acquisitions: Dict[int, AcquisitionData]
    ):
        """Load acquisitions"""
        pass
