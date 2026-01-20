from pathlib import Path
from typing import Callable, List, NamedTuple, Type

from ..analysis.registry import AnalysisRegistry
from ..loader import ABFLoader, JSONLoader, ScanImageLoader, AcquisitionData
from ..preprocess.base import Preprocessor


class ExpManager:
    def __init__(self):
        self.analysis_config: list = []
        self.analysis: dict = {}
        self.prepocessing_params: list = []
        self.epochs: dict[int, dict[int, AcquisitionData]] = {}
        self.loader = None
        self.callback_func: Callable = print

    def set_callback(self, callback_func: Callable) -> None:
        self.callback_func = callback_func

    def load_acqs(
        self,
        file_path: list[Path] | str | Path,
    ) -> None:
        if isinstance(file_path, (str, Path)):
            paths = [file_path]
        else:
            paths = file_path
        paths = [Path(i) for i in paths]
        if self.loader is None:
            if paths[0].suffix == ".mat":
                self.loader = ScanImageLoader(self.callback_func)
            elif paths[0].suffix == ".json":
                self.loader = JSONLoader(self.callback_func)
            elif paths[0].suffix == ".abf":
                self.loader = ABFLoader(self.callback_func)
            else:
                raise ValueError("File type not supported")
        self.epochs.update(self.loader.load_files(paths))
        self.callback_func("Loaded acquisitions")

    def add_analyses(self, param_type: List[Type[NamedTuple]]):
        self.analysis_config.extend(param_type)

    def add_prepocessor(self, preprocessor: Preprocessor | list[Preprocessor]):
        for epoch in self.epochs.values():
            for acq in epoch.values():
                acq.add_preprocessor(preprocessor)

    def clear_prepocessors(self):
        pass

        # def run_analysis(self):
        for cfg in self.analysis_config:
            analysis_temp = {}
            epoch_analysis = AnalysisRegistry.get_epoch(cfg)
            for key, value in self.epochs.items():
                analyzer = epoch_analysis(cfg)
                analyzer.analyze()
                analysis_temp[key] = analyzer
            self.analysis[cfg] = analysis_temp
