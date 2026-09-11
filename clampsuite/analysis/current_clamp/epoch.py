from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.curve_fit import Log, Sigmoid, fit_iv
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseConfig, BaseEpochAnalysis
from ..registry import register_epoch, register_epoch_config
from .acq import CurrentClampAcquisition, CurrentClampAcquisitionConfig


@register_epoch_config
@dataclass(frozen=True)
class CurrentClampConfig(BaseConfig):
    """Configuration for current clamp epoch and acquisition analysis.

    Serves as the single source of truth for current clamp analysis
    parameters. Instances are immutable and can be used for GUI
    generation and passed through ``ExpManager``.

    Attributes:
        acquisition_config: Parameters controlling per-acquisition
            spike detection and feature extraction.
        iv_start: Start time (s) of the window used to fit the I-V
            curve. If ``None``, the fit uses the full trace.
        iv_end: End time (s) of the window used to fit the I-V curve.
            If ``None``, the fit uses the full trace.
        rectify: Whether to fit the I-V curve as a rectifying
            (piecewise) relationship rather than a single line.
    """

    # Acquisition-level parameters
    acquisition_config: CurrentClampAcquisitionConfig = field(
        default_factory=CurrentClampAcquisitionConfig
    )

    # Epoch-level parameters
    iv_start: float | None = None
    iv_end: float | None = None
    rectify: bool = False

    @staticmethod
    def analysis_key() -> str:
        return "current_clamp"


