from pathlib import PurePath

from . import acq
from ..functions.utilities import load_scanimage_file, load_json_file


class BaseAcq(acq.Acq, analysis="base"):
    def load_acq(self):
        path_obj = PurePath(self.path)
        if path_obj.suffix == ".mat":
            acq_components = load_scanimage_file(path_obj)
            self.name = acq_components[0]
            self.acq_number = acq_components[1]
            self.array = acq_components[2]
            self.epoch = acq_components[3]
            self.pulse_pattern = acq_components[4]
            self.ramp = acq_components[5]
            self.pulse_amp = acq_components[6]
            self.time_stamp = acq_components[7]
        elif path_obj.suffix == ".json":
            load_json_file(self, path_obj)
        else:
            pass
