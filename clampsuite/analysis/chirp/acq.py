from ty_extensions._internal import Unknown
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal
from pathlib import Path

import numpy as np
from scipy import signal, fft

from ...functions.general import baseline_stability, delta
from ...functions.utilities import map_keys
from ...loader import AcquisitionData
from ..base import BaseAcquisitionAnalysis, BaseAcquisitionConfig
from ..registry import register_acq_config, register_acquisition


@register_acq_config
@dataclass(frozen=True)
class ChirpAcquisitionConfig(BaseAcquisitionConfig):
    """Configuration class for current clamp acquisition analysis.

    Attributes:
        chirp: The chirp used for the stimulus. Can be a numpy array, Path or str. Path
        or str must be to a .atf file. If .atf file is provided acquisition number will
        automatically be mapped to chirp sequence used in the .atf file.
        f0: The starting frequency of the chirp.
        f1: The ending frequency of the chirp.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "chirp"

    chirp: np.ndarray | Path | str
    f0: float
    f1: float


@register_acquisition
@dataclass
class ChirpAcquisition(BaseAcquisitionAnalysis):
    """Chirp acquisition analysis class

    Attributes:
        acq_data: Raw acquisition data and metadata (inherited from
            ``BaseAcquisitionAnalysis``), including pulse timing and
            sampling rate.
    """

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "chirp"

    def __post_init__(self):
        self._analysis_variables["q"] = np.nan
        self._analysis_variables["frequency_hz"] = np.nan
        self._analysis_variables["impedance_mOhm"] = np.nan
        self.config: ChirpAcquisitionConfig | None = None

    def _load_chirp(self, chirp):
        if isinstance(chirp, (Path, str)):
            temp = Path(chirp)
            chirp = np.loadtxt(
                temp,
                delimiter="\t",
                skiprows=3,
            )[:, 1:]
            return chirp
        else:
            return chirp

    def analyze(self, config: ChirpAcquisitionConfig) -> None:
        """Analyzes the ``AcquisitionData``.

        Args:
            config (ChirpAcquisitionConfig): _description_
        """
        self.config = config
        freqs, z = self.z()
        self["q"] = z.max() / z[0]

        indx = z.argmax()
        self["frequency_hz"] = freqs[indx]
        self["impedance_MOhm"] = z[indx]

    def z(self):
        if self.config is None:
            raise ValueError("Config not loaded. Analyze data first.")
        # Load data
        chirp: Unknown = self._load_chirp(self.config.chirp)
        chirp = chirp[:, self.acq_data.acq_number - 1]
        acquisition = self.acq_data.acquisition
        acquisition = acquisition[: chirp.size]

        # Create Z
        fastest = fft.next_fast_len(chirp.size)
        c_fft = fft.rfft(chirp, n=fastest)
        a_fft = fft.rfft(acquisition, n=fastest)
        z = ((np.abs(a_fft) / np.abs(c_fft)) / np.abs(c_fft) ** 2) * 1000
        freqs = fft.rfftfreq(fastest, 1 / self.acq_data.fs)
        mask = (freqs > self.config.f0) & (freqs < self.config.f1)
        return freqs[mask], z[mask]

    def data(
        self, output_type: Literal["ms", "samples"] = "ms", format_keys: bool = False
    ) -> tuple[dict, dict]:
        acq_data = self._analysis_variables.copy()
        freqs, z = self.z()
        freq_data = {"frequency_hz": freqs, "impedance_MOhm": z}
        if format_keys:
            key_mapper = map_keys(acq_data.keys())
            acq_data = {key_mapper[k]: v for k, v in acq_data.items()}
        return acq_data, freq_data
