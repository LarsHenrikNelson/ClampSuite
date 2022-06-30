import numpy as np

from ..base_acq.postsynaptic_event_base import PostSynapticEventBase


class PostSynapticEvent(PostSynapticEventBase):
    def __init__(
        self,
        acq_number,
        event_pos,
        y_array,
        sample_rate,
        curve_fit_decay=False,
        curve_fit_type="db_exp",
    ):
        super().__init__()
        self.acq_number = acq_number
        self.event_pos = int(event_pos)
        self.sample_rate = sample_rate
        self.s_r_c = sample_rate / 1000
        self.curve_fit_decay = curve_fit_decay
        self.curve_fit_type = curve_fit_type
        self.fit_tau = np.nan
        self.create_event_array(y_array)
        self.find_peak()
        self.find_event_parameters(y_array)
        self.peak_align_value = self.event_peak_x - self.array_start

