from ...acq import MiniEvent

def create_events(events):
        """This functions creates the events based on the list of peaks found
        from the deconvolution. Events less than 20 ms before the end of
        the acquisitions are not counted. Events get screened out based on
        the experimenters settings.
        """
        # Create the lists to store values need for analysis.
        self.postsynaptic_events = []
        self.final_events = []
        event_number = 0
        event_time = []

        # The for loop won't run if there are no events.
        # So there is no need to catch instances when
        # there are no events.

        for peak in events:
            if len(self.final_array) - peak < 20 * self.s_r_c:
                pass
            else:
                # Create the mini class then analyze.
                try:
                    event = MiniEvent()
                    event.analyze(
                        acq_number=self.acq_number,
                        event_pos=peak,
                        y_array=self.final_array,
                        event_length=self.event_length,
                        sample_rate=self.sample_rate,
                        curve_fit_decay=self.curve_fit_decay,
                        curve_fit_type=self.curve_fit_type,
                    )

                    # Screen out methods using the function.
                    # See the function below for further details.
                    if self.check_event(event, event_time):
                        self.postsynaptic_events += [event]
                        self.final_events += [peak]
                        event_time += [event.event_peak_x()]
                        event_number += 1
                except Exception:
                    pass