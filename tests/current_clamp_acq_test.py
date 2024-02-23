from clampsuite.acq import (
    Acquisition,
    CurrentClampAcq,
)
from clampsuite.functions.utilities import create_acq_data


def test_current_clamp_acq_creation():
    current_clamp = Acquisition("current_clamp")
    assert isinstance(current_clamp, CurrentClampAcq)

    data = create_acq_data()
    current_clamp.load_data(data)
    current_clamp.set_filter(filter_type="None", baseline_start=0, baseline_end=300)
    current_clamp.analyze()
