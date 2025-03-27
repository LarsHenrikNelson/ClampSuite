import json
import typing
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Callable, Literal, Union

import yaml
import numpy as np

from ..final_analysis import FinalAnalysis
from ..functions.filtering_functions import Filters, Windows
from ..functions.load_functions import NumpyEncoder
from ..loader import JSONLoader, ScanImageLoader, NeoLoader
from ..acq import Acquisition


class ExpManager:
    filters = list(typing.get_args(Filters))
    windows = list(typing.get_args(Windows))

    def __init__(self) -> None:
        self.acquisitions = {}
        self.final_analysis = None
        self.ui_prefs = None
        self.analysis_prefs = {}
        self.num_of_acqs = 0
        self.callback_func = print
        self.deleted_acqs = OrderedDict()
        self.acqs_deleted = 0
        self.start_acq = None
        self.end_acq = None
        self.analyzed = False
        self.loader = None

    def create_exp(
        self,
        analysis: Literal["mini", "current_clamp", "lfp", "oepsc", "filter"],
        file: Union[list, tuple, str, Path, PurePath],
    ) -> None:
        self._load_acqs(analysis, file)
        self._set_start_end_acq()

    def analyze_exp(
        self, filter_args=None, template_args=None, analysis_args=None
    ) -> None:
        acq_dict = self.acquisitions
        pref_dict = {}
        if filter_args is not None:
            pref_dict.update(filter_args)
        if template_args is not None:
            pref_dict.update(template_args)
        pref_dict.update(analysis_args)
        self.analysis_prefs = pref_dict
        for i in acq_dict.values():
            if filter_args is not None:
                i.set_filter(**filter_args)
            if template_args is not None:
                i.set_template(**template_args)
            i.analyze(**analysis_args)
            self.callback_func(f"Acquisition {i.acq_number} analyzed")
        self.analyzed = True
        self.callback_func("Analyzed acquisitions")

    def set_ui_prefs(self, pref_dict: dict) -> None:
        self.ui_prefs = pref_dict
        self.ui_prefs["Deleted acqs"] = {}

    def run_final_analysis(self, analysis, **kwargs) -> None:
        self.final_analysis = FinalAnalysis(analysis)
        self.final_analysis.analyze(self.acquisitions, **kwargs)

    def save_data(self, file_path: Union[Path, PurePath, str]) -> None:
        file_path = Path(file_path)
        file_path.mkdir()
        file_path = file_path / file_path.parts[-1]
        if self.ui_prefs is not None:
            for key, data in self.deleted_acqs.items():
                self.ui_prefs["Deleted acqs"] = {key: list(data.keys())}
            self.save_ui_prefs(file_path, self.ui_prefs)
        if self.final_analysis is not None:
            self.save_final_analysis(file_path)
        self._save_acqs(file_path)
        self.callback_func("Finished saving")

    @staticmethod
    def save_acq(acq, save_filename) -> None:
        x = deepcopy(acq)
        if x.analysis == "mini":
            x.save_postsynaptic_events()
        with open(f"{save_filename}_{x.name}.json", "w") as write_file:
            json.dump(x.__dict__, write_file, cls=NumpyEncoder)

    @staticmethod
    def save_acqs(acq_dict, file_path: Union[PurePath, Path, str]) -> None:
        for i in acq_dict.values():
            ExpManager.save_acq(i, file_path)
        print("Finished saving")

    def _save_acqs(self, file_path: Union[PurePath, Path, str]) -> None:
        self.callback_func("Saving acquisitions")
        count = 0
        count += len(self.acquisitions)
        count += len(self.deleted_acqs)
        saved = 0
        for acq in self.acquisitions.values():
            self.save_acq(acq, file_path)
            saved += 1
            self.callback_func(f"Saved acquisition {acq.acq_number}")
        for acq in self.deleted_acqs.values():
            self.save_acq(acq, file_path)
            saved += 1
            self.callback_func(f"Saved acquisition {acq.acq_number}")
        self.callback_func("Saved acqs")

    def save_ui_prefs(self, file_path: Union[PurePath, Path, str], ui_prefs) -> None:
        self.callback_func("Saving preferences")
        with open(f"{file_path}.yaml", "w") as file:
            yaml.dump(ui_prefs, file)
        self.callback_func("Saved preferences")

    def save_analysis_prefs(self, file_path: Union[PurePath, Path, str]) -> None:
        with open(f"{file_path}.yaml", "w") as file:
            yaml.dump(self.analysis_prefs, file)
        self.callback_func("Saved user preferences")

    def save_final_analysis(self, file_path: Union[PurePath, Path, str]) -> None:
        self.callback_func("Saving final analysis")
        self.final_analysis.save_data(file_path)
        self.callback_func("Saved final analysis")

    def load_file(self, file_path: str, extension: str) -> Union[list, PurePath]:
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
        file_paths_edit = [
            i for i in file_paths if (i.suffix == ".json") & (i.name[0] != ".")
        ]
        for path in file_paths:
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
    ) -> None:
        if isinstance(file_path, (str, Path, PurePath)):
            file_path = list(file_path)
        file_path = [Path(i) for i in file_path]
        if self.loader is None:
            if file_path[0].suffix == ".mat":
                self.loader = ScanImageLoader(analysis, self.callback_func)
            elif file_path[0].suffix == ".json":
                self.loader = JSONLoader(analysis, self.callback_func)
            else:
                self.loader = NeoLoader(analysis, self.callback_func)
        acquisitions = self.loader.load_files(file_path)
        self._create_acquisitions(acquisitions, analysis)
        self.callback_func("Loaded acquisitions")

    def _create_acquisitions(self, acquisitions: dict, analysis: str):
        for vals in acquisitions.values():
            obj = Acquisition(analysis)
            obj.load_data(vals)
            self.acquisitions[int(obj.acq_number)] = obj

    def _set_start_end_acq(self) -> None:
        self.start_acq = min(self.acquisitions.keys())
        self.end_acq = max(self.acquisitions.keys())

    def _set_deleted_acqs(self) -> None:
        for acq, value in self.acquisitions.items():
            deleted_acqs = []
            if not value.accepted:
                deleted_acqs.append(acq)
        for i in deleted_acqs:
            self.delete_acq(i)

    def set_callback(self, func: Callable[[int, str], None]):
        self.callback_func = func

    def get_acqs(self) -> list:
        return [i.name for i in self.acquisitions.values()]

    def delete_acq(self, acq: int) -> None:
        item = self.acquisitions.pop(acq)
        item.delete()
        self.deleted_acqs[acq] = item
        self.acqs_deleted += 1

    def reset_deleted_acqs(self) -> int:
        if self.deleted_acqs:
            del_dict = self.deleted_acqs
            for i in del_dict.values():
                i.accept()
            self.acquisitions.update(del_dict)
            self.acqs_deleted = 0
            return 1
        else:
            return 0

    def reset_recent_deleted_acq(self):
        if self.deleted_acqs:
            item = self.deleted_acqs.popitem()
            item[1].accept()
            self.acquisitions[item[0]] = item[1]
            self.acqs_deleted -= 1
            return item[0]
        else:
            return 0

    def acqs_exist(self, exp) -> bool:
        if len(self.acquisitions) > 0:
            return True
        else:
            return False

    def acq_exists(self, acq_num) -> bool:
        return acq_num in self.acquisitions

    def num_of_del_acqs(self) -> int:
        return len(self.deleted_acqs)

    def set_current_acq(self) -> int:
        if self.ui_prefs is not None:
            return self.ui_prefs["Acq_number"]
        else:
            raise AttributeError("UI prefs do not exist")

    def get_final_analysis_data(self) -> dict:
        if self.final_analysis is not None:
            return self.final_analysis.df_dict
        else:
            return {}
