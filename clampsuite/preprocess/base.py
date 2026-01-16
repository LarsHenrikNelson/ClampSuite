from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Dict, List, ClassVar, Type
from collections import defaultdict

import numpy as np


@dataclass
class Preprocessor(ABC):
    """Base class for all preprocessing steps."""

    name: ClassVar[str]
    module: ClassVar[str]

    @abstractmethod
    def process(self, array: np.ndarray, fs: float | int) -> np.ndarray:
        """Process the acquisition data and return the result."""
        pass


class PreprocessorRegistry:
    _preprocessor: Dict[str, dict[str, Type[Preprocessor]]] = defaultdict(dict)

    @classmethod
    def register_preprocessor(cls, param_type: Type[Preprocessor]):
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


def register_preprocessor(param_type: Type[Preprocessor]):
    return PreprocessorRegistry.register_preprocessor(param_type)
