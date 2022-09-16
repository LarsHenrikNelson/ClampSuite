import numpy as np


def s_exp_decay(x_array, amp_1, tau_1):
    y = amp_1 * np.exp((-x_array) / tau_1)
    return y


def db_exp_decay(x_array, amp_1, tau_1, amp_2, tau_2):
    y = (amp_1 * np.exp((-x_array) / tau_1)) + (amp_2 * np.exp((-x_array) / tau_2))
    return y


def t_exp_decay(x_array, amp_1, tau_1, amp_2, tau_2, amp_3, tau_3):
    y = (
        (amp_1 * np.exp((-x_array) / tau_1))
        + (amp_2 * np.exp((-x_array) / tau_2))
        + (amp_3 * np.exp((-x_array) / tau_3))
    )
    return y


def est_decay(event_array, event_peak_x, event_start_y):
    event_array
    return_to_baseline = int(
        (np.argmax(event_array[event_peak_x:] >= event_peak_y * 0.25)) + event_peak_x
    )
    decay_y = event_array[event_peak_x:return_to_baseline]
    if decay_y.size > 0:
        est_tau_y = ((event_peak_y - event_start_y) * (1 / np.exp(1))) + event_start_y
        decay_x = x_array[event_peak_x - array_start : return_to_baseline]
        est_tau_x = np.interp(est_tau_y, decay_y, decay_x)
    else:
        est_tau_x = np.nan
        est_tau_y = np.nan
    return est_tau_y, est_tau_x
