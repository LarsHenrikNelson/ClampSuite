import numpy as np

from clampsuite.acq import (
    Acquisition,
    CurrentClampAcq,
)
from clampsuite.functions.load_functions import (
    download_test_acquisitions,
    load_scanimage_file,
    SCANIMAGE_DATA_URL,
    URLS,
)


def test_current_clamp_acq_creation():
    current_clamp = Acquisition("current_clamp")
    assert isinstance(current_clamp, CurrentClampAcq)


def test_current_clamp_no_spikes():
    acq_type = "interneuron_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[0]],
    )
    data = load_scanimage_file(files[0])

    current_clamp = Acquisition("current_clamp")
    current_clamp.load_data(data)
    current_clamp.set_filter(filter_type="None", baseline_start=0, baseline_end=300)
    current_clamp.analyze()

    assert np.isnan(current_clamp.peaks[0])


def test_current_clamp_spikes():
    acq_type = "interneuron_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[-1], test_files[-1]],
        filetype="mat",
    )
    data = load_scanimage_file(files[0])

    current_clamp = Acquisition("current_clamp")
    current_clamp.load_data(data)
    current_clamp.set_filter(filter_type="None", baseline_start=0, baseline_end=300)
    current_clamp.analyze()

    assert len(current_clamp.peaks) > 1
