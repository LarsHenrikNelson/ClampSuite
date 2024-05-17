from pathlib import Path

from clampsuite.functions.load_functions import (
    download_test_acquisitions,
    find_stim_pulse_data,
    find_stim_pulses,
    load_json_file,
    load_mat,
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


def test_find_scanimage_stim(paired_pulse_data_scanimage):
    mat = load_mat(paired_pulse_data_scanimage[0])
    data_string = mat["AD0_1"]["UserData"]["headerString"]
    stim_chan = find_stim_pulses(data_string)
    assert stim_chan[0] == "ao2"


def test_get_scanimage_stim_info(paired_pulse_data_scanimage):
    mat = load_mat(paired_pulse_data_scanimage[0])
    data_string = mat["AD0_1"]["UserData"]["headerString"]
    num_pulses, isi, pulse_start = find_stim_pulse_data(data_string, "ao2")
    assert num_pulses == 2
    assert isi == 100.0
    assert pulse_start == 1000.0
