"""Fetch and reshape the CDC obesity table into a tidy frame.

Source: data.cdc.gov dataset
"Obesity among children and adolescents aged 2-19 years,
by selected characteristics: United States"
(NCHS, National Health and Nutrition Examination Survey)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CSV_URL = "https://data.cdc.gov/api/views/9gay-j69q/rows.csv?accessType=DOWNLOAD"

DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "obesity_2_19.csv"

# STUB_NAME_NUM -> characteristic each block of rows breaks obesity down by
GROUP_KINDS = {
    0: "total",
    1: "sex",
    2: "age",
    3: "race",
    4: "sex_race",
    5: "poverty",
}


DROPPED_COLUMNS = [
    "INDICATOR",
    "PANEL",
    "PANEL_NUM",
    "UNIT",
    "UNIT_NUM",
    "STUB_NAME",
    "STUB_NAME_NUM",
    "STUB_LABEL_NUM",
]

# STUB_NAME,STUB_NAME_NUM,STUB_LABEL_NUM,
#
# STUB_LABEL,
# YEAR,YEAR_NUM,AGE,AGE_NUM,ESTIMATE,SE,FLAG

RENAMES = {
    "STUB_LABEL": "group_label",
    "YEAR": "year_window",
    "YEAR_NUM": "cycle",
    "AGE": "age_band",
    "AGE_NUM": "age_num",
    "ESTIMATE": "estimate",
    "SE": "se",
    "FLAG": "flag",
}

COLUMN_ORDER = [
    "group_kind",
    "group_label",
    "age_band",
    "age_num",
    "year_window",
    "year_mid",
    "cycle",
    "estimate",
    "se",
    "flag",
]


# FLAG meanings: NCHS footnote codes on ESTIMATE
# - : quantity zero / not available
# * : does not meet NCHS standards of reliability or precision


def load_raw(
    source: str | Path | None = None, cache: Path | None = None
) -> pd.DataFrame:
    """Return the CSV exactly as published.

    Reads the cached file if it is there; otherwise download and
    save a copy.
    """
    cache = Path(cache) if cache is not None else DEFAULT_CACHE
    if cache.exists():
        return pd.read_csv(cache)

    frame = pd.read_csv(source if source is not None else CSV_URL)

    cache.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache, index=False)

    return frame


def year_midpoint(year_label: str) -> float:
    """Midpoint of a survey window: ``'2001-2004'`` -> ``2002.5``.

    The NHANES cycles are unevenly spaced, so YEAR_NUM's 1..10 index is not a
    usable time axis. Model against the midpoint instead.
    """
    start, end = (int(part) for part in str(year_label).split("-"))
    return (start + end) / 2


def tidy(raw: pd.DataFrame | None = None, drop_unreliable: bool = True) -> pd.DataFrame:
    """Reshape the published table into one row per (group, survey cycle).

    Rows without an ESTIMATE (suppressed cells) are always dropped. Rows the
    NCHS flagged ``*`` as failing its reliability standards are dropped too
    unless ``drop_unreliable`` is False.
    """
    frame = load_raw() if raw is None else raw.copy()

    frame["group_kind"] = frame["STUB_NAME_NUM"].map(GROUP_KINDS)
    if frame["group_kind"].isna().any():
        unknown = sorted(
            frame.loc[frame["group_kind"].isna(), "STUB_NAME_NUM"].unique()
        )
        raise ValueError(f"STUB_NAME_NUM values missing from GROUP_KINDS: {unknown}")
    frame["year_mid"] = frame["YEAR"].map(year_midpoint)

    frame = frame.drop(columns=DROPPED_COLUMNS, errors="ignore").rename(columns=RENAMES)

    frame = frame.dropna(subset=["estimate"])
    if drop_unreliable:
        frame = frame[frame["flag"] != "*"]

    frame = frame[COLUMN_ORDER]
    return frame.sort_values(["group_kind", "group_label", "year_mid"]).reset_index(
        drop=True
    )


def series_for(frame: pd.DataFrame, group_kind: str, group_label: str) -> pd.DataFrame:
    """One group's time series: 10 cycles, one row each."""
    selected = frame[
        (frame["group_kind"] == group_kind) & (frame["group_label"] == group_label)
    ]
    if group_kind != "age":
        selected = selected[selected["age_num"] == 0]
    return selected.sort_values("year_mid").reset_index(drop=True)


def available_groups(frame: pd.DataFrame) -> pd.DataFrame:
    """Every (group_kind, group_label) pair with the number of usable cycles."""
    all_ages = frame[(frame["age_num"] == 0) | (frame["group_kind"] == "age")]
    counts = (
        all_ages.groupby(["group_kind", "group_label"])
        .size()
        .reset_index(name="n_cycles")
        .sort_values(["group_kind", "group_label"])
    )
    return counts.reset_index(drop=True)
