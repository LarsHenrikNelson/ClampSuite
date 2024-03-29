from collections import defaultdict
from typing import Union

import numpy as np
import pandas as pd
from scipy.stats import linregress

from . import final_analysis
from ..acq import Acquisition


class FinalCurrentClampAnalysis(final_analysis.FinalAnalysis, analysis="current_clamp"):
    def analyze(self, acq_dict: dict, iv_start: int = 1, iv_end: int = 6, debug=False):
        self.iv_start = iv_start
        self.iv_end = iv_end
        self.df_dict = {}
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False
        if not debug:
            self._analyze(acq_dict)

    def _analyze(self, acq_dict: dict):
        self.create_raw_data(acq_dict)
        self.create_average_data()
        self.final_data_pulse()
        self.final_data_ramp()
        self.create_first_ap_dfs(acq_dict, self.pulse_indexes, self.ramp_indexes)

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

    def create_raw_data(self, acq_dict: dict[int, Acquisition]):
        raw_df = pd.DataFrame([acq_dict[i].acq_data() for i in acq_dict.keys()])
        raw_df["Epoch"] = pd.to_numeric(raw_df["Epoch"])
        raw_df["Pulse pattern"] = pd.to_numeric(raw_df["Pulse pattern"])
        raw_df["Pulse amp (pA)"] = pd.to_numeric(raw_df["Pulse amp (pA)"])
        raw_df["Ramp"] = pd.to_numeric(raw_df["Ramp"])
        raw_df["Acquisition"] = pd.to_numeric(raw_df["Acquisition"])
        raw_df.sort_values(["Epoch", "Ramp", "Cycle", "Pulse amp (pA)"], inplace=True)
        raw_df.reset_index(drop=True, inplace=True)
        self.df_dict["Raw data"] = raw_df

    def create_average_data(self):
        ave_df = (
            self.df_dict["Raw data"]
            .groupby(["Epoch", "Pulse amp (pA)"])
            .mean(numeric_only=True)
            .reset_index()
        )
        self.df_dict["Average data"] = ave_df

    def create_first_ap_dfs(
        self,
        acq_dict: dict,
        pulse_indexes: Union[list, np.ndarray],
        ramp_indexes: Union[list, np.ndarray],
    ):
        pulse_dict = self.create_first_aps(acq_dict, pulse_indexes)
        ramp_dict = self.create_first_aps(acq_dict, ramp_indexes)

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

    def create_first_aps(
        self, acq_dict: dict, indexes: Union[list, np.ndarray]
    ) -> tuple[dict, dict]:
        ap_dict = defaultdict(list)
        for i in indexes:
            if len(acq_dict[i].first_ap) >= 1:
                ap_dict[acq_dict[i].epoch].append(acq_dict[i].first_ap)
        return ap_dict

    def first_ap_dict(self, dictionary: dict[int, np.ndarray]) -> dict[int, np.ndarray]:
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

    def iv_curve(
        self,
        df: pd.DataFrame,
        start: int,
        end: Union[int, None],
        column: str,
        output_column: str,
    ) -> pd.DataFrame:
        if end is None:
            end = -1
        df_pivot = self.extract_features(df, column)
        slopes = []
        iv_lines = []
        iv_xs = []
        columns = df_pivot.columns.to_list()
        for i in columns:
            temp = df_pivot[i].dropna()
            y = temp.to_numpy()[start - 1 : end]
            x = temp.index.to_numpy()[start - 1 : end]
            iv_xs.append(x)
            reg = linregress(x=x, y=y)
            slopes += [reg.slope * 1000]
            iv_temp = reg.slope * x + reg.intercept
            iv_lines.append(iv_temp)
        resistance = pd.DataFrame(data=slopes, index=columns, columns=[output_column])
        self.create_dataframe(iv_xs, columns, f"{column} IV x")
        self.create_dataframe(iv_lines, columns, f"{column} IV lines")
        self.df_dict[column] = df_pivot.reset_index()
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

    def final_data_pulse(self):
        self.pulse_indexes = []
        raw_df = self.df_dict["Raw data"]
        df_pulses = raw_df[raw_df["Ramp"] == 0]
        resistance = self.iv_curve(
            df_pulses, self.iv_start, self.iv_end, "Delta V (mV)", "Membrane resistance"
        )
        sag_slope = self.iv_curve(
            df_pulses,
            1,
            self.iv_end,
            "Voltage sag (mV)",
            "Voltage sag slope",
        )
        if len(df_pulses["Spike threshold (mV)"].unique()) == 1 and np.isnan(
            df_pulses["Spike threshold (mV)"].unique()[0]
        ):
            temp = df_pulses.groupby(["Epoch"]).mean()
            temp.rename(columns={"Pulse amp (pA)": "Rheobase (pA)"}, inplace=True)
            temp = pd.concat([temp, resistance, sag_slope], axis=1).reset_index(
                names="Epoch"
            )
            self.df_dict["Final data (pulse)"] = temp
        else:
            df_ave_spike = self.pulse_averages(raw_df)
            iei = self.extract_features(df_pulses, "IEI").reset_index()
            self.df_dict["IEI"] = iei
            hertz = self.extract_features(df_pulses, "Hertz").reset_index()
            hertz.fillna(0, inplace=True)
            self.df_dict["Hertz"] = hertz
            df_concat = pd.concat(
                [df_ave_spike, resistance, sag_slope], axis=1
            ).reset_index(names="Epoch")
            df_concat.sort_values(by="Epoch")
            df_concat.rename(columns={"Pulse amp (pA)": "Rheobase (pA)"}, inplace=True)
            self.df_dict["Final data (pulse)"] = df_concat
            self.hertz = True
            self.pulse_ap = True

    def extract_features(self, df: pd.DataFrame, values: str) -> pd.DataFrame:
        df_average = df.groupby(
            ["Epoch", "Pulse amp (pA)", "Pulse pattern"],
            as_index=False,
            group_keys="Epoch",
        ).mean(numeric_only=True)
        df_pivot = df_average.pivot(
            index="Pulse amp (pA)", values=values, columns="Epoch"
        )
        return df_pivot

    def final_data_ramp(self):
        raw_df = self.df_dict["Raw data"]
        df_ramp = raw_df[raw_df["Ramp"] == 1]
        self.ramp_indexes = []
        if not df_ramp.empty:
            self.ramp_indexes = df_ramp["Acquisition"].to_numpy()
            final_ramp = df_ramp.groupby(["Epoch"]).mean(numeric_only=True)
            self.df_dict["Final data (ramp)"] = final_ramp
            self.ramp_ap = True
