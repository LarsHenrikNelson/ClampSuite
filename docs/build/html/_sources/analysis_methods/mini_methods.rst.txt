.. _mini_methods:

Mini methods
================
This section describes how mini or spontaneous postsynaptic events are found in the Mini
analysis module of ClampSuite to make the program less of a black box.

Background
~~~~~~~~~~~~
Automatic identification mini or spontaneous postsynaptic events is a somewhat challenging
analysis. Many programs use template matching. This essentially slides a template mini along
a signal and finds areas where of that highly overlap the template. Template matching works
well except if events have a large variance in amplitude and decay tau. There is a better
method. The method was first published in the paper Pernia-Andrade et al., 2012 from Peter
Jonas' lab. The Pernia-Andrade method uses FFT deconvolution to find mini events.

FFT deconvolution
~~~~~~~~~~~~~~~~~~~~~~~~
The FFT deconvolution method is pretty good method to find postsynaptic events. Deconvolution
is used to recover an original signal that has passed through some filter. Ideally you know
what the filter is and in the case of a postsynaptic event we know an equation to describe a 
postsynaptic event shown in python.

::

    Aprime = (tau_2 / tau_1) ** (tau_1 / (tau_1 - tau_2))
    y = (amplitude / Aprime * ((1 - (np.exp(-t_length / tau_1))) ** risepower * np.exp((-t_length / tau_2))))

In the case of the postsynaptic event imagine there is signal at zero except for random points that are
some height above the 