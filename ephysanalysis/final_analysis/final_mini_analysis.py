from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import statsmodels.api as sm

from ..functions.curve_fit import s_exp_decay, db_exp_decay, t_exp_decay


class FinalMiniAnalysis:
    """
    This class is used to compile all the data from a dictionary of
    acquistions that contain mini data. The class contains the raw data, and
    the averaged data. The number of events and acquisitions that were deleted
    also needed as input to the class however, the initial value is set to 0.
    """

    def __init__(
        self,
        acq_dict,
        events_deleted=0,
        acqs_deleted=0,
        sample_rate=10000,
        curve_fit_decay=False,
        curve_fit_type="db_exp",
    ):
        self.acq_dict = acq_dict
        self.events_deleted = events_deleted
        self.acqs_deleted = acqs_deleted
        self.sample_rate = sample_rate
        self.compute_data()

    def extract_raw_data(self):
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
        self.acq_dict = {
            i[0]: i[1]
            for i in self.acq_dict.items()
            if len(i[1].postsynaptic_events) > 0
        }
        df_list = [i.final_acq_data() for i in self.acq_dict.values()]

        self.raw_df = pd.concat(df_list, axis=0, ignore_index=True)

        self.raw_df["Acq time stamp"] = (
            self.raw_df["Acq time stamp"] - self.raw_df["Acq time stamp"].unique()[0]
        ) * 1000
        self.raw_df["Real time"] = (
            self.raw_df["Acq time stamp"] + self.raw_df["Event time (ms)"]
        )

    def extract_final_data(self):
        columns_for_analysis = [
            "IEI (ms)",
            "Amplitude (pA)",
            "Est tau (ms)",
            "Rise rate (pA/ms)",
            "Rise time (ms)",
        ]

        if "Curve fit tau (ms)" in list(self.raw_df.columns):
            columns_for_analysis.append("Curve fit _tau (ms)")

        means = self.raw_df[columns_for_analysis].mean().to_frame().T
        std = self.raw_df[columns_for_analysis].std().to_frame().T
        sem = self.raw_df[columns_for_analysis].sem().to_frame().T
        median = self.raw_df[columns_for_analysis].median().to_frame().T
        skew = self.raw_df[columns_for_analysis].skew().to_frame().T
        cv = std / means
        self.final_df = pd.concat([means, std, sem, median, skew, cv])
        self.final_df.insert(
            0, "Statistic", ["mean", "std", "sem", "median", "skew", "cv"]
        )

        total_events = sum([item.total_events() for item in self.acq_dict.values()])
        self.final_df["Ave event tau"] = [
            self.fit_tau_x,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        self.final_df["Events"] = [total_events, np.nan, np.nan, np.nan, np.nan, np.nan]
        self.final_df["Events deleted"] = [
            self.events_deleted,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        self.final_df["Acqs"] = [
            len(self.acq_dict.keys()),
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        self.final_df["Acqs deleted"] = [
            self.acqs_deleted,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]

        self.final_df.reset_index(inplace=True)
        self.final_df.drop(["index"], axis=1, inplace=True)

    def create_average_mini(self):
        peak_align_values = sum(
            [item.peak_values() for item in self.acq_dict.values()], []
        )
        events_list = sum([item.event_arrays() for item in self.acq_dict.values()], [])
        max_min = max(peak_align_values)
        start_values = [max_min - i for i in peak_align_values]
        arrays = [np.append(i * [j[0]], j) for i, j in zip(start_values, events_list)]
        max_length = max(map(len, arrays))
        end_values = [max_length - len(i) for i in arrays]
        final_arrays = [np.append(j, i * [j[-1]]) for i, j in zip(end_values, arrays)]
        self.average_mini = np.average(np.array(final_arrays), axis=0)
        self.average_mini_x = np.arange(self.average_mini.shape[0]) / (
            self.sample_rate / 1000
        )

    def analyze_average_mini(self):
        self.average_mini = self.average_mini - np.mean(self.average_mini[0:10])
        event_peak_x = np.argmin(self.average_mini)
        event_peak_y = np.min(self.average_mini)
        est_tau_y = event_peak_y * (1 / np.exp(1))
        self.decay_y = self.average_mini[event_peak_x:]
        self.decay_x = np.arange(len(self.decay_y)) / 10
        self.est_tau_x = np.interp(est_tau_y, self.decay_y, self.decay_x)
        init_param = np.array([event_peak_y, self.est_tau_x])
        upper_bound = (event_peak_y + 5, self.est_tau_x + 10)
        lower_bound = (event_peak_y - 5, self.est_tau_x - 10)
        bounds = [lower_bound, upper_bound]
        popt, pcov = curve_fit(
            s_exp_decay, self.decay_x, self.decay_y, p0=init_param, bounds=bounds
        )
        fit_amp, self.fit_tau_x = popt
        self.fit_decay_y = s_exp_decay(self.decay_x, fit_amp, self.fit_tau_x)
        self.decay_x = self.decay_x + event_peak_x / 10

    def compute_data(self):
        self.create_average_mini()
        self.analyze_average_mini()
        self.extract_raw_data()
        self.extract_final_data()

    def stem_components(self, column):
        array_x = self.final_obj.raw_df["Real time"].to_numpy()
        array_y = self.final_obj.raw_df[column].to_numpy()
        stems_y = np.stack([array_y, array_y * 0], axis=-1).flatten()
        stems_x = np.stack([array_x, array_x], axis=-1).flatten()
        return array_x, array_y, stems_x, stems_y

    def save_data(self, save_filename):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        temp_list = [
            pd.Series(self.average_mini, name="ave_mini"),
            pd.Series(self.average_mini_x, name="ave_mini_x"),
            pd.Series(self.fit_decay_y, name="fit_decay_y"),
            pd.Series(self.decay_x, name="decay_x"),
        ]
        extra_data = pd.concat(temp_list, axis=1)
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="openpyxl"
        ) as writer:
            self.raw_df.to_excel(writer, index=False, sheet_name="Raw data")
            self.final_df.to_excel(writer, index=False, sheet_name="Final data")
            extra_data.to_excel(writer, index=False, sheet_name="Extra data")
