"""Plain least-squares trend line per group"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from obesity.load import series_for


@dataclass
class TrendModel:
    group_kind: str
    group_label: str
    intercept: float
    slope: float
    n_obs: int
    year_range: tuple[float, float]

    @property
    def slope_per_decade(self) -> float:
        return self.slope * 10

    def predict(self, year_mid: float | np.ndarray) -> np.ndarray:
        years = np.atleast_1d(np.asarray(year_mid, dtype=float))
        return self.intercept + self.slope * years


def fit_trend(frame: pd.DataFrame, group_kind: str, group_label: str) -> TrendModel:
    """Fit one group's trend line with an unweighted least-squares fit."""
    series = series_for(frame, group_kind, group_label)
    if len(series) < 2:
        raise ValueError(
            f"{group_kind}/{group_label} has {len(series)} usable cycles; need at least 2"
        )

    years = series["year_mid"].to_numpy(dtype=float)
    estimates = series["estimate"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(years, estimates, deg=1)

    return TrendModel(
        group_kind=group_kind,
        group_label=group_label,
        intercept=float(intercept),
        slope=float(slope),
        n_obs=len(series),
        year_range=(float(years.min()), float(years.max())),
    )


def fit_all_groups(
    frame: pd.DataFrame, min_cycles: int = 2
) -> dict[tuple[str, str], TrendModel]:
    """Fit every group that has enough cycles to support a line"""
    from obesity.load import available_groups

    models: dict[tuple[str, str], TrendModel] = {}
    for row in available_groups(frame).itertuples():
        if row.n_cycles < min_cycles:
            continue
        models[(row.group_kind, row.group_label)] = fit_trend(
            frame, row.group_kind, row.group_label
        )
    return models
