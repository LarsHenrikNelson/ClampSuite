import pytest
import numpy as np

from clampsuite.functions.filtering_functions import (
    check_fir_filter_input,
    check_iir_filter_input,
    bessel,
    bessel_zero,
    butterworth,
    butterworth_zero,
)


@pytest.mark.parametrize(
    "high_pass, high_width, low_pass, low_width, sample_rate, error",
    [
        (300, 100, 600, 300, 10000, True),
        (None, 300, 600, 300, 10000, False),
        (300, None, 600, 300, 10000, False),
        (300, 300, None, 300, 10000, False),
        (300, 300, 600, None, 10000, False),
        (None, None, 600, 300, 10000, True),
        (300, 300, None, None, 10000, True),
        (300, 400, None, None, 10000, False),
        (None, None, 8000, 3000, 10000, False),
        (-1, 300, 800, 300, 10000, False),
        (10001, None, 600, 300, 10000, False),
        (300, 300, -1, 300, 10000, False),
        (300, 300, 10001, 300, 10000, False),
        (600, 300, 300, 100, 10000, False),
    ],
)
def test_check_fir_filter(
    high_pass, high_width, low_pass, low_width, sample_rate, error
):
    message = check_fir_filter_input(
        high_pass, high_width, low_pass, low_width, sample_rate
    )
    assert message.passed == error


@pytest.mark.parametrize(
    "high_pass, low_pass, sample_rate, error",
    [
        (300, 600, 10000, True),
        (300, None, 10000, True),
        (None, 600, 10000, True),
        (600, 300, 10000, False),
        (10001, 300, 10000, False),
        (300, 10001, 10000, False),
    ],
)
def test_check_iir_filter(high_pass, low_pass, sample_rate, error):
    message = check_iir_filter_input(high_pass, low_pass, sample_rate)
    assert message.passed == error


@pytest.mark.parametrize(
    "output, high_pass, low_pass, order, sample_rate",
    [
        (
            [0.24940892, 0.56918332, 0.40901479, -0.53533113, -0.33736032, -0.61047588],
            300,
            None,
            4,
            10000,
        ),
        (
            [
                2.00212639e-05,
                2.00742371e-04,
                9.77518682e-04,
                3.07605695e-03,
                7.08433313e-03,
                1.28568291e-02,
            ],
            300,
            600,
            4,
            10000,
        ),
        (
            [0.00024957, 0.00243364, 0.01150812, 0.03516785, 0.07902064, 0.14172472],
            None,
            600,
            4,
            10000,
        ),
    ],
)
def test_bessel(iir_input_data, output, high_pass, low_pass, order, sample_rate):
    temp = bessel(iir_input_data, order, sample_rate, high_pass, low_pass)
    assert np.allclose(temp, output)
