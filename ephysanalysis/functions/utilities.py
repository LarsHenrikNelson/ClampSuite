# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 10:35:28 2021

@author: LarsNelson

Last edited on Tue Feb 16 10:47:30 2022

Ephys analysis package version.
"""
from pathlib import PurePath
import re
from typing import Tuple

import numpy as np
from scipy.io import loadmat, matlab


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


def load_scanimage_file(
    path: PurePath,
) -> Tuple[np.array, str, str, str, str, str, str]:
    """
    This function takes pathlib.PurePath object as the input.
    """
    name = path.stem
    acq_number = name.split("_")[-1]
    matfile1 = load_mat(path)
    array = matfile1[name]["data"]
    data_string = matfile1[name]["UserData"]["headerString"]
    epoch = re.findall("epoch=(\D?\d*)", data_string)[0]
    analog_input = matfile1[name]["UserData"]["ai"]
    time_stamp = matfile1[name]["timeStamp"]
    if analog_input == 0:
        r = re.findall(r"pulseString_ao0=(.*?)state", data_string)
        pulse_pattern = re.findall("pulseToUse1=(\D?\d*)", data_string)[0]
    elif analog_input == 1:
        r = re.findall(r"pulseString_ao1=(.*?)state", data_string)
        pulse_pattern = re.findall("pulseToUse1=(\D?\d*)", data_string)[0]
    ramp = re.findall(r"ramp=(\D?\d*);", r[0])
    if ramp:
        ramp = ramp[0]
        pulse_amp = re.findall("amplitude=(\D?\d*)", r[0])[0]
    else:
        ramp = "0"
        pulse_amp = "0"
    return (name, acq_number, array, epoch, pulse_pattern, ramp, pulse_amp, time_stamp)
