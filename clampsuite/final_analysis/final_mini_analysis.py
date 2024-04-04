from typing import Union

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from ..functions.curve_fit import s_exp_decay
from . import final_analysis


class FinalMiniAnalysis(final_analysis.FinalAnalysis, analysis="mini"):
    """
    This class is used to compile all the data from a dictionary of
    acquistions that contain mini data. The class contains the raw data, and
    the averaged data. The number of events and acquisitions that were deleted
    also needed as input to the class however, the initial value is set to 0.
    """

    def analyze(
        self,
        acq_dict: dict,
        acqs_deleted: int = 0,
        sample_rate: Union[int, float] = 10000,
        curve_fit_type: str = "s_exp",
    ):
        self.acqs_deleted = acqs_deleted
        self.sample_rate = sample_rate
        self.curve_fit_type = curve_fit_type
        self.compute_data(acq_dict)

    def extract_raw_data(self, acq_dict: dict):
        """
        This function compiles the data from each acquisitions and puts it
        into a pandas dataframe. The data that are included are: amplitudes,
        taus, events times, time stamp of acquisition, rise times, rise rates,
        ieis, each event time adjust for the time stamp of the respective
        acquisition and the array for the average mini. One thing to note is
        that ieis have an added nan at the end of the data for each
        acquisition so that the ieis are aligned with the other data from
        the acquisition.

        Returns
        -------
        None.

        """
        acq_dict = {
            i[0]: i[1] for i in acq_dict.items() if len(i[1].postsynaptic_events) > 0
        }
        df_list = [pd.DataFrame(i.acq_data()) for i in acq_dict.values()]
        keys = list(acq_dict.keys())
        self.s_r_c = acq_dict[keys[0]].s_r_c

        raw_df = pd.concat(df_list, axis=0, ignore_index=True)

        raw_df["Acq time stamp"] = (
            raw_df["Acq time stamp"] - np.sort(raw_df["Acq time stamp"].unique())[0]
        ) * 1000
        raw_df["Real time"] = raw_df["Acq time stamp"] + raw_df["Event time (ms)"]
        raw_df.sort_values("Acquisition", inplace=True)
        raw_df.reset_index(drop=True, inplace=True)
        self.df_dict["Raw data"] = raw_df

        self.events_deleted = np.sum([i.deleted_events for i in acq_dict.values()])

    def extract_final_data(self, acq_dict: dict):
        columns_for_analysis = [
            "IEI (ms)",
            "Amplitude (pA)",
            "Est tau (ms)",
            "Rise rate (pA/ms)",
            "Rise time (ms)",
            "Voltage offset (mV)",
            "Rs (MOhm)",
        ]
        raw_df = self.df_dict["Raw data"]
        if "Curve fit tau (ms)" in list(raw_df.columns):
            columns_for_analysis.append("Curve fit _tau (ms)")
        means = raw_df[columns_for_analysis].mean().to_frame().T
        std = raw_df[columns_for_analysis].std().to_frame().T
        sem = raw_df[columns_for_analysis].sem().to_frame().T
        median = raw_df[columns_for_analysis].median().to_frame().T
        skew = raw_df[columns_for_analysis].skew().to_frame().T
        cv = std / means
        final_df = pd.concat([means, std, sem, median, skew, cv])
        final_df.insert(0, "Statistic", ["mean", "std", "sem", "median", "skew", "cv"])

        total_events = sum([item.total_events() for item in acq_dict.values()])
        final_df["Ave event tau"] = [
            self.fit_tau_x,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        final_df["Events"] = [total_events, np.nan, np.nan, np.nan, np.nan, np.nan]
        final_df["Events deleted"] = [
            self.events_deleted,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        final_df["Acqs"] = [
            len(acq_dict.keys()),
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        final_df["Acqs deleted"] = [
            self.acqs_deleted,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]

        final_df.reset_index(inplace=True)
        final_df.drop(["index"], axis=1, inplace=True)
        self.df_dict["Final data"] = final_df

    def create_average_mini(self, acq_dict: dict):
        peak_align_values = sum([item.peak_values() for item in acq_dict.values()], [])
        events_list = sum([item.get_event_arrays() for item in acq_dict.values()], [])
        max_min = max(peak_align_values)
        start_values = [max_min - i for i in peak_align_values]
        arrays = [np.append(i * [j[0]], j) for i, j in zip(start_values, events_list)]
        max_length = max(map(len, arrays))
        end_values = [max_length - len(i) for i in arrays]
        final_arrays = [np.append(j, i * [j[-1]]) for i, j in zip(end_values, arrays)]
        average_mini = np.average(np.array(final_arrays), axis=0)
        return average_mini

    def analyze_average_mini(self, average_mini: np.ndarray):
        average_mini = average_mini - np.mean(average_mini[0:10])
        event_peak_x = np.argmin(average_mini)
        event_peak_y = np.min(average_mini)
        est_tau_y = event_peak_y * (1 / np.exp(1))
        decay_y = average_mini[event_peak_x:]
        decay_x = np.arange(len(decay_y)) / self.s_r_c
        est_tau_x = np.interp(est_tau_y, decay_y, decay_x)
        init_param = np.array([event_peak_y, est_tau_x])
        upper_bound = (0, np.inf)
        lower_bound = (-np.inf, 0)
        bounds = [lower_bound, upper_bound]
        popt, _ = curve_fit(s_exp_decay, decay_x, decay_y, p0=init_param, bounds=bounds)
        fit_amp, self.fit_tau_x = popt
        fit_decay_y = s_exp_decay(decay_x, fit_amp, self.fit_tau_x)
        decay_x = decay_x + event_peak_x / 10
        average_mini_x = np.arange(average_mini.shape[0]) / (self.sample_rate / 1000)
        temp_list = [
            pd.Series(average_mini, name="ave_mini_y"),
            pd.Series(average_mini_x, name="ave_mini_x"),
            pd.Series(fit_decay_y, name="fit_decay_y"),
            pd.Series(decay_x, name="fit_decay_x"),
        ]
        extra_data = pd.concat(temp_list, axis=1)
        self.df_dict["Extra data"] = extra_data

    def compute_data(self, acq_dict: dict):
        self.extract_raw_data(acq_dict)
        average_mini = self.create_average_mini(acq_dict)
        self.analyze_average_mini(average_mini)
        self.extract_final_data(acq_dict)

    def stem_components(
        self, column: str
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        df = self.df_dict.get("Raw data")
        if df is not None:
            array_x = df.get("Real time").to_numpy()
            array_y = df.get(column).to_numpy()
            stems_y = np.stack([array_y, array_y * 0], axis=-1).flatten()
            stems_x = np.stack([array_x, array_x], axis=-1).flatten()
            return array_x, array_y, stems_x, stems_y

    def save_data(self, save_filename: str):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        prog_data = pd.DataFrame(self.program_data, index=None)
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="openpyxl"
        ) as writer:
            for key, df in self.df_dict.items():
                df.to_excel(writer, index=False, sheet_name=key)
            prog_data.to_excel(writer, index=False, sheet_name="Program data")

    def load_data(self, file_path: str):
        self.df_dict = pd.read_excel(file_path, sheet_name=None)
        if "Final data" in self.df_dict:
            self.load_final_data(self.df_dict)

    def load_final_data(self, df):
        df = self.df_dict["Final data"]
        self.events_deleted = df["Events deleted"].to_numpy()[0]
        self.acqs_deleted = df["Acqs deleted"].to_numpy()[0]

    def final_data(self) -> Union[None, pd.DataFrame]:
        return self.df_dict.get("Final data")

    def raw_data(self) -> Union[None, pd.DataFrame]:
        return self.df_dict.get("Raw data")

    def extra_data(self) -> Union[None, pd.DataFrame]:
        return self.df_dict.get("Extra data")

    def average_event_y(self) -> np.ndarray:
        df = self.extra_data()
        if df is not None:
            return df["ave_mini_y"].dropna().to_numpy()
        else:
            return np.array([])

    def average_event_x(self) -> np.ndarray:
        df = self.extra_data()
        if df is not None:
            return df["ave_mini_x"].dropna().to_numpy()
        else:
            return np.array([])

    def fit_decay_y(self) -> np.ndarray:
        df = self.extra_data()
        if df is not None:
            return df["fit_decay_y"].dropna().to_numpy()
        else:
            return np.array([])

    def fit_decay_x(self) -> np.ndarray:
        df = self.extra_data()
        if df is not None:
            return df["fit_decay_x"].dropna().to_numpy()
        else:
            return np.array([])

    def timestamp_array(self) -> np.ndarray:
        return self.df_dict["Raw data"]["Real time"].to_numpy().flatten()

    def get_raw_data(self, column) -> np.ndarray:
        return self.df_dict["Raw data"][column].to_numpy().flatten()
