import numpy as np

from ..base_acq import acquisition_base


class Acquisition(acquisition_base.AcquisitionBase):
    """
    This is the base class for acquisitions. It returns the array from a
    matfile and filters the array.
    
    To remove DC from the signal, signal is baselined to the mean of the 
    chosen baseline of the array. A highpass filter is usually not needed to
    for offline analysis because the signal can baselined using the mean.
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
