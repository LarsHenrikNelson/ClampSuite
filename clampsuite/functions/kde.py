import numpy as np
from KDEpy import FFTKDE


def create_kde(df, column):
    y = df[column].dropna().to_numpy()
    bw = np.cov(y)
    min_y = y.min() - bw * 0.01
    max_y = y.max() + bw * 0.01
    power2 = int(np.ceil(np.log2(y.size)))
    x = np.linspace(min_y, max_y, num=2**power2)
    try:
        if column != "Rise time (ms)":
            y_kde = FFTKDE(bw="ISJ", kernel="gaussian").fit(y).evaluate(x)
        else:
            y_kde = FFTKDE(bw="silverman", kernel="gaussian").fit(y).evaluate(x)
    except ValueError:
        y_kde = FFTKDE(kernel="gaussian").fit(y).evaluate()
    return y_kde, x
