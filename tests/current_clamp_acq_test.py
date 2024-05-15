import numpy as np

from clampsuite.acq import (
    Acquisition,
    CurrentClampAcq,
)
from clampsuite.functions.load_functions import (
    load_scanimage_file,
)


def test_current_clamp_acq_creation():
    current_clamp = Acquisition("current_clamp")
    assert isinstance(current_clamp, CurrentClampAcq)


def test_current_clamp_no_spikes(current_clamp_data_scanimage):
    data = load_scanimage_file(current_clamp_data_scanimage[0])

    current_clamp = Acquisition("current_clamp")
    current_clamp.load_data(data)
    current_clamp.set_filter(filter_type="None", baseline_start=0, baseline_end=300)
    current_clamp.analyze()

    assert np.isnan(current_clamp.peaks[0])


def test_current_clamp_spikes(current_clamp_data_scanimage):
    data = load_scanimage_file(current_clamp_data_scanimage[10])

    current_clamp = Acquisition("current_clamp")
    current_clamp.load_data(data)
    current_clamp.set_filter(filter_type="None", baseline_start=0, baseline_end=300)
    current_clamp.analyze()

    assert len(current_clamp.peaks) > 1
