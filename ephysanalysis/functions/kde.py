import numpy as np
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV


def create_kde(df, column):
    y = df[column].dropna().to_numpy()[:, np.newaxis]
    x = np.arange(y.shape[0])[:, np.newaxis]
    kde_obj = KernelDensity(kernel="gaussian")
    bandwidth = np.logspace(-1, 1, 20)
    grid = GridSearchCV(kde_obj, {"bandwidth": bandwidth})
    grid.fit(y)
    kde_final = grid.best_estimator_
    logprob = kde_final.score_samples(x)
    log_y = np.exp(logprob)
    return log_y, np.arange(y.shape[0])
