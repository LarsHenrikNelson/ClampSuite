from pathlib import Path
from typing import Callable, List, NamedTuple, Type

from ..analysis.registry import AnalysisRegistry
from ..loader import ABFLoader, JSONLoader, ScanImageLoader


class ExpManager:
    def __init__(self):
        self.analysis_params = []
        self.analysis = {}
        self.prepocessing_params = []
        self.acquisitions = {}
        self.loader = None

    def set_callback(self, callback_func: Callable) -> None:
        self.callback_func = callback_func

    def load_acqs(
        self,
        file_path: list[Path],
    ) -> None:
        if isinstance(file_path, (str, Path)):
            file_path = list(file_path)
        file_path = [Path(i) for i in file_path]
        if self.loader is None:
            if file_path[0].suffix == ".mat":
                self.loader = ScanImageLoader(self.callback_func)
            elif file_path[0].suffix == ".json":
                self.loader = JSONLoader(self.callback_func)
            else:
                self.loader = ABFLoader(self.callback_func)
        self.acquisitions.update(self.loader.load_files(file_path))
        self.callback_func("Loaded acquisitions")

    def add_analyses(self, param_type: List[Type[NamedTuple]]):
        self.analysis_params.append(param_type)

    def add_prepocessor(self, param_type: List[Type[NamedTuple]]):
        self.prepocessing_params.extend(param_type)

    def run_analysis(self):
        for i in self.analysis_params:
            analysis_temp = {}
            acq_analysis, final_analysis = AnalysisRegistry.get_analyses(i)
            for key, value in self.acquisitions.items():
                value.add_preprocessor(self.prepocessing_params)
                analyzer = acq_analysis(value, **i.acquisition())
                analyzer.analyze()
                analysis_temp[key] = analyzer
            self.analysis[i.analysis_key()] = analysis_temp
