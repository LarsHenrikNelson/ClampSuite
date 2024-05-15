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
    assert len(exp_manager.exp_dict[name].items()) == len(result)
