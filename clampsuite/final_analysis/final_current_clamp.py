from collections import defaultdict
from typing import Literal, Union
from pathlib import Path

import numpy as np
import pandas as pd

from ..acq import CurrentClampAcq
from ..functions.curve_fit import fit_iv, Sigmoid, Log
from ..functions.utilities import map_keys
from . import final_analysis


class FinalCurrentClampAnalysis(final_analysis.FinalAnalysis):
    def __init__(
        self,
        acq_dict: dict[int, CurrentClampAcq],
        iv_start: int | None = None,
        iv_end: int | None = None,
        rectify: bool = False,
    ):
        self.iv_start = iv_start
        self.iv_end = iv_end
        self.df_dict = {}
        self.rectify = rectify
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False
        self.acq_dict = acq_dict

    def analyze(
        self,
    ):
        self.create_raw_data()
        self.get_features()
        # self.final_data_pulse()
        # self.final_data_ramp()
        # self.create_first_ap_dfs(acq_dict, self.pulse_indexes, self.ramp_indexes)

    # def load_data(self, file_path: str | Path):
    #     self.df_dict = {}
    #     self.hertz = False
    #     self.pulse_ap = False
    #     self.ramp_ap = False

    #     with pd.ExcelFile(file_path) as dfs:
    #         for i in dfs.sheet_names:
    #             self.df_dict[i] = pd.read_excel(file_path, sheet_name=i)
    #             if i == "Hertz":
    #                 self.hertz = True
    #             if i == "Pulse APs":
    #                 self.pulse_ap = True
    #             if i == "Ramp APs":
    #                 self.ramp_ap = True

    def create_raw_data(self):
        spk_params = []
        acq_params = []
        for value in self.acq_dict.values():
            acq_data, spk_data = value.data()
            spk_params.append(pd.DataFrame(spk_data))
            acq_params.append(acq_data)
        spk_params = pd.concat(spk_params)
        key_mapping = map_keys(spk_params.columns)
        spk_params = spk_params.rename(columns=key_mapping)

        acq_params = pd.DataFrame(acq_params)
        key_mapping = map_keys(acq_params.columns)
        acq_params = acq_params.rename(columns=key_mapping)
        spk_params["HW (ms)"] = spk_params["HW Right (ms)"] - spk_params["HW Left (ms)"]
        spk_params["FW (ms)"] = spk_params["FW Right (ms)"] - spk_params["FW Left (ms)"]

        spk_params = spk_params.sort_values(
            ["Epoch", "Cycle", "Acq Number", "Spike Number"]
        ).reset_index(drop=True)

        acq_params = acq_params.sort_values(
            ["Epoch", "Cycle", "Acq Number"]
        ).reset_index(drop=True)

        self.df_dict["Spike Parameters"] = spk_params
        self.df_dict["Acq Parameters"] = acq_params

    def get_features(self):
        rheo_features = self.df_dict["Spike Parameters"].loc[
            self.df_dict["Spike Parameters"]
            .groupby(["Epoch", "Cycle"])["Acq Number"]
            .idxmin()
        ]
        rheo_features = (
            rheo_features.drop(columns=["Acq Number", "Spike Number", "Cycle"])
            .groupby("Epoch")
            .mean(numeric_only=True)
        )
        rheo_features = rheo_features.rename(
            columns={"Pulse Amp (pA)": "Rheobase (pA)"}
        )
        avg_data = (
            self.df_dict["Acq Parameters"]
            .groupby(["Epoch", "Pulse Amp (pA)"], as_index=False)
            .mean(numeric_only=True)
            .drop(columns=["Acq Number", "Cycle"])
        )
        sag_features = avg_data.loc[
            avg_data.groupby(["Epoch"])["Pulse Amp (pA)"].idxmin(),
            ["Epoch", "Sag (mV)", "Sag (ms)"],
        ]
        fi_features = self.fi_fit(self.df_dict["Acq Parameters"])
        iv_params = self.df_dict["Acq Parameters"]
        iv_params = iv_params.loc[iv_params["Freq (Hz)"] < 1e-6]
        iv_features = self.iv_fit(
            iv_params,
            start=self.iv_start,
            end=self.iv_end,
            rectify=self.rectify,
        )
        fr_features = (
            self.df_dict["Acq Parameters"]
            .groupby(["Epoch", "Cycle"], as_index=False)["Freq (Hz)"]
            .max()
            .rename(columns={"Freq (Hz)": "Max Freq (Hz)"})
            .drop(columns=["Cycle"])
            .groupby("Epoch", as_index=False)
            .mean()
        )
        features = (
            avg_data.drop(
                columns=["Sag (mV)", "Sag (ms)", "Pulse Amp (pA)", "Delta V (mV)"]
            )
            .groupby("Epoch")
            .mean(numeric_only=True)
        )
        features = pd.merge(features, rheo_features, on="Epoch", how="outer")
        features = pd.merge(features, sag_features, on="Epoch", how="outer")
        features = pd.merge(features, fi_features, on="Epoch", how="outer")
        features = pd.merge(features, iv_features, on="Epoch", how="outer")
        features = pd.merge(features, fr_features, on="Epoch", how="outer")
        self.df_dict["Epoch Parameters"] = features

    def fi_fit(self, acq_data):
        fi_output = []
        epochs = []
        fi_data = acq_data[acq_data["Pulse Amp (pA)"] >= 0]
        for key, value in fi_data.groupby("Epoch").groups.items():
            if len(value) > 2:
                current = fi_data.loc[value, "Pulse Amp (pA)"]
                firing_rate = fi_data.loc[value, "Freq (Hz)"]
            sig_fit = Sigmoid()
            sig_fit.fit(current, firing_rate)
            temp = sig_fit.params
            epochs.append(key)
            fi_output.append(temp._asdict())
        fi_features = pd.DataFrame(fi_output)
        key_mapping = map_keys(fi_features.columns)
        key_mapping = {key: f"FI {value}" for key, value in key_mapping.items()}
        fi_features = fi_features.rename(columns=key_mapping)
        fi_features["Epoch"] = epochs
        return fi_features

    def iv_fit(
        self,
        acq_data,
        column: str = "Delta V (mV)",
        start: int | float | None = None,
        end: int | float | None = None,
        rectify: bool = False,
    ):
        iv_output = []
        epochs = []
        for key, value in acq_data.groupby("Epoch").groups.items():
            current = acq_data.loc[value, "Pulse Amp (pA)"]
            voltage = acq_data.loc[value, column]
            temp = fit_iv(current, voltage, start, end, rectify)
            epochs.append(key)
            iv_output.append(temp._asdict())
        iv_features = pd.DataFrame(iv_output)
        key_mapping = map_keys(iv_features.columns)
        key_mapping = {key: f"{column} {value}" for key, value in key_mapping.items()}
        iv_features = iv_features.rename(columns=key_mapping)
        iv_features["Epoch"] = epochs
        return iv_features

    def log_fit(self, spike_data, column: str):
        log_output = []
        epochs = []
        for key, value in spike_data.groupby("Epoch").groups.items():
            y = spike_data.loc[value, column]
            x = spike_data.loc[value, "Spike Number"]
            log_fit = Log()
            log_fit.fit(x, y)
            temp = log_fit.params
            epochs.append(key)
            log_output.append(temp._asdict())
        log_features = pd.DataFrame(log_output)
        key_mapping = map_keys(log_features.columns)
        key_mapping = {key: f"{column} {value}" for key, value in key_mapping.items()}
        log_features = log_features.rename(columns=key_mapping)
        log_features["Epoch"] = epochs
        return log_features

    def create_first_aps(
        self, acq_dict: dict, indexes: Union[list, np.ndarray]
    ) -> dict:
        ap_dict = defaultdict(list)
        for i in indexes:
            if len(acq_dict[i].first_ap) >= 1:
                ap_dict[acq_dict[i].epoch].append(acq_dict[i].first_ap)
        return ap_dict

    def average_aps(self, ap_list: Union[list, np.ndarray]) -> np.ndarray:
        """
        This function takes a list of a lists/arrays, finds the max values
        and then aligns all the lists/arrays to the max value by adding an
        array of values to the beginning of each list/array (the value is the
        first value in each list/array)

        Parameters
        ----------
        dict_entry : Dictionary entry that contains a several lists/arrays.

        Returns
        -------
        average : The averaged list/array of several lists/arrays based on on
        the index of the maximum value.

        """
        ap_max_values = [np.argmax(i) for i in ap_list]
        max_ap = max(ap_max_values)
        start_values = [max_ap - i for i in ap_max_values]
        arrays = [np.append(i * [j[0]], j) for i, j in zip(start_values, ap_list)]
        length = min(map(len, arrays))
        arrays = [i[:length] for i in arrays]
        average = np.average(np.array(arrays), axis=0)
        return average

    def pulse_averages(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df_pulse = raw_df.loc[raw_df["Ramp"] == 0]
        if df_pulse.empty:
            return df_pulse
        indexes = []
        for i in df_pulse["Epoch"].unique():
            temp = df_pulse.loc[df_pulse["Epoch"] == i]
            for j in temp["Cycle"].unique():
                temp_2 = temp.loc[df_pulse["Cycle"] == j]
                ind = temp_2["Num spikes"].first_valid_index()
                if ind is None:
                    pass
                else:
                    indexes.append(ind)
        df_spikes = raw_df.iloc[indexes]
        self.pulse_indexes = raw_df["Acquisition"].iloc[indexes].to_numpy()
        df_ave_spike = df_spikes.groupby(["Epoch"]).mean(numeric_only=True)
        return df_ave_spike
