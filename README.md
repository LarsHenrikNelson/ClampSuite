# ClamPy version 0.1
&nbsp;&nbsp;&nbsp;&nbsp;ClamPy is a program for analyzing slice electrophysiology data. The program can analyze data from ScanImage files (.mat) for current clamp, s/mEPSC, and o/eEPSC experiments. The program runs on both PC and Mac (I don't have a Linux machine to test on) and does not necessarily need a new computer to run (It runs perfectly well on my 7 year MacBook Pro). You can call the acquisition classes to load your data into a Python script which is convient for creating figures for publication or for further analyzing your data. The program is not currently able to analyze other common electrophysiology file types however if you would like to use the program and have a file type that is not supported please send me some files and I can probably add support within a couple weeks.

&nbsp;&nbsp;&nbsp;&nbsp;There are currently four different modules: MiniAnalysis, Current Clamp, oEPSC/LFP and Filter design. The program exports user settings for the interface, an individual JSON file for each acquisition, and an Excel file for the raw and processed data. Each module is built to allow the user to delete acquisitions, events or modify baselines or peak values. Each module allows for drag and drop to loading of files for analysis or to reload already analyzed files.

<br/>

---

<br/>

## Modules

### MiniAnalysis
&nbsp;&nbsp;&nbsp;&nbsp;Minianalysis is setup to analyze both inward and outward currents using a variation of the fft deconvolution method as well as the original method [fft deconvolution method](https://pubmed.ncbi.nlm.nih.gov/23062335/). While the fft deconvolution requires a template, the template shape is not as crucial as it is for template matching algorithms. The module allows for control over filtering, offering a variatey for minimal-(Bessel, Butterworth), zero-phase filters (windowed FIR and Remez), median filter, and Savitsky-Golay filter. 

&nbsp;&nbsp;&nbsp;&nbsp;Currently the program analyzes amplitude of the event, rise time (time from baseline to the peak), rise rate (10-90%) and the estimated tau (2/3 peak amplitude or amplitude/e^1). The program can curve fit taus however, the curve fit function still needs some work and is mostly for visual inspection. 

The program also shows the final data in a couple ways that I have found informative such as stemplot for all event parameters and a kde plot for cumulative events parameters.

<br/>

### oEPSC/LFP
&nbsp;&nbsp;&nbsp;&nbsp; The oEPSC/LFP module analyzes optically/electrically evoked intracellular currents and/or LFP signals. For I/EPSCs the program finds the maximum current within a specified window. Windowed peak finding is necessary for NMDA current analysis if AMPAR . The program can also find the charge transfer, estimate the tau and curve-fit to find the tau. For LFPs the program finds the peak fiber volley, field potential, and the field potential rise slope. Future additions to the program will include multi-peak analysis.

<br/>

### Current Clamp
&nbsp;&nbsp;&nbsp;&nbsp; The current clamp module analyzes evoked potentials. The program analyzes the delta-V, spike frequency, rheobase, and spike-threshold. Additional analysis on the first spike of acquisitions that contain spikes include, peak spike voltage, first spike peak velocity, peak afterhyperpolarization potential. The program can compile all the data for ease of analysis if the pulse amplitude is include in the analysis file. The program can analyze upwards of 400 acquisitions in around a minute.

<br/>

### Filter design
&nbsp;&nbsp;&nbsp;&nbsp; The last module is a filter design tool. I initially built the GUI to experiment with different filtering techniques since filtering can have a huge impact on the quality of the analysis. 

<br/>

---

<br/>

## Design philosophy
&nbsp;&nbsp;&nbsp;&nbsp;I learned how to code by creating this program so I did not start out with some overarching design philosophy that other more experienced programmers might follow. I designed this program based on what my lab wanted to have from an ephys analysis program.

<br/>

### Open source
&nbsp;&nbsp;&nbsp;&nbsp;This program is and will always be open source.

<br/>

### Usability
&nbsp;&nbsp;&nbsp;&nbsp;Over the years I have heard many complaints about scientific software that is clunky and hard to use. With this program I created modules to analyze specific types of slice electrophysiology data with the intent that it would get you from the raw data to processed data faster without having to spend a week tweaking the parameters or take hours just to process data from a single cell.

&nbsp;&nbsp;&nbsp;&nbsp;I also designed this program in a way that I hope others can look at the code and understand how to parameters are calculated. I am currently in the process of fully commenting out the code so that each step of analysis is explained. We have a custom mini analysis program written in Igor Pro however, the code is hard to understand because Igor's syntax is not like a lot of programming languages. Lastly where ever I learned something from someone else's code or used and modified their code I made sure to include links to where I found the code. I want to make my code as little of a blackbox as possible.

<br/>

### Output file types
&nbsp;&nbsp;&nbsp;&nbsp;User settings files: The user settings are exported as a YAML file (essentially a text file) so that settings can be modified outside the program. 

&nbsp;&nbsp;&nbsp;&nbsp;Analyzed acquistion files: I chose to export acquisition data in a JSON file for a couple reasons. While JSON is not the most efficient for large arrays of data they are portable and can be opened in any programming language as well as a web browser. JSON files are also good for storing many different data types which are generated by the program. The reason I chose to generate a JSON file for each aquisition is that you can have all the data needed without opening a large file. The JSON file in Python just returns are dictionary which are easy to work with.

&nbsp;&nbsp;&nbsp;&nbsp;Final data files: I chose excel files to output the raw and processed final data because they allow for bundling multiple dataframes into one file (one sheet per dataframe) and most people are familiar with this filetype.

<br/>

---

<br/>

## To Do
- Add multi-peak finding for o/eEPSC module.
- Add acquisition manager to make it easier to integrate other file types and add load data for publication or further analysis
- Improve mini analysis decay curve fit.
- Save last used user settings.
- Add more color themes.
- Add performance stats to monitor memory and CPU usage.
- Integrate logging for debugging and performance issues.
