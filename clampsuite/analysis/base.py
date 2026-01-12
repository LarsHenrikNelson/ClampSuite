from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass

import pandas as pd

from ..loader import AcquisitionData


class BaseAcquisitionAnalysis(ABC):
    """Base class for per-acquisition analysis."""

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
