from glob import glob
from pathlib import PurePath, Path
from typing import Union

import yaml

from ..functions.load_functions import load_acq, load_file, save_acq
from ..final_analysis import FinalAnalysis


class ExpManager:
    def __init__(self):
        self.exp_dict = {}
        self.prefs_dict = {}
        self.final_analysis = None
        self.ui_prefs = {}
        self.analysis_prefs = {}
        self.num_of_acqs = 0
        self.callback_func = print

    def save_data(self, save_filename: Union[Path, PurePath, str]):

        self.save_ui_pref(save_filename)
        if self.final_analysis is not None:
            self.save_final_analysis(save_filename)
        self.save_acqs(save_filename)

    def create_exp(
        self, analysis: Union[str, None], file: Union[list, tuple, str, Path, PurePath]
    ):
        self._load_acqs(analysis, file)

    def analyze_exp(self, exp: str, **kwargs):
        acq_dict = self.exp_dict[exp]
        self.analysis_prefs = kwargs
        for i in acq_dict.values():
            i.analyze(**kwargs)

    def run_final_analysis(self, **kwargs):
        analysis = list(self.exp_dict.keys())
        if len(analysis) == 1:
            final_analysis = FinalAnalysis(analysis)
            final_analysis.analyze(self.exp_dict[analysis[0]], **kwargs)
        else:
            final_analysis = FinalAnalysis("oepsc")
            lfp = self.exp_dict.get("lfp")
            oepsc = self.exp_dict.get("oepsc")
            final_analysis.analyze(o_acq_dict=oepsc, lfp_acq_dict=lfp)

    def load_ui_pref(self, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            self.ui_prefs = yaml.safe_load(file)

    def save_ui_pref(self, save_filename: Union[PurePath, str]):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(self.ui_prefs, file)

    def load_final_analysis(self, analysis: str, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".xlsx")
        self.final_analysis = FinalAnalysis(analysis)
        self.final_analysis.load_data(file_name)

    def save_final_analysis(self, save_filename: Union[PurePath, str]):
        self.final_analysis(save_filename)

    def save_acqs(self, save_filename: Union[PurePath, str]):
        for i in self.exp_dict.values():
            for i, acq in enumerate(i.values()):
                save_acq(acq, save_filename)
                self.callback_func(int((100 * (i + 1) / self.num_of_acqs)))
        self.callback_func("Saved")

    def _load_data(self, analysis: str, file_path: Union[str, list, tuple]):
        if isinstance(file_path, str):
            temp_path = Path(file_path)
            if temp_path.is_dir():
                file_paths = list(temp_path.glob("*.*"))
        else:
            file_paths = [PurePath(i) for i in file_path]
        file_paths = [i for i in file_paths if i.name[0] != "."]
        for index, i in enumerate(file_paths):
            if i.suffix == ".yaml":
                yaml_file = file_paths.pop(index)
                self.load_ui_pref(yaml_file)
                can_load_data = True
            elif i.suffix == ".xlsx":
                xlsx_file = file_paths.pop(index)
                self.load_final_analysis(analysis, xlsx_file)
        if can_load_data:
            self._load_acqs(analysis=None, file_path=file_paths)
        else:
            print("No YAML file, cannot load data!")

    def _load_acqs(
        self,
        analysis: Union[str, None],
        file_path: Union[list, tuple, str, Path, PurePath],
    ):
        if isinstance(file_path, (str, Path, PurePath)):
            file_path = list(file_path)
        self.num_of_acqs += len(file_path)
        for count, i in enumerate(file_path):
            acq = load_acq(analysis, i)
            if acq is None:
                pass
            elif acq.analysis in self.exp_dict:
                self.exp_dict[acq.analysis][int(acq.acq_number)] = acq
                self.callback_func(int((100 * (count + 1) / self.num_of_acqs)))
            else:
                self.exp_dict[acq.analysis] = {}
                self.exp_dict[acq.analysis][int(acq.acq_number)] = acq
                self.callback_func(int((100 * (count + 1) / self.num_of_acqs)))
        self.callback_func("Loaded acqs")

    def set_callback(self, func):
        self.callback_func = func
