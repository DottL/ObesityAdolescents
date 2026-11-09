from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from obesity.load import series_for
from obesity.model import TrendModel, fit_trend

FIGURE_DIR = Path(__file__).resolve().parents[2] / "figures"

PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]


def _style(ax, title: str, ylabel: str = "Obesity prevalence (%)") -> None:
    ax.set_title(title, fontsize=12, loc="left")
    ax.set_xlabel("Survey cycle midpoint")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)


def plot_groups(frame, group_kind: str, labels=None, title=None, ax=None, show_se=True):
    if labels is None:
        subset = frame[frame["group_kind"] == group_kind]
        labels = sorted(subset["group_label"].unique())

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(9, 5.5))

    for colour, label in zip(PALETTE, labels):
        series = series_for(frame, group_kind, label)
        if series.empty:
            continue
        years = series["year_mid"].to_numpy(dtype=float)
        estimate = series["estimate"].to_numpy(dtype=float)

        ax.plot(
            years,
            estimate,
            marker="o",
            markersize=4,
            color=colour,
            label=label,
            linewidth=1.8,
        )
        if show_se:
            se = np.nan_to_num(series["se"].to_numpy(dtype=float), nan=0.0)
            ax.fill_between(
                years, estimate - se, estimate + se, color=colour, alpha=0.15, lw=0
            )

    _style(ax, title or f"Obesity prevalence by {group_kind}, ages 2-19")
    ax.legend(frameon=False, fontsize=9)
    if created:
        plt.tight_layout()
    return ax


def plot_trend(frame, group_kind: str, group_label: str, ax=None):
    """One group: observed points and the fitted trend line, over observed years only."""
    model: TrendModel = fit_trend(frame, group_kind, group_label)
    series = series_for(frame, group_kind, group_label)

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(9, 5.5))

    years = series["year_mid"].to_numpy(dtype=float)
    ax.plot(
        years,
        model.predict(years),
        color=PALETTE[0],
        linewidth=2,
        label="Fitted trend",
    )
    ax.errorbar(
        years,
        series["estimate"],
        yerr=np.nan_to_num(series["se"].to_numpy(dtype=float), nan=0.0),
        fmt="o",
        color="black",
        markersize=4,
        capsize=3,
        linewidth=1,
        label="NCHS estimate +/- SE",
    )

    _style(ax, f"{group_label} -- {model.slope_per_decade:+.1f} pp/decade")
    ax.legend(frameon=False, fontsize=9)
    if created:
        plt.tight_layout()
    return ax


def plot_race_small_multiples(frame):
    """Race groups as separate panels, raw data only"""
    labels = sorted(frame[frame["group_kind"] == "race"]["group_label"].unique())
    fig, axes = plt.subplots(len(labels), 1, figsize=(8, 3 * len(labels)), sharex=True)

    for ax, label in zip(np.atleast_1d(axes), labels):
        plot_groups(frame, "race", [label], title=label, ax=ax)
        ax.get_legend().remove()

    fig.suptitle(
        "Obesity prevalence by race and Hispanic origin, ages 2-19",
        fontsize=13,
        x=0.02,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig


def save_all(frame, outdir: Path | None = None) -> list[Path]:
    """Render the full figure set"""
    outdir = Path(outdir) if outdir else FIGURE_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    written = []

    def _save(fig, name):
        path = outdir / name
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        written.append(path)

    ax = plot_groups(frame, "sex", title="Obesity prevalence by sex, ages 2-19")
    _save(ax.figure, "sex_trends.png")

    ax = plot_groups(
        frame,
        "poverty",
        title="Obesity prevalence by percent of poverty level, ages 2-19",
    )
    _save(ax.figure, "poverty_trends.png")

    ax = plot_groups(frame, "age", title="Obesity prevalence by age band")
    _save(ax.figure, "age_trends.png")

    ax = plot_trend(frame, "total", "2-19 years")
    _save(ax.figure, "total_trend_projection.png")

    _save(plot_race_small_multiples(frame), "race_small_multiples.png")
    return written
