from typing import Union

import pandas as pd

from . import final_analysis


class FinalEvokedCurrent(final_analysis.FinalAnalysis, analysis="oepsc"):
    def analyze(
        self,
        o_acq_dict: Union[dict, None] = None,
        lfp_acq_dict: Union[dict, None] = None,
    ):
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
            raw_df = pd.merge(
                lfp_raw_df, o_raw_df, on=["Acq number", "Epoch"], suffixes=["", ""]
            )
        elif self.o_acq_dict is None and self.lfp_acq_dict is not None:
            raw_df = lfp_raw_df
        else:
            raw_df = o_raw_df
        raw_df["Epoch"] = pd.to_numeric(raw_df["Epoch"])
        self.df_dict["Raw data"] = raw_df

    def final_data(self):
        raw_df = self.df_dict["Raw data"]
        if self.lfp_acq_dict is not None and self.o_acq_dict is not None:
            final_df = raw_df.groupby(["Epoch", "Peak direction"]).mean(
                numeric_only=True
            )
            final_df.reset_index(inplace=True)
        elif self.o_acq_dict is not None and self.lfp_acq_dict is None:
            final_df = raw_df.groupby(["Epoch", "Peak direction"]).mean(
                numeric_only=True
            )
            final_df.reset_index(inplace=True)
        else:
            final_df = raw_df.groupby(["Epoch"]).mean(numeric_only=True)
            final_df.reset_index(inplace=True)
        self.df_dict["Final data"] = final_df

    def save_data(self, save_filename: str):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="openpyxl"
        ) as writer:
            for key, df in self.df_dict.items():
                df.to_excel(writer, index=False, sheet_name=key)

    def load_data(self, file_path: str):
        self.df_dict = pd.read_excel(file_path, sheet_name=None)
