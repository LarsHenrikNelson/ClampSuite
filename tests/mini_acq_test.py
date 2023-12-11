from clampsuite.acq import (
    Acquisition,
    MiniAnalysisAcq,
)

from clampsuite.functions.utilities import create_event_array, create_acq_data


def test_mini_acq():
    mini = Acquisition("mini")
    assert isinstance(mini, MiniAnalysisAcq)


def test_input_acq():
    mini = Acquisition("mini")

    data = create_acq_data()
    data["array"] = create_event_array(10000, 100000, 30, "negative")
    mini.load_data(data)
    mini.set_filter(
        baseline_start=0,
        baseline_end=300,
        filter_type="fir_zero_2",
        order=301,
        high_pass=None,
        high_width=None,
        low_pass=600,
        low_width=300,
        window="hann",
        polyorder=None,
    )
    mini.set_template(
        tmp_amplitude=-20,
        tmp_tau_1=0.3,
        tmp_tau_2=5.0,
        tmp_risepower=0.5,
        tmp_length=30,
        tmp_spacer=1.5,
    )
    mini.analyze(
        sensitivity=4,
        amp_threshold=4,
        mini_spacing=2,
        min_rise_time=0.5,
        max_rise_time=4,
        min_decay_time=0.5,
        event_length=30,
        decay_rise=True,
        invert=False,
        decon_type="wiener",
        curve_fit_decay=False,
        curve_fit_type="exp",
        baseline_corr=False,
        rc_check=False,
        rc_check_start=10000,
        rc_check_end=10300,
    )
