import numpy as np
from scipy.stats import linregress

from .acquisition_base import AcquisitionBase


class LFPBase(AcquisitionBase):
    """
    This class creates a LFP acquisition. This class subclasses the
    Acquisition class and takes input specific for LFP analysis.
    """

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

    def analyze_lfp(self):
        """
        This function runs all the other functions in one place. This makes
        it easy to troubleshoot.
        """
        self.field_potential()
        if self.fp_x is np.nan:
            pass
        else:
            self.fiber_volley()
            self.find_slope_array(self.fp_x)
            self.regression()

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
