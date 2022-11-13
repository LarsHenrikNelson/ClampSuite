Filtering tutorial
--------------------

Filtering is one of the most important steps and is usually the first step
in analyzing a time-based signal. ClampSuite includes FIR filters, minimal-phase
filters (Bessel), and other filters such as the exponentially weighted moving
average (EWMA), Savgol and median filter. All these filters are based off of SciPy
filters.

ClampSuite filters signals by first removing the mean from the selected baseline.
This removes any DC offset for the signal and usually provides enough of a high pass
filter that one is not need when implementing future filtering. Then the signal is filtered
using one of the selected filters.

For filters that need to have a low-pass and high-pass specified (fir, bessel, remez)
leave the input field black if you don't want to implement either or low pass or high pass.
I recommend implementing a loww pass around 500-600. A high pass is technically not need
since the DC offset if removed. If you choose to implement a high pass filter I would
recommend a cutoff no higher than 0.1. High pass filtering is usually used in situations where
you want to recover a high frequency signal such as getting spikes from the wideband signal
in recorded extracellularly. However for patch clamp ephys high pass filtering can introduce
artifacts or degrade your signal. For further explanation see this webpage.

FIR filters
~~~~~~~~~~~~
Finite impulse response (FIR) filters are the filter I would recommend using. The FIR filters
included in ClampSuite are fir_zero_1, fir_zero_2, remez_1, and remez_2. All of these
filters are (mostly) zerophase filters which means that they will not cause a shift in the timing
of the signal that they are filtering however they achieve zerophase filtering through
different means. Fir_zero_1 and remez_1 filter the signal in the forward and backwards
direction to achieve a zerophase filter. This also has the effect of increasing the
magnitude (effectiveness/degree) of the filtering. Fir_zero_2 and remez_2 implement a trick
that allows for filtering in one direction while acheiving zerophase. If you implement an even
ordered filter then the signal will be shifted forward by one sample due to the method used to
achieve the zerophase response. See this Matlab discussion for more imformation: website.

To implement the fir_zero_1 and fir_zero_2 filters you will need to make sure the following
information is input in the GUI: order, high pass, high width, low pass, low width, window type,
and beta/sigma. The window types included are: hann, hamming, blackmanharris, barthann, nuttal,
blackman, tukey, kaiser, gaussian, parzen and exponential. I would recommend using the hann or
hamming window. If you select the kaiser or gaussian window you will need to supply a beta/sigma
value.

To implement the remez_1 and remez_2 filters you will need to make sure the following
information is input in the GUI: order, high pass, high width, low pass, low width.
The Remez filter is a non-windowed FIR filter. I have noticed that the Remez filter
cannot implement sharp cutoffs for low or high pass filters.

The order of the filter depends on the how small the low width and high width are. A good
starting order is 151 for a width of 600 and 251 for a width of 300.

The FIR filters also need a width specified if the high pass or low pass is specified.
Low width and high width specify the width of the filters cutoff for the gain to go from
one to zero. The frequency at which the gain will be zero is low pass - low width or 
high pass + high width. I implemented the filters this way because this is how SciPy
does so in their tutorials.

Minimal-phase filters
~~~~~~~~~~~~~~~~~~~~~~~~
Minimal-phase filters are the digital version of the classic Bessel and Butterworth filters
Clampsuite has implementations of bessel, butterworth, bessel_zero, and butterworth_zero. 
The bessel and butterworth filters will affect the phase of you signal depending
on the frequency present. Bessel_zero and butterworth_zero are zerophase implementations
of the bessel and butterworth filters. The zero phase filters filter in both directions
and will filter your signal with double the magnitude.

To implement these filters you need to make sure the following information is input in
the GUI: order, high pass and low pass. The order needs to be an even value and specificies
the steepneess of the filter cutoff where 2 is less steep than 4.

Other filters
~~~~~~~~~~~~~~~~
The other filters are primarily moving window filters that are not frequency based like
the FIR and minimal-phase filters. The median filter only needs the orderinput, and the ewma,
ewma_a, and savgol filters needs both the order and polyorder/sum proportion specified. 
For these filters the larger the order the more the signal is filtered and the more potential
for artifacts. And order of 10-15 is usually sufficient. The order is the number of samples
included in the window.

The median filter just finds the median from a window the size specified by the order input.
The median filter repeats this step 
