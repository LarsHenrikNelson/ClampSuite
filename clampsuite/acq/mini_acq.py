from typing import Literal, Union

import numpy as np

from ..functions.filtering_functions import FIRFilter
from ..functions.mspsc import (
    EventMethods,
    deconvolve_array,
    find_events,
    template_match,
)
from ..functions.rc_check import calc_rs
from ..functions.template_psc import TemplateParams
from ..loader.acquisition_data import AcquisitionData
from .postsynaptic_event import MiniEvent


class MiniAnalysisAcq:
    def __init__(self, acq_data: AcquisitionData):
        self.acq_data = acq_data

    def analyze(
        self,
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
        method: EventMethods = "wiener",
        curve_fit_decay: bool = False,
        curve_fit_type: Literal["s_exp", "db_exp"] = "s_exp",
        baseline_corr: bool = False,
        deconvolve_filter: FIRFilter | None = None,
    ):
        # Set the attributes for the acquisition
        self.sensitivity = sensitivity
        self.amp_threshold = amp_threshold
        self.mini_spacing = mini_spacing
        self.min_rise_time = min_rise_time
        self.max_rise_time = max_rise_time
        self.min_decay_time = min_decay_time
        self.event_length = event_length
        self.decay_rise = decay_rise
        self.invert = invert
        self.curve_fit_decay = curve_fit_decay
        self.method = method
        self.curve_fit_type = curve_fit_type
        self.deleted_events = 0
        self.baseline_corr = baseline_corr
        self.template_params = template_params

        if deconvolve_filter is None:
            self.deconvolve_filter = FIRFilter(
                filter_type="fir",
                order=351,
                high_pass=None,
                high_width=None,
                low_pass=300,
                low_width=100,
                window="hann",
                fs=self.acq_data.fs,
            )
        else:
            self.deconvolve_filter = deconvolve_filter

        if method == "template_match":
            output = template_match(self.acq_data.array, template_params)
        else:
            output = deconvolve_array(self.acq_data.array, template_params, method, self.deconvolve_filter)

        events = find_events(output, self.mini_spacing, self.sensitivity)

    def create_mespc_array(self):
        """The function creates the mEPSC array by removing the RC
        check if there is one. The functions runs before the array
        is filtered.
        """
        if not self.rc_check:
            temp_array = self.array
            # self.rc_check_array = np.array([])
        elif self.rc_check:
            if self._rc_check_end == len(self.array):
                temp_array = np.copy(self.array[: self._rc_check_start])
                # self.rc_check_array = np.copy(self.array[self._rc_check_start :])
            else:
                temp_array = np.copy(self.array[self._rc_check_end :])
                # self.rc_check_array = np.copy(self.array[self._rc_check_end :])
        self.filter_array(temp_array)

    def get_rc_check(self):
        rc_check_array = self.array[self._rc_check_start : self._rc_check_end]
        return rc_check_array

    def set_array(self):
        """Used to reduce the memory load of the class
        since the filtered array is not needed.
        """
        self.final_array = self.filtered_array
        del self.filtered_array

    def set_sign(self):
        """Changes the sign of an array if the events are outward
        (i.e. positive) events.
        """
        if not self.invert:
            self.final_array = self.final_array * 1
        else:
            self.final_array = self.final_array * -1

    def analyze_rc_check(self):
        if self.rc_check:
            rc_check_array = self.get_rc_check()
            self.rs = calc_rs(
                rc_check_array,
                int(self._rc_check_pulse_start - self._rc_check_start),
                int(self._rc_check_pulse_end - self._rc_check_pulse_start),
                self.rc_amp,
            )
        else:
            self.rs = 0.0

    def plot_deconvolved_acq(self):
        deconvolved_array = self.create_deconvolved_array()
        mu, rms = self.deconvolved_rms(deconvolved_array)
        baseline = np.full(deconvolved_array.size, self.sensitivity * rms)
        return (deconvolved_array - mu), baseline


    def check_event(self, event: MiniEvent, events: list) -> bool:
        """The function is used to screen out events based
        on several values set by the experimenter.

        Args:
            event (MiniEvent): An analyzed MiniEvent
            events (list): List of previous events

        Returns:
            Bool: Boolean value can be used to determine if
            the event qualifies for inclusion in final events.
        """

        # Retrieve the peak of the previous event.
        if len(events) > 0:
            prior_peak = events[-1]
        else:
            prior_peak = 0

        # Retrieve the peak to compare to values set
        # by the experimenter.
        event_peak = event.event_peak_x()

        # The function checks, in order of importance, the
        # qualities of the event.
        if np.isnan(event_peak) or event_peak in events:
            return False
        elif (
            event_peak - prior_peak < self.mini_spacing
            or event.amplitude <= self.amp_threshold
            or event.rise_time <= self.min_rise_time
            or event.rise_time >= self.max_rise_time
            or event.final_tau_x <= self.min_decay_time
            or event.event_start_x() > event_peak
        ):
            return False
        elif self.decay_rise and event.final_tau_x <= event.rise_time:
            return False
        else:
            return True

    def create_new_event(self, x: Union[int, float]) -> bool:
        """Creates a new mini event based on the time
        of the event passed to the function. The new
        event is not screened like the automatically
        created events since creating new events is up
        to the discresion of the experimenter.

        Args:
            x (float): Time of event

        Returns:
            Bool: The return value is used to determine
            whether the event is valid.
        """
        # Convert from time to samples simce most people
        # will likely think in time and not samples.
        x = int(x * self.s_r_c)

        # Create new event instance and analyzed.
        event = MiniEvent()
        event.analyze(
            acq_number=self.acq_number,
            event_pos=x,
            y_array=self.final_array,
            event_length=self.event_length,
            sample_rate=self.sample_rate,
            curve_fit_decay=self.curve_fit_decay,
            curve_fit_type=self.curve_fit_type,
        )
        if not np.isnan(event.event_peak_x()):
            self.final_events += [x]
            self.postsynaptic_events += [event]
            return True
        else:
            return False

    def acq_data(self) -> dict:
        """
        Creates the final data using list comprehension by looping over each
        of the minis in contained in the postsynaptic event list.
        """
        final_dict = {}

        # Sort postsynaptic events before calculating the final results. This
        # is because of how the user interface works and facilates commandline
        # usage of the program. Essentially it is easier to just add new minis
        # to the end of the postsynaptic event list. This prevents a bunch of
        # issues since you cannot modify the position of plot elements in the
        # pyqtgraph data items list.

        if self.postsynaptic_events:
            self.postsynaptic_events.sort(key=lambda x: x._event_peak_x)
            self.final_events.sort()
            final_dict["Acquisition"] = [i.acq_number for i in self.postsynaptic_events]
            final_dict["Amplitude (pA)"] = [
                i.amplitude for i in self.postsynaptic_events
            ]
            final_dict["Est tau (ms)"] = [
                i.final_tau_x for i in self.postsynaptic_events
            ]
            final_dict["Event time (ms)"] = [
                i.event_peak_x() for i in self.postsynaptic_events
            ]
            final_dict["Acq time stamp"] = [
                self.time_stamp for i in self.postsynaptic_events
            ]
            final_dict["Voltage offset (mV)"] = [
                self.offset for i in self.postsynaptic_events
            ]
            final_dict["Rs (MOhm)"] = [self.rs for i in self.postsynaptic_events]
            final_dict["Rise time (ms)"] = [
                i.rise_time for i in self.postsynaptic_events
            ]
            final_dict["Rise rate (pA/ms)"] = [
                i.rise_rate for i in self.postsynaptic_events
            ]
            if self.curve_fit_decay:
                final_dict["Curve fit tau (ms)"] = [
                    i.fit_tau for i in self.postsynaptic_events
                ]

            final_dict["IEI (ms)"] = np.append(
                np.diff(final_dict["Event time (ms)"]), np.nan
            )
            self.freq = len(final_dict["Amplitude (pA)"]) / (
                len(self.final_array) / self.sample_rate
            )
        else:
            final_dict["Acquisition"] = [np.nan]
            final_dict["Amplitude (pA)"] = [np.nan]
            final_dict["Log amplitude (pA)"] = [np.nan]
            final_dict["Est tau (ms)"] = [np.nan]
            final_dict["Event time (ms)"] = [np.nan]
            final_dict["Acq time stamp"] = [np.nan]
            final_dict["Rise time (ms)"] = [np.nan]
            final_dict["Rise rate (pA/ms)"] = [np.nan]
            if self.curve_fit_decay:
                final_dict["Curve fit tau (ms)"] = [np.nan]

            final_dict["IEI (ms)"] = [np.nan]
            final_dict["Log IEI (ms)"] = [np.nan]
            self.freq = np.nan
        return final_dict

    def get_event_arrays(self) -> list:
        events = [i.event_array - i.event_start_y for i in self.postsynaptic_events]
        return events

    def peak_values(self) -> list:
        peak_align_values = [i.peak_align_value for i in self.postsynaptic_events]
        return peak_align_values

    def total_events(self) -> list:
        return len([i.amplitude for i in self.postsynaptic_events])

    def save_postsynaptic_events(self):
        """
        This helper function is called when you want to save the file. This
        makes the size of the file smaller so it is of more managable size.
        All the data that is need to recreate the minis is saved.

        Returns
        -------
        None.

        """
        self.saved_events_dict = []
        for i in self.postsynaptic_events:
            i.event_array = "saved"
            self.saved_events_dict += [i.__dict__]
        self.postsynaptic_events = "saved"

    def create_postsynaptic_events(self):
        """This function is used to create postsynaptic events from a
        saved JSON file since mini events are load as a dictionary.
        """
        self.postsynaptic_events = []
        for i in self.saved_events_dict:
            h = MiniEvent()
            h.load_event(event_dict=i, final_array=self.final_array)
            self.postsynaptic_events += [h]

    def del_postsynaptic_event(self, index: int):
        del self.postsynaptic_events[index]
        del self.final_events[index]
        self.deleted_events += 1

    def sort_index(self):
        return list(np.argsort(self.final_events))

    def list_of_events(self) -> list:
        return list(range(len(self.postsynaptic_events)))

    def plot_acq_y(self) -> np.ndarray:
        if hasattr(self, "final_array"):
            return self.final_array
        else:
            return self.array

    def plot_acq_x(self) -> np.ndarray:
        if hasattr(self, "final_array"):
            return np.arange(0, len(self.final_array)) / self.s_r_c
        else:
            return np.arange(0, len(self.array)) / self.s_r_c
