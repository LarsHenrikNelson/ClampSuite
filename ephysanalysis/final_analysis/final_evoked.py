import numpy as np
import pandas as pd


class FinalEvokedCurrent:
    def __init__(self, o_acq_dict=None, lfp_acq_dict=None):
        self.o_acq_dict = o_acq_dict
        self.lfp_acq_dict = lfp_acq_dict
        self.raw_data()
        self.final_data()

    def raw_data(self):
        if self.o_acq_dict is not None:
            o_raw_df = pd.DataFrame(
                [self.o_acq_dict[i].create_dict() for i in self.o_acq_dict.keys()]
            )
        if self.lfp_acq_dict is not None:
            lfp_raw_df = pd.DataFrame(
                [self.lfp_acq_dict[i].create_dict() for i in self.lfp_acq_dict.keys()]
            )
        if self.lfp_acq_dict is not None and self.o_acq_dict is not None:
            self.raw_df = pd.merge(
                lfp_raw_df, o_raw_df, on=["Acq number", "Epoch"], suffixes=["", ""]
            )
        elif self.o_acq_dict is None and self.lfp_acq_dict is not None:
            self.raw_df = lfp_raw_df
        else:
            self.raw_df = o_raw_df
        self.raw_df["Epoch"] = pd.to_numeric(self.raw_df["Epoch"])

    def final_data(self):
        if self.lfp_acq_dict is not None and self.o_acq_dict is not None:
            self.final_df = self.raw_df.groupby(["Epoch", "Peak direction"]).mean()
            self.final_df.reset_index(inplace=True)
        elif self.o_acq_dict is not None and self.lfp_acq_dict is None:
            self.final_df = self.raw_df.groupby(["Epoch", "Peak direction"]).mean()
            self.final_df.reset_index(inplace=True)
        else:
            self.final_df = self.raw_df.groupby(["Epoch"]).mean()
            self.final_df.reset_index(inplace=True)

    def save_data(self, save_filename):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="openpyxl"
        ) as writer:
            self.raw_df.to_excel(writer, index=False, sheet_name="Raw data")
            self.final_df.to_excel(writer, index=False, sheet_name="Final data")
