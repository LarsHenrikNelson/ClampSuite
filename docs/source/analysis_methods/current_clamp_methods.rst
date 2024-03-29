.. _current_clamp_methods:

Current clamp methods
======================
This section describes how current clamp acquisition are analyzed in the Current Clamp module of 
ClampSuite to make the program less of a black box. For an explanation
on how to use the GUI see: :doc:`current clamp </modules/current_clamp>`.

Background
~~~~~~~~~~~~
Analyzing current clamp acquisitions can be split into two main analysis sections: acquisitions without
spikes and those with spikes. Acquisitions with out spikes and those with spikes. Acquisitions with spikes
can be be further divided into acquisitions that are pulses and those that are ramps. ClampSuite can analyzed
pulses and ramps. The analyses for acquisitions without spikes includes delta v and voltage sag. The analysis 
acquisitions with spikes includes spike threshold, rheobase, spike frequency, spike frequency adaptation,
spike half-width, spike velocity, peak spike voltage and after-hyperpolarization potential. I will walk through
each of the analysis sections. The analysis sections occur in the order that ClampSuite analyzes the data.


Delta V
~~~~~~~~
Delta V is just the change in voltage from baseline to the mean of the voltage during the pulse. It is best to 
take the mean from the last 50% because cells might have voltage sag. However in practice the voltage sag usually
occurs in the first 10% and is usually not very large so it will contribute very little to the mean. The delta V
then is the mean of the pulse minus the baseline. Delta_v of the acquisitions with spikes can be calculated using
the spike threshold or by heavily smoothing the acquisition to minimize the influence of spikes and after-hyperpolarization.
ClampSuite uses the smoothing method since the spike threshold is already calculated.

Voltage sag
~~~~~~~~~~~~
Voltage sag occurs when the voltage at the start of the pulse is lower than the voltage at the end of the pulse.
Voltage sag is calculated by taking the difference between the minimum of the beginning of the pulse and 
the mean ending of the pulse. Voltage sag is caused by Ih currents. You can test for effects of Ih currents
by using ZD-7288 to block Ih currents during a flow-in experiment. The actual Ih currents can be tested in 
voltage clamp. Current clamp measures the effect Ih currents have on the cell voltage in response to current
input. Not all cells have Ih currents, medium spiny neurons in the dorsal striatum do not express the HCN channels.

Baseline stability
~~~~~~~~~~~~~~~~~~~~~
Baseline stability is absolute value of difference between the acquisition baseline before and after the pulse.
This measure is used by the Allen Brain Institute to determine whether a cell will be include in their
patch-seq experiments.

Spikes 
~~~~~~~
Spikes are fairly easy to find. ClampSuite just uses Scipy finds_peaks function. The two settings that ClampSuite
uses are: height and prominence. Height which is set by the threshold input during the analysis setup. prominence
is set internally and used to make sure is not picked up.

