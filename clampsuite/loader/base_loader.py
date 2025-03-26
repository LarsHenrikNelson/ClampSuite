import numpy as np
from ..acq import Acquisition


class BaseLoader:

    def __init__(self, analysis: str, callback_func: callable = print):
        self.analysis = analysis
        self.callback_func = callback_func
        self.acquisitions = {}

    def create_acquisitions(self):
        output = {}
        for vals in self.acquisitions.values():
            obj = Acquisition(self.analysis)
            obj.load_data(vals)
            output[int(obj.acq_number)] = obj
        return output
