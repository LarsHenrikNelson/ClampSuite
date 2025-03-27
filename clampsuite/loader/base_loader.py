import numpy as np
from ..acq import Acquisition


class BaseLoader:

    def __init__(self, analysis: str, callback_func: callable = print):
        self.callback_func = callback_func
