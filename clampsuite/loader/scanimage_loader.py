import re
from pathlib import PurePath, Path
from typing import Union

import numpy as np
from scipy.io import loadmat, matlab

from .base_loader import BaseLoader


class ScanImageLoader(BaseLoader):
    def __init__(self, callback_func: callable):
        super().__init__(callback_func)

    def load_mat(self, filename: str) -> dict:
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
                if isinstance(d[key], matlab.mat_struct):
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
                if isinstance(elem, matlab.mat_struct):
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
                    if isinstance(sub_elem, matlab.mat_struct):
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

    def find_stim_pulses(self, data_string):
        m = re.findall("lastLinesUsed={(.*?)}\rstate", data_string)
        pulse_output = 0
        if len(m) == 1:
            m = m[0].split()
            pulse_output = [i.replace("'", "") for i in m]
            pulse_output = [i for i in pulse_output if i not in {"ao1", "ao0"}]
        return pulse_output

    def find_pulse_data(self, data_string, component):
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

    def find_stim_pulse_data(self, data_string, component):
        temp_string = re.findall(f"pulseString_{component}=(.*?)state", data_string)
        pulse_width = 0.0
        num_pulses = 0
        pulse_start = 0.0
        isi = 0.0
        if len(temp_string) == 1:
            temp_string = temp_string[0]
            pulse_start = re.findall("delay=(.*?);", temp_string)
            if len(pulse_start) == 1:
                pulse_start = float(pulse_start[0])
            pulse_width = re.findall("pulseWidth=(.*?);", temp_string)
            if len(pulse_width) == 1:
                pulse_width = float(pulse_width[0])
            num_pulses = re.findall("numPulses=(.*?);", temp_string)
            if len(num_pulses) == 1:
                num_pulses = int(num_pulses[0])
            isi = re.findall("isi=(.*?);", temp_string)
            if len(isi) == 1:
                isi = float(isi[0])
        return num_pulses, isi, pulse_start

    def load_scanimage_file(self, path: Union[str, PurePath]) -> dict:
        """
        This function takes pathlib.PurePath object or string as the input.
        All the data that is in time is converted to samples.
        """
        acq_dict = {}
        acq_dict["name"] = PurePath(path).stem
        matfile1 = self.load_mat(path)
        name = [i for i in matfile1.keys() if "AD" in i][0]
        acq_dict["acq_number"] = int(name.split("_")[-1])
        acq_dict["array"] = matfile1[name]["data"]
        data_string = matfile1[name]["UserData"]["headerString"]
        acq_dict["epoch"] = re.findall(r"epoch=(\D?\d*)", data_string)[0]
        analog_input = matfile1[name]["UserData"]["ai"]
        acq_dict["time_stamp"] = matfile1[name]["timeStamp"]
        acq_dict["sample_rate"] = int(re.findall(r"inputRate=([0-9]*)", data_string)[0])
        s_r_c = int(acq_dict["sample_rate"] / 1000)
        acq_dict["pulse_amp"] = 0.0

        acq_dict["pulse_pattern"] = re.findall(
            rf"pulseToUse{analog_input}=(\D?\d*)", data_string
        )[0]
        amp, start, end, ramp, duration = self.find_pulse_data(
            data_string, f"pulseString_ao{analog_input}=(.*?)state"
        )

        acq_dict["pulse_amp"] = amp
        acq_dict["pulse_start"] = int(start * s_r_c)
        if end > 0:
            acq_dict["pulse_end"] = int(end * s_r_c)
        else:
            acq_dict["pulse_end"] = int(duration * s_r_c)
            acq_dict["pulse_end"] = duration
        acq_dict["ramp"] = ramp
        acq_dict["pulse_amp"] = amp

        rc_amp, rc_start, rc_end, _, _ = self.find_pulse_data(
            data_string, "RCCheck='(.*);'"
        )
        acq_dict["rc_check_pulse_start"] = int(rc_start * s_r_c)
        acq_dict["rc_check_pulse_end"] = int(rc_end * s_r_c)
        acq_dict["rc_amp"] = rc_amp
        return acq_dict

    def set_cycle(self, acquisitions):
        rows = len(acquisitions)
        temp_data = np.zeros((rows, 5))
        for index, key in enumerate(acquisitions):
            temp_data[index, 0] = acquisitions[key]["acq_number"]
            temp_data[index, 1] = acquisitions[key]["epoch"]
            temp_data[index, 2] = acquisitions[key]["pulse_amp"]
            temp_data[index, 3] = int(acquisitions[key]["ramp"])

        temp_data = temp_data[temp_data[:, 1].argsort()]
        temp_data = temp_data[temp_data[:, 0].argsort()]

        current_epoch = temp_data[0, 1]
        count = 0
        for i in range(1, rows):
            if current_epoch != temp_data[i, 1]:
                count = -1
                current_epoch = temp_data[i, 1]
            if temp_data[i - 1, 2] > 0 and temp_data[i, 2] < 0:
                count += 1
                temp_data[i, 4] = count
            else:
                temp_data[i, 4] = count
            if temp_data[i, 3] == 1:
                temp_data[i, 4] = 0
        for i in range(rows):
            acquisitions[int(temp_data[i, 0])]["cycle"] = int(temp_data[i, 4])

    def load_files(self, file_paths: list[str | Path]):
        acquisitions = {}
        n_files = len(file_paths)
        for count, i in enumerate(file_paths):
            acq_comp = self.load_scanimage_file(i)
            self.callback_func(f"Acquisition {count + 1} of {n_files} loaded")
            acquisitions[int(acq_comp["acq_number"])] = acq_comp
        self.set_cycle(acquisitions)
        return acquisitions
