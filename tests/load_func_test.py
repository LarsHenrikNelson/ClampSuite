from pathlib import Path

from clampsuite.functions.load_functions import (
    download_scanimage_test_acquisitions,
    load_json_file,
    load_scanimage_file,
    PARENT_URL,
    URLS,
)


def test_download():
    acq_type = "interneuron_current_clamp"
    prefix = URLS[acq_type][1]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL, acq_type=acq_type, acq_prefix=prefix, acqs=[281, 281]
    )
    home = Path().home()
    downloaded_file_path = home / f".clampsuite/{acq_type}/{prefix}{281}.mat"
    assert str(downloaded_file_path) == str(files[0])


def test_load_scanimage():
    acq_type = "interneuron_current_clamp"
    prefix = URLS[acq_type][1]
    files = download_scanimage_test_acquisitions(
        parent_url=PARENT_URL, acq_type=acq_type, acq_prefix=prefix, acqs=[281, 281]
    )
    out = load_scanimage_file(files[0])
    assert out
