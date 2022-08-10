import setuptools

install_deps = [
    "numpy",
    "pyqt5",
    "statmodels",
    "scipy",
    "scikit-learn",
    "matplotlib" "qdarkstyle",
    "pyqt",
    "pyqtgraph",
    "pandas",
    "yaml",
]

setuptools.setup(
    name="ephysanalysis",
    author="Lars Henrik Nelson",
    author_email="larshnelson@protonmail.com",
    version="0.1.9",
    description="Program for analyzing slice ephys data",
    url="",
    python_requires=">=3.9.12",
    packages=setuptools.findpackages(),
    install_requires=install_deps,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["ephysanalysis = ephysanalysis.__main__:main",]},
)
