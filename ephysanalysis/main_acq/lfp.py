import numpy as np

from ..base_acq import lfp_base


class LFPAnalysis(lfp_base.LFPBase):
    """
    This class creates a LFP acquisition. This class subclasses the
    Acquisition class and takes input specific for LFP analysis.
    """

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
        pulse_start=1000,
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
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.x_array = np.arange(len(self.array)) / (sample_rate / 1000)
        self.baseline_start = int(baseline_start * (sample_rate / 1000))
        self.baseline_end = int(baseline_end * (sample_rate / 1000))
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self.pulse_start = int(pulse_start * self.s_r_c)
        self.fp_x = np.nan
        self.fp_y = np.nan
        self.fv_x = np.nan
        self.fv_y = np.nan
        self.max_x = np.nan
        self.max_y = np.nan
        self.slope_y = np.nan
        self.slope_x = np.nan
        self.b = np.nan
        self.slope = np.nan
        self.regression_line = np.nan
        self.filter_array()
        self.analyze_lfp()
