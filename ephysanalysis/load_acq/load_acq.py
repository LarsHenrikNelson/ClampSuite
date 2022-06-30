import numpy as np

from ..base_acq import (
    current_clamp_base,
    lfp_base,
    mini_acq_base,
    postsynaptic_event_base,
    oepsc_base,
)


class LoadLFP(lfp_base.LFPBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.slope_x = np.array(self.slope_x)


class LoadoEPSC(oepsc_base.oEPSCBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])


class LoadCurrentClamp(current_clamp_base.CurrentClampBase):
    """
    This class loads the saved CurrentClamp JSON file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.sample_rate_correction = None
        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.peaks = np.asarray(self.peaks, dtype=np.int64)
        self.array = np.asarray(self.array)
        if self.sample_rate_correction is not None:
            self.s_r_c = self.sample_rate_correction


class LoadMiniAnalysis(mini_acq_base.MiniAnalysisBase):
    """
    This class loads the saved JSON file for an entire miniAnalysis session.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.sample_rate_correction = None

        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])

        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.sample_rate_correction is not None:
            self.s_r_c = self.sample_rate_correction

        self.final_array = np.array(self.final_array)
        self.create_postsynaptic_events()
        self.x_array = np.arange(len(self.final_array)) / self.s_r_c
        self.event_arrays = [
            i.event_array - i.event_start_y for i in self.postsynaptic_events
        ]

    def create_postsynaptic_events(self):
        self.postsynaptic_events = []
        for i in self.saved_events_dict:
            h = LoadMini(i, final_array=self.final_array)
            self.postsynaptic_events += [h]


class LoadMini(postsynaptic_event_base.PostSynapticEventBase):
    """
    This class create a new mini event from dictionary within a
    LoadMiniAnalysis JSON file.
    """

    def __init__(self, *args, final_array, **kwargs):
        super().__init__()
        self.sample_rate_correction = None

        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])

        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.sample_rate_correction is not None:
            self.s_r_c = self.sample_rate_correction

        self.x_array = np.arange(self.array_start, self.array_end)
        self.event_array = final_array[self.array_start : self.array_end]
