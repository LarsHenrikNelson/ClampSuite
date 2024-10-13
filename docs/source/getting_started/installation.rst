Installation
----------------
Venv installation
~~~~~~~~~~~~~~~~~~
1. Open a shell or terminal.
2. Create a virtual environment. On Windows I recommend using the Py installer so you can specify the Python version. If you are using Linux or Mac I recommend [Pyenv](https://github.com/pyenv/pyenv) to specify the Python version.
3. Activate the virtual environment.
4. There are a couple ways to install ClampSuite. To install run ``pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git`` for the stable branch (main) or ``pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git@develop`` for the development branch.
5. On run ``python -m clampsuite``

Anaconda
~~~~~~~~
1. Install an `Anaconda <https://www.anaconda.com/download/>`_ or `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ distribution of Python and your operating system. Note you will need to use an anaconda prompt if you did not add anaconda to the path.
2. Open an anaconda prompt if you are on Windows, otherwise open terminal and if (base) is on the commandline then anaconda conda is ready to use.
3. Anaconda has an experimental option for `pip interoperability <https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/pip-interoperability.html>`_ that makes it easier to install packages using pip however this is not need if you install a single program in a dedicated environment.
4. Create a new environment with ``conda create -n clampsuite python=3.11``.
5. To activate this new environment, run ``conda activate clampsuite``.
6. To install run ``pip install git+https://github.com/LarsHenrikNelson/Clampsuite.git``.
7. Install optional depedencies if needed.
8. Now run ``python -m clampsuite`` and you're all set.


Dependencies
~~~~~~~~~~~~~~
-  `bottleneck <https://github.com/pydata/bottleneck>`_
-  `KDEpy <https://kdepy.readthedocs.io/en/latest/index.html>`
-  `numpy <https://numpy.org/>`_
-  `openpyxl <https://openpyxl.readthedocs.io/en/stable/>`_
-  `pandas <https://pandas.pydata.org/>`_
-  `pyqtgraph <https://www.pyqtgraph.org/>`_
-  `PySide6 <http://pyqt.sourceforge.net/Docs/PySide6/>`_
-  `pyyaml <https://pyyaml.org/>`_
-  `qdarkstyle <https://github.com/ColinDuquesnoy/QDarkStyleSheet>`_
-  `scipy <https://scipy.org/>`_
-  `statsmodels <https://www.statsmodels.org/stable/index.html>`_
-  `xlsxwriter <https://github.com/jmcnamara/XlsxWriter>`_

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~~~
-  `h5py <https://www.h5py.org/>`_
-  `matplotlib <https://matplotlib.org/>`_