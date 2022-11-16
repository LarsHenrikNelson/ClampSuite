from glob import glob
from pathlib import PurePath, Path
from typing import Union

import yaml

from ..functions.load_functions import load_acqs
from ..final_analysis import FinalAnalysis


class ExpManager:
    def __init__(self):
        self.exp_dict = {}
        self.prefs_dict = {}
        self.final_analysis = None
        self.ui_prefs = {}

    def save_data(self, path, file_prefix=None):
        pass

    def create_exp(self, analysis: str, file: Union[list, tuple, str, Path, PurePath]):
        acq_dict = load_acqs(analysis, file)
        self.exp_dict[analysis] = acq_dict

    def analyze_exp(self, exp: str, **kwargs):
        acq_dict = self.exp_dict[exp]
        for i in acq_dict.values():
            i.analyze(**kwargs)

    def run_final_analysis(self, **kwargs):
        analysis = list(self.exp_dict.keys())
        final_analysis = FinalAnalysis(analysis)
        if len(analysis) == 1:
            final_analysis.analyze(self.exp_dict[analysis[0]], **kwargs)
        else:
            lfp = self.exp_dict.get("lfp")
            oepsc = self.exp_dict.get("oepsc")
            final_analysis.analyze(o_acq_dict=oepsc, lfp_acq_dict=lfp)

    def load_ui_pref(path=None):
        if path is None:
            file_name = glob("*.yaml")[0]
        elif PurePath(path).suffix == ".yaml":
            file_name = PurePath(path)
        else:
            directory = Path(path)
            file_name = list(directory.glob("*.yaml"))[0]
        with open(file_name, "r") as file:
            yaml_file = yaml.safe_load(file)
        return yaml_file

    def save_ui_pref(dictionary, save_filename):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(dictionary, file)
