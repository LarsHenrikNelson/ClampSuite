import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd

import clampsuite

from ..loader.acquisition_data import AcquisitionData


class BaseAcquisitionAnalysis(ABC):
    """Base class for per-acquisition analysis."""

    @abstractmethod
    def analyze(self, acq_data: AcquisitionData, **kwargs) -> Dict[str, Any]:
        """Run analysis on a single acquisition."""
        pass

    @abstractmethod
    def data(self) -> tuple[dict, dict]:
        """Return the data for this acquisition."""
        pass


class BaseFinalAnalysis(ABC):
    """Base class for combined/final analysis."""

    @abstractmethod
    def analyze(self, acquisition_results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Run analysis on combined acquisition results."""
        pass

    @property
    def required_acquisition_analyses(self) -> list[str]:
        """List of acquisition analyses that must run first."""
        return []

    def save_data(self, save_filename: str):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        program_data = {
            "Program": ["ClampSuite"],
            "Version": clampsuite.__version__,
            "Time stamp": [str(datetime.datetime.now())],
        }
        prog_data = pd.DataFrame(program_data, index=None)
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="xlsxwriter"
        ) as writer:
            for key, value in self.df_dict.items():
                value.to_excel(writer, index=False, sheet_name=key)
            prog_data.to_excel(writer, index=False, sheet_name="Program data")
