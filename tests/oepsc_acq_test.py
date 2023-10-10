from clampsuite.acq import (
    Acquisition,
    oEPSCAcq,
)


def test_oepsc_acq():
    oepsc = Acquisition("oepsc")
    assert isinstance(oepsc, oEPSCAcq)
