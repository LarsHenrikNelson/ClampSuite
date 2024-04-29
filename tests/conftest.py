import pytest

from clampsuite.functions.load_functions import (
    download_scanimage_test_acquisitions,
    PARENT_URL,
    URLS,
)


@pytest.fixture(scope="session")
def current_clamp_data():
    acq_type = "msn_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1] - 23],
    )
    return files


@pytest.fixture(scope="session")
def msn_mepsc_data():
    acq_type = "msn_mepsc"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1] - 5],
    )
    return files


@pytest.fixture(scope="session")
def olfp_data():
    acq_type = "msn_olfp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1]],
    )
    return files


@pytest.fixture(scope="session")
def oepsc_data():
    acq_type = "msn_oepsc"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[-1]],
    )
    return files
