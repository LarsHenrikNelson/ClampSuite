# %%
from ephysanalysis.acq.acq import Acq

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import signal, integrate, stats, interpolate
import numpy as np
import bottleneck as bn
import pandas as pd
from scipy.stats import linregress
import pickle
from glob import glob
import json
from sklearn.linear_model import LinearRegression
from patsy import cr
import copy
from pathlib import PurePath, Path
from scipy.fft import rfft, rfftfreq, irfft
from copy import deepcopy
from ephysanalysis.functions.curve_fit import db_exp_decay, s_exp_decay
from ephysanalysis.final_analysis.final_mini_analysis import FinalMiniAnalysis

# %%
# Mini analysis test
mini_dict = {}
for i in range(1, 11):
    path = f"D:/Lars Slice Ephys/2021_12_09/AD0_{i}.mat"
    f = Acq(analysis="mini", path=path)
    f.load_acq()
    f.analyze()
    mini_dict[str(i)] = f

#%%
final_data = FinalMiniAnalysis(mini_dict)

#%%
# oepsc analysis test
path = "/Volumes/Backup/Lars Slice Ephys/2022_07_21/AD1_1.mat"
f = Acq(analysis="oepsc", path=path)
f.load_acq()
f.analyze()

#%%
# oepsc analysis test
path = "D:/Lars Slice Ephys/2022_07_21/AD1_6.mat"
g = Acq(analysis="oepsc", path=path)
g.load_acq()
g.analyze()
