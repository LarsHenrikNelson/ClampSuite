import numpy as np

from ..base_acq import current_clamp_base


class CurrentClampAnalysis(current_clamp_base.CurrentClampBase):
    def __init__(
        self,
        acq_components,
        sample_rate,
        baseline_start,
        baseline_end,
        filter_type="None",
        order=None,
        high_pass=None,
        high_width=None,
        low_pass=None,
        low_width=None,
        window=None,
        polyorder=None,
        pulse_start=300,
        pulse_end=1000,
        ramp_start=300,
        ramp_end=4000,
        threshold=-15,
    ):
        super().__init__()
        self.sample_rate = sample_rate
        self.name = acq_components[0]
        self.acq_number = acq_components[1]
        self.array = acq_components[2]
        self.epoch = acq_components[3]
        self.pulse_pattern = acq_components[4]
        self.ramp = acq_components[5]
        self.pulse_amp = acq_components[6]
        self.time_stamp = acq_components[7]
        self.s_r_c = sample_rate / 1000
        self.x_array = np.arange(len(self.array)) / (sample_rate / 1000)
        self.baseline_start = int(baseline_start * (sample_rate / 1000))
        self.baseline_end = int(baseline_end * (sample_rate / 1000))
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self.pulse_start = int(pulse_start * self.s_r_c)
        self.pulse_end = int(pulse_end * self.s_r_c)
        self.ramp_start = int(ramp_start * self.s_r_c)
        self.ramp_end = int(ramp_end * self.s_r_c)
        self.x_array = np.arange(len(self.array)) / (self.s_r_c)
        self.threshold = threshold
