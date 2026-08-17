from abc import ABC, abstractmethod
from typing import Any, Generic, NamedTuple, TypeVar

import numpy as np
from scipy.optimize import curve_fit
from scipy.spatial.distance import correlation

T = TypeVar("T", bound=NamedTuple)


class ModelMetrics(NamedTuple):
    reduced_chisq: float = np.nan
    r2: float = np.nan
    residuals: np.ndarray = np.array([])
    parameter_uncertainties: np.ndarray = np.array([])
    correlation_matrix: np.ndarray = np.array([])


class CurveFitBase(ABC, Generic[T]):
    _params: T
    _model_metrics: ModelMetrics
    _fit_success: bool

    def __init__(self):
        self._params = self._create_nan_result()
        self._model_metrics = ModelMetrics()
        self._fit_success = False

    @property
    def params(self) -> T:
        return self._params

    @staticmethod
    @abstractmethod
    def _fit_function(x: np.ndarray, *params: Any, **kwargs: Any) -> np.ndarray:
        pass

    @abstractmethod
    def _create_result(self, popt: tuple) -> T:
        pass

    @abstractmethod
    def _create_nan_result(self) -> T:
        pass

    def _get_initial_params(self, x: np.ndarray, y: np.ndarray) -> None | tuple | list:
        return None

    def _get_bounds(self, x: np.ndarray, y: np.ndarray) -> None | tuple | list:
        return None

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self._params is None:
            raise ValueError("Must call fit() before predict()")
        return self._fit_function(x, *self._params)

    def fit(self, x: np.ndarray, y: np.ndarray, **kwargs):
        y = np.asarray(y)
        x = np.asarray(x)
        try:
            p0 = self._get_initial_params(x, y)
            bounds = self._get_bounds(x, y)

            popt, pcov = curve_fit(
                self._fit_function, x, y, p0=p0, bounds=bounds, **kwargs
            )

            self._params = self._create_result(popt)
            chisq = self._reduced_chisq(popt, x, y)
            uncertain = self._parameter_uncertainties(popt, pcov)
            residuals = self._residuals(x, y)
            r2 = self._r_squared(x, y)
            correlate = self._correlation(pcov)
            self._model_metrics = ModelMetrics(
                chisq, r2, residuals, uncertain, correlate
            )

            self._fit_success = True

        except RuntimeError as _:
            self._params = self._create_nan_result()
            self._fit_success = False

        return self._params

    def _reduced_chisq(self, popt: tuple, x: np.ndarray, y: np.ndarray) -> float:
        y_fit = self.predict(x)
        resid = y - y_fit
        chi_sq = np.sum(resid**2)
        dof = len(y) - len(popt)
        return chi_sq / dof

    def _parameter_uncertainties(self, popt, pcov) -> np.ndarray:
        param_errors = np.sqrt(np.diag(pcov))
        relative_errors = param_errors / np.abs(popt) * 100
        return relative_errors

    def _r_squared(self, x: np.ndarray, y: np.ndarray) -> float:
        y_fit = self.predict(x)
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def _correlation(self, pcov) -> np.ndarray:
        std_devs = np.sqrt(np.diag(pcov))
        correlation_matrix = pcov / np.outer(std_devs, std_devs)
        return correlation_matrix

    def _residuals(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        y_fit = self.predict(x)
        return y - y_fit
