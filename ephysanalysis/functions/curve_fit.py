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

