from typing import Literal, TypeAlias

import numpy as np
from scipy.fft import fft, ifft
from scipy import signal

from ..template_psc import create_template, TemplateParams
from ..filtering import fir_filter, filters


EventMethods: TypeAlias = Literal["fft", "weiner", "template_match"]

def deconvolve_array(
    array: np.ndarray,
    template_params: TemplateParams,
    decon_type: Literal["fft", "weiner"],
    filter_settings: filters.FIRFilter,
    lambd: int | float = 4,
) -> np.ndarray:
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
    template = create_template(**template_params._asdict())

    kernel = np.hstack((template, np.zeros(len(array) - len(template))))
    H = fft(kernel)

    # Choose the method for finding minis. FFT and Wiener are almost identical.
    # Convolution is similar to template fitting (correlation).
    if decon_type == "fft":
        deconvolved_array = np.real(ifft(fft(array) / H))
        deconvolved_array = fir_filter(array, filter_settings)
    elif decon_type == "wiener":
        deconvolved_array = np.real(
            ifft(fft(array) * np.conj(H) / (H * np.conj(H) + lambd**2))
        )
    deconvolved_array = fir_filter(array, filter_settings)
    return deconvolved_array

def template_match(array: np.ndarray, template_params: TemplateParams):
    template = create_template(**template_params._asdict())
    template_match = signal.correlate(array, template, mode="same")
    return template_match

def _rms(array: np.ndarray) -> tuple[float, float]:
    # Get the top and bottom 2.5% cutoff.
    bottom, top = np.percentile(array, [2.5, 97.5])

    # Return the middle values.
    middle = array[(array > bottom) & (array < top)]
    # Calculate the mean and rms.
    mu = np.mean(middle)
    rms = np.sqrt(np.mean(np.square(middle - mu)))

    return mu, rms

def find_events(array: np.ndarray, mini_spacing: float, sensitivity: float) -> list:
    # This is not the method from the original paper but it works a
    # lot better. The original paper used 4*std of the deconvolved array.
    # The problem with that method is that interneurons needs a
    # different sensitivity setting. I wanted to keep the settings as
    # consistent as possible between different cell types.

    mu, rms = _rms(array)

    # Find the events.
    peaks, _ = signal.find_peaks(
        array - mu,
        height=sensitivity * (rms),
        distance=mini_spacing,
        prominence=rms,
    )
    return peaks
