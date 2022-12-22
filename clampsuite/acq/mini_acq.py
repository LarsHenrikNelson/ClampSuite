from typing import Union, Literal

import numpy as np
from scipy.fft import fft, ifft
from scipy import signal, interpolate

from . import filter_acq
from .postsynaptic_event import MiniEvent
from ..functions.template_psc import create_template
from ..functions.filtering_functions import fir_zero_1


class MiniAnalysisAcq(filter_acq.FilterAcq, analysis="mini"):
    def analyze(
        self,
        baseline_start: Union[int, float] = 0,
        baseline_end: Union[int, float] = 80,
        filter_type: Literal[
            "remez_2",
            "remez_1",
            "fir_zero_2",
            "fir_zero_1",
            "ewma",
            "ewma_a",
            "savgol",
            "median",
            "bessel",
            "butterworth",
            "bessel_zero",
            "butterworth_zero",
            "None",
        ] = "fir_zero_2",
        order: int = 201,
        high_pass: Union[int, float] = None,
        high_width: Union[int, float] = None,
        low_pass: Union[int, float] = 600,
        low_width: Union[int, float] = 300,
        window: Literal[
            "hann",
            "hamming",
            "blackmanharris",
            "barthann",
            "nuttall",
            "blackman",
            "tukey",
            "kaiser",
            "gaussian",
            "parzen",
            "exponential",
        ] = "hann",
        polyorder: Union[str, None] = None,
        rc_check: bool = True,
        rc_check_start: Union[int, float] = 10000,
        rc_check_end: Union[int, float] = 10300,
        sensitivity: Union[int, float] = 4,
        amp_threshold: Union[int, float] = 4,
        mini_spacing: Union[int, float] = 2,
        min_rise_time: Union[int, float] = 0.5,
        max_rise_time: Union[int, float] = 4,
        min_decay_time: Union[int, float] = 0.5,
        decay_rise: bool = True,
        invert: bool = False,
        decon_type: Literal["fft", "wiener", "convolution"] = "wiener",
        curve_fit_decay: bool = False,
        curve_fit_type: str = Literal["s_exp", "db_exp"],
        baseline_corr: bool = False,
        tmp_amplitude: Union[int, float] = -20,
        tmp_tau_1: Union[int, float] = 0.3,
        tmp_tau_2: Union[int, float] = 5,
        tmp_risepower: Union[int, float] = 0.5,
        tmp_length: Union[int, float] = 30,
        tmp_spacer: Union[int, float] = 1.5,
    ):
        # Set the attributes for the acquisition
        self.baseline_start = int(baseline_start * (self.sample_rate / 1000))
        self.baseline_end = int(baseline_end * (self.sample_rate / 1000))
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.baseline_corr = baseline_corr
        self.rc_check = rc_check
        self.rc_check_start = int(rc_check_start * self.s_r_c)
        self.rc_check_end = int(rc_check_end * self.s_r_c)
        self.sensitivity = sensitivity
        self.amp_threshold = amp_threshold
        self.mini_spacing = mini_spacing
        self.min_rise_time = min_rise_time
        self.max_rise_time = max_rise_time
        self.min_decay_time = min_decay_time
        self.decay_rise = decay_rise
        self.invert = invert
        self.curve_fit_decay = curve_fit_decay
        self.decon_type = decon_type
        self.curve_fit_type = curve_fit_type
        self.tmp_amplitude = tmp_amplitude
        self.tmp_tau_1 = tmp_tau_1
        self.tmp_tau_2 = tmp_tau_2
        self.tmp_risepower = tmp_risepower
        self.tmp_length = tmp_length
        self.tmp_spacer = tmp_spacer
        self.deleted_events = 0

        # Runs the functions to analyze the acquisition
        # if self.baseline_corr:
        #     self.baseline_correction()
        temp_array = self.create_mespc_array()
        self.filter_array(temp_array)
        self.set_array()
        self.set_sign()
        self.create_events()

    def create_mespc_array(self):
        """The function creates the mEPSC array by removing the RC
        check if there is one. The functions runs before the array
        is filtered.
        """
        if self.rc_check is False:
            pass
        elif self.rc_check is True:
            if self.rc_check_end == len(self.array):
                temp_array = np.copy(self.array[: self.rc_check_start])
                self.rc_check_array = np.copy(self.array[self.rc_check_start :])
            else:
                temp_array = np.copy(self.array[self.rc_check_end :])
                self.rc_check_array = np.copy(self.array[self.rc_check_end :])
        return temp_array

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

    def baseline_correction(self):
        end = len(self.array)
        num_knots = 8
        knots = np.arange(
            int(end / num_knots),
        )
        spl = interpolate.LSQUnivariateSpline(self.plot_acq_x(), self.array, t=knots)
        baseline = spl(self.plot_acq_x())
        self.array = self.array - baseline

    def deconvolve_array(self, lambd: Union[int, float] = 4) -> np.ndarray:
        """The Wiener deconvolution equation can be found on GitHub from pbmanis
        and danstowell. The basic idea behind this function is deconvolution
        or divsion in the frequency domain. I have found that changing lambd
        from 2-10 does not seem to affect the performance of the Wiener
        equation. The fft deconvolution type is the most simple and default
        choice and is also what the original paper used.

        Pernía-Andrade, A. J. et al. A Deconvolution-Based Method with High
        Sensitivity and Temporal Resolution for Detection of Spontaneous
        Synaptic Currents In Vitro and In Vivo. Biophysical Journal 103,
        1429–1439 (2012).


        Parameters
        ----------
        array : Filtered signal in a numpy array form. There are edge effects if
            an unfiltered signal is used.
        kernel : A representative PSC or PSP. Can be an averaged or synthetic
            template.
        lambd : Signal to noise ratio. A SNR anywhere from 1 to 10 seems to work
            without determining the exact noise level.

        Returns
        -------
        deconvolved_array: numpy array
            Time domain deconvolved signal that is returned for filtering.

        """
        # The kernel needs to be the same length as the array that is being
        # deconvolved.
        template = create_template(
            amplitude=self.tmp_amplitude,
            tau_1=self.tmp_tau_1,
            tau_2=self.tmp_tau_2,
            risepower=self.tmp_risepower,
            length=self.tmp_length,
            spacer=self.tmp_spacer,
            sample_rate=self.sample_rate,
        )

        kernel = np.hstack((template, np.zeros(len(self.final_array) - len(template))))
        H = fft(kernel)

        # Choose the method for finding minis. FFT and Wiener are almost identical.
        # Convolution is similar to template fitting (correlation).
        if self.decon_type == "fft":
            deconvolved_array = np.real(ifft(fft(self.final_array) / H))
        elif self.decon_type == "wiener":
            deconvolved_array = np.real(
                ifft(fft(self.final_array) * np.conj(H) / (H * np.conj(H) + lambd**2))
            )
        elif self.decon_type == "convolution":
            deconvolved_array = signal.convolve(self.final_array, template, mode="same")
        return deconvolved_array

    def create_deconvolved_array(self):
        deconvolved_array = self.deconvolve_array()
        if self.decon_type == "fft" or self.decon_type == "wiener":
            filtered_decon_array = fir_zero_1(
                array=deconvolved_array,
                sample_rate=self.sample_rate,
                order=351,
                high_pass=None,
                high_width=None,
                low_pass=300,
                low_width=100,
                window="hann",
            )
            return filtered_decon_array
        else:
            return deconvolved_array

    def find_events(self):
        # This is not the method from the original paper but it works a
        # lot better. The original paper used 4*std of the deconvolved array.
        # The problem with that method is that interneurons needs a
        # different sensitivity setting. I wanted to keep the settings as
        # consistent as possible between different cell types.

        deconvolved_array = self.create_deconvolved_array()

        # Get the top and bottom 2.5% cutoff.
        bottom, top = np.percentile(deconvolved_array, [2.5, 97.5])

        # Return the middle values.
        middle = np.hstack(
            deconvolved_array[
                np.argwhere((deconvolved_array > bottom) & (deconvolved_array < top))
            ]
        )
        # Calculate the mean and rms.
        mu = np.mean(middle)
        rms = np.sqrt(np.mean(np.square(middle - mu)))

        # Find the events.
        peaks, _ = signal.find_peaks(
            deconvolved_array - mu,
            height=self.sensitivity * (rms),
            distance=self.mini_spacing * self.s_r_c,
            prominence=rms,
        )

        # There was an issue with the peaks list being a numpy array
        # so it is converted to a python list.
        events = peaks.tolist()
        return events

    def create_events(self):
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

        events = self.find_events()

        # The for loop won't run if there are no events.
        # So there is no need to catch instances when
        # there are no events.

        for peak in events:
            if len(self.final_array) - peak < 20 * self.s_r_c:
                pass
            else:
                # Create the mini class then analyze.
                event = MiniEvent()
                event.analyze(
                    acq_number=self.acq_number,
                    event_pos=peak,
                    y_array=self.final_array,
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
                else:
                    pass

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

    def create_new_mini(self, x: Union[int, float]) -> bool:
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
            i.x_array = "saved"
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
            h.load_mini(event_dict=i, final_array=self.final_array)
            self.postsynaptic_events += [h]

    def del_postsynaptic_event(self, index):
        del self.postsynaptic_events[index]
        del self.final_events[index]
        self.deleted_events += 1

    def sort_index(self):
        return list(np.argsort(self.final_events))

    def list_of_events(self):
        return list(range(len(self.postsynaptic_events)))

    def plot_acq_y(self):
        return self.final_array

    def plot_acq_x(self):
        return np.arange(0, len(self.final_array)) / self.s_r_c
