from KDEpy import FFTKDE


def create_kde(df, column):
    y = df[column].dropna().to_numpy()
    try:
        if column != "Rise time (ms)":
            x, y1 = FFTKDE(bw="ISJ", kernel="gaussian").fit(y).evaluate()
        else:
            x, y1 = FFTKDE(bw="silverman", kernel="gaussian").fit(y).evaluate()
    except:
        x, y1 = FFTKDE(kernel="gaussian").fit(y).evaluate()
    return y1, x
