import math
import re
from collections.abc import Iterable
from typing import Literal

import numpy as np
from numpy.random import default_rng
from scipy import fft

from clampsuite.functions.template_psc import create_template


def round_sig(x, sig=2):
    if np.isnan(x):
        return np.nan
    elif x == 0:
        return 0
    elif x != 0 or not np.isnan(x):
        temp = math.floor(math.log10(abs(x)))
        if np.isnan(temp):
            return round(x, 0)
        else:
            return round(x, sig - int(temp) - 1)


def map_keys(keys: Iterable) -> dict:
    upper_values = {"hw", "fw", "auc", "ahp", "ai", "iv", "fi", "iei", "sfa", "cv"}
    capitalize_values = {"acq", "number"}
    lower_values = {"exp", "log"}
    unit_map = {
        "mv": "(mV)",
        "pa": "(pA)",
        "hz": "(Hz)",
        "ms": "(ms)",
        "pa/ms": "(pA/ms)",
        "mv/ms": "(mV/ms)",
        "index": "(ms)",
    }
    key_mapping = {}
    for key in keys:
        tokens = re.split(r"([_()\s])", key)

        result = []
        for token in tokens:
            if token == "_":
                result.append(" ")
            elif token.lower() in upper_values:
                result.append(token.upper())
            elif token.lower() in lower_values:
                result.append(token.lower())
            elif token in unit_map:
                result.append(unit_map[token])
            elif token.isalpha() or token in capitalize_values:
                result.append(token.capitalize())
            else:
                result.append(token)
        temp = "".join(result)
        key_mapping[key] = temp
    return key_mapping
