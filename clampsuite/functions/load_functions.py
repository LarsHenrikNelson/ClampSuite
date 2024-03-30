import json
import re
from math import nan
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import Union

import numpy as np
from scipy.io import loadmat, matlab


def load_mat(filename: str) -> dict:
    """
    This function loads a matlab file and puts it into a dictionary that is
    easy to use in python. The function was written by  on Stack Overflow.
    This function should be called instead of direct scipy.io.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects.
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


def find_pulse_data(data_string, component):
    temp_string = re.findall(component, data_string)
    amp = 0.0
    start = 0.0
    end = 0.0
    ramp = "0"
    duration = 0.0
    width = 0.0
    if len(temp_string) == 1:
        temp_string = temp_string[0]
        amp_temp = re.findall("amplitude=(.*?);", temp_string)
        if len(amp_temp) == 1:
            amp = float(amp_temp[0])
        start_temp = re.findall("delay=(.*?);", temp_string)
        if len(start_temp) == 1:
            start = float(start_temp[0])
        duration_temp = re.findall("duration=(.*?);", temp_string)
        if len(duration_temp) == 1:
            duration = float(duration_temp[0])
        width_temp = re.findall("pulseWidth=(.*?);", temp_string)
        if len(width_temp) == 1:
            width = float(width_temp[0])
            end = start + width
        ramp_temp = re.findall(r"ramp=(.*?);", temp_string)
        if len(width_temp) == 1:
            ramp = ramp_temp[0]
    return amp, start, end, ramp, duration


def load_scanimage_file(path: Union[str, PurePath]) -> dict:
    """
    This function takes pathlib.PurePath object or string as the input.
    All the data that is in time is converted to samples.
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
    acq_dict["s_r_c"] = int(acq_dict["sample_rate"] / 1000)
    acq_dict["pulse_amp"] = 0.0
    if analog_input == 0:
        # r = re.findall(r"pulseString_ao0=(.*?)state", data_string)
        acq_dict["pulse_pattern"] = re.findall("pulseToUse0=(\D?\d*)", data_string)[0]
        amp, start, end, ramp, duration = find_pulse_data(
            data_string, "pulseString_ao0=(.*?)state"
        )

    elif analog_input == 1:
        # r = re.findall(r"pulseString_ao1=(.*?)state", data_string)
        acq_dict["pulse_pattern"] = re.findall("pulseToUse1=(\D?\d*)", data_string)[0]
        amp, start, end, ramp, duration = find_pulse_data(
            data_string, "pulseString_ao1=(.*?)state"
        )
    acq_dict["pulse_amp"] = amp
    acq_dict["_pulse_start"] = int(start * acq_dict["s_r_c"])
    if end > 0:
        acq_dict["_pulse_end"] = int(end * acq_dict["s_r_c"])
    else:
        acq_dict["_pulse_end"] = int(duration * acq_dict["s_r_c"])
        acq_dict["pulse_end"] = duration
    acq_dict["ramp"] = ramp
    acq_dict["pulse_amp"] = amp
    acq_dict["pulse_start"] = acq_dict["s_r_c"]

    rc_amp, rc_start, rc_end, _, _ = find_pulse_data(data_string, "RCCheck='(.*);'")
    acq_dict["_rc_check_start"] = int(rc_start * acq_dict["s_r_c"])
    acq_dict["_rc_check_end"] = int(rc_end * acq_dict["s_r_c"])
    acq_dict["rc_amp"] = rc_amp
    acq_dict["rc_check_start"] = rc_start
    acq_dict["rc_check_end"] = rc_end
    acq_dict["_rc_check_duration"] = int(acq_dict["_rc_check_end"]-acq_dict["_rc_check_start"])
    return acq_dict


def load_neo_acq(analog_sig, acq_num):
    acq_dict = {}
    acq_dict["sample_rate"] = int(analog_sig.sampling_rate)
    acq_dict["s_r_c"] = int(acq_dict["sample_rate"] / 1000)
    acq_dict["acq_num"] = acq_num
    name = re.findall(r"\((.*)\)", analog_sig.name)[0]
    acq_dict["name"] = name
    acq_dict["time_stamp"] = acq_num * len(analog_sig) / analog_sig.sampling_rate
    acq_dict["array"] = analog_sig.as_array().flatten()

    # Other stuff that neo file does not include
    acq_dict["pulse_pattern"] = "0"
    acq_dict["epoch"] = 0
    acq_dict["ramp"] = "0"
    acq_dict["pulse_amp"] = 0
    acq_dict["pulse_start"] = 0
    acq_dict["pulse_end"] = 0
    acq_dict["_pulse_start"] = 0
    acq_dict["_pulse_end"] = 0
    acq_dict["rc_amp"] = 0
    acq_dict["rc_start"] = 0
    acq_dict["rc_end"] = 0
    acq_dict["_rc_start"] = 0
    acq_dict["_rc_end"] = 0
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
    for key in data.keys():
        if isinstance(data[key], list):
            if key not in ["postsynaptic_events", "final_events"]:
                data[key] = np.array(data[key])
    return data
