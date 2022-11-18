from collections import OrderedDict
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
        self.deleted_acqs = {}

    def create_exp(
        self, analysis: Union[str, None], file: Union[list, tuple, str, Path, PurePath]
    ):
        self._load_acqs(analysis, file)

    def analyze_exp(self, exp: str, **kwargs):
        total = 0
        acq_dict = self.exp_dict[exp]
        self.analysis_prefs = kwargs
        for i in self.exp_dict:
            total += len(i)
        for count, i in enumerate(acq_dict.values()):
            i.analyze(**kwargs)
            self.callback_func(int((100 * (count + 1) / total)))
        self.callback_func("Loaded acquisitions")

    def set_ui_pref(self, pref_dict: dict):
        self.ui_prefs = pref_dict

    def run_final_analysis(self, **kwargs):
        analysis = list(self.exp_dict.keys())
        if len(analysis) == 1:
            self.final_analysis = FinalAnalysis(analysis[0])
            self.final_analysis.analyze(self.exp_dict[analysis[0]], **kwargs)
        else:
            self.final_analysis = FinalAnalysis("oepsc")
            lfp = self.exp_dict.get("lfp")
            oepsc = self.exp_dict.get("oepsc")
            self.final_analysis.analyze(o_acq_dict=oepsc, lfp_acq_dict=lfp)

    def save_data(self, save_filename: Union[Path, PurePath, str]):
        self.save_ui_pref(save_filename)
        if self.final_analysis is not None:
            self.save_final_analysis(save_filename)
        self.save_acqs(save_filename)
        self.callback_func("Finished saving")

    def save_acqs(self, save_filename: Union[PurePath, str]):
        count = 0
        for i in self.exp_dict.keys():
            count += len(self.exp_dict[i].keys())
        for i in self.deleted_acqs.keys():
            count += len(self.deleted_acqs.keys())
        for i in self.exp_dict.values():
            for i, acq in enumerate(i.values()):
                save_acq(acq, save_filename)
                self.callback_func(int((100 * (i + 1) / count)))
        self.callback_func("Saved acqs")

    def save_ui_pref(self, save_filename: Union[PurePath, str]):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(self.ui_prefs, file)
        self.callback_func("Saved preferences")

    def save_analysis_pref(self, save_filename: Union[PurePath, str]):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(self.analysis_prefs, file)

    def save_final_analysis(self, save_filename: Union[PurePath, str]):
        self.final_analysis.save_data(save_filename)
        self.callback_func("Saved final analysis")

    def load_ui_pref(self, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            self.ui_prefs = yaml.safe_load(file)

    def load_analysis_pref(self, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            self.analysis_prefs = yaml.safe_load(file)

    def load_final_analysis(self, analysis: str, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".xlsx")
        self.final_analysis = FinalAnalysis(analysis)
        self.final_analysis.load_data(file_name)

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
                self.callback_func("Loaded settings")

            elif i.suffix == ".xlsx":
                xlsx_file = file_paths.pop(index)
                self.load_final_analysis(analysis, xlsx_file)
                self.callback_func("Loaded final data")
        if can_load_data:
            self._load_acqs(analysis=None, file_path=file_paths)
            self._set_deleted_acqs()
        else:
            self.callback_func("No YAML file, cannot load data!")

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
            self._set_acq(acq)
            self.callback_func(int((100 * (count + 1) / self.num_of_acqs)))
        self.callback_func("Loaded acquisitions")

    def _set_acq(self, acq):
        if acq is None:
            pass
        elif acq.analysis in self.exp_dict:
            self.exp_dict[acq.analysis][int(acq.acq_number)] = acq
        else:
            self.exp_dict[acq.analysis] = {}
            self.exp_dict[acq.analysis][int(acq.acq_number)] = acq

    def _set_deleted_acqs(self):
        for i in self.exp_dict:
            for j in i.values():
                if j.name in self.ui_prefs["Deleted Acqs"]:
                    self.deleted_acqs[j.analysis][int(j.acq_number)] = self.exp_dict[
                        j.analysis
                    ].pop(int(j.acq_number))

    def set_callback(self, func):
        self.callback_func = func

    def get_acqs(self, exp):
        return [i.name for i in self.exp_dict[exp].values()]

    def delete_acq(self, exp, acq):
        item = self.exp_dict[exp].pop(acq)
        if exp in self.deleted_acqs:
            self.deleted_acqs[exp][acq] = item
        else:
            self.deleted_acqs[exp] = OrderedDict()
            self.deleted_acqs[exp][acq] = item

    def reset_deleted_acqs(self, exp):
        del_dict = dict(self.deleted_acqs)
        self.exp_dict[exp].update(del_dict)
        self.deleted_acqs = {}

    def reset_recent_deleted_acq(self, exp):
        item = self.deleted_acqs[exp].popitem()
        self.exp_dict[exp][item[0]] = item[1]
        return item(0)

    def acqs_exist(self):
        if self.exp_dict:
            return True
        else:
            return False

    def num_of_del_acqs(self):
        del_acqs = 0
        for i in self.exp_dict.values():
            del_acqs += len(i)
        return i

    def set_current_acq(self):
        return self.ui_prefs["Acq_number"]

    def get_final_analysis_data(self):
        if self.final_analysis is not None:
            return self.final_analysis.df_dict
        else:
            return None
