from dataclasses import dataclass
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
from ..base import BaseAcquisitionAnalysis, BaseEpochAnalysis
from ..registry import register_acquisition, register_epoch


@register_acquisition
class AcquisitionAnalysis(BaseAcquisitionAnalysis):
    @staticmethod
    def analysis_key():
        return "postsynaptic"

    def __init__(
        self,
        acq_data: AcquisitionData,
        template_params: TemplateParams,
        sensitivity: Union[int, float] = 4,
        amp_threshold: Union[int, float] = 4,
        mini_spacing: Union[int, float] = 2,
        min_rise_time: Union[int, float] = 0.5,
        max_rise_time: Union[int, float] = 4,
        min_decay_time: Union[int, float] = 0.5,
        event_length: Union[int, float] = 30,
        decay_rise: bool = True,
        invert: bool = False,
        method: EventMethods = "weiner",
        est_decay: bool = False,
        curve_fit_decay: Literal[0, 1, 2] = 0,
    ):
        self.acq_data = acq_data
        self.template_params = template_params
        self.sensitivity = sensitivity
        self.amp_threshold = amp_threshold
        self.mini_spacing = mini_spacing
        self.min_rise_time = min_rise_time
        self.max_rise_time = max_rise_time
        self.min_decay_time = min_decay_time
        self.event_length = event_length
        self.decay_rise = decay_rise
        self.invert: bool = invert
        self.method = method
        self.est_decay = est_decay
        self.curve_fit_decay = curve_fit_decay

        self._analysis_variables = {}
        self._analysis_variables["events"]: list[PostsynapticEvent] = []
        self._decon_filter = FIRFilter(
            order=351,
            high_pass=None,
            high_width=0,
            low_pass=300,
            low_width=100,
            window="hann",
        )

    @property
    def event_criteria(self) -> create_events.EventCriteria:
        return create_events.EventCriteria(
            mini_spacing=self.mini_spacing,
            amp_threshold=self.amp_threshold,
            min_rise_time=self.min_rise_time,
            max_rise_time=self.max_rise_time,
            min_decay_time=self.min_decay_time,
            decay_rise=self.decay_rise,
        )

    def analyze(self) -> None:
        acquisition = self.acq_data.acquisition

        if self.method == "template_match":
            output = template_match(acquisition, self.template_params)
        else:
            output = deconvolve_array(
                acquisition,
                self.acq_data.fs,
                self.template_params,
                self.method,
                self._decon_filter,
            )

        events = find_events(output, self.mini_spacing, self.sensitivity)
        size = acquisition.size
        event_peaks: list[int] = []
        postsynaptic_events: list[PostsynapticEvent] = []
        for peak in events:
            if (size - peak) >= (self.event_length * self.acq_data.s_r_c):
                event = PostsynapticEvent(
                    array=acquisition,
                    fs=self.acq_data.fs,
                    start_index=peak,
                    event_length=self.event_length,
                    curve_fit_type=self.curve_fit_decay,
                )
                event.find_peak()
                event_peak = event._analysis_variables["event_index"]

                # Screen out methods using the function.
                # See the function below for further details.
                if not np.isnan(event_peak) or event_peak not in event_peaks:
                    event_peaks.append(event_peak)
                    postsynaptic_events += [event]

        for event in postsynaptic_events:
            event.find_baseline()
            event.estimate_decay()

        for index, event in enumerate(postsynaptic_events):
            if index < len(postsynaptic_events) and index > 0:
                event.curve_fit_decay(
                    self.curve_fit_decay,
                    event[index + 1]._analysis_variables["baseline_index"],
                )
            else:
                event.curve_fit_decay(self.curve_fit_decay)
