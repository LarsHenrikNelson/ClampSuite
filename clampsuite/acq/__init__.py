"""
Even though only Acq is needed to interface
with all the modules, all the modules need to
be imported otherwise there is a circular
import error.
"""

from .acquisition import Acquisition
from .current_clamp_acq import CurrentClampAcq
from .filter_acq import FilterAcq
from .lfp_acq import LFPAcq
from .postsynaptic_event import MiniEvent
from .mini_acq import MiniAnalysisAcq
from .oepsc_acq import oEPSCAcq

analyses = {
    "current_clamp": CurrentClampAcq,
    "filter": FilterAcq,
    "lfp": LFPAcq,
    "mini": MiniAnalysisAcq,
    "oepsc": oEPSCAcq,
}
