import copy

import clampsuite

from ..functions.filtering_functions import Filters, Windows


class Acquisition:
    """
    This class is used to create any acquisition object type.
    The classes are stored in _class_type and are automatically
    created by passing the analysis method and a file path. All
    the rest of the attributes for the object are created when
    the
    """

    _class_type = {}

    def __init_subclass__(cls, analysis, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._class_type[analysis] = cls

    def __new__(cls, analysis: str, **kwargs):
        subclass = cls._class_type[analysis]
        obj = object.__new__(subclass)
        obj.analysis = analysis
        obj.version = clampsuite.__version__
        for key, value in kwargs.items():
            setattr(obj, key, value)
        setattr(obj, "accepted", True)
        return obj

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        """
        Seems to work. Needs more testing. __deepcopy__ needs to work if
        someone wants to pickle a file.
        """
        new_acq = Acquisition(copy.deepcopy(self.analysis, memo))
        new_acq.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new_acq

    def __repr__(self):
        return f"({self.analysis}, {self.name})"

    def deep_copy(self):
        new_acq = Acquisition(copy.deepcopy(self.analysis))
        new_acq.__dict__.update(copy.deepcopy(self.__dict__))
        return new_acq

    def load_data(self, data: dict):
        for key, item in data.items():
            setattr(self, key, item)
        # self.s_r_c = int(self.sample_rate / 1000)
        if "saved_events_dict" in data:
            self.create_postsynaptic_events()
            self.event_arrays = [
                i.event_array - i.event_start_y for i in self.postsynaptic_events
            ]

    def set_epoch(self, epoch):
        self.epoch = epoch

    def set_pulse_amp(self, pulse_amp):
        self.pulse_amp = pulse_amp

    def set_ramp(self, ramp):
        self.ramp = ramp

    def plot_acq_y(self):
        raise NotImplementedError

    def plot_acq_x(self):
        raise NotImplementedError

    def delete(self):
        self.accepted = False

    def accept(self):
        self.accepted = True

    @staticmethod
    def filters():
        return [i.name for i in Filters]

    @staticmethod
    def windows():
        return [i.name for i in Windows]

    def run_analysis(self):
        raise NotImplementedError


if __name__ == "__main__":
    Acquisition()
