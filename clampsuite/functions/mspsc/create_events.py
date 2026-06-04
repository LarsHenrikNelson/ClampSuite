from typing import Literal, NamedTuple

import numpy as np

from ...loader.acquisition_data import AcquisitionData
from .event import PostsynapticEvent


class EventCriteria(NamedTuple):
    mini_spacing: float | int
    amp_threshold: float | int
    min_rise_time: float | int
    max_rise_time: float | int
    min_decay_time: float | int
    decay_rise: float | int


def check_event(
    event: PostsynapticEvent,
    previous_event: PostsynapticEvent | None,
    event_criteria: EventCriteria,
) -> bool:
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
    if previous_event is None:
        prior_peak = 0
    else:
        prior_peak = previous_event["peak_index"] / (previous_event.fs / 1000)

    # Retrieve the peak to compare to values set
    # by the experimenter.
    event_peak = event["peak_index"] / (event.fs / 1000)

    # The function checks, in order of importance, the
    # qualities of the event.
    event_start = event["start_index"] / (event.fs / 1000)
    if (
        (event_peak - prior_peak) < event_criteria.mini_spacing
        or event.amplitude() <= event_criteria.amp_threshold
        or event.rise_time() <= event_criteria.min_rise_time
        or event.rise_time() >= event_criteria.max_rise_time
        or event.est_tau() <= event_criteria.min_decay_time
        or event.est_tau() < 0
        or event_start > event_peak
    ):
        return False
    elif event_criteria.decay_rise and event.est_tau() <= event.rise_time():
        return False
    else:
        return True


def create_events(
    events: list | np.ndarray,
    event_length: float,
    array: np.ndarray,
    fs: float | int,
    event_criteria: EventCriteria,
    curve_fit_type: Literal[0, 1, 2] = 0,
) -> list[PostsynapticEvent]:
    """This functions creates the events based on the list of peaks found
    from the deconvolution. Events less than 20 ms before the end of
    the acquisitions are not counted. Events get screened out based on
    the experimenters settings.
    """
    # Create the lists to store values need for analysis.
    postsynaptic_events = []
    event_peaks = []

    # The for loop won't run if there are no events.
    # So there is no need to catch instances when
    # there are no events.

    size = len(array)
    s_r_c = fs / 1000

    for peak in events:
        if size - peak < 20 * s_r_c:
            pass
        else:
            # Create the mini class then analyze.
            try:
                event = PostsynapticEvent(
                    array=array,
                    fs=fs,
                    start_index=peak,
                    event_length=event_length,
                )
                event.find_peak()
                event_peak = event._analysis_variables["event_index"]

                # Screen out methods using the function.
                # See the function below for further details.
                if not np.isnan(event_peak) or event_peak not in event_peaks:
                    event_peaks.append(event_peak)
                    postsynaptic_events += [event]
            except Exception:
                pass
    return postsynaptic_events
