from typing import Union

import numpy as np


def create_template(
    amplitude: Union[int, float],
    tau_1: Union[int, float],
    tau_2: Union[int, float],
    risepower: Union[int, float],
    length: Union[int, float],
    spacer: Union[int, float] = 1.5,
    sample_rate: int = 10000,
) -> np.ndarray:
    """Creates a template based on several factors.

    Args:
        amplitude (float): Amplitude of template
        tau_1 (float): Rise tau (ms) of template
        tau_2 (float): Decay tau (ms) of template
        risepower (float): Risepower of template
        length (float): Length of time (ms) for template
        spacer (int, optional): Delay (ms) until template starts. Defaults to 1.5.

    Returns:
        np.array: Numpy array of the template.
    """
    s_r_c = sample_rate / 1000
    tau_1 = int(tau_1 * s_r_c)
    tau_2 = int(tau_2 * s_r_c)
    length = int(length * s_r_c)
    spacer = int(spacer * s_r_c)
    template = np.zeros(length + spacer)
    t_length = np.arange(0, length)
    offset = len(template) - length
    Aprime = (tau_2 / tau_1) ** (tau_1 / (tau_1 - tau_2))
    y = (
        amplitude
        / Aprime
        * ((1 - (np.exp(-t_length / tau_1))) ** risepower * np.exp((-t_length / tau_2)))
    )
    template[offset:] = y
    return template


if __name__ == "__main__":
    create_template()
