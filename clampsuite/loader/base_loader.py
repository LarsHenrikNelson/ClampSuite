from ast import Call
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Callable

import numpy as np

from .acquisition_data import AcquisitionData


class BaseLoader(ABC):

    def __init__(self, callback_func: Callable = print):
        self.callback_func = callback_func

    @abstractmethod
    def load_files(self, file_paths: list[str | Path]) -> defaultdict[int, dict[int, AcquisitionData]]:
        pass

    def group_epochs(self, acquisitions) -> defaultdict[int, dict[int, AcquisitionData]]:
        epoch_dict: defaultdict[int, dict[int, AcquisitionData]] = defaultdict(dict)
        for key, value in acquisitions.items():
            epoch_dict[value.epoch][key] = value
        return epoch_dict