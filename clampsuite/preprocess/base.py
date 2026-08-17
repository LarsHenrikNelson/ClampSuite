from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, fields
from typing import ClassVar

import numpy as np


@dataclass
class Preprocessor(ABC):
    """Base class for all preprocessing steps."""

    name: ClassVar[str]
    module: ClassVar[str]

    @abstractmethod
    def __call__(self, array: np.ndarray, fs: float) -> np.ndarray:
        """Process the acquisition data and return the result."""


class PreprocessorRegistry:
    _preprocessor: ClassVar[dict[str, dict[str, type[Preprocessor]]]] = defaultdict(
        dict
    )

    @classmethod
    def register_preprocessor(cls, param_type: type[Preprocessor]):
        cls._preprocessor[param_type.module][param_type.name] = param_type
        return param_type

    @classmethod
    def preprocessors(cls):
        return cls._preprocessor.keys()

    @classmethod
    def get_preprocessor(cls, key: str):
        if key in cls._preprocessor:
            return cls._preprocessor[key]
        else:
            raise KeyError("Preprocessor not found")


def register_preprocessor(param_type: type[Preprocessor]):
    return PreprocessorRegistry.register_preprocessor(param_type)
