from clampsuite.acq import (
    Acquisition,
    LFPAcq,
)


def test_lfp_acq():
    lfp = Acquisition("lfp")
    assert isinstance(lfp, LFPAcq)
