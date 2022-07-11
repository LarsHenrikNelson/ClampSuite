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


# %%
path = "D:/Lars Slice Ephys/2021_12_09/Cell 1 Analysis/Cell_1_AD0_1.json"
h = Acq(analysis="base", path=path)
i = Acq(analysis="filter", path=path)
f = Acq(analysis="mini", path=path)

#%%
path = "D:/Lars Slice Ephys/2021_12_09/Cell 1 Analysis/Cell_1_AD0_1.json"
f = Acq(analysis="mini", path=path)
f.load_acq()

#%%
path = "D:/Lars Slice Ephys/2021_12_09/AD0_1.mat"
g = Acq(analysis="mini", path=path)
g.load_acq()
g.analyze()

#%%
h.load_acq()
i.load_acq()
f.load_acq()

#%%
xy = MiniAnalysis(
    acq_components=acq_components,
    sample_rate=10000,
    baseline_start=0,
    baseline_end=80,
    filter_type="fir_zero_2",
    order=201,
    low_pass=600,
    low_width=600,
    window="hann",
    template=None,
    rc_check=True,
    rc_check_start=10000,
    rc_check_end=10300,
    sensitivity=2.5,
    amp_threshold=7,
    mini_spacing=5,
    min_rise_time=0.5,
    min_decay_time=0.7,
    invert=False,
    curve_fit_decay=True,
    decon_type="wiener",
)
xy.analyze()


#%%
# filtering decon array test
filt = signal.firwin2(
    301, freq=[0, 100, 400, 10000 / 2], gain=[1, 1, 0, 0], window="hann", fs=10000,
)

#%%
y = signal.filtfilt(
    filt, 1.0, xy.deconvolved_array - np.mean(xy.deconvolved_array[0:800])
)
plt.plot(y)

#%%
kernel = np.hstack((xy.template, np.zeros(len(xy.final_array) - len(xy.template))))

#%%
convolved = signal.convolve(xy.final_array, xy.template, mode="same")

#%%
correlated = signal.correlate(xy.final_array, xy.template[30:], mode="same")

#%%
mu, std = stats.norm.fit(xy.final_decon_array)
peaks, _ = signal.find_peaks(xy.final_decon_array, height=2.25 * abs(std))
events = peaks

#%%
z = bn.move_mean(xy.final_array, window=5, min_count=1) ** 2
mu, std = stats.norm.fit(xy.final_decon_array)
peaks, _ = signal.find_peaks(xy.final_decon_array, height=2.5 * abs(std))
events = peaks

#%%
xy_fft_orig = rfft(xy.array[:100000])
xy_freq = rfftfreq(len(xy.array[:100000]), 1 / 10000)

xy_fft_filt = rfft(xy.final_array)
xy_freq_filt = rfftfreq(len(xy.final_array), 1 / 10000)

kernel = np.hstack((xy.template, np.zeros(len(xy.final_array) - len(xy.template))))
temp_fft = rfft(kernel)
temp_freq = rfftfreq(len(kernel), 1 / 10000)

