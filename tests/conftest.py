import pytest

from clampsuite.functions.load_functions import (
    download_test_acquisitions,
    SCANIMAGE_DATA_URL,
    CSJSON_DATA_URL,
    URLS,
)


@pytest.fixture(scope="session")
def current_clamp_data_scanimage():
    acq_type = "msn_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1] - 23],
        filetype="mat",
    )
    return files


@pytest.fixture(scope="session")
def current_clamp_data_json():
    acq_type = "msn_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=CSJSON_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1] - 23],
        filetype="json",
    )
    return files


@pytest.fixture(scope="session")
def msn_mepsc_data_scanimage():
    acq_type = "msn_mepsc"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1] - 5],
        filetype="mat",
    )
    return files


@pytest.fixture(scope="session")
def olfp_data_scanimage():
    acq_type = "msn_olfp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1]],
        filetype="mat",
    )
    return files


@pytest.fixture(scope="session")
def oepsc_data_scanimage():
    acq_type = "msn_oepsc"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1]],
        filetype="mat",
    )
    return files


@pytest.fixture(scope="session")
def paired_pulse_data_scanimage():
    acq_type = "paired_pulse"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1]],
        filetype="mat",
    )
    return files


@pytest.fixture(scope="session")
def iir_input_data():
    return [0.335343, 0.95949, 1.23483421, 0.445458, 0.55432584, 0.112348591]


@pytest.fixture(scope="session")
def iir_zero_input_data():
    return [
        0.335343,
        0.95949,
        1.23483421,
        0.445458,
        0.55432584,
        0.112348591,
        0.335343,
        0.95949,
        1.23483421,
        0.445458,
        0.55432584,
        0.112348591,
        0.335343,
        0.95949,
        1.23483421,
        0.445458,
        0.55432584,
        0.112348591,
        0.335343,
        0.95949,
        1.23483421,
        0.445458,
        0.55432584,
        0.112348591,
    ]
