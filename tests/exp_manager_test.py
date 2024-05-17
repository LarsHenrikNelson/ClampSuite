from clampsuite.manager import ExpManager

import pytest


def test_exp_manager_data():
    assert len(ExpManager.windows) > 0
    assert len(ExpManager.filters) > 0


@pytest.mark.parametrize(
    "data, name",
    [
        ("current_clamp_data_scanimage", "current_clamp"),
        ("msn_mepsc_data_scanimage", "mini"),
        ("oepsc_data_scanimage", "oepsc"),
        ("olfp_data_scanimage", "lfp"),
    ],
)
def test_create_exp(request, data, name):
    result = request.getfixturevalue(data)
    exp_manager = ExpManager()
    exp_manager.create_exp(name, result)
    assert name in exp_manager.exp_dict.keys()


@pytest.mark.parametrize(
    "data, name",
    [
        ("current_clamp_data_scanimage", "current_clamp"),
        ("msn_mepsc_data_scanimage", "mini"),
        ("oepsc_data_scanimage", "oepsc"),
        ("olfp_data_scanimage", "lfp"),
    ],
)
def test_mini_analysis_data(request, data, name):
    result = request.getfixturevalue(data)
    exp_manager = ExpManager()
    exp_manager.create_exp(name, result)
    assert name in exp_manager.exp_dict
    assert len(exp_manager.exp_dict[name].items()) == len(result)


def test_delete_acq(msn_mepsc_data_scanimage):
    exp_manager = ExpManager()
    exp_manager.create_exp("mini", msn_mepsc_data_scanimage)
    exp_manager.delete_acq(exp="mini", acq=61)
    assert 61 in exp_manager.deleted_acqs["mini"].keys()
    assert 61 not in exp_manager.exp_dict["mini"].keys()


@pytest.mark.parametrize(
    "data, name",
    [
        ("current_clamp_data_scanimage", "current_clamp"),
        ("msn_mepsc_data_scanimage", "mini"),
        ("oepsc_data_scanimage", "oepsc"),
        ("olfp_data_scanimage", "lfp"),
    ],
)
def test_static_load_acq(request, data, name):
    result = request.getfixturevalue(data)
    acq = ExpManager.load_acq(analysis=name, path=result[0])
    assert acq.analysis == name


@pytest.mark.parametrize(
    "data, name",
    [
        ("current_clamp_data_scanimage", "current_clamp"),
        ("msn_mepsc_data_scanimage", "mini"),
        ("oepsc_data_scanimage", "oepsc"),
        ("olfp_data_scanimage", "lfp"),
    ],
)
def test_static_load_acqs(request, data, name):
    result = request.getfixturevalue(data)
    acq_dict = ExpManager.load_acqs(analysis=name, file_path=result)
    keys = list(acq_dict.keys())
    assert len(keys) != 0
    assert acq_dict[keys[0]].analysis == name


def test_set_start_end_acqs(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))
    assert manager.start_acq == keys[0]
    assert manager.end_acq == keys[-1]

    del manager.exp_dict["lfp"][keys[0]]
    manager._set_start_end_acq()
    assert manager.start_acq == keys[1]


def test_del_acq(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))
    manager.delete_acq(exp="lfp", acq=keys[0])
    assert keys[0] in manager.deleted_acqs["lfp"]
    assert keys[0] not in manager.exp_dict["lfp"]


def test_reset_recent_deleted(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))

    manager.delete_acq(exp="lfp", acq=keys[0])
    manager.reset_recent_deleted_acq(exp="lfp")
    assert keys[0] not in manager.deleted_acqs["lfp"]
    assert keys[0] in manager.exp_dict["lfp"]


def test_reset_deleted(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))
    del_keys = [keys[0], keys[3]]
    manager.delete_acq(exp="lfp", acq=del_keys[0])
    manager.delete_acq(exp="lfp", acq=del_keys[1])
    manager.reset_deleted_acqs(exp="lfp")

    assert del_keys[0] not in manager.deleted_acqs["lfp"]
    assert del_keys[0] in manager.exp_dict["lfp"]

    assert del_keys[1] not in manager.deleted_acqs["lfp"]
    assert del_keys[1] in manager.exp_dict["lfp"]


def test_number_of_deleted_acqs(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))

    manager.delete_acq(exp="lfp", acq=keys[0])
    assert manager.num_of_del_acqs() == 1


def test_acqs_exist(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    assert manager.acqs_exist("lfp")


def test_acq_exist(olfp_data_scanimage):
    manager = ExpManager()
    manager.create_exp(analysis="lfp", file=olfp_data_scanimage)
    keys = sorted(list(manager.exp_dict["lfp"].keys()))
    assert manager.acq_exists("lfp", keys[0])
    assert not manager.acq_exists("lfp", keys[-1] + 1)
