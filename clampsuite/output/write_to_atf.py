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
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    n_samples, n_channels = data.shape

    # 2. Pad trailing edge to the nearest multiple of 64 (Digidata DMA buffer block)
    remainder = n_samples % 64
    if remainder != 0:
        pad_size = 64 - remainder
        padding = np.zeros((pad_size, n_channels))
        output_data = np.vstack((data, padding))
    else:
        output_data = data

    # 3. Construct time vector column matching exact sampling rate
    time = np.arange(output_data.shape[0]) / fs
    output = np.hstack((time.reshape(-1, 1), output_data))

    # 4. Handle file path resolution correctly
    if filename is None:
        filename = "output"

    if path is not None:
        target_path = Path(path)
        if target_path.suffix.lower() != ".atf":
            target_path = target_path / f"{filename}.atf"
    else:
        target_path = Path.cwd() / f"{filename}.atf"

    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. Write ATF file
    header = _atf_header(output)
    with open(target_path, "w") as wr:
        wr.write(header)
        np.savetxt(wr, output, delimiter="\t", fmt="%.5e")
