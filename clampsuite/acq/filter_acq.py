from typing import Literal, Union

import numpy as np

from ..functions.filtering_functions import (
    ewma_filter,
    savgol_filter,
    fir_filter,
    iir_filter,
    remez_filter,
    median_filter,
    Filters,
)


class FilterAcq:
    def __init__(self, filter: Filters):
        self.filter = filter

    def analyze(self, array) -> None:
        if self.filter.filter_family == "ewma":
            output = ewma_filter(array, self.filter)
        elif self.filter.filter_family == "savgol":
            output = savgol_filter(array, self.filter)
        elif self.filter.filter_family == "fir":
            output = fir_filter(array, self.filter)
        elif self.filter.filter_family == "iir":
            output = iir_filter(array, self.filter)
        elif self.filter.filter_family == "remez":
            output = remez_filter(array, self.filter)
        elif self.filter.filter_family == "median":
            output = median_filter(array, self.filter)
        return output
