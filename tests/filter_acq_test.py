from clampsuite.acq import (
    Acquisition,
    FilterAcq,
)
from .test_utils import create_acq_data


def test_filter_acq_creation():
    filter = Acquisition("filter")
    assert isinstance(filter, FilterAcq)

    data = create_acq_data()
    filter.load_data(data)


def test_bandpass_fir_filter():
    filter = Acquisition("filter")
    data = create_acq_data()
    filter.load_data(data)
    filter.set_filter(
        baseline_start=0,
        baseline_end=300,
        filter_type="fir_zero_2",
        order=301,
        high_pass=300,
        high_width=100,
        low_pass=1000,
        low_width=100,
        window="hann",
        polyorder=None,
    )

    filter.analyze()
