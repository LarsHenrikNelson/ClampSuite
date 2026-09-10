from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import numpy as np
from fontTools.misc.bezierTools import curveCurveIntersections
from scipy import signal

from clampsuite.types import CurrentClamp

from ...functions.current_clamp import (
    SPIKE_PARAMS,
    Spike,
    ThresholdType,
    adaptation_index,
    ai_sfa,
    coefficient_of_variation,
    divisor_sfa,
    local_sfa,
    membrane_time_constant_deltav,
    membrane_time_constant_min,
    voltage_sag,
)
from ...functions.curve_fit import DExpDecay, SExpDecay
from ...functions.general import baseline_stability, delta
from ...functions.utilities import map_keys
from ...loader import AcquisitionData
from ..base import BaseAcquisitionAnalysis, BaseAcquisitionConfig
from ..registry import register_acq_config, register_acquisition

PlotOutput = tuple[np.ndarray, np.ndarray]


@register_acq_config
@dataclass(frozen=True)
class CurrentClampAcquisitionConfig(BaseAcquisitionConfig):
    """Configuration class for current clamp acquisition analysis.

    Attributes:
        min_spike_voltage: Minimum voltage a spike needs to reach
            to be considered a spike.
        threshold_method: Method used to find the spike threshold.
            min_spikes: The minimum number of spikes an acquisition must have to be
        considered a "spiking acquisition".
            velocity_threshold: The velocity in mV/ms a spike needs to achieve to be
        considered a spike.
            fit_sag_decay: An integer indicating what type of exponential decay to fit to
        the voltage sag decay. Use 0 if you do not want to fit a decay.
            fraction_window: A tuple containing the start and end *fraction** of the '
            pulse injection that you want to get the delta V from. `start=0.5` and
            `end=1.0` with a pulse of 1 ms will go from 0.5 ms to 1 ms.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "current_clamp"

    min_spike_voltage: float = 0
    threshold_method: ThresholdType = "third_derivative"
    min_spikes: int = 1
    velocity_threshold: float = 0.0
    fit_sag_decay: Literal[0, 1, 2] = 0
    fraction_window: tuple[float, float] = (0.5, 1.0)


@register_acquisition
@dataclass
class CurrentClampAcquisition(BaseAcquisitionAnalysis):
    """Current clamp acquisition analysis class

    Attributes:
        acq_data: Raw acquisition data and metadata (inherited from
            ``BaseAcquisitionAnalysis``), including pulse timing and
            sampling rate.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "current_clamp"

    def __post_init__(self):
        pulse_start = self.acq_data.pulse_start_index
        pulse_end = self.acq_data.pulse_end_index
        self._pulse_end = pulse_end
        self._pulse_start = pulse_start

        self._analysis_variables["baseline_mv"] = np.nan
        self._analysis_variables["delta_v_mv"] = np.nan
        self._analysis_variables["delta_v_index"] = np.nan
        self._analysis_variables["freq_hz"] = 0.0
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

        # for i in SPIKE_PARAMS:
        #     self._analysis_variables[i] = np.array([])
        self._spikes = []

    def analyze(self, config: CurrentClampAcquisitionConfig | None) -> None:
        """Analyzes the ``AcquisitionData``.

        Args:
            config: Analysis configuration. Default parameters for the config if passed
                as ``None`` are min_spike_voltage=0,
                threshold_method="third_derivative", min_spikes=1,
                velocity_threshold=0.0, fit_sag_decay=0, fraction_window=(0.5,1.0).
        """
        if config is None:
            config = CurrentClampAcquisitionConfig()
        # Analysis functions
        acquisition = self.acq_data.acquisition
        self["baseline_mv"] = np.mean(acquisition[: self._pulse_start])

        spike_list = self._create_spikes(acquisition, config)
        self._spikes = self._analyze_spikes(spike_list, config.threshold_method)

        self["freq_hz"] = len(self._spikes) / (
            (self._pulse_end - self._pulse_start) / self.acq_data.fs
        )

        spike_times = (
            np.array([i["peak_index"] for i in self._spikes]) / self.acq_data.fs
        )
        self["local_sfa"] = local_sfa(spike_times)
        self["divisor_sfa"] = divisor_sfa(spike_times)
        self["ai_sfa"] = ai_sfa(spike_times)
        self["adaptation"] = adaptation_index(spike_times)
        self["coefficient_of_variation"] = coefficient_of_variation(spike_times)

        delta_v_index, delta_v_mv = self.get_delta_v(
            acquisition, self._spikes, config.fraction_window
        )
        self["delta_v_mv"] = delta_v_mv
        self["delta_v_index"] = delta_v_index

        if self.acq_data.pulse_amp < 0:
            self._analysis_variables.update(
                voltage_sag(acquisition, self._pulse_start, self._pulse_end)
            )
            if config.fit_sag_decay > 0:
                index = self._analysis_variables["sag_index"]
                x_temp = np.arange(0, self._pulse_end - index) / self.acq_data.s_r_c
                if config.fit_sag_decay == 1:
                    temp_output = SExpDecay()

                else:
                    temp_output = DExpDecay()
                temp_output.fit(x_temp, acquisition[index : self._pulse_end])
                self._analysis_variables["sag_fit"] = temp_output

        if self._analysis_variables["delta_v_mv"] < 0 and self.acq_data.pulse_amp < 0:
            self._analysis_variables["mem_tau_deltav_index"] = (
                membrane_time_constant_deltav(
                    acquisition,
                    self._analysis_variables["delta_v_mv"],
                    self._pulse_start,
                )
            )
            self._analysis_variables["mem_tau_min_index"] = membrane_time_constant_min(
                acquisition,
                self._pulse_start,
            )

        self._analysis_variables["baseline_stability"] = baseline_stability(
            acquisition, self._pulse_start, self._pulse_end
        )

        rebound_spikes, _ = signal.find_peaks(
            acquisition[self._pulse_end :],
            height=config.min_spike_voltage,
            prominence=int(1 * self.acq_data.s_r_c),
        )
        if len(rebound_spikes) > 0:
            self._analysis_variables["rebound_spike"] = len(rebound_spikes)
            self._analysis_variables["rebound_spike_start_index"] = (
                rebound_spikes[0] + self._pulse_end
            )

    def _create_spikes(self, acquisition, config):
        spike_index, _ = signal.find_peaks(
            acquisition[self._pulse_start : self._pulse_end],
            height=config.min_spike_voltage,
            distance=int(2 * (self.acq_data.fs / 1000)),
            prominence=2,
        )

        spike_index += self._pulse_start
        spike_list = []
        end = len(spike_index) - 1
        for index, i in enumerate(spike_index):
            if len(spike_index) == 1:
                start_index = int((i - self._pulse_start) * 0.1) + self._pulse_start
                end_index = self._pulse_end
            elif index == 0:
                start_index = int((i - self._pulse_start) * 0.1) + self._pulse_start
                end_index = spike_index[index + 1]
            elif index == end:
                end_index = self._pulse_end
                start_index = spike_index[index - 1]
            else:
                start_index = spike_index[index - 1]
                end_index = spike_index[index + 1]
            spike = Spike(
                self.acq_data.acquisition, start_index, end_index, i, self.acq_data.fs
            )
            spike.find_threshold("percentage")
            spike.find_velocity()
            if len(spike_list) > 0:
                spike_list[-1].set_end_index(spike["threshold_index"])
            if spike["max_velocity_mv/ms"] > config.velocity_threshold:
                spike_list.append(spike)
        return spike_list

    def _analyze_spikes(self, spike_list: list[Spike], threshold_method: ThresholdType):
        for spike in spike_list:
            if threshold_method == "allen_institute":
                thresholds = [i["max_velocity_mv/ms"] for i in spike_list]
                spike.analyze(threshold_method, np.mean(thresholds) * 0.05)
            else:
                spike.analyze(threshold_method)
        return spike_list

    def get_delta_v(
        self,
        acquisition: np.ndarray,
        peaks: np.ndarray | list,
        fraction_window: tuple[float, float],
    ) -> tuple[int, float]:
        """This function finds the delta-v for a pulse. It simply takes the mean
        value from the pulse start to end for pulses without spikes. For
        pulses with spikes it takes the mode of the moving mean.

        Args:
            acquisition (np.ndarray): _description_
            peaks (np.ndarray | list): _description_
            fraction_window (tuple[float, float]): _description_

        Returns:
            tuple[int, float]: _description_
        """
        if len(peaks) == 0:
            delta_v_index, delta_v = delta(
                acquisition, self._pulse_start, self._pulse_end, fraction_window
            )
        else:
            delta_v_index = self._spikes[0]["threshold_index"]
            delta_v = acquisition[delta_v_index] - self["baseline_mv"]
        return delta_v_index, delta_v

    def spike_half_widths(self) -> tuple[np.ndarray, np.ndarray]:
        """Get x/y coordinates for plotting spike half-width markers.

        Returns:
            tuple:

            - ``x``: Array of shape ``(2, n)`` giving the left and right
            half-width times (s) for each of the ``n`` spikes, one
            column per spike (row 0 = left edge, row 1 = right edge).
            - ``y``: Array of shape ``(2, n)`` giving the voltage (mV) at
            the half-width, duplicated across both rows so the pair can
            be plotted as a horizontal line.
        """
        x = (
            np.array([[i["hw_left_index"], i["hw_right_index"]] for i in self._spikes])
            / self.acq_data.s_r_c
        ).T
        y = np.array([[i["hw_mv"], i["hw_mv"]] for i in self._spikes]).T
        return x, y

    def spike_widths(self):
        """Get x/y coordinates for plotting spike width markers.

        Returns:
            tuple:

            - ``x``: Array of shape ``(2, n)`` giving the left and right
            width times (s) for each of the ``n`` spikes, one
            column per spike (row 0 = left edge, row 1 = right edge).
            - ``y``: Array of shape ``(2, n)`` giving the voltage (mV) at
            the width, duplicated across both rows so the pair can
            be plotted as a horizontal line.
        """
        x = (
            np.array([[i["fw_left_index"], i["fw_right_index"]] for i in self._spikes])
            / self.acq_data.s_r_c
        ).T
        y = np.array([[i["fw_mv"], i["fw_mv"]] for i in self._spikes]).T
        return x, y

    def _get_spike_data(self, key1: str, key2: str | None = None) -> PlotOutput:
        x = np.array([i[key1] for i in self._spikes])
        if len(x) > 0:
            if key2 is None:
                y = self.acq_data.acquisition[x]
            else:
                y = np.array([i[key2] for i in self._spikes])
        else:
            y = np.array([])
        return x / self.acq_data.s_r_c, y

    def peaks(self) -> PlotOutput:
        """Get x/y coordinates for plotting spike peak markers.

        Returns:
            A tuple ``(x, y)`` where:

            - ``x``: Array of shape ``(1,n)`` giving the peak time in ms for each spike.
            - ``y``: Array of shape ``(1,n)`` giving the peak voltage in mV for each
            spike.
        """
        return self._get_spike_data("peak_index")

    def ahps(self) -> PlotOutput:
        """Get x/y coordinates for plotting spike AHP markers.

        Returns:
            A tuple ``(x, y)`` where:
            - ``x``: Array of shape ``(1,n)`` giving the AHP time in ms for each spike.
            - ``y``: Array of shape ``(1,n)`` giving the AHP voltage in mV for each
            spike.
        """
        return self._get_spike_data("ahp_index")

    def thresholds(self) -> PlotOutput:
        return self._get_spike_data("threshold_index")

    def sag(self) -> PlotOutput:
        """Get x/y coordinates for plotting the acquisition voltage sag size. The line
        goes from the steady state to the sag level. The line is centered at the
        maximum voltage sag.

        Returns:
            A tuple ``(x, y)`` where:
            - ``x``: Array of shape ``(1,n)`` giving the voltage sag time in ms.
            - ``y``: Array of shape ``(1,n)`` giving the voltage sag in mV.
        """
        sag = self["sag_mv"]
        x = self["sag_index"] / self.acq_data.s_r_c
        delta = self["baseline_mv"] + self["delta_v_mv"]
        y = np.array([delta, delta + sag])
        x = np.array([x, x])
        return x, y

    def sag_decay(self) -> PlotOutput:
        """Get x/y arrays for plotting the acquisition sag decay.

        Returns:
            A tuple ``(x, y)`` where:
            - ``x``: Array of shape ``(1,n)`` giving the voltage sag time in ms.
            - ``y``: Array of shape ``(1,n)`` giving the voltage sag in mV.
        """
        if self["sag_fit"] is not None:
            start = self["sag_index"]
            fit_object = self["sag_fit"]
            end = self._pulse_end
            x = np.arange(0, end - start)
            y = fit_object.predict(x / self.acq_data.s_r_c)
            x = (x + start) / self.acq_data.s_r_c
        else:
            x = np.array([])
            y = np.array([])
        return x, y

    def delta_v(self) -> PlotOutput:
        """Get x/y coordinates for plotting the acquisition delta V size. The line
        goes from the baseline to the steady state. The line is centered start of the
        steady state.

        Returns:
            A tuple ``(x, y)`` where:
            - ``x``: Array of shape ``(1,n)`` giving the voltage sag time in ms.
            - ``y``: Array of shape ``(1,n)`` giving the voltage sag in mV.
        """
        b = self["baseline_mv"]
        delta = self["delta_v_mv"]
        delta_index = self["delta_v_index"]
        y = np.array([b, b + delta])
        x = np.array([delta_index, delta_index]) / self.acq_data.s_r_c
        return x, y

    def min_velocity(self):
        return self._get_spike_data("min_velocity_mv/ms", "min_velocity_index")

    def max_velocity(self):
        return self._get_spike_data("max_velocity_mv/ms", "max_velocity_index")

    def acquisition(self) -> PlotOutput:
        return np.arange(
            self.acq_data.acquisition.size
        ) / self.acq_data.s_r_c, self.acq_data.acquisition

    def derivative(self) -> PlotOutput:
        return np.arange(
            self.acq_data.acquisition.size
        ) / self.acq_data.s_r_c, -1 * np.gradient(self.acq_data.acquisition)

    def data(
        self, output_type: Literal["ms", "samples"] = "ms", format_keys: bool = False
    ) -> tuple[dict, dict]:
        acq_data = self._analysis_variables.copy()
        spk_data = defaultdict(list)
        for spike in self._spikes:
            sdata = spike.data()
            for key, value in sdata.items():
                spk_data[key].append(value)
        n_spikes = len(self._spikes)
        spk_data = {key: np.array(value) for key, value in spk_data.items()}
        spk_data["spike_number"] = np.arange(n_spikes)
        spk_data["epoch"] = np.array([self.acq_data.epoch] * n_spikes)
        spk_data["acq_number"] = np.array([self.acq_data.acq_number] * n_spikes)
        spk_data["cycle"] = np.array([self.acq_data.cycle] * n_spikes)
        spk_data["pulse_amp_pa"] = np.array([self.acq_data.pulse_amp] * n_spikes)

        if output_type == "ms":
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

        if format_keys:
            key_mapper = map_keys(acq_data.keys())
            acq_data = {key_mapper[k]: v for k, v in acq_data.items()}
            key_mapper = map_keys(spk_data.keys())
            spk_data = {key_mapper[k]: v for k, v in spk_data.items()}
        return acq_data, spk_data
