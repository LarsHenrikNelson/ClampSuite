Installation
----------------
Anaconda
~~~~~~~~
1. Install an `Anaconda <https://www.anaconda.com/download/>`_ or `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ distribution of Python and your operating system. Note you will need to use an anaconda prompt if you did not add anaconda to the path.
2. Open an anaconda prompt if you are on Windows, otherwise open terminal and if (base) is on the commandline then anaconda conda is ready to use.
3. Anaconda has an experimental option for `pip interoperability <https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/pip-interoperability.html>`_ that makes it easier to install packages using pip however this is not need if you install a single program in a dedicated environment.
4. Create a new environment with ``conda create -n clampsuite python=3.10``.
5. To activate this new environment, run ``conda activate clampsuite``.
6. To install run ``pip install clampsuite``.
7. Install optional depedencies if needed.
8. Now run ``python -m clampsuite`` and you're all set.
9.  Running the command ``clampsuite --version`` in the terminal will print the install version of clampsuite.

Alternative
~~~~~~~~~~~~
You can also run the package with out installing it by downloading the package from Github `<https://github.com/LarsHenrikNelson/ClampSuite>`_. There 
are two branches, main and develop. The main branch will always be a stable version of ClampSuite and the develop branch will contain the newest 
additions but may not be stable.

1. Install an `Anaconda <https://www.anaconda.com/download/>`_ distribution of Python and your operating system. You might need to use an anaconda prompt if you did not add anaconda to the path.
2. For windows open Anaconda prompt. If you are on Mac open terminal and if (base) is on the commandline then anaconda conda is ready to use.
3. Create a new environment using the env.yaml file by typing ``conda create -f`` then drag and drop the env.yaml file into prompt/terminal and hit enter.
4. To activate this new environment, run ``conda activate clampsuite``.
5. Type ``cd`` the drag and drop the ClampSuite folder into the terminal and hit enter
6. Now run ``python -m clampsuite`` and you're all set.

Dependencies
~~~~~~~~~~~~~~
-  `bottleneck <https://github.com/pydata/bottleneck>`_
-  `numpy <https://numpy.org/>`_
-  `openpyxl <https://openpyxl.readthedocs.io/en/stable/>`_
-  `pandas <https://pandas.pydata.org/>`_
-  `pyqtgraph <https://www.pyqtgraph.org/>`_
-  `PyQt5 <http://pyqt.sourceforge.net/Docs/PyQt5/>`_
-  `pyyaml <https://pyyaml.org/>`_
-  `qdarkstyle <https://github.com/ColinDuquesnoy/QDarkStyleSheet>`_
-  `scikit-learn <https://scikit-learn.org/stable/>`_
-  `scipy <https://scipy.org/>`_
-  `statsmodels <https://www.statsmodels.org/stable/index.html>`_
-  `xlsxwriter <https://github.com/jmcnamara/XlsxWriter>`_

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~~~
-  `h5py <https://www.h5py.org/>`_
-  `matplotlib <https://matplotlib.org/>`_