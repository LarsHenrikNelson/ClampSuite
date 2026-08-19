from pathlib import Path

import numpy as np


def _atf_header(array: np.ndarray) -> str:
    cols = array.shape[1] + 1
    header = f"ATF\t1.0\n0\t{cols}     \n"
    columns = ""
    for i in range(cols - 1):
        columns += '""\t'
    columns += '""\n'
    header += columns
    return header


def write_atf(
    data: np.ndarray,
    fs: float,
    filename: str | None = None,
    path: str | Path | None = None,
):
    """Writes a numpy array to an .atf file.

    Args:
        data: Must 2D where cols are signals and rows are samples.
        fs: Sample rate of the data
        filename: Filename to use for atf file. Defaults to None.
        path: Path to save .atf file. If path contains .atf, filename is ignored. Defaults to None.
    """
    offset = int(data.shape[0] * 15625 / 10**6)
    app = np.array([np.zeros(offset), np.zeros(offset)]).T
    output = np.concatenate((app, data, app))
    time = np.arange(output.shape[0]) / fs
    time = time.reshape((time.size, 1))
    output = np.concatenate((time, output), axis=1)
    if filename is None:
        filename = "output"
    if path is not None:
        path = Path(path)
        if ".aft" not in path.stem:
            path = path / filename
    else:
        path = Path.cwd() / f"{filename}.atf"
    header = _atf_header(output)
    with open(path, "w") as wr:
        wr.write(header)
        np.savetxt(wr, output, delimiter="\t", fmt="%.5e")
