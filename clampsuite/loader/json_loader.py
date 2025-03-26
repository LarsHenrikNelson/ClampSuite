import json
from math import nan
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Union

import numpy as np

from .base_loader import BaseLoader


class NumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy types. Numpy types are not accepted by the
    json encoder and need to be converted to python types.
    """

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (PurePath, PurePosixPath, PureWindowsPath)):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class NumpyDecoder(json.JSONDecoder):
    """
    Special json encoder for numpy types. Numpy types are not accepted by the
    json encoder and need to be converted to python types.
    """

    def default(self, obj):
        if isinstance(obj, int):
            return np.int64(obj)
        elif obj is nan:
            return np.nan
        elif isinstance(obj, float):
            return np.float64(obj)
        elif isinstance(obj, list):
            return np.array(obj)
        elif isinstance(obj, (PurePath, PurePosixPath, PureWindowsPath)):
            return str(obj)
        return json.JSONDecoder.default(self, obj)


def load_json_file_legacy(path: Union[PurePath, str]) -> dict:
    """
    This function loads a json file and sets each key: value pair
    as an attribute of the an obj. The function has to catch a lot
    things that I have changed over the course of the program so
    that all of our saved files can be loaded.
    """
    with open(path, "r") as rf:
        data = json.load(rf, cls=NumpyDecoder)
    if data["analysis"] == "oepsc":
        if not data.get("find_ct"):
            data["find_ct"] = False
        if not data.get("find_est_deay"):
            data["find_est_deay"] = False
        if not data.get("find_ct"):
            data["curve_fit_decay"] = False
    altered_keys = {"fv_x", "fp_x", "pulse_start", "slope", "slope_x"}
    for key in data:
        if key in altered_keys:
            new_key = "_" + key
            data[new_key] = data.pop(key)
        if key == "peak_x":
            new_key = "_" + key
            data[key] = data[key] * 10
            data[new_key] = data.pop(key)
        if isinstance(data[key], list):
            if key not in ["postsynaptic_events", "final_events"]:
                data[key] = np.array(data[key])
    if "pulse_amp" in data:
        data["pulse_amp"] = float(data["pulse_amp"])
    if "sample_rate_correction" in data and data["sample_rate_correction"] is not None:
        data["s_r_c"] = data.get("sample_rate_correction")
    return data


class JSONLoader(BaseLoader):
    def load_json_file(self, path: Union[PurePath, str]) -> dict:
        """
        This function loads a json file and sets each key: value pair
        as an attribute of the an obj. The function has to catch a lot
        things that I have changed over the course of the program so
        that all of our saved files can be loaded.
        """
        with open(path, "r") as rf:
            data = json.load(rf, cls=NumpyDecoder)
        if data["analysis"] == "oepsc":
            if not data.get("find_ct"):
                data["find_ct"] = False
            if not data.get("find_est_deay"):
                data["find_est_deay"] = False
            if not data.get("find_ct"):
                data["curve_fit_decay"] = False
        for key in data.keys():
            if isinstance(data[key], list):
                if key not in ["postsynaptic_events", "final_events"]:
                    data[key] = np.array(data[key])
        return data

    def load_files(self, file_paths: list[str | Path]):
        nacqs = len(file_paths)
        for count, i in enumerate(file_paths):
            data = self.load_json_file(i)
            self.acquisitions[data["acq_number"]] = data
            self.callback_func(f"Loaded {count+1} of {nacqs}")
