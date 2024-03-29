oEPSC/LFP
===========

The oEPSC/LFP module is designed to analyzed either evoked PSCs or LFPs or both. 
Both outward (positive) and inward currents can be automatically analyzed for evoked
PSCs. The program does not currently support analyzing multiple peaks for evoked PSCs.
oEPSC/LFP has three steps: Setup, Analysis, and Final data.

Setup
~~~~~~~~~
To begin analyzing data just drap and drop your files into into the acquistion part of
the GUI.

.. image:: _static/oepsc-lfp-setup.png
    :scale: 50
    :align: center

Filtering
--------------
For an in-depth discussion of filtering see the :doc:`filtering tutorial </analysis_methods/filtering>`.
Filtering can change the amplitude, rise rate/time and tau of the events so it is important
to keep the filtering settings the same for each experiment.

oEPSC setttings
---------------------
There are several settings for evoked PSC. The reason the module uses windows is for measuring
NMDAR currents when there are contaminating AMPAR currents. If NMDAR currents are recorded at
+40 mV with a standard interenl (low K+) and AMPA receptors are not blocked, AMPAR currents make
up the first portion of the positive currents. The NMDAR currents have a slow onset so the peak
can be measured after the AMPAR currents begin to decrease which is around 45 ms after the start
of the pulse. 

* **Pulse start**: The pulse start is the when the electrical or optical stimulation occurs
  you need to specify this so that the baseline and charge transfer can be measured.
* **Negative window start**: The negative window start sets when to start looking for the peak
  negative current.
* **Negative window end**: The negative window end sets when to stop looking for the peak
  negative current.
* **Positive window start**: The positive window start sets when to start looking for the peak
  positive current.
* **Positive window end**: The positive window end sets when to stop looking for the peak
  positive current.
* **Charge transfer**: Check the box to measure the charge transfer. The charge transfer is the
  just the area under the curve so it measures the total current.
* **Est decay**: Check the box to measure the estimated decay. The estimated decay is about 2/3
  of the peak amplitude found by using this equation: peak * (1 / exp(1)).
* **Curve fit decay**: Check the box to curve fit the decay. If your currents are large (> 200 pA)
  curve fitting will likely give the exact same answer as estimating the decay.
* **Curve fit type**: Select the curve fit type: s_exp is a single exponential decay fit by minimizing
  this equation: peak * exp((-x_array) / tau). db_exp is a double exponential decay fit by
  minimizing this equation: (amp_1 * exp((-x_array) / tau_1)) + (amp_2 * exp((-x_array) / tau_2)).

LFP setttings
-----------------
LFPs only need filtering (see :doc:`filtering tutorial </analysis_methods/filtering>`) and the pulse 
start specified.
* **Pulse start**: The pulse start is the when the electrical or optical stimulation occurs you need
|  to specify this so that the baseline and charge transfer can be measured.

Buttons
------------
* **Analyze acquisition(s)**: Starts the analysis. Once the data is finished analyzing the
  the Analysis tab will be automatically opened.
* **Final analysis**: Runs the final analysis. There is also a final analysis button on the
  Analysis tab. They both compile and show the final data in the Final Data tab.
* **Reset analysis**: This resets the analysis and removes the acquisitions but keeps the
  settings.


Analysis
~~~~~~~~~~~~
The analysis tab has two main windows. The left window is for evoked PSCs and the right window
is for LFPs. Both windows share the **Acquisition** spinbox

.. image:: _static/oepsc-lfp.png
    :scale: 50
    :align: center

* **Acquisition**: This spinbox is used to select the acquisition you want to view. Values
  can be changed using the arrow buttons or by inputing a number and hitting enter.
* **Epoch**: Shows the epoch of the aquisition. Epoch is using by ScanImage to define when
  what cell your are recording. For file types that include many acquisitions each file will be
  assigned an epoch. For file types that contain a single acquisition and do not specify epoch
  you can edit the epoch by typing in the epoch number and hitting enter.
* **Final analysis**: Click the button to run the final analysis.

oEPSC
---------
* **Amplitude (pA)**: The amplitude of the evoked PSC.
* **Charge transfer**: The charge transfer of the evoked PSC.
* **Est decay (ms)**: The estimated decay of the evoked PSC.
* **Fit decay (ms)**: The fit decay of the evoked PSC.
* **Set point as peak**: Select a point on the PSC plot and click the button to set the point
  as the peak.
* **Delete oEPSC**: Click the button to delete the current oEPSC.

LFP
--------
* **Fiber volley (mV)**: Amplitude of the fiber volley in millivolts.
* **Field potential (mV)**: Amplitude of the field potential in millivolts.
* **Set point as fiber volley**: Select a point on the LFP plot and click the button to set the
  point as the fiber volley.
* **Set point as field potential**: Select a point on the LFP plot and click the button to set the
  point as the field potential.
* **Set point as slope start**: Select a point on the LFP plot and click teh button to set the
  point as the start of the fiber volley to field potential slope.
* **Delete LFP**: Click the button to delete the current LFP.


Final data
~~~~~~~~~~~~~~~
The Final data tab contains the raw and final data. 

.. image:: _static/oepsc-lfp-final.png
    :scale: 50
    :align: center