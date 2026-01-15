from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Dict, List, ClassVar
from collections import defaultdict

import numpy as np


@dataclass
class Preprocessor(ABC):
    """Base class for all preprocessing steps."""

    @abstractmethod
    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        """Process the acquisition data and return the result."""
        pass

    @property
    @abstractmethod
    def name(self) -> str: ...


class PreprocessorRegistry:
    _preprocessor: Dict[str, dict[str, Preprocessor]] = defaultdict(dict)

    @classmethod
    def register_preprocessor(cls, param_type: str):
        def decorator(analysis_cls):
            cls._preprocessor[param_type][analysis_cls.name] = analysis_cls
            return analysis_cls

        return decorator


def register_preprocessor(param_type: str):
    return PreprocessorRegistry.register_preprocessor(param_type)
