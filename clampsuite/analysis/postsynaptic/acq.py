from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Literal, Union

import numpy as np
import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.curve_fit import Log, Sigmoid, fit_iv
from ...functions.mspsc import (
    EventMethods,
    PostsynapticEvent,
    create_events,
    deconvolve_array,
    find_events,
    template_match,
)
from ...functions.template_psc import TemplateParams
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ...preprocess.filter import FIRFilter
from ..base import BaseAcquisitionAnalysis, BaseAcquisitionConfig
from ..registry import register_acq_config, register_acquisition


@register_acq_config
@dataclass(frozen=True)
class PostSynapticAcquisitionConfig(BaseAcquisitionConfig):
    @staticmethod
    def analysis_key() -> str:
        return "psc"

    template_params: TemplateParams = field(default_factory=TemplateParams)
    sensitivity: int | float = 4
    amp_threshold: int | float = 4
    mini_spacing: int | float = 2
    min_rise_time: int | float = 0.5
    max_rise_time: int | float = 4
    min_decay_time: int | float = 0.5
    event_length: int | float = 30
    decay_rise: bool = True
    invert: bool = False
    method: EventMethods = "weiner"
    est_decay: bool = False
    curve_fit_decay: Literal[0, 1, 2] = 0


@register_acquisition
@dataclass
class PostSynapticAcquisition(BaseAcquisitionAnalysis):
    @staticmethod
    def analysis_key():
        return "psc"

    def __post_init__(self):
        events: list[PostsynapticEvent] = []
        self._events = events
        self._decon_filter = FIRFilter(
            order=351,
            high_pass=None,
            high_width=0,
            low_pass=300,
            low_width=100,
            window="hann",
        )

    def analyze(self, config: PostSynapticAcquisitionConfig | None) -> None:
        if config is None:
            config = PostSynapticAcquisitionConfig()

        acquisition = self.acq_data.acquisition

        if config.method == "template_match":
            output = template_match(acquisition, config.template_params)
        else:
            output = deconvolve_array(
                acquisition,
                self.acq_data.fs,
                config.template_params,
                config.method,
                self._decon_filter,
            )

        events = find_events(
            output, config.mini_spacing, config.sensitivity, self.acq_data.fs
        )
        size = acquisition.size
        event_peaks: list[int | float] = []
        postsynaptic_events: list[PostsynapticEvent] = []
        for peak in events:
            if (size - peak) >= (config.event_length * self.acq_data.s_r_c):
                event = PostsynapticEvent(
                    array=acquisition,
                    fs=self.acq_data.fs,
                    start_index=peak,
                    event_length=config.event_length,
                )
                event.find_peak()
                event_peak: int | float = event._analysis_variables["peak_index"]

                # Screen out methods using the function.
                # See the function below for further details.
                if not np.isnan(event_peak) or event_peak not in event_peaks:
                    event_peaks.append(event_peak)
                    postsynaptic_events += [event]

        for event in postsynaptic_events:
            event.analyze()

        criteria = create_events.EventCriteria(
            config.mini_spacing,
            config.amp_threshold,
            config.min_rise_time,
            config.max_rise_time,
            config.min_decay_time,
            config.decay_rise,
        )
        cleaned_events: list[PostsynapticEvent] = []
        for index, event in enumerate(postsynaptic_events):
            if index > 0:
                check = create_events.check_event(
                    event, postsynaptic_events[index - 1], criteria
                )
            else:
                check = create_events.check_event(event, None, criteria)
            if check:
                cleaned_events.append(event)
        postsynaptic_events: list[PostsynapticEvent] = cleaned_events

        end_index = len(postsynaptic_events) - 1
        for index, event in enumerate(postsynaptic_events):
            if index < end_index and index > 0:
                event.curve_fit_decay(
                    config.curve_fit_decay,
                    postsynaptic_events[index + 1]["baseline_index"],
                )
            else:
                event.curve_fit_decay(config.curve_fit_decay, None)
        self._events = postsynaptic_events
    
    def events(self)-> tuple[np.ndarray, np.ndarray]:
        y = []
        x = []
        for event in self._events:
            x_, y_ = event.event()
            y.append(y_)
            x.append(x_)
        return np.array(x), np.array(y)

    def data(
        self, output_type: Literal["ms", "samples"] = "ms", format_keys: bool = False
    ):
        acq_data = {}
        event_data = defaultdict(list)
        for event in self._events:
            sdata = event.data(output_type=output_type)
            for key, value in sdata.items():
                event_data[key].append(value)
        event_data = {key: np.array(value) for key, value in event_data.items()}
        for i in ["est_tau_ms", "rise_time_ms", "amplitude_pa", "rise_rate_pa_ms"]:
            temp = event_data[i][(event_data[i] > 0) & ~np.isnan(event_data[i])]
            acq_data[i] = np.mean(temp)
            acq_data[f"{i}_log"] = np.exp(np.mean(np.log(temp)))
        return acq_data, event_data
