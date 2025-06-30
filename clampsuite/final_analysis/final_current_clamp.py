from collections import defaultdict
from typing import Union

import numpy as np
import pandas as pd

from . import final_analysis
from ..acq import CurrentClampAcq
from ..functions.curve_fit.iv_curve import fit_iv
from ..functions.utilities import map_keys


class FinalCurrentClampAnalysis(final_analysis.FinalAnalysis):
    def __init__(self, acq_dict: dict[int, CurrentClampAcq]):
        self.iv_start = 0
        self.iv_end = -1
        self.df_dict = {}
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False
        self.acq_dict = acq_dict

    def analyze(self, iv_start: int = 1, iv_end: int = 6, debug=False):
        if not debug:
            self._analyze(self.acq_dict)

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

    def create_raw_data(self, acq_dict: dict[int, CurrentClampAcq]):
        spk_params = []
        acq_params = []
        for value in acq_dict.values():
            acq_data, spk_data = value.data()
            spk_params.append(pd.DataFrame(spk_data))
            acq_params.append(acq_data)
        spk_params = pd.concat(spk_params)
        key_mapping = map_keys(spk_params.columns())
        spk_params = spk_params.rename(columns=key_mapping)

        acq_params = pd.DataFrame(acq_params)
        key_mapping = map_keys(acq_params.columns())
        acq_params = acq_params.rename(columns=key_mapping)

        self.df_dict["Spike parameters"] = spk_params
        self.df_dict["Acq parameters"] = acq_params

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

    def test(self):
        groups = self.df_dict["raw_data"].groupby(["Epoch"]).indices
        output = defaultdict(list)
        for epoch, indexes in groups.items():
            output["Epoch"].append(epoch)
            temp_df = self.df_dict["raw_data"].iloc[indexes]
            pulse_amp = temp_df["Pulse amp (pA)"].to_numpy()
            mem_res_output = fit_iv(
                temp_df["Delta V (mV)"].to_numpy(),
                pulse_amp,
                self.iv_start,
                self.iv_end,
            )
            output["Membrane resistance"].append(mem_res_output)
            sag_index = np.where(pulse_amp <= 0)[0][0]
            sag_res_output = fit_iv(
                temp_df["Voltage sag (mV)"].to_numpy(), pulse_amp, 0, sag_index
            )
            output["Sag resistance"].append(sag_res_output)

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
