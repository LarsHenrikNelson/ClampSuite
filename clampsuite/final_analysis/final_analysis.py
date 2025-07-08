import datetime

import pandas as pd

import clampsuite


class FinalAnalysis:
    def save_data(self, save_filename: str):
        """
        This function saves the resulting pandas data frames to an excel file.
        The function saves the data to the current directory so all that is
        needed is a name for the excel file.
        """
        program_data = {
            "Program": ["ClampSuite"],
            "Version": clampsuite.__version__,
            "Time stamp": [str(datetime.datetime.now())],
        }
        prog_data = pd.DataFrame(program_data, index=None)
        with pd.ExcelWriter(
            f"{save_filename}.xlsx", mode="w", engine="xlsxwriter"
        ) as writer:
            for key, value in self.df_dict.items():
                value.to_excel(writer, index=False, sheet_name=key)
            prog_data.to_excel(writer, index=False, sheet_name="Program data")

    def load_data(self):
        raise NotImplementedError

    def set_program_data(self, df):
        self.program_data = df.to_dict()