@register_epoch
@dataclass
class CurrentClampEpoch(BaseEpochAnalysis[CurrentClampConfig]):
    """Aggregates current clamp acquisitions into epoch-level features.

    A ``CurrentClampEpoch`` represents one current-clamp stimulation
    protocol (e.g. a family of current-step sweeps) and computes
    summary statistics across all acquisitions in that protocol,
    including rheobase, sag, f-I curve fits, and I-V curve fits.

    Attributes:
        config: Configuration for acquisition- and epoch-level
            analysis parameters.
    """

    config: CurrentClampConfig = field(default_factory=CurrentClampConfig)

    @staticmethod
    def analysis_key() -> str:
        """Analysis key for the registry identification

        Returns:
            str: Key
        """
        return "current_clamp"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: dict[int, AcquisitionData]
    ):
        """Loads the acquisitions and creates ``CurrentClampAcquistion`` instances.

        Args:
            epoch_id (int): Epoch that the acquisitions belong to.
            acquisitions (dict[int, AcquisitionData]): Acquisitions used for the
            current clamp analysis.
        """
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = CurrentClampAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def features(self):
        self.create_raw_data()
        self.get_epoch_features()
        self.get_acq_features()

    def create_raw_data(self):
        """Generates the ``Spike Parameters`` and `` Acq Parameters`` dataframes from
        the raw acquisition data.
        """
        spk_params = []
        acq_params = []
        for value in self._acquisitions.values():
            acq_data, spk_data = value.data()
            spk_params.append(pd.DataFrame(spk_data))
            acq_params.append(acq_data)
        spk_params = pd.concat(spk_params)
        key_mapping = map_keys(spk_params.columns)
        spk_params = spk_params.rename(columns=key_mapping)

        acq_params = pd.DataFrame(acq_params)
        key_mapping = map_keys(acq_params.columns)
        acq_params = acq_params.rename(columns=key_mapping)
        if not spk_params.empty:
            spk_params["HW (ms)"] = (
                spk_params["HW Right (ms)"] - spk_params["HW Left (ms)"]
            )
            spk_params["FW (ms)"] = (
                spk_params["FW Right (ms)"] - spk_params["FW Left (ms)"]
            )

            spk_params = spk_params.sort_values(
                ["Cycle", "Acq Number", "Spike Number"]
            ).reset_index(drop=True)

        acq_params = acq_params.sort_values(["Cycle", "Acq Number"]).reset_index(
            drop=True
        )

        self.df_dict["Spike Parameters"] = spk_params
        self.df_dict["Acq Parameters"] = acq_params

    def get_acq_features(self):
        """Adds spike data to the ``acquisition Parameters`` dataframe. Only the first
        spike is used from ``Spike parameters``.
        """
        spk_params = self.df_dict["Spike Parameters"]
        spk_params = spk_params[spk_params["Spike Number"] == 0]
        acq = self.df_dict["Acq Parameters"]
        self.df_dict["Acq Parameters"] = acq.merge(
            spk_params.drop(columns=["Pulse Amp (pA)", "Cycle", "Epoch"]),
            on="Acq Number",
            how="left",
        )

    def get_epoch_features(self):
        """Pulls all relevant data into a single epoch based summary."""
        rheo_features = self.df_dict["Spike Parameters"].loc[
            self.df_dict["Spike Parameters"].groupby(["Cycle"])["Acq Number"].idxmin()
        ]
        rheo_features = (
            rheo_features.drop(columns=["Acq Number", "Spike Number", "Cycle"])
            .groupby("Epoch")
            .mean(numeric_only=True)
        )
        rheo_features = rheo_features.rename(
            columns={"Pulse Amp (pA)": "Rheobase (pA)"}
        )
        avg_data = (
            self.df_dict["Acq Parameters"]
            .groupby(["Pulse Amp (pA)"], as_index=False)
            .mean(numeric_only=True)
            .drop(columns=["Acq Number", "Cycle"])
        )
        sag_features = (
            avg_data.loc[
                avg_data["Pulse Amp (pA)"].idxmin(),
                ["Sag (mV)", "Sag (ms)", "Sag Ratio"],
            ]
            .to_frame()
            .T
        )
        fi_features = self.fi_fit(self.df_dict["Acq Parameters"])
        iv_params = self.df_dict["Acq Parameters"]
        iv_params = iv_params.loc[iv_params["Freq (Hz)"] < 1e-6]
        iv_features = self.iv_fit(
            iv_params,
            start=self.config.iv_start,
            end=self.config.iv_end,
            rectify=self.config.rectify,
        )
        fr_features = (
            self.df_dict["Acq Parameters"]
            .groupby(["Cycle"], as_index=False)["Freq (Hz)"]
            .max()
            .rename(columns={"Freq (Hz)": "Max Freq (Hz)"})
            .drop(columns=["Cycle"])
            .mean()
            .to_frame()
            .T
        )
        avg_data = (
            avg_data.drop(
                columns=["Sag (mV)", "Sag (ms)", "Pulse Amp (pA)", "Delta V (mV)"]
            )
            .groupby("Epoch")
            .mean(numeric_only=True)
        )
        avg_data = pd.concat(
            [
                avg_data.reset_index(drop=True),
                rheo_features.reset_index(drop=True),
                sag_features.reset_index(drop=True),
                fi_features.reset_index(drop=True),
                iv_features.reset_index(drop=True),
                fr_features.reset_index(drop=True),
            ],
            axis=1,
        )
        self.df_dict["Epoch Parameters"] = avg_data

    def fi_fit(self, acq_data: pd.DataFrame) -> pd.DataFrame:
        """Fit an F-I curve to per-acquisition frequency and current data.

        Args:
            acq_data (pd.DataFrame): Per-acquisition parameters, must contain
                ``"Pulse Amp (pA)"`` and ``Freq (Hz)``. FI curve fit is limited
                by to the Pulse Amp (pA) > 0 and Freq (Hz) < max(Freq (Hz))

        Returns:
            pd.DataFrame: A one-row DataFrame of fit parameters, with column names
                prefixed by ``column``.
        """
        fi_data = acq_data[acq_data["Pulse Amp (pA)"] >= 0]
        selector = fi_data["Freq (Hz)"] <= fi_data["Freq (Hz)"].max()
        current = fi_data.loc[selector, "Pulse Amp (pA)"]
        firing_rate = fi_data.loc[selector, "Freq (Hz)"]
        sig_fit = Sigmoid()
        sig_fit.fit(current, firing_rate)
        fi_features = pd.DataFrame(sig_fit.params._asdict(), index=np.array([1]))
        key_mapping = map_keys(fi_features.columns)
        key_mapping = {key: f"FI {value}" for key, value in key_mapping.items()}
        fi_features = fi_features.rename(columns=key_mapping)
        return fi_features

    def iv_fit(
        self,
        acq_data: pd.DataFrame,
        column: str = "Delta V (mV)",
        start: float | None = None,
        end: float | None = None,
        rectify: bool = False,
    ) -> pd.DataFrame:
        """Fit an I-V curve to per-acquisition voltage/current data.

        Args:
            acq_data (pd.DataFrame): Per-acquisition parameters, must contain
                ``"Pulse Amp (pA)"`` and ``column``.
            column: Name of the voltage column to fit against current.
            start: Start time (s) of the fit window, or ``None`` to
                use the full trace.
            end: End time (s) of the fit window, or ``None`` to use
                the full trace.
            rectify: Whether to fit a rectifying (piecewise) I-V curve.

        Returns:
            A one-row DataFrame of fit parameters, with column names
            prefixed by ``column``.
        """
        current = acq_data["Pulse Amp (pA)"].to_numpy()
        voltage = acq_data[column].to_numpy()
        temp = fit_iv(current, voltage, start, end, rectify)
        iv_features = pd.DataFrame(temp._asdict(), index=np.array([1]))
        key_mapping = map_keys(iv_features.columns)
        key_mapping = {key: f"{column} {value}" for key, value in key_mapping.items()}
        iv_features = iv_features.rename(columns=key_mapping)
        return iv_features
