from clampsuite.manager import ExpManager


def test_exp_manager_data():
    assert len(ExpManager.windows) > 0
    assert len(ExpManager.filters) > 0


def test_current_clamp_data(current_clamp_data):
    exp_manager = ExpManager()
    exp_manager.create_exp("current_clamp", current_clamp_data)
