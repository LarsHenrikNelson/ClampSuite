import json
import typing
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Callable, Literal, Union

import yaml

from ..acq import Acquisition
from ..final_analysis import FinalAnalysis
from ..functions.filtering_functions import Filters, Windows
from ..functions.load_functions import NumpyEncoder, load_json_file, load_scanimage_file


class ExpManager:
    filters = list(typing.get_args(Filters))
    windows = list(typing.get_args(Windows))

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
        self.analyzed = False

    def create_exp(
        self, analysis: Union[str, None], file: Union[list, tuple, str, Path, PurePath]
    ):
        self._load_acqs(analysis, file)
        self._set_start_end_acq()

    def analyze_exp(
        self, exp: str, filter_args=None, template_args=None, analysis_args=None
    ):
        if self.exp_dict.get(exp):
            acq_dict = self.exp_dict[exp]
            pref_dict = {}
            if filter_args is not None:
                pref_dict.update(filter_args)
            if template_args is not None:
                pref_dict.update(template_args)
            pref_dict.update(analysis_args)
            self.analysis_prefs = pref_dict
            total = len(acq_dict)
            for count, i in enumerate(acq_dict.values()):
                if filter_args is not None:
                    i.set_filter(**filter_args)
                if template_args is not None:
                    i.set_template(**template_args)
                i.analyze(**analysis_args)
                self.callback_func(int((100 * (count + 1) / total)))
            self.analyzed = True
            self.callback_func(f"Analyed {exp} acquisitions")

    def set_ui_prefs(self, pref_dict: dict):
        self.ui_prefs = pref_dict
        self.ui_prefs["Deleted acqs"] = {}

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

    def save_data(self, file_path: Union[Path, PurePath, str]):
        if self.ui_prefs is not None:
            for key, data in self.deleted_acqs.items():
                self.ui_prefs["Deleted acqs"] = {key: list(data.keys())}
            self.save_ui_prefs(file_path, self.ui_prefs)
        if self.final_analysis is not None:
            self.save_final_analysis(file_path)
        self._save_acqs(file_path)
        self.callback_func("Finished saving")

    @staticmethod
    def save_acq(acq, save_filename):
        x = deepcopy(acq)
        if x.analysis == "mini":
            x.save_postsynaptic_events()
        with open(f"{save_filename}_{x.name}.json", "w") as write_file:
            json.dump(x.__dict__, write_file, cls=NumpyEncoder)

    @staticmethod
    def save_acqs(acq_dict, file_path: Union[PurePath, Path, str]):
        for i in acq_dict.values():
            ExpManager.save_acq(i, file_path)
        print("Finished saving")

    def _save_acqs(self, file_path: Union[PurePath, Path, str]):
        self.callback_func("Saving acquisitions")
        count = 0
        for i in self.exp_dict.keys():
            count += len(self.exp_dict[i].keys())
        for i in self.deleted_acqs.keys():
            count += len(self.deleted_acqs.keys())
        saved = 0
        for i in self.exp_dict.values():
            for acq in i.values():
                self.save_acq(acq, file_path)
                saved += 1
                self.callback_func(int((100 * (saved) / count)))
        for i in self.deleted_acqs.values():
            for acq in i.values():
                self.save_acq(acq, file_path)
                saved += 1
                self.callback_func(int((100 * (saved) / count)))
        self.callback_func("Saved acqs")

    def save_ui_prefs(self, file_path: Union[PurePath, Path, str], ui_prefs):
        self.callback_func("Saving preferences")
        with open(f"{file_path}.yaml", "w") as file:
            yaml.dump(ui_prefs, file)
        self.callback_func("Saved preferences")

    def save_analysis_prefs(self, file_path: Union[PurePath, Path, str]):
        with open(f"{file_path}.yaml", "w") as file:
            yaml.dump(self.analysis_prefs, file)
        self.callback_func("Saved user preferences")

    def save_final_analysis(self, file_path: Union[PurePath, Path, str]):
        self.callback_func("Saving final analysis")
        self.final_analysis.save_data(file_path)
        self.callback_func("Saved final analysis")

    def load_file(self, file_path: str, extension: str):
        file_path = PurePath(file_path)
        if file_path is None:
            p = Path()
            file_name = list(p.glob(f"*{extension}"))[0]
        elif file_path.suffix == extension:
            file_name = file_path
        else:
            directory = Path(file_path)
            file_name = list(directory.glob(extension))[0]
        return file_name

    def load_ui_prefs(self, file_path: Union[None, str, Path, PurePath] = None) -> dict:
        file_name = self.load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            ui_prefs = yaml.safe_load(file)
            return ui_prefs

    def load_analysis_prefs(
        self, file_path: Union[None, str, Path, PurePath] = None
    ) -> dict:
        file_name = self.load_file(file_path, extension=".yaml")
        with open(file_name, "r") as file:
            analysis_prefs = yaml.safe_load(file)
        return analysis_prefs

    def load_final_analysis(self, analysis: str, file_path: Union[None, str] = None):
        file_name = self.load_file(file_path, extension=".xlsx")
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
                self.ui_prefs = self.load_ui_prefs(path)
                can_load_data = True
                self.analyzed = True
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
        num_of_acqs = len(file_path)
        for count, i in enumerate(file_path):
            if not Path(i).exists():
                raise AttributeError("File path does not exist")
            acq = self.load_acq(analysis, i)
            self._set_acq(acq)
            self.callback_func(int((100 * (count + 1) / num_of_acqs)))
        self.callback_func("Loaded acquisitions")

    @staticmethod
    def load_acq(
        analysis: Union[Literal["mini", "current_clamp", "lfp", "oepsc"], None],
        path: Union[str, Path, PurePath],
    ) -> Acquisition:
        path_obj = PurePath(path)
        if not Path(path_obj).exists():
            return None
        if path_obj.suffix == ".mat":
            acq_comp = load_scanimage_file(path_obj)
        elif path_obj.suffix == ".json":
            acq_comp = load_json_file(path_obj)
        else:
            print("File type not recognized!")
            return None
        if acq_comp.get("analysis"):
            obj = Acquisition(acq_comp.analysis)
        elif isinstance(analysis, str):
            obj = Acquisition(analysis)
        else:
            print("No analysis specified!")
            return None
        obj.load_data(acq_comp)
        return obj

    @staticmethod
    def load_acqs(
        analysis: Union[str, None],
        file_path: Union[list, tuple, str, Path, PurePath],
    ):
        acq_dict = {}
        if isinstance(file_path, (str, Path, PurePath)):
            file_path = list(file_path)
        for i in file_path:
            acq = ExpManager.load_acq(analysis, i)
            if acq is not None:
                acq_dict[int(acq.acq_number)] = acq
        return acq_dict

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
            if len(temp) > 0:
                start_acq.append(min(temp))
                end_acq.append(max(temp))
        self.start_acq = min(start_acq)
        self.end_acq = max(end_acq)

    def _set_deleted_acqs(self):
        for exp in self.exp_dict:
            acqs = self.ui_prefs["Deleted acqs"].get(exp)
            if acqs:
                for acq in acqs:
                    self.delete_acq(exp, acq)

    def set_callback(self, func: Callable[[int, str], None]):
        self.callback_func = func

    def get_acqs(self, exp: str) -> list:
        return [i.name for i in self.exp_dict[exp].values()]

    def delete_acq(self, exp: str, acq: int):
        item = self.exp_dict[exp].pop(acq)
        if exp in self.deleted_acqs:
            item.delete()
            self.deleted_acqs[exp][acq] = item
        else:
            self.deleted_acqs[exp] = OrderedDict()
            self.deleted_acqs[exp][acq] = item
        self.acqs_deleted += 1

    def reset_deleted_acqs(self, exp: str):
        if self.deleted_acqs[exp]:
            del_dict = dict(self.deleted_acqs)[exp]
            for i in del_dict.values():
                i.accept()
            self.exp_dict[exp].update(del_dict)
            self.deleted_acqs = {}
            self.acqs_deleted = 0
            return 1
        else:
            return 0

    def reset_recent_deleted_acq(self, exp: str):
        if self.deleted_acqs[exp]:
            item = self.deleted_acqs[exp].popitem()
            item.accept()
            self.exp_dict[exp][item[0]] = item[1]
            self.acqs_deleted -= 1
            return item[0]
        else:
            return 0

    def acqs_exist(self, exp) -> bool:
        return self.exp_dict.get(exp)

    def num_of_del_acqs(self):
        del_acqs = 0
        for i in self.deleted_acqs.values():
            del_acqs += len(i)
        return i

    def set_current_acq(self):
        return self.ui_prefs["Acq_number"]

    def get_final_analysis_data(self) -> dict:
        if self.final_analysis is not None:
            return self.final_analysis.df_dict
        else:
            return {}
