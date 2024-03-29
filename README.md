# Clampsuite <img src="clampsuite/logo/d_logo.png" width="100" title="clampsuite" align="right">

&nbsp;&nbsp;&nbsp;&nbsp;ClampSuite (v0.0.4) is a suite of programs for analyzing slice electrophysiology data. The program can analyze data from ScanImage files (.mat) for current clamp, s/mEPSC, and o/eEPSC experiments. The program runs on both PC and intel-based Macs. ClampSuite has not been tested on M1 Mac or Linux. ClampSuite should run on both newer and older computers (it runs well on my 9 year old MacBook Pro and iMac). In addition to providing a GUI for analysis you can call the acquisition classes used by the program to load your data into a Python script which is convient for creating figures for publication or for further analyzing your data. The program is not currently able to analyze other common electrophysiology file types however if you would like to use the program and have a file type that is not supported please send me some files and I can probably add support within a couple weeks. If want to test ClampSuite before you commit to using ClampSuite you can download some test files here: https://gin.g-node.org/LarsHenrikNelson/ClampSuite. Each folder contains example ScanImage acquisitions and a preferences file.

&nbsp;&nbsp;&nbsp;&nbsp;There are currently four different modules: MiniAnalysis, Current Clamp, oEPSC/LFP and Filter design. The program exports user settings for the interface, an individual JSON file for each acquisition, and an Excel file for the raw and processed data. Each module is built to allow the user to delete acquisitions, events or modify baselines or peak values. Each module allows for drag and drop to loading of files for analysis or to reload already analyzed files. As of now older ClampSuite json files may load but the data limit may not show correctly.

## Installation for Anaconda
1. Install an [Anaconda](https://www.anaconda.com/download/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) distribution of Python and your operating system. Note you will need to use an anaconda prompt if you did not add anaconda to the path.
2. Open an anaconda prompt / command prompt with `conda` for **python 3** in the path
3. Create a new environment with `conda create --name clampsuite python=3.10`.
4. To activate this new environment, run `conda activate clampsuite`
5. Anaconda has an experimental option for [pip interoperability](https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/pip-interoperability.html) that makes it easier to install packages using pip.
6. To install run `pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git` for the stable branch (main) or `pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git@develop` for the development branch.
7. Now run `python - m clampsuite` and you're all set.
8. Running the command `pip show clampsuite` in the terminal will print the details of the version of clampsuite you installed.

## Venv installation
1. Open a shell or terminal.
2. Create a virtual environment. On Windows I recommend using the Py installer so you can specify the Python version. If you are using Linux or Mac I recommend [Pyenv](https://github.com/pyenv/pyenv) to specify the Python version.
3. Activate the virtual environment.
4. To install run`pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git` for the stable branch (main) or `pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git@develop` for the development branch.
5. Run `python -m clampsuite`


<br/>

## Usage
&nbsp;&nbsp;&nbsp;&nbsp;Instructions on how to use ClampSuite are avaible [here](https://clampsuite.readthedocs.io) but are still under construction.

<br/>

---

<br/>

## Modules

### Mini Analysis
&nbsp;&nbsp;&nbsp;&nbsp;Mini Analysis can analyze both inward and outward currents using a variation of the fft deconvolution method as well as the original method [fft deconvolution method](https://pubmed.ncbi.nlm.nih.gov/23062335/). While the fft deconvolution requires a template, the template shape is not as crucial as it is for template matching algorithms. The module allows for control over filtering, offering a variatey for minimal-(Bessel, Butterworth), zero-phase filters (windowed FIR and Remez) and other useful filters.

&nbsp;&nbsp;&nbsp;&nbsp; Mini Analysis analyzes the amplitude, rise time (time from baseline to the peak), rise rate (10-90%) and the estimated tau (2/3 peak amplitude or amplitude/e^1) for each event. The program can curve fit taus however, the curve fit function is not fully functional is mostly for visual inspection. 

<img src="clampsuite/images/mini-analysis.png" title="mini analysis widget" align="right">


<br/>

### oEPSC/LFP
&nbsp;&nbsp;&nbsp;&nbsp; The oEPSC/LFP module analyzes optically/electrically evoked intracellular currents and/or LFP signals. For I/EPSCs the program finds the maximum current within a specified window. Windowed peak finding is necessary for NMDA current analysis if AMPAR . The program can also find the charge transfer, estimate the tau and curve-fit to find the tau. For LFPs the program finds the peak fiber volley, field potential, and the field potential rise slope. Future additions to the program will include multi-peak analysis.
<img src="clampsuite/images/oepsc-lfp.png" title="oepsc-lfp widget" align="right">

<br/>

### Current Clamp
&nbsp;&nbsp;&nbsp;&nbsp; The current clamp module analyzes evoked potentials. The program analyzes the delta-V, spike frequency, rheobase, and spike-threshold. Additional analysis on the first spike of acquisitions that contain spikes include, peak spike voltage, first spike peak velocity, peak afterhyperpolarization potential. The program can compile all the data for ease of analysis if the pulse amplitude is include in the analysis file. The program can analyze upwards of 400 acquisitions in around a minute.
<img src="clampsuite/images/current-clamp.png" title="current clamp widget" align="right">

<br/>

### Filter design
&nbsp;&nbsp;&nbsp;&nbsp; The last module is a filter design tool. This tool allows you to compare different filter types. Filtering has a huge impact on signal analysis.

<img src="clampsuite/images/filter-widget.png" title="filter-widget" align="right">

<br/>

---

<br/>

## Output file types
&nbsp;&nbsp;&nbsp;&nbsp;User settings files: The user settings are exported as a YAML file (essentially a text file) so that settings can be modified outside the program. Individual
settings specific to each analysis session are also exported when the data is saved.

&nbsp;&nbsp;&nbsp;&nbsp;Analyzed acquistion files: I chose to export acquisition data in a JSON file for a couple reasons. While JSON is not the most efficient for large arrays of data they are portable and can be opened in any programming language as well as a web browser. JSON files are also good for storing many different data types which are generated by the program. The reason I chose to generate a JSON file for each aquisition is that you can have all the data needed without opening a large file. The JSON file in Python returns a dictionary which is easy to work with.

&nbsp;&nbsp;&nbsp;&nbsp;Final data files: I chose excel files to output the raw and processed final data because they allow for bundling multiple dataframes into one file (one sheet per dataframe) and most people are familiar with this filetype.

<br/>

---

<br/>