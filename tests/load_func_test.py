from pathlib import Path

from clampsuite.functions.load_functions import (
    download_test_acquisitions,
    load_json_file,
    load_scanimage_file,
    SCANIMAGE_DATA_URL,
    URLS,
)


def test_download():
    acq_type = "msn_current_clamp"
    prefix = URLS[acq_type][1]
    test_files = URLS[acq_type][0]
    files = download_test_acquisitions(
        parent_url=SCANIMAGE_DATA_URL,
        acq_type=acq_type,
        acq_prefix=prefix,
        acqs=[test_files[0], test_files[0]],
        filetype="mat",
    )
    home = Path().home()
    downloaded_file_path = home / f".clampsuite/{acq_type}/{prefix}{test_files[0]}.mat"
    assert str(downloaded_file_path) == str(files[0])


def test_load_scanimage(current_clamp_data_scanimage):
    out = load_scanimage_file(current_clamp_data_scanimage[0])
    assert out["array"].size > 0


def test_load_json(current_clamp_data_json):
    out = load_json_file(current_clamp_data_json[0])
    assert out["array"].size > 0
