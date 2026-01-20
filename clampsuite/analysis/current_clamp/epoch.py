from dataclasses import dataclass, field
from typing import Dict, Literal

import pandas as pd

from ...functions.current_clamp import ThresholdType
from ...functions.curve_fit import Log, Sigmoid, fit_iv
from ...functions.utilities import map_keys
from ...loader.acquisition_data import AcquisitionData
from ..base import BaseEpochAnalysis, BaseConfig
from ..registry import register_epoch, register_epoch_config
from .acq import CurrentClampAcquisition, CurrentClampAcquisitionConfig


@register_epoch_config
@dataclass(frozen=True)
class CurrentClampConfig(BaseConfig):
    """Single source of truth for current clamp analysis parameters.

    This class can be used for GUI generation and passed through ExpManager.
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
    config: CurrentClampConfig = field(default_factory=CurrentClampConfig)

    @staticmethod
    def analysis_key():
        return "current_clamp"

    def load_acquisitions(
        self, epoch_id: int, acquisitions: Dict[int, AcquisitionData]
    ):
        self.epoch_id = epoch_id
        for key, value in acquisitions.items():
            temp = CurrentClampAcquisition(acq_data=value)
            self._acquisitions[key] = temp

    def analyze(self):
        for value in self._acquisitions.values():
            value.analyze(self.config.acquisition_config)
        self.create_raw_data()
        self.get_features()

    def create_raw_data(self):
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
        spk_params["HW (ms)"] = spk_params["HW Right (ms)"] - spk_params["HW Left (ms)"]
        spk_params["FW (ms)"] = spk_params["FW Right (ms)"] - spk_params["FW Left (ms)"]

        spk_params = spk_params.sort_values(
            ["Cycle", "Acq Number", "Spike Number"]
        ).reset_index(drop=True)

        acq_params = acq_params.sort_values(["Cycle", "Acq Number"]).reset_index(
            drop=True
        )

        self.df_dict["Spike Parameters"] = spk_params
        self.df_dict["Acq Parameters"] = acq_params

    def get_features(self):
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
        sag_features = avg_data.loc[
            avg_data["Pulse Amp (pA)"].idxmin(),
            ["Epoch", "Sag (mV)", "Sag (ms)"],
        ]
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
            .mean()
        )
        features = (
            avg_data.drop(
                columns=["Sag (mV)", "Sag (ms)", "Pulse Amp (pA)", "Delta V (mV)"]
            )
            .groupby("Epoch")
            .mean(numeric_only=True)
        )
        features = pd.concat(
            [rheo_features, sag_features, fi_features, iv_features, fr_features], axis=1
        )
        self.df_dict["Epoch Parameters"] = features

    def fi_fit(self, acq_data):
        fi_data = acq_data[acq_data["Pulse Amp (pA)"] >= 0]
        selector = fi_data["Freq (Hz)"] <= fi_data["Freq (Hz)"].max()
        current = fi_data.loc[selector, "Pulse Amp (pA)"]
        firing_rate = fi_data[selector, "Freq (Hz)"]
        sig_fit = Sigmoid()
        sig_fit.fit(current, firing_rate)
        fi_features = pd.DataFrame(sig_fit.params._asdict())
        key_mapping = map_keys(fi_features.columns)
        key_mapping = {key: f"FI {value}" for key, value in key_mapping.items()}
        fi_features = fi_features.rename(columns=key_mapping)
        return fi_features

    def iv_fit(
        self,
        acq_data,
        column: str = "Delta V (mV)",
        start: int | float | None = None,
        end: int | float | None = None,
        rectify: bool = False,
    ):
        current = acq_data["Pulse Amp (pA)"].to_numpy()
        voltage = acq_data[column].to_numpy()
        temp = fit_iv(current, voltage, start, end, rectify)
        iv_features = pd.DataFrame(temp._asdict())
        key_mapping = map_keys(iv_features.columns)
        key_mapping = {key: f"{column} {value}" for key, value in key_mapping.items()}
        iv_features = iv_features.rename(columns=key_mapping)
        return iv_features

    def log_fit(self, spike_data, column: str):
        log_output = []
        epochs = []
        for key, value in spike_data.groupby("Epoch").groups.items():
            y = spike_data.loc[value, column]
            x = spike_data.loc[value, "Spike Number"]
            log_fit = Log()
            log_fit.fit(x, y)
            temp = log_fit.params
            epochs.append(key)
            log_output.append(temp._asdict())
        log_features = pd.DataFrame(log_output)
        key_mapping = map_keys(log_features.columns)
        key_mapping = {key: f"{column} {value}" for key, value in key_mapping.items()}
        log_features = log_features.rename(columns=key_mapping)
        log_features["Epoch"] = epochs
        return log_features
