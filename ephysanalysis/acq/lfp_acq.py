import numpy as np
from scipy.stats import linregress

from . import filter_acq


class LFPAcq(filter_acq.FilterAcq, analysis="lfp"):
    """
    This class creates a LFP acquisition. This class subclasses the
    Acquisition class and takes input specific for LFP analysis.
    """

    def analyze_lfp(
        self,
        sample_rate=10000,
        baseline_start=0,
        baseline_end=800,
        filter_type="None",
        order=None,
        high_pass=None,
        high_width=None,
        low_pass=None,
        low_width=None,
        window=None,
        polyorder=None,
        pulse_start=1000,
    ):
        """
        This function runs all the other functions in one place. This makes
        it easy to troubleshoot.
        """
        # Set all the attributes for analysis.
        self.sample_rate = sample_rate
        self.s_r_c = sample_rate / 1000
        self.filter_type = filter_type
        self.order = order
        self.high_pass = high_pass
        self.high_width = high_width
        self.low_pass = low_pass
        self.low_width = low_width
        self.window = window
        self.polyorder = polyorder
        self.x_array = np.arange(len(self.array)) / (sample_rate / 1000)
        self.baseline_start = int(baseline_start * (sample_rate / 1000))
        self.baseline_end = int(baseline_end * (sample_rate / 1000))
        self.baselined_array = self.array - np.mean(
            self.array[self.baseline_start : self.baseline_end]
        )
        self.pulse_start = int(pulse_start * self.s_r_c)
        self.fp_x = np.nan
        self.fp_y = np.nan
        self.fv_x = np.nan
        self.fv_y = np.nan
        self.max_x = np.nan
        self.max_y = np.nan
        self.slope_y = np.nan
        self.slope_x = np.nan
        self.b = np.nan
        self.slope = np.nan
        self.regression_line = np.nan

        # Run the analysis
        self.filter_array()
        self.field_potential()
        if self.fp_x is np.nan:
            pass
        else:
            self.fiber_volley()
            self.find_slope_array(self.fp_x)
            self.regression()

    def field_potential(self):
        """
        This function finds the field potential based on the largest value in
        the array.

        Returns
        -------
        None.

        """
        # The end value was chosed based on experimental data.
        w_end = self.pulse_start + 200

        # The start value was chosen based on experimental data.
        w_start = self.pulse_start + 44

        if abs(np.max(self.filtered_array[w_start:w_end])) < abs(
            np.min(self.filtered_array[w_start:w_end])
        ):
            self.fp_y = np.min(self.filtered_array[w_start:w_end])
            self.fp_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start
        else:
            self.fp_y = np.nan
            self.fp_x = np.nan

    def fiber_volley(self):
        """
        This function finds the fiber volley based on the position of the
        field potential. The window for finding the fiber volley is based on
        experimental data.

        Returns
        -------
        None.

        """
        w_start = self.pulse_start + 9
        if self.fp_x < (self.pulse_start + 74):
            w_end = self.fp_x - 20
        else:
            w_end = self.fp_x - 40
            if w_end > (self.pulse_start + 49):
                w_end = self.pulse_start + 49
        if self.fp_x is np.nan or None:
            self.fv_y = np.nan
            self.fv_x = np.nan
        else:
            self.fv_y = np.min(self.filtered_array[w_start:w_end])
            self.fv_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start

    def find_slope_array(self, w_end):
        """
        This function returns the array for slope of the field potential onset
        based upon the 10-90% values of the field potential rise. The field
        potential x coordinate needs to be passed to this function.

        Returns
        -------
        None.

        """
        start = self.pulse_start
        # baseline_start = start - int(15.1*self.s_r_c)
        # analysis_end = start + int(20.0*self.s_r_c)
        x_values = np.arange(0, len(self.filtered_array) - 1)
        if w_end is not np.nan:
            # if (abs(np.max(self.filtered_array[baseline_start:analysis_end]))
            #     < abs(np.min(self.filtered_array[baseline_start:analysis_end]))):
            #     w_end = (np.argmin(self.filtered_array[(start+ 44):analysis_end])
            #              + (start+ 44)
            #               )
            if w_end < (start + 74):
                x = w_end - 19
            else:
                x = w_end - 39
                if x > (start + 49):
                    x = start + 49
            w_start = np.argmin(self.filtered_array[(start + 9) : x]) + (start + 9)
            if w_end < w_start:
                self.slope_y = [np.nan]
                self.slope_x = [np.nan]
                self.max_x = [np.nan]
                self.max_y = [np.nan]
            else:
                self.max_x = np.argmax(self.filtered_array[w_start:w_end]) + w_start
                self.max_y = np.max(self.filtered_array[w_start:w_end])
                y_array_subset = self.filtered_array[self.max_x : w_end]
                x_array_subset = x_values[self.max_x : w_end]
                self.slope_y = y_array_subset[
                    int(len(y_array_subset) * 0.1) : int(len(y_array_subset) * 0.9)
                ]
                self.slope_x = x_array_subset[
                    int(len(x_array_subset) * 0.1) : int(len(x_array_subset) * 0.9)
                ]
        else:
            self.max_x = [np.nan]
            self.max_y = [np.nan]
            self.slope_y = [np.nan]
            self.slope_x = [np.nan]

    def regression(self):
        """
        This function runs a regression on the slope array created by the
        find_slop_array function.

        Returns
        -------
        None.

        """
        if len(self.slope_y) > 5:
            reg = linregress(self.slope_x, self.slope_y)
            self.slope = reg[0]
            self.reg_line = [(self.slope * i) + reg[1] for i in self.slope_x]
        else:
            self.b = np.nan
            self.slope = np.nan
            self.reg_line = np.nan

    def change_fv(self, x, y):
        self.fv_x = x
        self.fv_y = y

    def change_fp(self, x, y):
        self.fp_x = x
        self.fp_y = y

    def plot_elements_x(self):
        return [self.fv_x / self.s_r_c, self.fp_x / self.s_r_c]

    def plot_elements_y(self):
        return [self.fv_y, self.fp_y]

    def create_dict(self):
        """
        This function returns a dictionary of all the values you will need to
        analyze the lfp. The dictionary is not an attribute of the class to
        keep the size of the created object small.

        Returns
        -------
        lfp_dict : TYPE
            DESCRIPTION.

        """
        lfp_dict = {
            "fv_amp": self.fv_y,
            "fv_time": self.fv_x / self.s_r_c,
            "fp_amp": self.fp_y,
            "fp_time": self.fp_x / self.s_r_c,
            "fp_slope": self.slope,
            "Epoch": self.epoch,
            "Acq number": self.acq_number,
        }
        return lfp_dict