#%%
fig, ax = plt.subplots()
# ax.plot(xy_freq, np.abs(xy_fft_filt), "white")
ax.plot(temp_freq, np.abs(xy_fft_filt / temp_fft), "white")
# ax.plot(peaks / 10, xy.final_decon_array[peaks], "mo")
# ax.set_ylim(0, 20000)
ax.set_xlim(0, 2000)
ax.set_facecolor("black")
ax.tick_params(axis="both", colors="white", labelsize=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(axis="both", labelsize=18)
ax.spines[["top", "left", "right", "bottom"]].set_color("white")
ax.set_xlabel("Frequency", fontsize=20, fontweight="bold")
ax.set_ylabel("Amplitude (AU)", fontsize=20, fontweight="bold")
l = ax.figure.subplotpars.left
r = ax.figure.subplotpars.right
t = ax.figure.subplotpars.top
b = ax.figure.subplotpars.bottom
figw = float(6) / (r - l)
figh = float(4) / (t - b)
ax.figure.set_size_inches(figw, figh)


#%%
fig.savefig("D:/Lab meeting 2022_06_07/ftt_filt2_decon", bbox_inches="tight")

#%%
x = copy.deepcopy(acq_dict["1"])

test = FinalMiniAnalysis(acq_dict)
k = test.final_df

x = acq_dict["170"]
x.save_postsynaptic_events()
with open("Cell_6_AD0_170.json", "w") as write_file:
    json.dump(x.__dict__, write_file, cls=NumpyEncoder)


json_dict = {}
file_list = glob("*.json")
for i in range(len(file_list)):
    with open(file_list[i]) as file:
        data = json.load(file)
        x = LoadMiniAnalysis(data)
        json_dict[str(x.acq_number)] = x

json_dict["172"].postsynaptic_events = [
    x
    for _, x in sorted(
        zip(json_dict["172"].final_events, json_dict["172"].postsynaptic_events)
    )
]


with open("test", "wb") as pic:
    pickle.dump(acq_dict, pic, protocol=pickle.HIGHEST_PROTOCOL)

with open("test", "rb") as pic_o:
    test = pickle.load(pic_o)

j = pd.read_excel("Test.xlsx", sheet_name=None)

test_load = LoadMiniSaveData(j)

#%%
# Testing out the LFP and oEPSC function
# August 4, 2021
lfp_acq_dict = {}
oepsc_acq_dict = {}
for i in range(11, 44):
    path = PurePath(f"D:/Lars Slice Ephys/2021_11_21/AD0_{i}.mat")
    acq_components = load_scanimage_file(path)
    o = oEPSCAnalysis(
        acq_components=acq_components,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=1000,
        filter_type="fir_zero_2",
        order=51,
        low_pass=600,
        low_width=600,
        window="hann",
    )
    oepsc_acq_dict[str(i)] = o
for i in range(11, 44):
    path = PurePath(f"D:/Lars Slice Ephys/2021_11_21/AD1_{i}.mat")
    acq_components = load_scanimage_file(path)
    l = LFPAnalysis(
        acq_components=acq_components,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=1000,
        filter_type="fir_zero_2",
        order=201,
        low_pass=600,
        low_width=600,
        window="hann",
    )
    lfp_acq_dict[str(i)] = l

#%%
fig, ax = plt.subplots()
ax.plot(
    oepsc_acq_dict["11"].x_array, oepsc_acq_dict["11"].filtered_array, color="white"
)
# ax.plot(
#     oepsc_acq_dict["11"].x_array,
#     oepsc_acq_dict["11"].filtered_array,
#     color="red",
#     alpha=0.75,
# )
# ax.plot(acq.spike_x_array(), acq.first_ap, color="magenta")
# ax.plot(acq2.x_array[acq.pulse_start:3035], np.gradient(acq2.array)[acq.pulse_start:3035], "magenta")
ax.set_xlim(900, 1400)
ax.set_facecolor("black")
ax.tick_params(axis="both", colors="white", labelsize=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(axis="both", labelsize=18)
ax.spines[["top", "left", "right", "bottom"]].set_color("white")
ax.set_xlabel("Time", fontsize=20, fontweight="bold")
ax.set_ylabel("Amplitude (mV/ms)", fontsize=20, fontweight="bold")
l = ax.figure.subplotpars.left
r = ax.figure.subplotpars.right
t = ax.figure.subplotpars.top
b = ax.figure.subplotpars.bottom
figw = float(6) / (r - l)
figh = float(4) / (t - b)
ax.figure.set_size_inches(figw, figh)

#%%
fig.savefig("D:/Lab meeting 2022_06_07/oepsc_filt", bbox_inches="tight")


#%%
test = FinalEvokedCurrent(o_acq_dict=oepsc_acq_dict, lfp_acq_dict=lfp_acq_dict)
# test.save_data('Test')

#%%
# Testing out the current clamp final analysis using Oct 29, 2021
acq_dict = {}
for i in range(1, 474):
    path = PurePath(f"D:\Lars Slice Ephys/2021_10_06/AD0_{i}.mat")
    acq_components = load_scanimage_file(path)
    acq = CurrentClamp(
        acq_components=acq_components,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=300,
        pulse_start=300,
        pulse_end=1000,
        ramp_start=300,
        ramp_end=4000,
    )
    acq.analyze()
    acq_dict[str(i)] = acq

#%%
test_acq = acq_dict["11"]

#%%
test = FinalCurrentClampAnalysis(acq_dict)


#%%
for i in test.deltav_df.columns:
    plt.plot(test.deltav_df)


final_obj = LoadCurrentClampData("test.xlsx")

# %%
i = 291
path = PurePath(f"/Volumes/Backup/Lars Slice Ephys/2021_10_06/AD0_{i}.mat")
acq_components = load_scanimage_file(path)
acq = CurrentClamp(
    acq_components=acq_components,
    sample_rate=10000,
    baseline_start=0,
    baseline_end=300,
    pulse_start=300,
    pulse_end=1000,
    ramp_start=300,
    ramp_end=4000,
)
acq.analyze()

#%%
dv = np.gradient(acq.first_ap)
dvv = np.gradient(dv)
dvvv = np.gradient(dvv)

# %%
i = 34
path = PurePath(f"/Volumes/Backup/Lars Slice Ephys/2021_10_06/AD0_{i}.mat")
acq_components = load_scanimage_file(path)
acq2 = CurrentClamp(
    acq_components=acq_components,
    sample_rate=10000,
    baseline_start=0,
    baseline_end=300,
    pulse_start=300,
    pulse_end=1000,
    ramp_start=300,
    ramp_end=4000,
)
acq2.analyze()
#%%
dv2 = np.gradient(acq2.first_ap)
dvv2 = np.gradient(dv2)
dvvv2 = np.gradient(dvv2)

#%%
fig, ax = plt.subplots()
ax.plot(acq.spike_x_array(), np.gradient(np.gradient(acq.first_ap)), color="white")
ax.plot(acq.spike_x_array(), acq.first_ap, color="magenta")
ax.plot(acq.plot_ahp_x(), acq.ahp_y, color="green", marker="o")
# ax.plot(acq2.x_array[acq.pulse_start:3035], np.gradient(acq2.array)[acq.pulse_start:3035], "magenta")
ax.set_facecolor("black")
ax.tick_params(axis="both", colors="white", labelsize=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(axis="both", labelsize=18)
ax.spines[["top", "left", "right", "bottom"]].set_color("white")
ax.set_xlabel("Time", fontsize=20, fontweight="bold")
ax.set_ylabel("Amplitude (mV/ms)", fontsize=20, fontweight="bold")
l = ax.figure.subplotpars.left
r = ax.figure.subplotpars.right
t = ax.figure.subplotpars.top
b = ax.figure.subplotpars.bottom
figw = float(6) / (r - l)
figh = float(4) / (t - b)
ax.figure.set_size_inches(figw, figh)


#%%
fig.savefig("D:\Lab meeting 2022_06_07/cc_inter", bbox_inches="tight")


# %%
i = 292
path = PurePath(f"D:\Lars Slice Ephys/2021_10_06/AD0_{i}.mat")
acq_components = load_scanimage_file(path)
ak = Acquisition(
    acq_components=acq_components,
    sample_rate=10000,
    baseline_start=0,
    baseline_end=300,
)

# %%
sos = signal.bessel(4, Wn=600, btype="lowpass", output="sos", fs=10000, norm="phase")
w, h = signal.sosfreqz(sos, fs=10000)
db = 20 * np.log10(np.maximum(np.abs(h), 1e-5))
plt.plot(w, db)

# %%
lo = signal.remez(51, [0, 600, 1200, 10000 / 2], [1, 0], fs=10000,)
w, h = signal.freqz(lo, fs=10000)
db = 20 * np.log10(np.maximum(np.abs(h), 1e-5))


# %%
lo = signal.firwin2(
    51, [0, 600, 1200, 10000 / 2], [1, 1, 0, 0], fs=10000, window="rectangular"
)
w, h = signal.freqz(lo, fs=10000)
db = 20 * np.log10(np.maximum(np.abs(h), 1e-5))

#%%
fig, ax = plt.subplots()
ax.plot(w, db, color="white")
ax.axvline(300, color="red")
ax.set_facecolor("black")
ax.tick_params(axis="both", colors="white", labelsize=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(axis="both", labelsize=18)
ax.spines[["top", "left", "right", "bottom"]].set_color("white")
ax.set_xlabel("Frequency (Hz)", fontsize=20, fontweight="bold")
ax.set_ylabel("Gain (dB)", fontsize=20, fontweight="bold")
l = ax.figure.subplotpars.left
r = ax.figure.subplotpars.right
t = ax.figure.subplotpars.top
b = ax.figure.subplotpars.bottom
figw = float(6) / (r - l)
figh = float(4) / (t - b)
ax.figure.set_size_inches(figw, figh)

# %%
fig.savefig("D:\Lab meeting 2022_06_07/rectangular_filter_freq", bbox_inches="tight")

# %%
excel_file = pd.read_excel(
    "D:/Lars Slice Ephys/2021_12_09/Cell 1 Analysis/Cell_1.xlsx", sheet_name=None
)
raw = excel_file["Raw data"]

#%%
excel_file = pd.read_csv(
    "D:/Lab meeting 2022_06_07/test.csv", keep_default_na=False, na_values=[""]
)
excel_file.reset_index(inplace=True)

# %%
fig, ax = plt.subplots()
ax.plot(excel_file["index"], excel_file["x0000"], color="white")
ax.plot(
    excel_file["y0000"][:3].astype(float),
    excel_file["x0001"][:3].astype(float),
    marker="o",
    color="magenta",
    linestyle="None",
    markersize=10,
)
ax.set_facecolor("black")
ax.tick_params(axis="both", colors="white", labelsize=12)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.tick_params(axis="both", labelsize=18)
ax.spines[["top", "left", "right", "bottom"]].set_color("white")
ax.set_xlabel("Time (ms)", fontsize=20, fontweight="bold")
ax.set_ylabel("Amplitude (pA)", fontsize=20, fontweight="bold")
l = ax.figure.subplotpars.left
r = ax.figure.subplotpars.right
t = ax.figure.subplotpars.top
b = ax.figure.subplotpars.bottom
figw = float(6) / (r - l)
figh = float(4) / (t - b)
ax.figure.set_size_inches(figw, figh)

# %%
fig.savefig("D:\Lab meeting 2022_06_07/mini", bbox_inches="tight")

# %%
with open("C:/Users/LarsNelson/Desktop/test/save_filename_AD1_1.json") as file:
    data = json.load(file)
    x = LoadLFP(data)
# %%
