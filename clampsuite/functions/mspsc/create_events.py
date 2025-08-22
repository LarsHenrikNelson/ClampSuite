from typing import Literal

import numpy as np

from ...acq import MiniEvent
from ...loader.acquisition_data import AcquisitionData


def check_event(event: MiniEvent, events: list, event_criteria: dict) -> bool:
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
            event_peak - prior_peak < event_criteria["mini_spacing"]
            or event.amplitude <= event_criteria["amp_threshold"]
            or event.rise_time <= event_criteria["min_rise_time"]
            or event.rise_time >= event_criteria["max_rise_time"]
            or event.final_tau_x <= event_criteria["min_decay_time"]
            or event.event_start_x() > event_peak
        ):
            return False
        elif event_criteria["decay_rise"] and event.final_tau_x <= event.rise_time:
            return False
        else:
            return True

def create_events(events: list[int], event_length: float, acq: AcquisitionData, curve_fit_type: Literal["none", "s_exp", "d_exp"] = "None"):
        """This functions creates the events based on the list of peaks found
        from the deconvolution. Events less than 20 ms before the end of
        the acquisitions are not counted. Events get screened out based on
        the experimenters settings.
        """
        # Create the lists to store values need for analysis.
        postsynaptic_events = []
        final_events = []
        event_number = 0
        event_time = []

        # The for loop won't run if there are no events.
        # So there is no need to catch instances when
        # there are no events.
        
        size = len(acq.array)

        for peak in events:
            if size - peak < 20 * acq.s_r_c:
                pass
            else:
                # Create the mini class then analyze.
                try:
                    event = MiniEvent()
                    event.analyze(
                        acq_number=acq.acq_number,
                        event_pos=peak,
                        array=acq.array,
                        event_length=event_length,
                        sample_rate=acq.fs,
                        curve_fit_type=curve_fit_type,
                    )

                    # Screen out methods using the function.
                    # See the function below for further details.
                    if check_event(event, event_time):
                        postsynaptic_events += [event]
                        final_events += [peak]
                        event_time += [event.event_peak_x()]
                        event_number += 1
                except Exception:
                    pass