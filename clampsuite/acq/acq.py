import copy

import numpy as np


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

    def __new__(cls, analysis: str, path: str, *args):
        subclass = cls._class_type[analysis]
        obj = object.__new__(subclass)
        obj.analysis = analysis
        obj.version = "0.0.3"
        return obj

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        """
        Seems to work. Needs more testing. __deepcopy__ needs to work if
        someone wants to pickle a file.
        """
        new_acq = Acquisition(
            copy.deepcopy(self.analysis, memo), copy.deepcopy(self.path, memo)
        )
        new_acq.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new_acq

    def __repr__(self):
        return f"({self.analysis}, {self.name})"

    def deep_copy(self):
        new_acq = Acquisition(copy.deepcopy(self.analysis), copy.deepcopy(self.path))
        new_acq.__dict__.update(copy.deepcopy(self.__dict__))
        return new_acq

    def load_data(self, data: dict):
        for key, item in data.items():
            setattr(self, key, item)
        if data.get("saved_events_dict"):
            self.create_postsynaptic_events()
            self.x_array = np.arange(len(self.final_array)) / self.s_r_c
            self.event_arrays = [
                i.event_array - i.event_start_y for i in self.postsynaptic_events
            ]

if __name__ == "__main__":
    Acquisition()
