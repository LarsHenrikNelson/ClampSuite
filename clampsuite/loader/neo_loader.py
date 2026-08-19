from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

import numpy as np
from neo.rawio import AxonRawIO
from scipy import signal

from .acquisition_data import AcquisitionData
from .base_loader import BaseLoader


class ABFLoader(BaseLoader):
    _epoch_map: ClassVar = {1: "step", 2: "ramp"}

    def __init__(
        self,
        callback_func: Callable = print,
        nchannels: int = 1,
        pulse_data: bool = False,
    ):
        super().__init__(callback_func)
        self.main_channel = 0
        self.secondary_channel = None
        self.acq_count = 0
        self.epoch_count = 0
        self.cycle_count = 0
        self.nchannels = nchannels
        self.pulse_data = pulse_data

    def load_segment(
        self,
        file,
        segment: int,
        channel_index: None | int = 0,
        offset: int = 0,
    ) -> np.ndarray:
        acq = file.get_analogsignal_chunk(
            block_index=0, seg_index=segment, channel_indexes=channel_index
        )
        if offset > 0:
            acq = acq[offset:-offset]
        return acq

    def process_secondary_channel(self, file: AxonRawIO, segment: int, acq_dict: dict):
        temp = self.load_segment(file, segment, channel_index=self.secondary_channel)
        abs_tt = np.abs(np.diff(temp))
        ppeaks, _ = signal.find_peaks(abs_tt)
        threshold = np.mean(abs_tt[ppeaks])
        indexes = np.where(abs_tt > threshold * 3)[0]
        if len(indexes) > 0:
            acq_dict["_pulse_start_index"] = indexes[0]
            if len(indexes) > 1:
                acq_dict["_pulse_end_index"] = indexes[1]
            else:
                acq_dict["_pulse_end_index"] = len(temp)
            acq_dict["acq_type"] = "other"
        else:
            acq_dict["_pulse_start_index"] = 0
            acq_dict["_pulse_end_index"] = len(temp)
            acq_dict["acq_type"] = "other"
            acq_dict["pulse_amp"] = 0

    def get_units(self, file, channel=0):
        return file._axon_info["listADCInfo"][channel]["ADCChUnits"].decode()

    def pulse_from_epoch(self, file: AxonRawIO, acq_dict: dict[int, dict]):
        epoch_info = file._axon_info["dictEpochInfoPerDAC"]
        epoch_key = next(iter(epoch_info.keys()))
        epoch_type = epoch_info[epoch_key][1]["nEpochType"]
        pulse_start_index = epoch_info[epoch_key][0]["lEpochInitDuration"]
        pulse_end_index = (
            epoch_info[epoch_key][1]["lEpochInitDuration"] + pulse_start_index
        )
        amp_start = epoch_info[epoch_key][0]["fEpochInitLevel"]
        amp_start_increment = epoch_info[epoch_key][0]["fEpochLevelInc"]
        current_start = amp_start
        amp_increment = epoch_info[epoch_key][1]["fEpochLevelInc"]
        amp_start = epoch_info[epoch_key][1]["fEpochInitLevel"]
        acqs_keys = sorted(acq_dict.keys())
        current_amp = amp_start
        for key in acqs_keys:
            acq_dict[key]["_pulse_start_index"] = pulse_start_index
            acq_dict[key]["_pulse_end_index"] = pulse_end_index
            acq_dict[key]["acq_type"] = self._epoch_map[epoch_type]
            acq_dict[key]["pulse_amp"] = current_amp
            acq_dict[key]["amp_start"] = current_start
            current_amp += amp_increment
            current_start += amp_start_increment

    def process_acquisitions(self, file: AxonRawIO) -> dict:
        op_mode = file._axon_info["protocol"]["nOperationMode"]
        dac_info = file._axon_info.get("listDACInfo", [])

        enabled_dacs = []
        for i, dac in enumerate(dac_info):
            enabled = dac.get("nWaveformEnable", 0)
            if enabled:
                enabled_dacs.append(i)

        if op_mode == 5 and dac_info[enabled_dacs[0]]["nWaveformSource"] == 1:
            n_adc = file._axon_info["sections"]["ADCSection"]["llNumEntries"]
            n_samples = file._axon_info["protocol"]["lNumSamplesPerEpisode"] / n_adc
            offset = int(n_samples * 15625 / 10**6)
        else:
            offset = 0
        temp_dict = {}
        if file.header is None:
            raise ValueError("File header is None")
        nacqs = file.header["nb_segment"][0]
        filename = Path(file.filename).stem
        t = file._axon_info["rec_datetime"]
        time = t.hour * 3600 + t.minute * 60 + t.second
        for i in range(nacqs):
            acq_dict = {}
            self.acq_count += 1
            acq_dict["acq_number"] = self.acq_count
            acq_dict["time_stamp"] = time + file.segment_t_start(
                block_index=0, seg_index=i
            )
            acq_dict["epoch"] = self.epoch_count
            acq_dict["cycle"] = self.cycle_count
            acq_dict["name"] = f"{filename}_{str(self.acq_count).zfill(3)}"
            acq_dict["acq_type"] = "other"
            acq_dict["pulse_pattern"] = str(i)

            gain = file.header["signal_channels"][self.main_channel][5]
            acq_dict["gain"] = gain
            acq_dict["array"] = self.load_segment(
                file, i, channel_index=self.main_channel, offset=offset
            )
            acq_dict["rc_check_pulse_start_index"] = acq_dict["array"].size
            acq_dict["rc_check_pulse_end_index"] = acq_dict["array"].size
            acq_dict["rc_amp"] = 0
            acq_dict["_pulse_start_index"] = 0
            acq_dict["_pulse_end_index"] = acq_dict["array"].size
            acq_dict["pulse_amp"] = 0.0
            acq_dict["amp_start"] = 0.0
            acq_dict["_fs"] = file.header["signal_channels"][self.main_channel][2]
            acq_dict["units"] = self.get_units(file, channel=0)
            temp_dict[self.acq_count] = acq_dict
            self.callback_func(f"Acquisition {i + 1} of {nacqs} from {filename}")
        epoch_info = file._axon_info["dictEpochInfoPerDAC"]
        if epoch_info:
            self.pulse_from_epoch(file, temp_dict)
        temp_dict = {key: AcquisitionData(**val) for key, val in temp_dict.items()}
        return temp_dict

    def process_data_files(self, data_files: list) -> dict[int, AcquisitionData]:
        output_dict = {}
        for file in data_files:
            self.cycle_count += 1
            nchans = len(file.header["signal_channels"])
            if nchans > 1 and self.nchannels > 1:
                self.secondary_channel = 1
            temp = self.process_acquisitions(file)
            output_dict.update(temp)
        return output_dict

    def load_files(
        self, file_paths: list[Path] | list[str]
    ) -> defaultdict[int, dict[int, AcquisitionData]]:
        data_files = []
        self.cycle_count = 0
        self.epoch_count += 1
        files = [Path(i) for i in file_paths]
        files.sort()
        for i in files:
            output = AxonRawIO(i)
            output.parse_header()
            data_files.append(output)
        acquisition_dict: dict[int, AcquisitionData] = self.process_data_files(
            data_files
        )
        output_dict: defaultdict[int, dict[int, AcquisitionData]] = self.group_epochs(
            acquisition_dict
        )
        return output_dict
