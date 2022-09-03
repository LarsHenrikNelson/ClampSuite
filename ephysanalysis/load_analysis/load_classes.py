# -*- coding: utf-8 -*-
"""
Created on Mon Jan 10 14:51:16 2022

Last updated on Wed Feb 16 12:33:00 2021

@author: LarsNelson
"""
import numpy as np
import pandas as pd


class LoadMiniSaveData:
    def __init__(self, excel_file):
        extra_data = excel_file["Extra data"]
        self.raw_df = excel_file["Raw data"]
        self.final_df = excel_file["Final data"]
        self.average_mini = extra_data["ave_mini"].dropna().to_numpy()
        self.average_mini_x = extra_data["ave_mini_x"].dropna().to_numpy()
        self.fit_decay_y = extra_data["fit_decay_y"].dropna().to_numpy()
        self.decay_x = extra_data["decay_x"].dropna().to_numpy()


class LoadEvokedCurrentData:
    def __init__(self, excel_file):
        self.raw_df = excel_file["Raw data"]
        self.final_df = excel_file["Final data"]


class LoadCurrentClampData:
    def __init__(self, file_path):
        with pd.ExcelFile(file_path) as dfs:
            self.raw_df = pd.read_excel(file_path, sheet_name="Raw data")
            self.iv_df = pd.read_excel(file_path, sheet_name="IV_df")
            print
            self.deltav_df = pd.read_excel(file_path, sheet_name="Deltav_df")
            self.final_df = pd.read_excel(
                file_path, sheet_name="Final data", header=[0, 1]
            ).drop(labels=0)
            if "Pulse APs" in dfs.sheet_names:
                self.pulse_ap_df = pd.read_excel(file_path, "Pulse APs").to_numpy()
            if "Ramp APs" in dfs.sheet_names:
                self.ramp_df = pd.read_excel(file_path, "Ramp APs").to_numpy()

        self.plot_epochs = self.iv_df.columns.to_list()[:-1]
        self.plot_epochs = [int(i) for i in self.plot_epochs]
        self.process_final_data()

    def process_final_data(self):
        self.final_df.rename(
            columns={"Unnamed: 2_level_1": "", "Unnamed: 1_level_1": ""},
            level=1,
            inplace=True,
        )
        self.final_df.rename(columns={"Unnamed: 0_level_0": ""}, level=0, inplace=True)
        self.final_df["Epoch"] = self.final_df["Epoch"].astype("int64")
        self.final_df["Ramp"] = self.final_df["Ramp"].astype("int64")
        self.final_df[""] = self.final_df[""].astype("int64")
        self.final_df.set_index(self.final_df[""]["Pulse_amp"], inplace=True)
