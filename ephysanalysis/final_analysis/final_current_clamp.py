from collections import defaultdict

import numpy as np
import pandas as pd
import statsmodels.api as sm


class FinalCurrentClampAnalysis:
    def __init__(self, acq_dict, iv_start=1, iv_end=6):
        self.acq_dict = acq_dict
        self.iv_start = iv_start
        self.iv_end = iv_end
        self.df_dict = {}
        self.hertz = False
        self.pulse_ap = False
        self.ramp_ap = False
        self.analyze()

    def analyze(self):
        self.create_raw_data()
        self.average_data()
        self.final_data()
        self.iv_curve_dataframe()
        self.deltav_dataframe()
        self.create_first_ap_dfs()

    def create_raw_data(self):
        raw_df = pd.DataFrame(
            [self.acq_dict[i].create_dict() for i in self.acq_dict.keys()]
        )
        raw_df["Epoch"] = pd.to_numeric(raw_df["Epoch"])
        raw_df["Pulse_pattern"] = pd.to_numeric(raw_df["Pulse_pattern"])
        raw_df["Pulse_amp"] = pd.to_numeric(raw_df["Pulse_amp"])
        self.df_dict["Raw data"] = raw_df

    def average_data(self):
        # I need to separate the delta v and spike ieis from the rest of the
        # dataframe to clean it up.
        df_averaged_data = (
            self.df_dict["Raw data"]
            .groupby(["Pulse_pattern", "Epoch", "Pulse_amp", "Ramp"])
            .mean()
        )
        df_averaged_data.reset_index(inplace=True)
        df_averaged_data.drop(["Pulse_pattern", "Pulse_start"], axis=1, inplace=True)
        df_averaged_data[["Pulse_amp", "Ramp", "Epoch"]] = df_averaged_data[
            ["Pulse_amp", "Ramp", "Epoch"]
        ].astype(int)
        self.df_dict["Averaged data"] = df_averaged_data

    def final_data(self):
        # Pivot the dataframe to get it into wideform format
        pivoted_df = self.df_dict["Averaged data"].pivot_table(
            index=["Epoch", "Ramp"], columns=["Pulse_amp"], aggfunc=np.nanmean
        )

        pivoted_df.reset_index(inplace=True)

        # Add the input resistance calculate
        resistance_df = self.membrane_resistance(pivoted_df)
        final_df = pd.concat([pivoted_df, resistance_df], axis=1)

        final_df["Baseline_ave", "Average"] = final_df["Baseline"].mean(axis=1)
        del final_df["Baseline"]

        final_df["Baseline_stability_ave", "Average"] = final_df[
            "Baseline_stability"
        ].mean(axis=1)
        del final_df["Baseline_stability"]

        columns_list = final_df.columns.levels[0].tolist()

        if "Spike_threshold (mV)" in columns_list:
            final_df[("Spike_threshold_ap", "first")] = (
                final_df["Spike_threshold (mV)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del final_df["Spike_threshold (mV)"]

        if "Spike_threshold_time (ms)" in columns_list:
            final_df[("Spike_threshold_time_ap", "first")] = (
                final_df["Spike_threshold_time (ms)"]
                .replace(0, np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            del final_df["Spike_threshold_time (ms)"]

        if "Hertz" in columns_list:
            final_df[("Pulse", "Rheo")] = (final_df["Hertz"] > 0).idxmax(
                axis=1, skipna=True
            )
            hertz_df = final_df.pop("Hertz")
            epoch = final_df.loc[:, ("Epoch", "")].copy()
            hertz_df.insert(0, "Epoch", epoch)
            ramp = final_df.loc[:, ("Ramp", "")].copy()
            hertz_df.insert(0, "Ramp", ramp)
            hertz_df.T.reset_index(inplace=True)
            self.df_dict["Hertz"] = hertz_df
            self.hertz = True

        if "Spike_width" in columns_list:
            final_df[("Spike", "width")] = (
                final_df["Spike_width"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Spike_width"]

        if "Spike_freq_adapt" in columns_list:
            final_df[("Spike", "Spike_freq_adapt")] = (
                final_df["Spike_freq_adapt"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Spike_freq_adapt"]

        if "Local_sfa" in columns_list:
            final_df[("Spike", "Local_sfa")] = (
                final_df["Local_sfa"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Local_sfa"]

        if "Divisor_sfa" in columns_list:
            final_df[("Spike", "Divisor_sfa")] = (
                final_df["Divisor_sfa"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Divisor_sfa"]

        if "Max_AP_vel" in columns_list:
            final_df[("Spike", "Max_AP_vel")] = (
                final_df["Max_AP_vel"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Max_AP_vel"]

        if "Peak_AHP (mV)" in columns_list:
            final_df[("Spike", "Peak_AHP (mV)")] = (
                final_df["Peak_AHP (mV)"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Peak_AHP (mV)"]

        if "Peak_AHP (ms)" in columns_list:
            final_df[("Spike", "Peak_AHP (ms)")] = (
                final_df["Peak_AHP (ms)"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Peak_AHP (ms)"]

        if "Spike_peak_volt" in columns_list:
            final_df[("Spike", "Spike_peak_volt")] = (
                final_df["Spike_peak_volt"].replace(0, np.nan).bfill(axis=1).iloc[:, 0]
            )
            del final_df["Spike_peak_volt"]

        if "Spike_iei" in columns_list:
            iei_df = final_df.pop("Spike_iei").T.reset_index()
            self.df_dict["IEI"] = iei_df

        if "Spike_time (ms)" in columns_list:
            spike_time_df = final_df.pop("Spike_time (ms)").T.reset_index()
            self.df_dict["Spike time (ms)"] = spike_time_df

        final_df.pop("Delta_v")
        self.df_dict["Final data"] = final_df

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
        iv_df = pd.DataFrame(self.iv_line)
        iv_df = iv_df.transpose()
        iv_df.columns = self.plot_epochs
        iv_df["iv_plot_x"] = self.iv_plot_x
        self.df_dict["IV"] = iv_df

    def deltav_dataframe(self):
        deltav_df = pd.DataFrame(self.iv_y)
        deltav_df = deltav_df.transpose()
        deltav_df.columns = self.plot_epochs
        deltav_df["deltav_x"] = self.deltav_x
        self.df_dict["Delta V"] = deltav_df

    def temp_df(self):
        temp_df = self.df_dict["Final data"].copy()
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
            for key, value in df_dict.items():
                if i == "Final data":
                    value.to_excel(writer, sheet_name=key)
                else:
                    value.to_excel(writer, index=False, sheet_name=key)
            # self.raw_df.to_excel(writer, index=False, sheet_name="Raw data")
            # self.final_df.to_excel(writer, sheet_name="Final data")
            # self.iv_df.to_excel(writer, index=False, sheet_name="IV_df")
            # self.deltav_df.to_excel(writer, index=False, sheet_name="Deltav_df")
            # self.iei_df.to_excel(writer, index=False, sheet_names="Spike_iei")
            # if not self.pulse_ap_df.empty:
            #     self.pulse_ap_df.to_excel(writer, index=False, sheet_name="Pulse APs")
            # if not self.ramp_ap_df.empty:
            #     self.ramp_ap_df.to_excel(writer, index=False, sheet_name="Ramp APs")
