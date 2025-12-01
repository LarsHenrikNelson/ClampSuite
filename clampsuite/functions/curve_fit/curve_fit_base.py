from abc import ABC, abstractmethod
from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit


class CurveFitBase(ABC):
    def __init__(self):
        self._params: NamedTuple | None = None
        self._fit_success: bool = False

    @property
    def params(self) -> NamedTuple:
        return self._params

    @staticmethod
    @abstractmethod
    def _fit_function(x: np.ndarray, *params) -> np.ndarray:
        pass

    @abstractmethod
    def _create_result(popt):
        pass

    @abstractmethod
    def _create_nan_result(self) -> NamedTuple:
        pass

    def _get_initial_params(self, x: np.ndarray, y: np.ndarray) -> None:
        return None

    def _get_bounds(self, x: np.ndarray, y: np.ndarray) -> None:
        return None

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self._params is None:
            raise ValueError("Must call fit() before predict()")
        return self._fit_function(x, *self._params)

    def fit(self, x: np.ndarray, y: np.ndarray, **kwargs):
        try:
            p0 = self._get_initial_params(x, y)
            bounds = self._get_bounds(x, y)

            popt, _ = curve_fit(
                self._fit_function, x, y, p0=p0, bounds=bounds, **kwargs
            )

            self._params = self._create_result(popt)
            self._fit_success = True

        except Exception:
            self._params = self._create_nan_result()
            self._fit_success = False

        return self._params
