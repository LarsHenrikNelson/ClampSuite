from enum import Enum


Filters = Enum(
    "Filters",
    [
        "remez_2",
        "remez_1",
        "fir_zero_2",
        "fir_zero_1",
        "savgol",
        "ewma",
        "ewma_a",
        "median",
        "bessel",
        "butterworth",
        "bessel_zero",
        "butterworth_zero",
    ],
)

Windows = Enum(
    "Windows",
    [
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
    ],
)
