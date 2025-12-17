from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Dict, List
from collections import defaultdict

import numpy as np


@dataclass
class Preprocessor(ABC):
    """Base class for all preprocessing steps."""

    @abstractmethod
    def process(self, data: np.ndarray, fs: float | int) -> np.ndarray:
        """Process the acquisition data and return the result."""
        pass


class PreprocessorRegistry:
    _preprocessor: Dict[str, List[Preprocessor]] = defaultdict(list)

    @classmethod
    def register_preprocessor(cls, param_type: str):
        def decorator(analysis_cls):
            cls._preprocessor[param_type].append(analysis_cls)
            return analysis_cls

        return decorator


def register_preprocessor(param_type: str):
    return PreprocessorRegistry.register_preprocessor(param_type)
