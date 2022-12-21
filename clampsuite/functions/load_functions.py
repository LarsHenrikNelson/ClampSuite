from copy import deepcopy
import json
from math import nan
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
import re
from typing import Union, Literal

import numpy as np
from scipy.io import loadmat, matlab

from ..acq import Acquisition


"""
This function loads a matlab file and puts it into a dictionary that is easy
to use in python. The function was written by  on Stack Overflow.
"""


def load_mat(filename: str) -> dict:
    """
    This function should be called instead of direct scipy.io.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    """

    def _check_vars(d):
        """
        Checks if entries in dictionary are mat-objects. If yes
        todict is called to change them to nested dictionaries
        """
        for key in d:
            if isinstance(d[key], matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
            elif isinstance(d[key], np.ndarray):
                d[key] = _toarray(d[key])
        return d

    def _todict(matobj):
        """
        A recursive function which constructs from matobjects nested dictionaries
        """
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, matlab.mio5_params.mat_struct):
                d[strg] = _todict(elem)
            elif isinstance(elem, np.ndarray):
                d[strg] = _toarray(elem)
            else:
                d[strg] = elem
        return d

    def _toarray(ndarray):
        """
        A recursive function which constructs ndarray from cellarrays
        (which are loaded as numpy ndarrays), recursing into the elements
        if they contain matobjects.
        """
        if ndarray.dtype != "float64":
            elem_list = []
            for sub_elem in ndarray:
                if isinstance(sub_elem, matlab.mio5_params.mat_struct):
                    elem_list.append(_todict(sub_elem))
                elif isinstance(sub_elem, np.ndarray):
                    elem_list.append(_toarray(sub_elem))
                else:
                    elem_list.append(sub_elem)
            return np.array(elem_list)
        else:
            return ndarray

    data = loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_vars(data)


def load_scanimage_file(path: Union[str, PurePath]) -> dict:
    """
    This function takes pathlib.PurePath object as the input.
    """
    acq_dict = {}
    name = PurePath(path).stem
    acq_dict["name"] = name
    acq_dict["acq_number"] = name.split("_")[-1]
    matfile1 = load_mat(path)
    acq_dict["array"] = matfile1[name]["data"]
    data_string = matfile1[name]["UserData"]["headerString"]
    acq_dict["epoch"] = re.findall("epoch=(\D?\d*)", data_string)[0]
    analog_input = matfile1[name]["UserData"]["ai"]
    acq_dict["time_stamp"] = matfile1[name]["timeStamp"]
    acq_dict["sample_rate"] = int(re.findall(r"inputRate=([0-9]*)", data_string)[0])
    if analog_input == 0:
        r = re.findall(r"pulseString_ao0=(.*?)state", data_string)
        acq_dict["pulse_pattern"] = re.findall("pulseToUse0=(\D?\d*)", data_string)[0]
    elif analog_input == 1:
        r = re.findall(r"pulseString_ao1=(.*?)state", data_string)
        acq_dict["pulse_pattern"] = re.findall("pulseToUse1=(\D?\d*)", data_string)[0]
    ramp = re.findall(r"ramp=(\D?\d*);", r[0])
    if ramp:
        acq_dict["ramp"] = ramp[0]
        acq_dict["pulse_amp"] = re.findall("amplitude=(\D?\d*)", r[0])[0]
    else:
        acq_dict["ramp"] = "0"
        acq_dict["pulse_amp"] = "0"
    return acq_dict


class NumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy types. Numpy types are not accepted by the
    json encoder and need to be converted to python types.
    """

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
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
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
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


def load_json_file(path: Union[PurePath, str]) -> dict:
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
    if "sample_rate_correction" in data and data["sample_rate_correction"] is not None:
        data["s_r_c"] = data.get("sample_rate_correction")
    return data


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
        obj = Acquisition(acq_comp.get("analysis"))
    elif isinstance(analysis, str):
        obj = Acquisition(analysis)
    else:
        print("No analysis specified!")
        return None
    obj.load_data(acq_comp)
    return obj


def load_acqs(
    analysis: Union[Literal["mini", "current_clamp", "lfp", "oepsc"], None],
    file_path: Union[list, tuple, str, Path, PurePath],
    callback_func=print,
) -> dict:
    if isinstance(file_path, (str, Path, PurePath)):
        file_path = list(file_path)
    for count, i in enumerate(file_path):
        print("Loading acquisitions")
        acq_dict = {}
        if PurePath(i).suffix == (".mat", ".json"):
            acq = load_acq(analysis, i)
            if acq is None:
                pass
            else:
                acq_dict[int(acq.acq_number)] = acq
                callback_func(int((100 * (count + 1) / len(file_path))))
    return acq_dict


def load_file(file_path: str, extension: str):
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


def save_acq(acq, save_filename):
    x = deepcopy(acq)
    if x.analysis == "mini":
        x.save_postsynaptic_events()
    with open(f"{save_filename}_{x.name}.json", "w") as write_file:
        json.dump(x.__dict__, write_file, cls=NumpyEncoder)


if __name__ == "__main__":
    load_acq()
    load_acqs()
    load_file()
