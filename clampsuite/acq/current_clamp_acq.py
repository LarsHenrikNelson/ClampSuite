from typing import Literal, Union
from collections import defaultdict

import numpy as np
from scipy import signal

from ..functions.current_clamp import (
    SPIKE_PARAMS,
    ThresholdType,
    adaptation_index,
    ai_sfa,
    coefficient_of_variation,
    divisor_sfa,
    find_all_ahps,
    find_all_spk_auc,
    find_all_spk_thresholds,
    find_all_spk_velocities,
    find_all_spk_widths,
    local_sfa,
    voltage_sag,
    membrane_time_constant_deltav,
    membrane_time_constant_min,
)
from ..functions.general import baseline_stability, delta
from ..functions.curve_fit import SExpDecay, DExpDecay
from ..functions.utilities import map_keys
from ..loader.acquisition_data import AcquisitionData

PlotOutput = tuple[np.ndarray, np.ndarray]


class CurrentClampAcq:
    def __init__(self, acq_data: AcquisitionData):
        self.acq_data = acq_data

        self._analysis_variables = {}
        self._analysis_variables["baseline_mv"] = np.nan
        self._analysis_variables["delta_v_mv"] = np.nan
        self._analysis_variables["freq_hz"] = 0.0
        self._analysis_variables["iei_index"] = 0.0
        self._analysis_variables["spike_index"] = np.array([])
        self._analysis_variables["spike_mv"] = np.array([])
        self._analysis_variables["spike_number"] = np.array([])
        self._analysis_variables["mem_tau_min_index"] = np.nan
        self._analysis_variables["mem_tau_deltav_index"] = np.nan
        self._analysis_variables["sag_mv"] = np.nan
        self._analysis_variables["sag_index"] = np.nan
        self._analysis_variables["baseline_stability"] = np.nan
        self._analysis_variables["rebound_spike"] = 0
        self._analysis_variables["local_sfa"] = np.nan
        self._analysis_variables["divisor_sfa"] = np.nan
        self._analysis_variables["ai_sfa"] = np.nan
        self._analysis_variables["adaptation"] = np.nan
        self._analysis_variables["coefficient_of_variation"] = np.nan
        self._analysis_variables["sag_fit"] = None

        for i in SPIKE_PARAMS:
            self._analysis_variables[i] = np.array([])

    def analyze(
        self,
        baseline_start: int = 0,
        baseline_end: int = 3000,
        min_spike_voltage: Union[int, float] = 0,
        threshold_method: ThresholdType = "third_derivative",
        min_spikes: int = 1,
        side: Literal["left", "right"] = "right",
        proportion: float = 0.5,
        fit_sag_decay: Literal[0, 1, 2] = 0,
    ) -> None:
        pulse_start = self.acq_data.pulse_start_index
        pulse_end = self.acq_data.pulse_end_index
        if pulse_end < pulse_start:
            raise ValueError("pulse_end must be greater than pulse_start")
        if baseline_end < baseline_start:
            raise ValueError("baseline_end must be greater than baseline_start")
        self.min_spike_voltage = min_spike_voltage
        self.threshold_method = threshold_method
        self.min_spikes = min_spikes
        self.proportion = proportion
        self.side = side
        self.baseline_start = baseline_start
        self.baseline_end = baseline_end
        self.pulse_end = pulse_end
        self.pulse_start = pulse_start
        self.fit_sag_decay = fit_sag_decay

        # Analysis functions
        acquisition = self.acq_data.acquisition
        self._analysis_variables["baseline_mv"] = np.mean(
            acquisition[self.baseline_start : self.baseline_end]
        )
        spike_index, _ = signal.find_peaks(
            acquisition[self.pulse_start : self.pulse_end],
            height=self.min_spike_voltage,
        )
        spike_index += self.pulse_start
        self._analysis_variables["spike_index"] = spike_index
        self._analysis_variables["spike_mv"] = acquisition[spike_index]
        self._analysis_variables["spike_number"] = np.arange(1, spike_index.size + 1)
        self._analysis_variables["freq_hz"] = len(spike_index) / (
            (self.pulse_end - self.pulse_start) / self.acq_data.fs
        )
        if len(spike_index) > 1:
            self._analysis_variables["iei_index"] = np.mean(np.diff(spike_index))
        if len(spike_index) > 0:
            self._analysis_variables.update(
                find_all_spk_thresholds(
                    acquisition,
                    spike_index,
                    self.pulse_start,
                    self.threshold_method,
                )
            )
            self._analysis_variables.update(
                find_all_ahps(acquisition, spike_index, self.pulse_end)
            )
            self._analysis_variables.update(
                find_all_spk_widths(
                    acquisition,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            temp = find_all_spk_auc(
                acquisition,
                self._analysis_variables["threshold_index"],
                self.pulse_end,
            )
            for key in temp.keys():
                temp[key] *= (1 / self.acq_data.fs) * 1000
            self._analysis_variables.update(temp)
            self._analysis_variables.update(
                find_all_spk_velocities(
                    acquisition,
                    self._analysis_variables["threshold_index"],
                    self.pulse_end,
                )
            )
            self._analysis_variables["local_sfa"] = local_sfa(spike_index)
            self._analysis_variables["divisor_sfa"] = divisor_sfa(spike_index)
            self._analysis_variables["ai_sfa"] = ai_sfa(spike_index)
            self._analysis_variables["adaptation"] = adaptation_index(spike_index)
            self._analysis_variables["coefficient_of_variation"] = (
                coefficient_of_variation(spike_index)
            )

        self._analysis_variables["delta_v_mv"] = self.get_delta_v(
            acquisition, spike_index
        )

        if self.acq_data.pulse_amp < 0:
            self._analysis_variables.update(
                voltage_sag(acquisition, self.pulse_start, self.pulse_end)
            )
            if self.fit_sag_decay > 0:
                index = self._analysis_variables["sag_index"]
                x_temp = np.arange(0, pulse_end - index) / self.acq_data.s_r_c
                if self.fit_sag_decay == 1:
                    temp_output = SExpDecay()

                else:
                    temp_output = DExpDecay()
                temp_output.fit(x_temp, acquisition[index:pulse_end])
                self._analysis_variables["sag_fit"] = temp_output

        if self._analysis_variables["delta_v_mv"] < 0 and self.acq_data.pulse_amp < 0:
            self._analysis_variables["mem_tau_deltav_index"] = (
                membrane_time_constant_deltav(
                    acquisition,
                    self._analysis_variables["delta_v_mv"],
                    self.pulse_start,
                )
            )
            self._analysis_variables["mem_tau_min_index"] = membrane_time_constant_min(
                acquisition,
                self.pulse_start,
            )

        self._analysis_variables["baseline_stability"] = baseline_stability(
            acquisition, self.pulse_start, self.pulse_end
        )

        rebound_spikes, _ = signal.find_peaks(
            acquisition[self.pulse_end :],
            height=self.min_spike_voltage,
            prominence=int(1 * self.acq_data.s_r_c),
        )
        if len(rebound_spikes) > 0:
            self._analysis_variables["rebound_spike"] = len(rebound_spikes)
            self._analysis_variables["rebound_spike_start_index"] = (
                rebound_spikes[0] + self.pulse_end
            )

    def get_delta_v(self, acquisition: np.ndarray, peaks: np.ndarray):
        """This function finds the delta-v for a pulse. It simply takes the mean
        value from the pulse start to end for pulses without spikes. For
        pulses with spikes it takes the mode of the moving mean.
        """

        if len(peaks) == 0:
            delta_v = delta(
                acquisition,
                self.pulse_start,
                self.pulse_end,
                self.proportion,
                self.side,
            )
        else:
            index = self._analysis_variables["threshold_index"][0]
            delta_v = acquisition[index] - self._analysis_variables["baseline_mv"]
        return delta_v

    def spike_half_widths(self):
        x = (
            np.array(
                [
                    self._analysis_variables["hw_left_index"],
                    self._analysis_variables["hw_right_index"],
                ]
            )
            / self.acq_data.s_r_c
        )
        y = np.array(
            [self._analysis_variables["hw_mv"], self._analysis_variables["hw_mv"]]
        )
        return x, y

    def spike_widths(self):
        x = (
            np.array(
                [
                    self._analysis_variables["fw_left_index"],
                    self._analysis_variables["fw_right_index"],
                ]
            )
            / self.acq_data.s_r_c
        )
        y = np.array(
            [self._analysis_variables["fw_mv"], self._analysis_variables["fw_mv"]]
        )
        return x, y

    def peaks(self):
        x = self._analysis_variables["spike_index"] / self.acq_data.s_r_c
        if len(x) > 0:
            y = self.acq_data.acquisition[self._analysis_variables["spike_index"]]
        else:
            y = np.array([])
        return x, y

    def ahps(self):
        x = self._analysis_variables["ahp_index"] / self.acq_data.s_r_c
        if len(x) > 0:
            y = self.acq_data.acquisition[self._analysis_variables["ahp_index"]]
        else:
            y = np.array([])
        return x, y

    def thresholds(self) -> PlotOutput:
        x = self._analysis_variables["threshold_index"] / self.acq_data.s_r_c
        if len(x) > 0:
            y = self.acq_data.acquisition[self._analysis_variables["threshold_index"]]
        else:
            y = np.array([])
        return x, y

    def sag(self) -> PlotOutput:
        sag = self._analysis_variables["sag_mv"]
        x = self._analysis_variables["sag_index"] / self.acq_data.s_r_c
        delta = (
            self._analysis_variables["baseline_mv"]
            + self._analysis_variables["delta_v_mv"]
        )
        y = np.array([delta, delta + sag])
        x = np.array([x, x])
        return x, y

    def sag_decay(self) -> PlotOutput:
        if self._analysis_variables["sag_fit"] is not None:
            start = self._analysis_variables["sag_index"]
            fit_object = self._analysis_variables["sag_fit"]
            end = self.pulse_end
            x = np.arange(0, end - start)
            y = fit_object.predict(x / self.acq_data.s_r_c)
            x = (x + start) / self.acq_data.s_r_c
        else:
            x = np.array([])
            y = np.array([])
        return x, y

    def delta_v(self) -> PlotOutput:
        b = self._analysis_variables["baseline_mv"]
        delta = self._analysis_variables["delta_v_mv"]
        y = np.array([b, b + delta])
        start = self.pulse_start
        end = self.pulse_end
        mid = (end - start) * self.proportion
        mid = (start + mid) / self.acq_data.s_r_c
        x = np.array([mid, mid])
        return x, y

    def min_velocity(self):
        return self._analysis_variables["min_velocity"], self._analysis_variables[
            "min_velocity_index"
        ] / self.acq_data.s_r_c

    def max_velocity(self):
        return self._analysis_variables["max_velocity"], self._analysis_variables[
            "max_velocity_index"
        ] / self.acq_data.s_r_c

    def acquisition(self) -> PlotOutput:
        return np.arange(
            self.acq_data.acquisition.size
        ) / self.acq_data.s_r_c, self.acq_data.acquisition

    def derivative(self) -> PlotOutput:
        return np.arange(
            self.acq_data.acquisition.size
        ) / self.acq_data.s_r_c, -1 * np.gradient(self.acq_data.acquisition)

    def data(self) -> tuple[dict, dict]:
        acq_data = self._analysis_variables.copy()
        spk_data = {}
        for param in SPIKE_PARAMS:
            value = acq_data.pop(param)
            spk_data[param] = value
        spk_data["spike_index"] = acq_data.pop("spike_index")
        spk_data["spike_mv"] = acq_data.pop("spike_mv")
        spk_data["spike_number"] = acq_data.pop("spike_number")
        spk_data["epoch"] = [self.acq_data.epoch] * value.size
        spk_data["acq_number"] = [self.acq_data.acq_number] * value.size
        spk_data["cycle"] = [self.acq_data.cycle] * value.size
        spk_data["pulse_amp_pa"] = [self.acq_data.pulse_amp] * value.size

        for key, value in spk_data.items():
            if "index" in key:
                spk_data[key] = value / self.acq_data.s_r_c

        for key, value in acq_data.items():
            if "index" in key:
                acq_data[key] = value / self.acq_data.s_r_c

        sag_fit_data = acq_data.pop("sag_fit")
        if sag_fit_data is not None:
            sag_fit_data = sag_fit_data.params._asdict()
            sag_fit_data = {f"sag_fit_{k}": v for k, v in sag_fit_data.items()}
            acq_data.update(sag_fit_data)

        acq_data["epoch"] = self.acq_data.epoch
        acq_data["acq_number"] = self.acq_data.acq_number
        acq_data["cycle"] = self.acq_data.cycle
        acq_data["pulse_amp_pa"] = self.acq_data.pulse_amp
        return acq_data, spk_data
