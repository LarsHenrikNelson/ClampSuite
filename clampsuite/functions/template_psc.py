from dataclasses import dataclass
from typing import Union, NamedTuple

import numpy as np


@dataclass(frozen=True)
class TemplateParams:
    amplitude: float = 15
    rise_tau: float = 0.3
    decay_tau: float = 5
    risepower: float = 0.5
    length: float = 30
    spacer: float = 1.5
    sample_rate: float = 10000


def create_template(
    amplitude: Union[int, float] = -20,
    rise_tau: Union[int, float] = 0.3,
    decay_tau: Union[int, float] = 5,
    risepower: Union[int, float] = 0.5,
    length: Union[int, float] = 30,
    spacer: Union[int, float] = 1.5,
    sample_rate: int = 10000,
) -> np.ndarray:
    """Creates a template based on several factors.

    Args:
        amplitude (float): Amplitude of template
        rise_tau (float): Rise tau (ms) of template
        decay_tau (float): Decay tau (ms) of template
        risepower (float): Risepower of template
        length (float): Length of time (ms) for template
        spacer (int, optional): Delay (ms) until template starts. Defaults to 1.5.

    Returns:
        np.array: Numpy array of the template.
    """
    s_r_c = sample_rate / 1000
    rise_tau = int(rise_tau * s_r_c)
    decay_tau = int(decay_tau * s_r_c)
    length = int(length * s_r_c)
    spacer = int(spacer * s_r_c)
    template = np.zeros(length + spacer)
    t_length = np.arange(0, length)
    offset = len(template) - length
    Aprime = (decay_tau / rise_tau) ** (rise_tau / (rise_tau - decay_tau))
    y = (
        amplitude
        / Aprime
        * (
            (1 - (np.exp(-t_length / rise_tau))) ** risepower
            * np.exp((-t_length / decay_tau))
        )
    )
    template[offset:] = y
    return template
