from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, Literal

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

    @abstractmethod
    def data(
        self, output_type: Literal["ms", "samples"] = "ms", format_keys: bool = False
    ) -> tuple[dict, dict] | dict:
        """Return the data for this acquisition."""

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


@dataclass(frozen=True)
class BaseAcquisitionConfig(ABC):
    """Base class for analysis parameters."""

    @staticmethod
    @abstractmethod
    def analysis_key() -> str: ...


@dataclass(frozen=True)
class BaseConfig(ABC):
    """Base class for analysis parameters."""

    acquisition_config: BaseAcquisitionConfig

    @staticmethod
    @abstractmethod
    def analysis_key() -> str: ...


ConfigT = TypeVar("ConfigT", bound=BaseConfig)


@dataclass
class BaseEpochAnalysis(ABC, Generic[ConfigT]):
    """Base class for epoch analysis"""

    config: ConfigT

    def __post_init__(self):
        self._acquisitions: dict[str | int, BaseAcquisitionAnalysis] = {}
        self.epoch_id: int = 0
        self.df_dict: dict[str, pd.DataFrame] = {}

    @staticmethod
    @abstractmethod
    def analysis_key() -> str: ...

    def analyze(self):
        """Analyzes the acquistions in an epoch."""
        for value in self._acquisitions.values():
            value.analyze(self.config.acquisition_config)

    @abstractmethod
    def load_acquisitions(
        self, epoch_id: int, acquisitions: dict[int, AcquisitionData]
    ):
        """Load acquisitions"""

    @abstractmethod
    def features(self):
        """Create data features from the raw acquisition data. Features are specific
        to the analysis.
        """
