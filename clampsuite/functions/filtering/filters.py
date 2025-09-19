from typing import Literal, NamedTuple, TypeAlias


Windows = Literal[
    "hann",
    "hamming",
    "blackmanharris",
    "barthann",
    "nuttall",
    "blackman",
    "tukey",
    "kaiser",
    "gaussian",
    "parzen",
]


class MedianFilter(NamedTuple):
    filter_family: str = "median"
    filter_type: str = "median"
    order: int = 4


class EWMAFilter(NamedTuple):
    filter_family: str = "ewma"
    filter_type: Literal["ewma", "ewma_a"] = "ewma"
    window: int = 30
    sum_proportion: float = 0.5


class SavgolFilter(NamedTuple):
    filter_family: str = "savgol"
    filter_type = "savgol"
    order: int = 11
    polyorder: int = 3


class FIRFilter(NamedTuple):
    filter_family: str = "fir"
    filter_type: Literal["fir", "fir_zero"] = "fir_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200
    window: Windows = "hann"
    beta_sigma: float | None = None
    fs: float = 10000.0


class RemezFilter(NamedTuple):
    filter_family: str = "remez"
    filter_type: Literal["remez", "remez_zero"] = "remez_zero"
    order: int = 301
    high_pass: int | float | None = None
    high_width: int | float | None = None
    low_pass: int | float | None = 500
    low_width: int | float | None = 200
    fs: float = 10000.0


class IIRFilter(NamedTuple):
    filter_family: str = "iir"
    filter_type: Literal["bessel", "butterworth", "bessel_zero", "butterworth_zero"] = (
        "butterworth_zero"
    )
    order: int = 4
    high_pass: int | float | None = None
    low_pass: int | float | None = 500
    fs: float = 10000.0


Filters: TypeAlias = (
    MedianFilter | EWMAFilter | SavgolFilter | FIRFilter | IIRFilter | RemezFilter
)


