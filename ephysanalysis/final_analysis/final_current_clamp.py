from collections import defaultdict

import numpy as np
import pandas as pd
import statsmodels.api as sm


class FinalCurrentClampAnalysis:
    def __init__(self, acq_dict, iv_start=1, iv_end=6):
        self.acq_dict = acq_dict
        self.iv_start = iv_start
        self.iv_end = iv_end
        self.create_raw_data()
        self.average_data()
        self.final_data()
        self.iv_curve_dataframe()
        self.deltav_dataframe()

    def create_raw_data(self):
        self.raw_df = pd.DataFrame(
            [self.acq_dict[i].create_dict() for i in self.acq_dict.keys()]
        )
        self.raw_df["Epoch"] = pd.to_numeric(self.raw_df["Epoch"])
        self.raw_df["Pulse_pattern"] = pd.to_numeric(self.raw_df["Pulse_pattern"])
        self.raw_df["Pulse_amp"] = pd.to_numeric(self.raw_df["Pulse_amp"])

    def average_data(self):
        # I need to separate the delta v and spike ieis from the rest of the
        # dataframe to clean it up.
        self.df_averaged_data = self.raw_df.groupby(
            ["Pulse_pattern", "Epoch", "Pulse_amp", "Ramp"]
        ).mean()
        self.df_averaged_data.reset_index(inplace=True)
        self.df_averaged_data.drop(["Pulse_pattern"], axis=1, inplace=True)
        self.df_averaged_data[["Pulse_amp", "Ramp", "Epoch"]] = self.df_averaged_data[
            ["Pulse_amp", "Ramp", "Epoch"]
        ].astype(int)

    def final_data(self):
        # Pivot the dataframe to get it into wideform format
        pivoted_df = self.df_averaged_data.pivot_table(
            index=["Epoch", "Ramp"], columns=["Pulse_amp"], aggfunc=np.nanmean
        )

        pivoted_df.reset_index(inplace=True)

        # Add the input resistance calculate
        resistance_df = self.membrane_resistance(pivoted_df)
        self.final_df = pd.concat([pivoted_df, resistance_df], axis=1)

        self.final_df["Baseline_ave", "Average"] = self.final_df["Baseline"].mean(
            axis=1
        )
        del self.final_df["Baseline"]

        columns_list = self.final_df.columns.levels[0].tolist()

        if "Spike_threshold (mV)" in columns_list:
            self.final_df[("Spike_threshold_ap", "first")] = (
                self.final_df["Spike_threshold (mV)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Spike_threshold (mV)"]

        if "Spike_threshold_time (ms)" in columns_list:
            self.final_df[("Spike_threshold_time_ap", "first")] = (
                self.final_df["Spike_threshold_time (ms)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Spike_threshold_time (ms)"]

        if "Hertz" in columns_list:
            self.final_df[("Pulse", "Rheo")] = (self.final_df["Hertz"] > 0).idxmax(
                axis=1, skipna=True
            )

        if "Spike_width" in columns_list:
            self.final_df[("Spike", "width")] = (
                self.final_df["Spike_width"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del self.final_df["Spike_width"]

        if "Spike_freq_adapt" in columns_list:
            self.final_df[("Spike", "Spike_freq_adapt")] = (
                self.final_df["Spike_freq_adapt"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Spike_freq_adapt"]

        if "Local_sfa" in columns_list:
            self.final_df[("Spike", "Local_sfa")] = (
                self.final_df["Local_sfa"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del self.final_df["Local_sfa"]

        if "Divisor_sfa" in columns_list:
            self.final_df[("Spike", "Divisor_sfa")] = (
                self.final_df["Divisor_sfa"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del self.final_df["Divisor_sfa"]

        if "Max_AP_vel" in columns_list:
            self.final_df[("Spike", "Max_AP_vel")] = (
                self.final_df["Max_AP_vel"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del self.final_df["Max_AP_vel"]

        if "Peak_AHP (mV)" in columns_list:
            self.final_df[("Spike", "Peak_AHP (mV)")] = (
                self.final_df["Peak_AHP (mV)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Peak_AHP (mV)"]

        if "Peak_AHP (ms)" in columns_list:
            self.final_df[("Spike", "Peak_AHP (ms)")] = (
                self.final_df["Peak_AHP (ms)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Peak_AHP (ms)"]

        if "Spike_peak_volt" in columns_list:
            self.final_df[("Spike", "Spike_peak_volt")] = (
                self.final_df["Spike_peak_volt"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del self.final_df["Spike_peak_volt"]

            self.final_df.pop("Delta_v")

    def create_first_ap_dfs(self):
        # Creating the final first action potentials and final data. It takes
        # manipulating to get the data to show up correctly in the TableWidget.
        pulse_dict, ramp_dict = self.create_first_aps()

        if pulse_dict:
            pulse_ap = self.first_ap_dict(pulse_dict)
        else:
            pulse_ap = {}

        if ramp_dict:
            ramp_ap = self.first_ap_dict(ramp_dict)
        else:
            ramp_ap = {}

        if pulse_ap:
            self.pulse_df = pd.DataFrame(
                dict([(k, pd.Series(v)) for k, v in pulse_ap.items()])
            )
        else:
            self.pulse_df = pd.DataFrame()

        if ramp_ap:
            self.ramp_df = pd.DataFrame(
                dict([(k, pd.Series(v)) for k, v in ramp_ap.items()])
            )
        else:
            self.ramp_df = pd.DataFrame()

    def create_first_aps(self):
        pulse_dict = defaultdict(lambda: defaultdict(list))
        ramp_dict = defaultdict(lambda: defaultdict(list))
        for i in self.acq_dict.keys():
            if len(self.acq_dict[i].first_ap) <= 1:
                pass
            else:
                if self.acq_dict[i].ramp == "0":
                    pulse_dict[self.acq_dict[i].epoch][
                        self.acq_dict[i].pulse_amp
                    ].append(self.acq_dict[i].first_ap)
                if self.acq_dict[i].ramp == "1":
                    ramp_dict[self.acq_dict[i].epoch][
                        self.acq_dict[i].pulse_amp
                    ].append(self.acq_dict[i].first_ap)
        return pulse_dict, ramp_dict

    def first_ap_dict(self, dictionary):
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

    def average_aps(self, dict_entry):
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

    def membrane_resistance(self, df):
        df1 = df[df[("Ramp", "")] == 0]
        if df1.empty == True:
            return df
        else:
            df2 = df1["Delta_v"].copy()
            df2.dropna(axis=0, how="all", inplace=True)
            index_1 = df2.index.values
            self.plot_epochs = df1["Epoch"].to_list()
            self.iv_y = df2.to_numpy()
            self.deltav_x = np.array(df2.T.index.map(int))
            self.iv_plot_x = self.deltav_x[self.iv_start - 1 : self.iv_end]
            x_constant = sm.add_constant(self.iv_plot_x)
            slope = []
            self.iv_line = []
            if len(self.iv_y) == 1:
                y = self.iv_y[0][self.iv_start - 1 : self.iv_end]
                model_1 = sm.OLS(y, x_constant)
                results_1 = model_1.fit()
                slope_1 = results_1.params
                slope += [slope_1[1] * 1000]
                self.iv_line += [slope_1[1] * self.iv_plot_x + slope_1[0]]
            else:
                for i in self.iv_y:
                    y = i[self.iv_start - 1 : self.iv_end]
                    model_1 = sm.OLS(y, x_constant)
                    results_1 = model_1.fit()
                    slope_1 = results_1.params
                    slope += [slope_1[1] * 1000]
                    self.iv_line += [slope_1[1] * self.iv_plot_x + slope_1[0]]
            resistance = pd.DataFrame(data=slope, index=index_1, columns=["I/V Curve"])
            resistance.columns = pd.MultiIndex.from_product(
                [resistance.columns, ["Resistance"]]
            )
            return resistance

    def iv_curve_dataframe(self):
        self.iv_df = pd.DataFrame(self.iv_line)
        self.iv_df = self.iv_df.transpose()
        self.iv_df.columns = self.plot_epochs
        self.iv_df["iv_plot_x"] = self.iv_plot_x

    def deltav_dataframe(self):
        self.deltav_df = pd.DataFrame(self.iv_y)
        self.deltav_df = self.deltav_df.transpose()
        self.deltav_df.columns = self.plot_epochs
        self.deltav_df["deltav_x"] = self.deltav_x

    def temp_df(self):
        temp_df = self.final_df.copy()
        mi = temp_df.columns
        ind = pd.Index([e[0] + "_" + str(e[1]) for e in mi.tolist()])
        temp_df.columns = ind
        return temp_df

    def save_data(self, save_filename):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="xlsxwriter"
        ) as writer:
            self.raw_df.to_excel(writer, index=False, sheet_name="Raw data")
            self.final_df.to_excel(writer, sheet_name="Final data")
            self.iv_df.to_excel(writer, sheet_name="IV_df")
            self.deltav_df.to_excel(writer, sheet_name="Deltav_df")
            if not self.pulse_df.empty:
                self.pulse_df.to_excel(writer, index=False, sheet_name="Pulse APs")
            if not self.ramp_df.empty:
                self.ramp_df.to_excel(writer, index=False, sheet_name="Ramp APs")
        return None
