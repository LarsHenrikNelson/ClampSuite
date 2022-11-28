from collections import OrderedDict
from pathlib import PurePath, Path
from typing import Callable, Union

import yaml

from ..functions.load_functions import load_acq, load_file, save_acq
from ..final_analysis import FinalAnalysis


class ExpManager:
    def __init__(self):
        self.exp_dict = {}
        self.final_analysis = None
        self.ui_prefs = None
        self.analysis_prefs = {}
        self.num_of_acqs = 0
        self.callback_func = print
        self.deleted_acqs = {}
        self.acqs_deleted = 0
        self.start_acq = None
        self.end_acq = None

    def create_exp(
        self, analysis: Union[str, None], file: Union[list, tuple, str, Path, PurePath]
    ):
        self._load_acqs(analysis, file)
        self._set_start_end_acq()

    def analyze_exp(self, exp: str, **kwargs):
        if self.exp_dict.get(exp):
            acq_dict = self.exp_dict[exp]
            self.analysis_prefs = kwargs
            total = len(acq_dict)
            for count, i in enumerate(acq_dict.values()):
                i.analyze(**kwargs)
                self.callback_func(int((100 * (count + 1) / total)))
            self.callback_func(f"Analyed {exp} acquisitions")

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
        if self.ui_pref is not None:
            for key, data in self.deleted_acqs.items():
                self.ui_prefs[f"Deleted acqs"] = {key: list(data.keys())}
            self.save_ui_pref(save_filename, self.ui_pref)
        if self.final_analysis is not None:
            self.save_final_analysis(save_filename)
        self.save_acqs(save_filename)
        self.callback_func("Finished saving")

    def save_acqs(self, save_filename: Union[PurePath, Path, str]):
        self.callback_func("Saving acquisitions")
        count = 0
        for i in self.exp_dict.keys():
            count += len(self.exp_dict[i].keys())
        for i in self.deleted_acqs.keys():
            count += len(self.deleted_acqs.keys())
        saved = 0
        for i in self.exp_dict.values():
            for acq in i.values():
                save_acq(acq, save_filename)
                saved += 1
                self.callback_func(int((100 * (saved) / count)))
        for i in self.deleted_acqs.values():
            for acq in i.values():
                save_acq(acq, save_filename)
                saved += 1
                self.callback_func(int((100 * (saved) / count)))
        self.callback_func("Saved acqs")

    def save_ui_pref(self, save_filename: Union[PurePath, Path, str], ui_prefs):
        self.callback_func("Saving preferences")
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(ui_prefs, file)
        self.callback_func("Saved preferences")

    def save_analysis_pref(self, save_filename: Union[PurePath, Path, str]):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(self.analysis_prefs, file)
        self.callback_func("Saved user preferences")

    def save_final_analysis(self, save_filename: Union[PurePath, Path, str]):
        self.callback_func("Saving final analysis")
        self.final_analysis.save_data(save_filename)
        self.callback_func("Saved final analysis")

    def load_ui_pref(self, file_path: Union[None, str, Path, PurePath] = None) -> dict:
        file_name = load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            ui_prefs = yaml.safe_load(file)
            return ui_prefs

    def load_analysis_pref(
        self, file_path: Union[None, str, Path, PurePath] = None
    ) -> dict:
        file_name = load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            analysis_prefs = yaml.safe_load(file)
        return analysis_prefs

    def load_final_analysis(self, analysis: str, file_path: Union[None, str] = None):
        file_name = load_file(file_path, extension=".xlsx")
        self.final_analysis = FinalAnalysis(analysis)
        self.final_analysis.load_data(file_name)

    def load_exp(
        self, analysis: str, file_path: Union[str, list, tuple, PurePath, Path]
    ):
        if isinstance(file_path, (str, PurePath)):
            temp_path = Path(file_path)
            if temp_path.is_dir():
                file_paths = list(temp_path.glob("*.*"))
        elif isinstance(file_path, Path):
            if file_path.is_dir():
                file_paths = list(file_path.glob("*.*"))
        else:
            file_paths = [PurePath(i) for i in file_path]
        file_paths_edit = [i for i in file_paths if i.name[0] != "."]
        for path in file_paths_edit:
            if path.suffix == ".yaml":
                self.ui_pref = self.load_ui_pref(path)
                can_load_data = True
                self.callback_func("Loaded settings")
            elif path.suffix == ".xlsx":
                self.load_final_analysis(analysis, path)
                self.callback_func("Loaded final data")
        if can_load_data:
            self._load_acqs(analysis=None, file_path=file_paths_edit)
            self._set_start_end_acq()
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

    def _set_start_end_acq(self):
        start_acq = []
        end_acq = []
        for i in self.exp_dict.values():
            temp = list(i.keys())
            start_acq.append(min(temp))
            end_acq.append(max(temp))
        self.start_acq = min(start_acq)
        self.end_acq = max(end_acq)

    def _set_deleted_acqs(self):
        for exp in self.exp_dict:
            acqs = self.ui_prefs[f"Deleted acqs"][exp]
            for acq in acqs:
                self.delete_acq(exp, acq)

    def set_callback(self, func: Callable[[int, str], None]):
        self.callback_func = func

    def get_acqs(self, exp: str) -> list:
        return [i.name for i in self.exp_dict[exp].values()]

    def delete_acq(self, exp: str, acq: int):
        item = self.exp_dict[exp].pop(acq)
        if exp in self.deleted_acqs:
            self.deleted_acqs[exp][acq] = item
        else:
            self.deleted_acqs[exp] = OrderedDict()
            self.deleted_acqs[exp][acq] = item
        self.acqs_deleted += 1

    def reset_deleted_acqs(self, exp: str):
        if self.deleted_acqs[exp]:
            del_dict = dict(self.deleted_acqs)[exp]
            self.exp_dict[exp].update(del_dict)
            self.deleted_acqs = {}
            self.acqs_deleted = 0

    def reset_recent_deleted_acq(self, exp: str):
        if self.deleted_acqs[exp]:
            item = self.deleted_acqs[exp].popitem()
            self.exp_dict[exp][item[0]] = item[1]
            self.acqs_deleted -= 1

    def acqs_exist(self) -> bool:
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

    def get_final_analysis_data(self) -> dict:
        if self.final_analysis is not None:
            return self.final_analysis.df_dict
        else:
            return {}
