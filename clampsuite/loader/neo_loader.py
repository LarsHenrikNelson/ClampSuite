from pathlib import Path
from typing import Callable, Type

from neo.rawio import get_rawio, AxonRawIO
import numpy as np
from scipy import signal

from .base_loader import BaseLoader
from .acquisition_data import AcquisitionData


class ABFLoader(BaseLoader):
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
        return acq[offset:-offset]

    def process_secondary_channel(self, file: AxonRawIO, segment: int, acq_dict: dict):
        if file.header is None:
            raise ValueError("File header is None")
        else:
            gain = file.header["signal_channels"][self.secondary_channel][5]
        temp = self.load_segment(
            file, segment, gain=gain, channel_index=self.secondary_channel
        )
        abs_tt = np.abs(np.diff(temp))
        ppeaks, _ = signal.find_peaks(abs_tt)
        threshold = np.mean(abs_tt[ppeaks])
        indexes = np.where(abs_tt > threshold * 3)[0]
        if len(indexes) > 0:
            acq_dict["pulse_start_index"] = indexes[0]
            if len(indexes) > 1:
                acq_dict["pulse_end_index"] = indexes[1]
            else:
                acq_dict["pulse_end_index"] = len(temp)
            acq_dict["ramp"] = 0
        else:
            acq_dict["pulse_start_index"] = 0
            acq_dict["pulse_end_index"] = len(temp)
            acq_dict["ramp"] = 0
            acq_dict["pulse_amp"] = 0

    def get_units(self, file, channel=0):
        return file._axon_info["listADCInfo"][channel]["ADCChUnits"].decode()

    def pulse_from_epoch(self, file: AxonRawIO, acq_dict: dict[int, dict]):
        epoch_info = file._axon_info["dictEpochInfoPerDAC"]
        epoch_key = list(epoch_info.keys())[0]
        pulse_start_index = epoch_info[epoch_key][0]["lEpochInitDuration"]
        pulse_end_index = (
            epoch_info[epoch_key][1]["lEpochInitDuration"] + pulse_start_index
        )
        amp_increment = epoch_info[epoch_key][1]["fEpochLevelInc"]
        amp_start = epoch_info[epoch_key][1]["fEpochInitLevel"]
        acqs_keys = sorted(list(acq_dict.keys()))
        current_amp = amp_start
        for key in acqs_keys:
            acq_dict[key]["pulse_start_index"] = pulse_start_index
            acq_dict[key]["pulse_end_index"] = pulse_end_index
            acq_dict[key]["ramp"] = 0
            acq_dict[key]["pulse_amp"] = current_amp
            current_amp += amp_increment

    def process_acquisitions(self, file: AxonRawIO) -> dict:
        op_mode = file._axon_info["protocol"]["nOperationMode"]
        if op_mode == 5:
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
            acq_dict["ramp"] = 0
            acq_dict["pulse_pattern"] = str(i)

            gain = file.header["signal_channels"][self.main_channel][5]
            acq_dict["gain"] = gain
            acq_dict["array"] = self.load_segment(
                file, i, channel_index=self.main_channel, offset=offset
            )
            acq_dict["rc_check_pulse_start_index"] = acq_dict["array"].size
            acq_dict["rc_check_pulse_end_index"] = acq_dict["array"].size
            acq_dict["rc_amp"] = 0
            acq_dict["pulse_start_index"] = 0
            acq_dict["pulse_end_index"] = acq_dict["array"].size
            acq_dict["pulse_amp"] = 0
            acq_dict["fs"] = file.header["signal_channels"][self.main_channel][2]
            acq_dict["units"] = self.get_units(file, channel=0)
            temp_dict[self.acq_count] = acq_dict
            self.callback_func(f"Acquisition {i + 1} of {nacqs} from {filename}")
        if self.pulse_data:
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

    def load_files(self, files: list[str | Path]) -> dict[int, AcquisitionData]:
        data_files = []
        self.cycle_count = 0
        self.epoch_count += 1
        files = [Path(i) for i in files]
        files.sort()
        for i in files:
            output = AxonRawIO(i)
            output.parse_header()
            data_files.append(output)
        output_dict = self.process_data_files(data_files)
        return output_dict
