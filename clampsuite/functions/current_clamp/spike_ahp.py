import numpy as np

AHP_KEYS = ["ahp_index"]


def find_all_ahps(voltages: np.ndarray, peaks: np.ndarray, pulse_end: int):
    output = np.zeros(len(peaks))
    for index in range(len(peaks)):
        if index < (len(peaks) - 1):
            t = np.argmin(voltages[peaks[index] : peaks[index + 1]]) + peaks[index]
        else:
            t = np.argmin(voltages[peaks[index] : pulse_end]) + peaks[index]
        output[index] = t
    return {"ahp_index": output}
