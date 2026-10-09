from collections.abc import Callable
from typing import Literal, TypeAlias

import numpy as np
from scipy import signal

THRESHOLD_KEYS = ["threshold_index", "threshold_mv"]


def third_derivative(
    derivatives: dict[str, np.ndarray], start: int, end: int, fs: float, **kwargs
):
    dddv = -derivatives["dddv"][start:end]
    curr = dddv.argmax()
    step = max(1, int(fs / 10000))
    while curr > step and (dddv[curr] - dddv[curr - step]) > 0:
        curr -= 1
    return start + curr


def max_curvature(derivatives: dict[str, np.ndarray], start: int, end: int, **kwargs):
    dv = derivatives["dv"][start:end]
    v = derivatives["v"][start:end]
    peak = np.argmax(-1 * (dv / v))
    peak = peak - 2 + start
    return peak


def method_vii(derivatives: dict[str, np.ndarray], start: int, end: int, **kwargs):
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["ddv"][start:end]
    method_vii = ddv * (1 + dv**2) ** (-3 / 2)
    peak = method_vii.argmax() + start
    return peak


def method_ii(derivatives: dict[str, np.ndarray], start: int, end: int, **kwargs):
    dddv = derivatives["dddv"][start:end]
    ddv = derivatives["ddv"][start:end]
    dv = derivatives["dv"][start:end]
    temp = (dddv * dv - ddv**2) / (np.ma.array(dv**3, mask=dv != 0))
    peak = temp.data.argmax() + start
    return peak


def first_derivative(
    derivatives: dict[str, np.ndarray], start: int, end: int, fs: float, **kwargs
):
    dv = derivatives["dv"][start:end]

    peak_idx = dv.argmax()
    gate_10pct = dv[peak_idx] * 0.10

    # Stage 2: Backtrack from peak until velocity drops below 10% gate
    below_gate = np.where(dv[:peak_idx] <= gate_10pct)[0]
    curr = below_gate[-1] if len(below_gate) > 0 else 0

    # Stage 3: Backtrack down the remaining foot until slope stops decreasing
    step = max(1, int(fs / 10000))

    while curr > step and (dv[curr] - dv[curr - step]) > 0:
        curr -= 1

    return start + curr


def second_derivative(
    derivatives: dict[str, np.ndarray], start: int, end: int, fs: float, **kwargs
):
    ddv = derivatives["ddv"][start:end]
    curr = ddv.argmax()
    step = max(1, int(fs / 10000))
    while curr > step and (ddv[curr] - ddv[curr - step]) > 0:
        curr -= 1
    return start + curr


def piecewise_threshold(
    derivatives: dict[str, np.ndarray], start: int, end: int, **kwargs
) -> float:
    """
    Finds spike threshold by calculating the analytical intersection
    of the <10% baseline fit and 10-90% upstroke fit on dV/dt.

    Returns a float representing the sub-sample threshold index.
    """
    dv_seg = derivatives["dv"][start:end]
    peak_idx = dv_seg.argmax()
    peak_val = dv_seg[peak_idx]

    val_5 = peak_val * 0.05
    val_10 = peak_val * 0.10
    val_90 = peak_val * 0.90

    idx_5_matches = np.where(dv_seg <= val_5)[0]
    if len(idx_5_matches) == 0:
        return float(start)
    idx_5 = idx_5_matches[-1]

    # Locate index boundaries on the upstroke
    idx_10_matches = np.where(dv_seg[:peak_idx] <= val_10)[0]
    if len(idx_10_matches) == 0:
        return float(start + peak_idx)
    idx_10 = idx_10_matches[-1]

    idx_90_matches = np.where(dv_seg[:peak_idx] >= val_90)[0]
    idx_90 = idx_90_matches[0] if len(idx_90_matches) > 0 else peak_idx

    # 1. Fit Line 1: Subthreshold Baseline (<10% peak dV/dt)
    x1 = np.arange(0, idx_5 + 1)
    y1 = dv_seg[: idx_5 + 1]
    if len(x1) < 2:
        return float(start + idx_5)
    m1, c1 = np.polyfit(x1, y1, 1)

    # 2. Fit Line 2: Linear Upstroke (10% to 90% peak dV/dt)
    x2 = np.arange(idx_10, idx_90 + 1)
    y2 = dv_seg[idx_10 : idx_90 + 1]
    if len(x2) < 2:
        return float(start + idx_10)
    m2, c2 = np.polyfit(x2, y2, 1)

    # 3. Solve analytical intersection: m1*x + c1 = m2*x + c2
    if abs(m2 - m1) < 1e-6:
        return float(start + idx_10)

    x_intersect = (c1 - c2) / (m2 - m1)

    return float(start + x_intersect)


