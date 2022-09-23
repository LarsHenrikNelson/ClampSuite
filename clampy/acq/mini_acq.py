import numpy as np
import pandas as pd
from scipy.fft import fft, ifft
from scipy import signal, stats, interpolate

from . import filter_acq
from .postsynaptic_event import MiniEvent


class MiniAnalysisAcq(filter_acq.FilterAcq, analysis="mini"):
    def analyze(
        self,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=80,
        filter_type="remez_2",
        order=201,
        high_pass=None,
        high_width=None,
        low_pass=600,
        low_width=300,
        window=None,
        polyorder=None,
        template=None,
        rc_check=True,
        rc_check_start=10000,
        rc_check_end=10300,
        sensitivity=3,
        amp_threshold=4,
        mini_spacing=2,
        min_rise_time=0.5,
        max_rise_time=4,
        min_decay_time=0.5,
        invert=False,
        decon_type="wiener",
        curve_fit_decay=False,
        curve_fit_type="db_exp",
        baseline_corr=False,
        temp_tau_1=3,
        temp_tau_2=50,
        temp_amplitude=-20,
        temp_risepower=0.5,
        temp_t_psc=np.arange(0, 300),
        temp_spacer=20,
    ):
        # Set the attributes for the acquisition
        self.sample_rate = sample_rate
        self.s_r_c = sample_rate / 1000
        self.x_array = np.arange(len(self.array)) / (sample_rate / 1000)
        self.baseline_start = int(baseline_start * (sample_rate / 1000))
        self.baseline_end = int(baseline_end * (sample_rate / 1000))
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.baseline_corr = baseline_corr
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self.rc_check = rc_check
        self.rc_check_start = int(rc_check_start * self.s_r_c)
        self.rc_check_end = int(rc_check_end * self.s_r_c)
        self.sensitivity = sensitivity
        self.amp_threshold = amp_threshold
        self.mini_spacing = int(mini_spacing * self.s_r_c)
        self.min_rise_time = min_rise_time
        self.max_rise_time = max_rise_time
        self.min_decay_time = min_decay_time
        self.invert = invert
        self.curve_fit_decay = curve_fit_decay
        self.decon_type = decon_type
        self.curve_fit_type = curve_fit_type

        # Runs the functions to analyze the acquisition
        self.create_template(template)
        self.create_mespc_array()
        if self.baseline_corr:
            self.baseline_correction()
        self.filter_array()
        self.set_array()
        self.set_sign()
        self.decon_filt()
        self.create_events()

    def tm_psp(self, amplitude, tau_1, tau_2, risepower, t_psc, spacer=0):
        template = np.zeros(len(t_psc) + spacer)
        offset = len(template) - len(t_psc)
        Aprime = (tau_2 / tau_1) ** (tau_1 / (tau_1 - tau_2))
        y = (
            amplitude
            / Aprime
            * ((1 - (np.exp(-t_psc / tau_1))) ** risepower * np.exp((-t_psc / tau_2)))
        )
        template[offset:] = y
        return template

    def create_template(self, template):
        if template is None:
            tau_1 = 3
            tau_2 = 50
            amplitude = -20
            risepower = 0.5
            t_psc = np.arange(0, 300)
            spacer = 20
            self.template = self.tm_psp(
                amplitude, tau_1, tau_2, risepower, t_psc, spacer=spacer
            )
        else:
            self.template = template

    def create_mespc_array(self):
        if self.rc_check is False:
            pass
        elif self.rc_check is True:
            if self.rc_check_end == len(self.array):
                temp_array = np.copy(self.baselined_array[: self.rc_check_start])
                self.rc_check_array = np.copy(
                    self.baselined_array[self.rc_check_start :]
                )
            else:
                temp_array = np.copy(self.baselined_array[self.rc_check_end :])
                self.rc_check_array = np.copy(self.baselined_array[self.rc_check_end :])
            self.baselined_array = temp_array
        self.x_array = np.arange(len(self.baselined_array)) / (self.s_r_c)

    def set_array(self):
        self.final_array = self.filtered_array
        del self.filtered_array

    def set_sign(self):
        if not self.invert:
            self.final_array = self.final_array * 1
        else:
            self.final_array = self.final_array * -1

    def baseline_correction(self):
        a, b, c = 0.93259504, -249.26795569, -1.17790283
        end = len(self.baselined_array)
        smooth = a * np.log(end + b) + c
        spl = interpolate.UnivariateSpline(
            self.x_array, self.final_array, s=end * smooth
        )
        baseline = spl(self.x_array)
        self.baselined_array = self.baselined_array - baseline

    def deconvolution(self, lambd=4):
        """
        The Wiener deconvolution equation can be found on GitHub from pbmanis
        and danstowell. The basic idea behind this function is deconvolution
        or divsion in the frequency domain. I have found that changing lambd
        from 2-10 does not seem to affect the performance of the Wiener
        equation. The fft deconvolution type is the most simple and default
        choice.

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

        kernel = np.hstack(
            (self.template, np.zeros(len(self.final_array) - len(self.template)))
        )
        H = fft(kernel)

        if self.decon_type == "fft":
            deconvolved_array = np.real(ifft(fft(self.final_array) / H))
        elif self.decon_type == "wiener":
            deconvolved_array = np.real(
                ifft(fft(self.final_array) * np.conj(H) / (H * np.conj(H) + lambd**2))
            )
        else:
            deconvolved_array = signal.convolve(
                self.final_array, self.template, mode="same"
            )
        return deconvolved_array

    def decon_filt(self):
        """
        This function takes the deconvolved array, filters it and finds the
        peaks of the which is where mini events are located.

        Parameters
        ----------
        array : Filtered signal in a numpy array form.There are edge effects if
            an unfiltered signal is used.
        template : A representative PSC or PSP. Can be an averaged or synthetic
            template. The template works best when there is a small array of
            before the mini onset.

        Returns
        -------
        None.

        """
        deconvolved_array = self.deconvolution()
        baselined_decon_array = deconvolved_array - np.mean(deconvolved_array[0:800])
        if self.decon_type == "fft" or self.decon_type == "wiener":
            filt = signal.firwin2(
                351,
                freq=[0, 300, 400, self.sample_rate / 2],
                gain=[1, 1, 0, 0],
                window="hann",
                fs=self.sample_rate,
            )
            y = signal.filtfilt(filt, 1.0, baselined_decon_array)
            self.final_decon_array = y
        else:
            self.final_decon_array = deconvolved_array
        mu, std = stats.norm.fit(self.final_decon_array)
        peaks, _ = signal.find_peaks(
            self.final_decon_array - mu, height=self.sensitivity * abs(std)
        )
        self.events = peaks.tolist()

    def create_events(self):
        """
        This functions creates the events based on the list of peaks found
        from the deconvolution. Events less than 20 ms before the end of
        the acquisitions are not counted. Events get screened out based on the
        amplitude, min_rise_time, and min_decay_time passed by the
        experimenter.

        Returns
        -------
        None.

        """
        self.postsynaptic_events = []
        self.final_events = []
        event_number = 0
        event_time = []
        if len(self.events) == 0:
            pass
        for peak in self.events:
            if len(self.final_array) - peak < 20 * self.s_r_c:
                pass
            else:
                if event_number > 0:
                    prior_peak = self.postsynaptic_events[event_number - 1].event_peak_x
                else:
                    prior_peak = 0
                event = MiniEvent()
                event.analyze(
                    acq_number=self.acq_number,
                    event_pos=peak,
                    y_array=self.final_array,
                    sample_rate=self.sample_rate,
                    curve_fit_decay=self.curve_fit_decay,
                    curve_fit_type=self.curve_fit_type,
                    prior_peak=prior_peak,
                )
                if np.isnan(event.event_peak_x) or event.event_peak_x in event_time:
                    pass
                else:
                    if event_number > 0:
                        if (
                            event.event_peak_x
                            - self.postsynaptic_events[-1].event_peak_x
                            > self.mini_spacing
                            and event.amplitude >= self.amp_threshold
                            and event.rise_time >= self.min_rise_time
                            and event.rise_time <= self.max_rise_time
                            and event.final_tau_x >= self.min_decay_time
                            and event.final_tau_x >= event.rise_time
                        ):
                            self.postsynaptic_events += [event]
                            self.final_events += [peak]
                            event_time += [event.event_peak_x]
                            event_number += 1
                        else:
                            pass
                    else:
                        if (
                            event.amplitude > self.amp_threshold
                            and event.rise_time > self.min_rise_time
                            and event.rise_time < self.max_rise_time
                            and event.final_tau_x > self.min_decay_time
                            and event.final_tau_x > event.rise_time
                        ):
                            self.postsynaptic_events.append(event)
                            self.final_events += [peak]
                            event_time += [event.event_peak_x]
                            event_number += 1
                        else:
                            pass
        # else:
        #     peak = self.events[0]
        #     event = MiniEvent()
        #     event.analyze(
        #         acq_number=self.acq_number,
        #         event_pos=peak,
        #         y_array=self.final_array,
        #         sample_rate=self.sample_rate,
        #         curve_fit_decay=self.curve_fit_decay,
        #         curve_fit_type=self.curve_fit_type,
        #     )
        #     event_time += [event.event_peak_x]
        #     if event.event_peak_x is np.nan or event.event_peak_x in event_time:
        #         pass
        #     else:
        #         if (
        #             event.amplitude > self.amp_threshold
        #             and event.rise_time > self.min_rise_time
        #             and event.final_tau_x > self.min_decay_time
        #             and event.rise_time < self.max_rise_time
        #             and event.final_tau_x > event.rise_time
        #         ):
        #             self.postsynaptic_events += [event]
        #             self.final_events += [peak]
        #             event_time += [event.event_peak_x]
        #             event_number += 1
        #         else:
        #             pass

    def create_new_mini(self, x):
        """
        Creates a new mini event based on the x position.
        The x position needs to be in samples not time.
        """
        # Convert from time to samples
        x = int(x * self.s_r_c)
        event = MiniEvent()
        event.analyze(
            acq_number=self.acq_number,
            event_pos=x,
            y_array=self.final_array,
            sample_rate=self.sample_rate,
            curve_fit_decay=self.curve_fit_decay,
            curve_fit_type=self.curve_fit_type,
        )
        if not np.isnan(event.event_peak_x):
            self.final_events += [x]
            self.postsynaptic_events += [event]
            return True
        else:
            return False

    def final_acq_data(self):
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
            self.postsynaptic_events.sort(key=lambda x: x.event_peak_x)
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
            final_dict["Est tau (ms)"] = [np.nan]
            final_dict["Event time (ms)"] = [np.nan]
            final_dict["Acq time stamp"] = [np.nan]
            final_dict["Rise time (ms)"] = [np.nan]
            final_dict["Rise rate (pA/ms)"] = [np.nan]
            if self.curve_fit_decay:
                final_dict["Curve fit tau (ms)"] = [np.nan]

            final_dict["IEI (ms)"] = [np.nan]
            self.freq = np.nan
        return pd.DataFrame(final_dict)

    def get_event_arrays(self):
        events = [i.event_array - i.event_start_y for i in self.postsynaptic_events]
        return events

    def peak_values(self):
        peak_align_values = [
            i.event_peak_x - i.array_start for i in self.postsynaptic_events
        ]
        return peak_align_values

    def total_events(self):
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
        self.array = "saved"
        # self.final_decon_array = "saved"
        self.events = "saved"
        self.x_array = "saved"
        for i in self.postsynaptic_events:
            i.x_array = "saved"
            i.event_array = "saved"
            self.saved_events_dict += [i.__dict__]
        self.postsynaptic_events = "saved"

    def create_postsynaptic_events(self):
        self.postsynaptic_events = []
        for i in self.saved_events_dict:
            h = MiniEvent()
            h.load_mini(event_dict=i, final_array=self.final_array)
            self.postsynaptic_events += [h]
