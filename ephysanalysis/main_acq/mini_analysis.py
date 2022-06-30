from click import pass_context
import numpy as np

from ..base_acq import mini_acq_base


class MiniAnalysis(mini_acq_base.MiniAnalysisBase):
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
        template=None,
        rc_check=False,
        rc_check_start=None,
        rc_check_end=None,
        sensitivity=3,
        amp_threshold=7,
        mini_spacing=7.5,
        min_rise_time=1,
        min_decay_time=2,
        invert=False,
        decon_type="wiener",
        curve_fit_decay=False,
        curve_fit_type="db_exp",
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
        self.rc_check = rc_check
        self.rc_check_start = int(rc_check_start * self.s_r_c)
        self.rc_check_end = int(rc_check_end * self.s_r_c)
        self.sensitivity = sensitivity
        self.amp_threshold = amp_threshold
        self.mini_spacing = int(mini_spacing * self.s_r_c)
        self.min_rise_time = min_rise_time
        self.min_decay_time = min_decay_time
        self.invert = invert
        self.curve_fit_decay = curve_fit_decay
        self.decon_type = decon_type
        self.curve_fit_type = curve_fit_type
        self.create_template(template)

    def analyze(self):
        self.filter_array()
        self.create_mespc_array()
        self.set_sign()
        self.wiener_deconvolution()
        self.wiener_filt()
        self.create_events()
