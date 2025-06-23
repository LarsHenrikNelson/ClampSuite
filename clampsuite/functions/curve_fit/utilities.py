import numpy as np


def _detect_pos_neg(y):
    maximum = np.abs(y.max())
    minimum = np.abs(y.min())
    if maximum > minimum:
        return "positive"
    else:
        return "negative"
