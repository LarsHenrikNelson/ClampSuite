import numpy as np
from scipy import signal


def field_potential(self) -> None:
    """
    This function finds the field potential based on the largest value in
    the array.

    Returns
    -------
    None.

    """
    # The end value was chosed based on experimental data.
    w_end = self._pulse_start + int(20 * self.s_r_c)

    # The start value was chosen based on experimental data.
    w_start = self._pulse_start + int(4.4 * self.s_r_c)

    if abs(np.max(self.filtered_array[w_start:w_end])) < abs(
        np.min(self.filtered_array[w_start:w_end])
    ):
        self.fp_y = np.min(self.filtered_array[w_start:w_end])
        self._fp_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start
    else:
        self.fp_y = np.nan
        self._fp_x = np.nan


def find_fiber_volley(self) -> None:
    if np.isnan(self._fp_x) or self._fp_x is None:
        self.fv_y = np.nan
        self._fv_x = np.nan
    else:
        peaks, _ = signal.find_peaks(
            -1 * self.filtered_array[self._pulse_start : self._fp_x],
            width=int(0.5 * self.s_r_c),
        )
        if len(peaks) > 0:
            self._fv_x = int(peaks[0] + self._pulse_start)
            self.fv_y = self.filtered_array[self._fv_x]
        else:
            self.fv_y, self._fv_x = self.fiber_volley_sec()


def fiber_volley_sec(self) -> tuple[float, int]:
    """
    This function finds the fiber volley based on the position of the
    field potential. The window for finding the fiber volley is based on
    experimental data.

    Returns
    -------
    None.

    """
    w_start = self._pulse_start + int(0.9 * self.s_r_c)
    if self._fp_x < (self._pulse_start + 74):
        w_end = self._fp_x - int(2 * self.s_r_c)
    else:
        w_end = self._fp_x - int(4 * self.s_r_c)
        if w_end > (self._pulse_start + int(49 * self.s_r_c)):
            w_end = self._pulse_start + int(49 * self.s_r_c)
    fv_y = np.min(self.filtered_array[w_start:w_end])
    fv_x = np.argmin(self.filtered_array[w_start:w_end]) + w_start
    return fv_y, fv_x


def find_slope_array_sec(self, w_end: int) -> None:
    """
    This function returns the array for slope of the field potential onset
    based upon the 10-90% values of the field potential rise. The field
    potential x coordinate needs to be passed to this function.

    Returns
    -------
    None.

    """
    start = self._pulse_start
    x_values = np.arange(0, len(self.filtered_array) - 1)
    if w_end is not np.nan:
        w_end = int(w_end)
        if w_end < (start + int(7.4 * self.s_r_c)):
            x = w_end - int(1.9 * self.s_r_c)
        else:
            x = w_end - int(3.9 * self.s_r_c)
            if x > (start + int(4.9 * self.s_r_c)):
                x = start + int(4.9 * self.s_r_c)
        w_start = np.argmin(
            self.filtered_array[(start + int(0.9 * self.s_r_c)) : x]
        ) + (start + int(0.9 * self.s_r_c))
        if w_end < w_start:
            self.slope_y = [np.nan]
            self._slope_x = [np.nan]
            self.max_x = np.nan
            self.max_y = np.nan
        else:
            self.max_x = np.argmax(self.filtered_array[w_start:w_end]) + w_start
            self.max_y = np.max(self.filtered_array[w_start:w_end])
            y_array_subset = self.filtered_array[self.max_x : w_end]
            x_array_subset = x_values[self.max_x : w_end]
            self.slope_y = y_array_subset[
                int(len(y_array_subset) * 0.1) : int(len(y_array_subset) * 0.9)
            ]
            self._slope_x = x_array_subset[
                int(len(x_array_subset) * 0.1) : int(len(x_array_subset) * 0.9)
            ]
    else:
        self.max_x = np.nan
        self.max_y = np.nan
        self.slope_y = [np.nan]
        self._slope_x = [np.nan]


def find_slope_start(self):
    peaks, _ = signal.find_peaks(
        self.filtered_array[self._fv_x : self._fp_x], width=int(0.5 * self.s_r_c)
    )
    if len(peaks) > 0:
        indices = peaks + self._fv_x
        temp = np.argmax(self.filtered_array[indices])
        self.max_x = indices[temp]
    else:
        self.max_x = self._fv_x + int(1 * self.s_r_c)
    self.max_y = self.filtered_array[self.max_x]


def find_slope_array(self) -> None:
    x_array_subset = np.arange(self.max_x, self._fp_x + 1)
    y_array_subset = self.filtered_array[self.max_x : self._fp_x + 1]
    self.slope_y = y_array_subset[
        int(len(y_array_subset) * 0.1) : int(len(y_array_subset) * 0.9)
    ]
    self._slope_x = x_array_subset[
        int(len(x_array_subset) * 0.1) : int(len(x_array_subset) * 0.9)
    ]
