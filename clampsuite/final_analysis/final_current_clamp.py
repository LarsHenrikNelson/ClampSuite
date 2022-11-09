from collections import defaultdict
from typing import Union

import numpy as np
import pandas as pd
from scipy.stats import linregress
import statsmodels.api as sm

from . import final_analysis


class FinalCurrentClampAnalysis(final_analysis.FinalAnalysis, analysis="current_clamp"):
    def analyze(self, acq_dict: dict, iv_start: int = 1, iv_end: int = 6):
        self.iv_start = iv_start
        self.iv_end = iv_end
        self.df_dict = {}
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False
        self._analyze(acq_dict)

    def _analyze(self, acq_dict: dict):
        self.create_raw_data(acq_dict)
        self.final_data_pulse()
        self.final_data_ramp()
        self.create_first_ap_dfs(acq_dict)

    def load_data(self, file_path: str):
        self.df_dict = {}
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False

        with pd.ExcelFile(file_path) as dfs:
            for i in dfs.sheet_names:
                self.df_dict[i] = pd.read_excel(file_path, sheet_name=i)
                if i == "Hertz":
                    self.hertz = True
                if i == "Pulse APs":
                    self.pulse_ap = True
                if i == "Ramp APs":
                    self.ramp_ap = True

    def create_raw_data(self, acq_dict):
        raw_df = pd.DataFrame([acq_dict[i].create_dict() for i in acq_dict.keys()])
        raw_df["Epoch"] = pd.to_numeric(raw_df["Epoch"])
        raw_df["Pulse_pattern"] = pd.to_numeric(raw_df["Pulse_pattern"])
        raw_df["Pulse_amp"] = pd.to_numeric(raw_df["Pulse_amp"])
        raw_df["Ramp"] = pd.to_numeric(raw_df["Ramp"])
        self.df_dict["Raw data"] = raw_df

    def create_first_ap_dfs(self, acq_dict: dict):
        # Creating the final first action potentials and final data. It takes
        # manipulating to get the data to show up correctly in the TableWidget.
        pulse_dict, ramp_dict = self.create_first_aps(acq_dict)

        if pulse_dict:
            pulse_ap = self.first_ap_dict(pulse_dict)
        else:
            pulse_ap = {}

        if ramp_dict:
            ramp_ap = self.first_ap_dict(ramp_dict)
        else:
            ramp_ap = {}

        if pulse_ap:
            pulse_ap_df = pd.DataFrame(
                dict([(k, pd.Series(v)) for k, v in pulse_ap.items()])
            )
            self.pulse_ap = True
            self.df_dict["Pulse APs"] = pulse_ap_df

        if ramp_ap:
            ramp_ap_df = pd.DataFrame(
                dict([(k, pd.Series(v)) for k, v in ramp_ap.items()])
            )
            self.ramp_ap = True
            self.df_dict["Ramp APs"] = ramp_ap_df

    def create_first_aps(self, acq_dict: dict) -> tuple[dict, dict]:
        pulse_dict = defaultdict(lambda: defaultdict(list))
        ramp_dict = defaultdict(lambda: defaultdict(list))
        for i in acq_dict.keys():
            if len(acq_dict[i].first_ap) <= 1:
                pass
            else:
                if acq_dict[i].ramp == "0":
                    pulse_dict[acq_dict[i].epoch][acq_dict[i].pulse_amp].append(
                        acq_dict[i].first_ap
                    )
                if acq_dict[i].ramp == "1":
                    ramp_dict[acq_dict[i].epoch][acq_dict[i].pulse_amp].append(
                        acq_dict[i].first_ap
                    )
        return pulse_dict, ramp_dict

    def first_ap_dict(self, dictionary: dict) -> dict:
        ap_dict = {}
        if len(dictionary.keys()) > 1:
            for i in dictionary.keys():
                average = self.average_aps(dictionary[i])
                ap_dict[i] = average
        else:
            i = list(dictionary.keys())[0]
            average = self.average_aps(dictionary[i])
            ap_dict[i] = average
        return ap_dict

    def average_aps(self, dict_entry: Union[list, np.ndarray]) -> np.ndarray:
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
        first_pulse = min(map(int, list(dict_entry)))
        ap_max_values = [np.argmax(i) for i in dict_entry[str(first_pulse)]]
        max_ap = max(ap_max_values)
        start_values = [max_ap - i for i in ap_max_values]
        arrays = [
            np.append(i * [j[0]], j)
            for i, j in zip(start_values, dict_entry[str(first_pulse)])
        ]
        length = min(map(len, arrays))
        arrays = [i[:length] for i in arrays]
        average = np.average(np.array(arrays), axis=0)
        return average

    def membrane_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        df1 = df[df["Ramp"] == 0]
        if df1.empty == True:
            return None
        else:
            df_average = df1.groupby(
                ["Epoch", "Pulse_amp", "Pulse_pattern"],
                as_index=False,
                group_keys="Epoch",
            ).mean(numeric_only=True)
            df_pivot = df_average.pivot(
                index="Pulse_amp", values="Delta_v", columns="Epoch"
            )
            df_pivot.columns.name = ""
            slopes = []
            iv_lines = []
            iv_xs = []
            iv_ys = []
            columns = df_pivot.columns.to_list()
            for i in columns:
                temp = df_pivot[i].dropna()
                y = temp.to_numpy()[self.iv_start - 1 : self.iv_end]
                x = temp.index.to_list()[self.iv_start - 1 : self.iv_end]
                iv_xs.append(x)
                iv_ys.append(y)
                reg = linregress(x=x, y=y)
                slopes += [reg.slope * 1000]
                iv_temp = reg.slope * y + reg.intercept
                iv_lines.append(iv_temp)
            resistance = pd.DataFrame(
                data=slopes, index=columns, columns=["Membrane resistance"]
            )
            self.create_dataframe(iv_xs, columns, "iv_x")
            self.create_dataframe(iv_xs, columns, "iv_y")
            self.create_dataframe(iv_lines, columns, "IV lines")
            self.df_dict["Delta V"] = df_pivot.reset_index()
            return resistance

    def create_dataframe(
        self,
        data: Union[list, np.ndarray],
        columns: list[str],
        name: str,
        tranpose: bool = True,
    ):
        if tranpose:
            df = pd.DataFrame(data).T
        else:
            df = pd.DataFrame(data)
        df.columns = columns
        self.df_dict[name] = df

    def save_data(self, save_filename: str):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="xlsxwriter"
        ) as writer:
            for key, value in self.df_dict.items():
                if key == "Final data":
                    value.to_excel(writer, sheet_name=key)
                else:
                    value.to_excel(writer, index=False, sheet_name=key)

    def pulse_averages(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        raw_df["Cycle"] = raw_df.groupby(["Pulse_amp", "Epoch"]).cumcount()
        df_pulse = raw_df.loc[raw_df["Ramp"] == 0]
        if df_pulse.empty:
            return df_pulse
        indexes = []
        for i in df_pulse["Epoch"].unique():
            temp = df_pulse.loc[df_pulse["Epoch"] == i]
            for j in temp["Cycle"].unique():
                temp_2 = temp.loc[df_pulse["Cycle"] == j]
                ind = temp_2["Spike_threshold (mV)"].first_valid_index()
                if ind is None:
                    pass
                else:
                    indexes.append(ind)
        df_spikes = raw_df.iloc[indexes]
        df_ave_spike = df_spikes.groupby(["Epoch"]).mean(numeric_only=True)
        return df_ave_spike

    def final_data_pulse(self):
        raw_df = self.df_dict["Raw data"]
        df_ave_spike = self.pulse_averages(raw_df)
        resistance = self.membrane_resistance(raw_df)
        df_concat = pd.concat([df_ave_spike, resistance], axis=1).reset_index(
            names="Epoch"
        )
        df_concat.sort_values(by="Epoch")

        self.df_dict["Final data (pulse)"] = df_concat

    def pulse_hertz(self):
        pass

    def pulse_iei(self):
        pass

    def final_data_ramp(self):
        raw_df = self.df_dict["Raw data"]
        df_ramp = raw_df[raw_df["Ramp"] == 1]
        if not df_ramp.empty:
            final_ramp = df_ramp.groupby(["Epoch"]).mean(numeric_only=True)
            self.df_dict["Final data (ramp)"] = final_ramp