def legacy(derivatives: dict[str, np.ndarray], start: int, end: int, **kwargs):
    # While many papers use a single threshold to find the threshold
    # potential this does not work if you want to analyze both
    # interneurons and other neuron types. I have created a shifting
    # threshold based on where the maximum velocity occurs of the first
    # spike occurs.
    dv = derivatives["dv"][start:end]
    peak_dv, _ = signal.find_peaks(dv, height=6)
    try:
        peak = (np.argwhere(np.gradient(dv[: peak_dv[0]]) < (0.3))[0] + start)[-1]
    except IndexError:
        peak = np.argmin(dv[: peak_dv[0]]) + start
    finally:
        peak = np.nan
    return peak


def derivative_threshold(
    derivatives: dict[str, np.ndarray],
    start: int,
    end: int,
    threshold: float = 5.0,
    **kwargs,
):
    dv = derivatives["dv"][start:end]
    peak = np.argwhere(dv > threshold)[0][0] + start - 1
    return peak


def percentage_threshold(
    derivatives: dict[str, np.ndarray],
    start: int,
    end: int,
    **kwargs,
):
    dv = derivatives["dv"][start:end]
    peak = np.where(dv > dv.max() * 0.05)[0][0] - 1
    return peak


ThresholdFunctions: dict[str, Callable] = {
    "third_derivative": third_derivative,
    "max_curvature": max_curvature,
    "method_vii": method_vii,
    "method_ii": method_ii,
    "first_derivative": first_derivative,
    "second_derivative": second_derivative,
    "legacy": legacy,
    "allen_institute": derivative_threshold,
    "percentage": percentage_threshold,
    "piecewise": piecewise_threshold,
}

ThresholdType: TypeAlias = Literal[
    "third_derivative",
    "max_curvature",
    "method_vii",
    "method_ii",
    "first_derivative",
    "second_derivative",
    "legacy",
    "allen_institute",
    "percentage",
]


def find_all_spk_thresholds(
    voltages: np.ndarray,
    peaks: np.ndarray,
    pulse_start: int = 0,
    threshold_method: ThresholdType = "third_derivative",
):
    output = np.zeros(len(peaks), dtype=int)
    dv = np.gradient(voltages)
    ddv = np.gradient(dv)
    dddv = np.gradient(ddv)
    derivatives = {"v": voltages, "dv": dv, "ddv": ddv, "dddv": dddv}
    if threshold_method == "allen_institute":
        threshold: list[float] = []
        for index, peak in enumerate(peaks):
            if index == 0:
                threshold.append(np.max(dv[pulse_start:peak]))
            else:
                threshold.append(np.max(dv[peaks[index - 1], peak]))
            threshold_value = float(np.mean(threshold))
    thresh_func = ThresholdFunctions[threshold_method]
    for index in range(len(peaks)):
        end_index = peaks[index]
        if index > 0:
            start_index = (
                voltages[peaks[index - 1] : peaks[index]].argmin() + peaks[index - 1]
            )
        else:
            start_index = int((peaks[index] - pulse_start) * 0.1) + pulse_start
        try:
            if threshold_method == "allen_institute":
                output[index] = derivative_threshold(
                    derivatives, start_index, end_index, threshold_value
                )
            else:
                output[index] = thresh_func(derivatives, start_index, end_index)
        except IndexError:
            output[index] = ThresholdFunctions["first_derivative"](
                derivatives, start_index, end_index
            )
        except IndexError:
            output[index] = start_index
    return {"threshold_index": output, "threshold_mv": voltages[output]}
