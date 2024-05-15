from clampsuite.manager import ExpManager


def test_exp_manager_data():
    assert len(ExpManager.windows) > 0
    assert len(ExpManager.filters) > 0


def test_current_clamp_data(current_clamp_data_scanimage):
    exp_manager = ExpManager()
    exp_manager.create_exp("current_clamp", current_clamp_data_scanimage)
    assert "current_clamp" in exp_manager.exp_dict.keys()
    assert len(exp_manager.exp_dict["current_clamp"].items()) == len(
        current_clamp_data_scanimage
    )


def test_mini_analysis_data(msn_mepsc_data_scanimage):
    exp_manager = ExpManager()
    exp_manager.create_exp("mini", msn_mepsc_data_scanimage)
    assert "mini" in exp_manager.exp_dict.keys()
    assert len(exp_manager.exp_dict["mini"].items()) == len(msn_mepsc_data_scanimage)


def test_oepsc_analysis_data(oepsc_data_scanimage):
    exp_manager = ExpManager()
    exp_manager.create_exp("oepsc", oepsc_data_scanimage)
    assert "oepsc" in exp_manager.exp_dict.keys()
    assert len(exp_manager.exp_dict["oepsc"].items()) == len(oepsc_data_scanimage)


def test_lfp_analysis_data(olfp_data_scanimage):
    exp_manager = ExpManager()
    exp_manager.create_exp("lfp", olfp_data_scanimage)
    assert "lfp" in exp_manager.exp_dict.keys()
    assert len(exp_manager.exp_dict["lfp"].items()) == len(olfp_data_scanimage)
