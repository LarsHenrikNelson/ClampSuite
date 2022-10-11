import bottleneck as bn
import numpy as np
from scipy import signal
from scipy import stats

from . import filter_acq


class CurrentClampAcq(filter_acq.FilterAcq, analysis="current_clamp"):
    def analyze(
        self,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=100,
        filter_type="None",
        order=None,
        high_pass=None,
        high_width=None,
        low_pass=None,
        low_width=None,
        window=None,
        polyorder=None,
        pulse_start=300,
        pulse_end=1000,
        ramp_start=300,
        ramp_end=4000,
        threshold=-15,
        min_spikes=2,
    ):
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
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self._pulse_start = int(pulse_start * self.s_r_c)
        self.pulse_end = int(pulse_end * self.s_r_c)
        self.ramp_start = int(ramp_start * self.s_r_c)
        self.ramp_end = int(ramp_end * self.s_r_c)
        self.x_array = np.arange(len(self.array)) / (self.s_r_c)
        self.threshold = threshold
        self.min_spikes = min_spikes

        # Analysis functions
        self.get_delta_v()
        self.find_baseline_stability()
        self.find_spike_parameters()
        self.first_spike_parameters()
        self.get_ramp_rheo()
        self.find_spike_width()
        self.find_AHP_peak()
        self.spike_adaptation()
        self.calculate_sfa_local_var()
        self.calculate_sfa_divisor()

    def get_delta_v(self):
        """
        This function finds the delta-v for a pulse. It simply takes the mean
        value from the pulse start to end for pulses without spikes. For
        pulses with spikes it takes the mode of the moving mean.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if self.ramp == "0":
            self.baseline_mean = np.mean(
                self.array[self.baseline_start : self.baseline_end]
            )
            max_value = np.max(self.array[self._pulse_start : self.pulse_end])
            self.start = int(
                self._pulse_start + ((self.pulse_end - self._pulse_start) / 2)
            )
            if max_value < self.threshold:
                self.delta_v = (
                    np.mean(self.array[self.start : self.pulse_end])
                    - self.baseline_mean
                )
            else:
                m = stats.mode(
                    bn.move_mean(
                        self.array[self.start : self.pulse_end],
                        window=1000,
                        min_count=1,
                    ),
                    keepdims=True,
                )
                self.delta_v = m[0][0] - self.baseline_mean
        elif self.ramp == "1":
            self.delta_v = np.nan
            self.baseline_mean = np.mean(
                self.array[self.baseline_start : self.baseline_end]
            )
        return self.delta_v

    def find_spike_parameters(self):
        """
        This function returns the spike parameters of a pulse or ramp that
        spikes. A separate function characterizes the first spike in a train
        of spikes. This function is to determine whether spikes exist.

        Returns
        -------
        self.rheo_x
            The x position in an array of the spike threshold. Also used to
            calculate the rheobase for a ramp.
        self.spike_threshold
            The threshold at which the first spike occurs.
        self.peaks
            The x_position of the action potential peaks. This is used to
            calculate the self.hertz_exact and self.iei
        """
        # Find the peaks of the spikes. The prominence is set to avoid picking
        # peaks that are just noise.
        if self.ramp == "0":
            self.peaks, _ = signal.find_peaks(
                self.array[: self.pulse_end],
                height=self.threshold,
                prominence=int(1 * self.s_r_c),
            )
        elif self.ramp == "1":
            self.peaks, _ = signal.find_peaks(
                self.array[: self.ramp_end], height=self.threshold, prominence=10
            )
        if len(self.peaks) < self.min_spikes:
            # If there are no peaks fill in values with np.nan. This helps with
            # analysis further down the line as nan values are fairly easy to
            # work with.
            self.peaks = np.array([np.nan])
            self.spike_threshold = np.nan
            self.rheo_x = np.nan
            self.hertz_exact = np.nan
            self.iei = np.array([np.nan])
            self.iei_mean = np.nan
            self.ap_v = np.nan
            self.peak_volt = np.nan
        else:
            # Get the peak voltage
            self.peak_volt = self.array[self.peaks[0]]

            # Differentiate the array to find the peak dv/dt.
            dv = np.gradient(self.array)
            dt = np.gradient(np.arange(len(self.x_array)) / 10)
            peak_dv, _ = signal.find_peaks(dv, height=6)

            # Pull out the index of the first peak and find the peak velocity.
            self.ap_v = (dv / dt)[peak_dv[0]]

            # Calculate this early so that it does not need to be calculated
            # a second time.
            baseline_std = np.std(dv[self.baseline_start : self.baseline_end])

            # Calculate the IEI and correction for sample rate
            if len(self.peaks) > 1:
                self.iei = np.diff(self.peaks) / self.s_r_c
                self.iei_mean = self.iei.mean()
            else:
                self.iei = [np.nan]
                self.iei_mean = np.nan

            # While many papers use a single threshold to find the threshold
            # potential this does not work if you want to analyze both
            # interneurons and other neuron types. I have created a shifting
            # threshold based on where the maximum velocity occurs of the first
            # spike occurs.
            if self.ramp == "0":
                # This takes the last value of an array of values that are
                # less than the threshold of the second derivative. It was
                # the most robust way to find the spike threshold time.
                try:
                    self.rheo_x = (
                        np.argwhere(
                            np.gradient(dv[self._pulse_start : peak_dv[0]]) < (0.3)
                        )
                        + self._pulse_start
                    )[-1][0]
                except:
                    self.rheo_x = (
                        np.argmin(dv[self._pulse_start : peak_dv[0]])
                        + self._pulse_start
                    )

                # Find the spike_threshold using the timing found above
                self.spike_threshold = self.array[self.rheo_x]

                # Calculates the exact hertz by dividing the number peaks by
                # length of the pulse. If there is only one spike the hertz
                # returns an impossibly fast number is you take only divide by
                # the start of the spike_threshold to the end of the pulse.
                self.hertz_exact = len(self.peaks) / (
                    (self.pulse_end - self._pulse_start) / self.sample_rate
                )

            elif self.ramp == "1":
                # This takes the last value of an array of values that are
                # less than the threshold. It was the most robust way to find
                # the spike threshold time.
                self.rheo_x = (
                    np.argwhere(dv[self._pulse_start : peak_dv[0]] < (8 * baseline_std))
                    + self._pulse_start
                )[-1][0]
                self.spike_threshold = self.array[self.rheo_x]
                self.hertz_exact = len(self.peaks) / (
                    (self.ramp_end - self.rheo_x) / self.sample_rate
                )

    def first_spike_parameters(self):
        """
        This function analyzes the parameter of the first action potential in
        a pulse that contains at least one action potential.

        Returns
        -------
        None.

        """
        if np.isnan(self.peaks[0]):
            # If there are no peaks fill in values with np.nan. This helps with
            # analysis further down the line as nan values are fairly easy to
            # work with.
            self.first_ap = np.array([np.nan])
            self.indices = np.nan
        else:
            if self.ramp == "0":
                # To extract the first action potential and to find the
                # half-width of the spike you have create an array whose value
                # is the spike threshold wherever the value drops below the
                # spike threshold. This is used because of how scipy.find_peaks
                # works and was a robust way to find the first
                # action_potential.
                masked_array = self.array.copy()
                mask = np.array(self.array > self.spike_threshold)

                # First using a mask to find the indices of each action
                # potential.
                self.indices = np.nonzero(mask[1:] != mask[:-1])[0]
                if self.indices.size > 2:
                    self.indices = self.indices[self.indices >= self.rheo_x]
                    if self.indices.size > 2:
                        self.ap_index = [
                            self.indices[0] - int(5 * self.s_r_c),
                            self.indices[2],
                        ]
                    else:
                        self.ap_index = [
                            self.indices[0] - int(5 * self.s_r_c),
                            self.pulse_end,
                        ]
                else:
                    self.ap_index = [
                        self.indices[0] - int(5 * self.s_r_c),
                        self.pulse_end,
                    ]

                # Extract the first action potential based on the ap_index.
                self.first_ap = np.split(self.array, self.ap_index)[1]

            elif self.ramp == "1":
                # To extract the first action potential and to find the
                # half-width of the spike you have create an array whose value
                # is the spike threshold wherever the value drops below the
                # spike threshold. This is used because of how scipy.find_peaks
                # works and was a robust way to find the first action_potential.
                masked_array = self.array.copy()

                # First using a mask to find the indices of each action
                # potential. The index pulls out the action potential fairly
                # close to the spike so the first index is set to 5 ms before
                # the returned index.
                mask = np.array(self.array > self.spike_threshold)
                self.indices = np.nonzero(mask[1:] != mask[:-1])[0]
                if len(self.indices) > 2:
                    self.indices = self.indices[self.indices >= self.rheo_x]
                    self.ap_index = [
                        self.indices[0] - int(5 * self.s_r_c),
                        self.indices[2],
                    ]
                else:
                    self.ap_index = [
                        self.indices[0] - int(5 * self.s_r_c),
                        self.ramp_end,
                    ]

                # Extract the first action potential based on the ap_index.
                self.first_ap = np.split(self.array, self.ap_index)[1]

    def find_spike_width(self):
        # Create the masked array using the mask found earlier to find
        # The pulse half-width.
        if not np.isnan(self.peaks[0]):
            if self.ramp == "0":
                end = self.pulse_end
            else:
                end = self.ramp_end
            masked_array = self.array.copy()
            mask = np.array(self.array > self.spike_threshold)
            masked_array[~mask] = self.spike_threshold
            self.width_comp = signal.peak_widths(
                masked_array[:end], self.peaks, rel_height=0.5
            )
        else:
            self.width_comp = None

    def find_baseline_stability(self):
        if self.ramp == "0":
            self.baseline_stability = np.abs(
                np.mean(self.array[: self._pulse_start])
                - np.mean(self.array[self.pulse_end :])
            )
        elif self.ramp == "1":
            self.baseline_stability = np.abs(
                np.mean(self.array[: self.ramp_start])
                - np.mean(self.array[self.ramp_end :])
            )
        else:
            self.baseline_stability = np.nan

    def spike_adaptation(self):
        """
        This function calculates the spike frequency adaptation. A positive
        number means that the spikes are speeding up and a negative number
        means that spikes are slowing down. This function was inspired by the
        Allen Brain Institutes IPFX analysis program
        https://github.com/AllenInstitute/ipfx/tree/
        db47e379f7f9bfac455cf2301def0319291ad361
        """

        if len(self.iei) <= 1:
            self.spike_adapt = np.nan
        else:
            # self.iei = self.iei.astype(float)
            if np.allclose((self.iei[1:] + self.iei[:-1]), 0.0):
                self.spike_adapt = np.nan
            norm_diffs = (self.iei[1:] - self.iei[:-1]) / (self.iei[1:] + self.iei[:-1])
            norm_diffs[(self.iei[1:] == 0) & (self.iei[:-1] == 0)] = 0.0
            self.spike_adapt = np.nanmean(norm_diffs)

    def get_ramp_rheo(self):
        """
        This function gets the ramp rheobase. The ramp pulse is recreated
        based on the values in the matfile and then the current is extracted.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if self.ramp == "1":
            if self.rheo_x is np.nan:
                self.ramp_rheo = np.nan
            else:
                # Create the ramp current values.
                ramp_values = np.linspace(
                    0, int(self.pulse_amp), num=self.ramp_end - self.ramp_start
                )

                # Create an array of zeros where the ramp will be placed.
                ramp_array = np.zeros(len(self.array))

                # Insert the ramp into the array of zeros.
                ramp_array[self.ramp_start : self.ramp_end] = ramp_values

                # Extract the ramp rheobase.
                self.ramp_rheo = ramp_array[self.rheo_x]
        else:
            self.ramp_rheo = np.nan

    def calculate_sfa_local_var(self):
        """
        The idea for the function was initially inspired by a program called
        Easy Electropysiology (https://github.com/easy-electrophysiology).

        This function calculates the local variance in spike frequency
        accomadation that was drawn from the paper:
        Shinomoto, Shima and Tanji. (2003). Differences in Spiking Patterns
        Among Cortical Neurons. Neural Computation, 15, 2823-2842.

        Returns
        -------
        None.

        """
        if len(self.iei) < 2 or self.iei is np.nan:
            self.local_var = np.nan
        else:
            isi_shift = self.iei[1:]
            isi_cut = self.iei[:-1]
            n_minus_1 = len(isi_cut)
            self.local_var = (
                np.sum((3 * (isi_cut - isi_shift) ** 2) / (isi_cut + isi_shift) ** 2)
                / n_minus_1
            )

    def calculate_sfa_divisor(self):
        """
        The idea for the function was initially inspired by a program called
        Easy Electropysiology (https://github.com/easy-electrophysiology).
        """
        self.sfa_divisor = self.iei[0] / self.iei[-1]

    def find_AHP_peak(self):
        """
        Rather than divide the afterhyperpolarization potential into different
        segments it seems best to pull out the peak of the AHP and its timing
        compared to the the first spike or spike threshold. It seems to me to
        be less arbitrary. The AHP
        """
        if not np.isnan(self.peaks[0]):
            peak = np.argmax(self.first_ap)
            dvv = np.gradient(np.gradient(self.first_ap[: int(peak + 5 * self.s_r_c)]))
            corr_factor = len(self.first_ap) - len(
                self.first_ap[: int(peak + 5 * self.s_r_c)]
            )
            base = (np.argmin(dvv[::-1] < 0.15) * -1) - corr_factor
            self.ahp_y = self.first_ap[base]
            self.ahp_x = self.spike_x_array()[base]
        else:
            self.ahp_x = np.nan
            self.ahp_y = np.nan

    # Helper functions that correct x-values for plotting
    def spike_width(self):
        if self.width_comp is not None:
            return self.width_comp[0][0] / self.s_r_c
        else:
            return np.nan

    def spike_width_y(self):
        if self.width_comp is not None:
            return [self.width_comp[1][0], self.width_comp[1][0]]

    def spike_width_x(self):
        return [
            self.width_comp[2][0] / self.s_r_c,
            self.width_comp[3][0] / self.s_r_c,
        ]

    def spike_threshold_time(self):
        if not np.isnan(self.rheo_x):
            return self.rheo_x / self.s_r_c
        else:
            return self.rheo_x

    def spike_x_array(self):
        return self.x_array[self.ap_index[0] : self.ap_index[1]]

    def spike_peaks_x(self):
        if not np.isnan(self.peaks[0]):
            return np.array(self.peaks) / self.s_r_c
        else:
            return []

    def spike_peaks_y(self):
        if not np.isnan(self.peaks[0]):
            return self.array[self.peaks]
        else:
            return []

    def plot_rheo_x(self):
        return [self.rheo_x / self.s_r_c]

    def plot_delta_v(self):
        """
        This function creates the elements to plot the delta-v as a vertical
        line in the middle of the pulse. The elements are corrected so that
        they will plot in milliseconds.
        """
        if self.ramp == "0":
            x = (
                int(((self.pulse_end - self._pulse_start) / 2) + self._pulse_start)
                / self.s_r_c
            )
            voltage_response = self.delta_v + self.baseline_mean
            plot_x = [x, x]
            plot_y = [self.baseline_mean, voltage_response]
        elif self.ramp == "1":
            plot_x = np.nan
            plot_y = np.nan
        return plot_x, plot_y

    def plot_ahp_x(self):
        return [self.ahp_x]

    def first_peak_time(self):
        return self.peaks[0] / self.s_r_c

    def create_dict(self):
        """
        This create a dictionary of all the values created by the class. This
        makes it very easy to concentatenate the data from multiple
        acquisitions together.

        Returns
        -------
        None.

        """
        current_clamp_dict = {
            "Acquisition": self.acq_number,
            "Pulse_pattern": self.pulse_pattern,
            "Pulse_amp": self.pulse_amp,
            "Ramp": self.ramp,
            "Epoch": self.epoch,
            "Baseline": self.baseline_mean,
            "Pulse_start": self._pulse_start / self.s_r_c,
            "Delta_v": self.delta_v,
            "Spike_threshold (mV)": self.spike_threshold,
            "Spike_threshold_time (ms)": self.spike_threshold_time(),
            "Spike_peak_volt": self.peak_volt,
            "Spike_time (ms)": self.first_peak_time(),
            "Hertz": self.hertz_exact,
            "Spike_iei": self.iei_mean,
            "Spike_width": self.spike_width(),
            "Max_AP_vel": self.ap_v,
            "Spike_freq_adapt": self.spike_adapt,
            "Local_sfa": self.local_var,
            "Divisor_sfa": self.sfa_divisor,
            "Peak_AHP (mV)": self.ahp_y,
            "Peak_AHP (ms)": self.ahp_x,
            "Ramp_rheobase": self.ramp_rheo,
            "Baseline_stability": self.baseline_stability,
        }
        return current_clamp_dict
