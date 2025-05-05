from pathlib import Path

import neo
import numpy as np
from scipy import signal

from .base_loader import BaseLoader


class NeoLoader(BaseLoader):
    def __init__(self, callback_func: callable = print, nchannels=2):
        super().__init__(callback_func)
        self.main_channel = 0
        self.secondary_channel = None
        self.acq_count = 0
        self.epoch_count = 0
        self.cycle_count = 0
        self.nchannels = nchannels

    def load_segment(self, file, segment: int, gain: float, channel_index: int = 0):
        acq = file.get_analogsignal_chunk(
            block_index=0, seg_index=segment, channel_indexes=channel_index
        )
        array = acq * gain
        return array

    def process_secondary_channel(self, file, segment: int, acq_dict: dict):
        gain = file.header["signal_channels"][self.secondary_channel][5]
        temp = self.load_segment(
            file, segment, gain=gain, channel_index=self.secondary_channel
        )
        abs_tt = np.abs(np.diff(temp))
        ppeaks, _ = signal.find_peaks(abs_tt)
        threshold = np.mean(abs_tt[ppeaks])
        indexes = np.where(abs_tt > threshold * 3)[0]
        if len(indexes) > 0:
            acq_dict["pulse_start"] = indexes[0] / acq_dict["s_r_c"]
            acq_dict["_pulse_start"] = indexes[0]
            if len(indexes) > 1:
                acq_dict["pulse_end"] = indexes[1] / acq_dict["s_r_c"]
                acq_dict["_pulse_end"] = indexes[1]
            else:
                acq_dict["pulse_end"] = len(temp) / acq_dict["s_r_c"]
                acq_dict["_pulse_end"] = len(temp)
            acq_dict["pulse_ramp"] = "0"
        else:
            acq_dict["pulse_start"] = 0
            acq_dict["_pulse_start"] = 0
            acq_dict["_pulse_end"] = len(temp)
            acq_dict["pulse_end"] = len(temp) / acq_dict["s_r_c"]
            acq_dict["pulse_ramp"] = "0"
            acq_dict["pulse_duration"] = 0
            acq_dict["pulse_width"] = 0
            acq_dict["pulse_amp"] = 0

    def process_acquisitions(self, file: str | Path):
        temp_dict = {}
        nacqs = file.header["nb_segment"][0]
        filename = Path(file.filename).stem
        for i in range(nacqs):
            acq_dict = {}
            self.acq_count += 1
            acq_dict["acq_number"] = self.acq_count
            acq_dict["time_stamp"] = file.segment_t_start(block_index=0, seg_index=i)
            acq_dict["epoch"] = str(self.epoch_count)
            acq_dict["cycle"] = self.cycle_count
            acq_dict["name"] = f"{filename}_{str(self.acq_count).zfill(3)}"
            acq_dict["_rc_check_pulse_start"] = 0
            acq_dict["_rc_check_pulse_end"] = 0
            acq_dict["ramp"] = "0"
            acq_dict["rc_check_pulse_start"] = 0
            acq_dict["rc_check_pulse_end"] = 0
            acq_dict["pulse_pattern"] = str(i)
            gain = file.header["signal_channels"][self.main_channel][5]
            acq_dict["array"] = self.load_segment(
                file, i, gain=gain, channel_index=self.main_channel
            )
            acq_dict["sample_rate"] = file.header["signal_channels"][self.main_channel][
                2
            ]
            acq_dict["s_r_c"] = int(acq_dict["sample_rate"] / 1000)
            if self.secondary_channel is not None:
                self.process_secondary_channel(file, i, acq_dict)
            temp_dict[self.acq_count] = acq_dict
            self.callback_func(f"Acquisition {i + 1} of {nacqs} from {filename}")
        if self.secondary_channel is not None:
            self.set_pulse(file, nacqs, temp_dict)
        return temp_dict

    def set_pulse(self, file, nacqs, acq_dict: dict):
        gain = file.header["signal_channels"][self.secondary_channel][5]
        pulse_starts = [value["_pulse_start"] for value in acq_dict.values()]
        pulse_ends = [value["_pulse_end"] for value in acq_dict.values()]
        ps, ps_count = np.unique(pulse_starts, return_counts=True)
        pe, pe_count = np.unique(pulse_ends, return_counts=True)
        pe, pe_count = np.unique(pulse_ends, return_counts=True)
        ps = ps[np.argmax(ps_count)]
        pe = pe[np.argmax(pe_count)]
        for index, value in zip(range(nacqs), acq_dict.values()):
            value["_pulse_start"] = ps
            value["_pulse_end"] = pe
            value["pulse_start"] = ps / value["s_r_c"]
            value["pulse_end"] = pe / value["s_r_c"]
            gain = file.header["signal_channels"][self.secondary_channel][5]
            temp = self.load_segment(
                file, index, gain=gain, channel_index=self.secondary_channel
            )
            value["pulse_duration"] = value["pulse_end"] - value["pulse_start"]
            value["pulse_width"] = value["_pulse_end"] - value["_pulse_start"]
            value["pulse_amp"] = int(
                np.mean(temp[value["_pulse_start"] : value["_pulse_end"]])
                - np.mean(temp[: value["_pulse_start"]])
            )

    def process_data_files(self, data_files: list):
        output_dict = {}
        for file in data_files:
            self.cycle_count += 1
            nchans = len(file.header["signal_channels"])
            if nchans > 1 and self.nchannels > 1:
                self.secondary_channel = 1
            temp = self.process_acquisitions(file)
            output_dict.update(temp)
        return output_dict

    def load_files(self, files=list[str | Path]):
        data_files = []
        self.cycle_count = 0
        self.epoch_count += 1
        files.sort()
        for i in files:
            output = neo.rawio.get_rawio(i)
            if isinstance(output, list):
                output = output[0](i)
            else:
                output = output(i)
            output.parse_header()
            data_files.append(output)
        output_dict = self.process_data_files(data_files)
        return output_dict
