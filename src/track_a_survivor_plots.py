#!/usr/bin/env python3
"""Visualise the Track A metastasis survivor ``TOP2A - EPAS1``.

Produces three judge-facing PNGs:

  survivor_scatter_top2a_vs_epas1.png
    2D scatter of TOP2A (y) vs EPAS1 (x) with M0 / M1 colouring.

  survivor_score_histogram.png
    Distribution of the law score ``TOP2A - EPAS1`` split by M0 / M1.

  expanded_panel_comparison.png
    Cross-task bar chart of best delta_baseline under the 11-gene panel
    (original Tier 1 / Tier 2 / survival / metastasis runs) vs the
    45-gene expanded panel (survival_expanded + metastasis_expanded).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RESULTS = Path("results")
OUT = RESULTS / "track_a_task_landscape" / "plots"


def survivor_scatter() -> Path:
    df = pd.read_csv("data/kirc_metastasis_expanded.csv")
    m1 = df[df["label"] == "disease"]
    m0 = df[df["label"] == "control"]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.scatter(m0["EPAS1"], m0["TOP2A"], s=26, alpha=0.6, color="tab:blue",
               label=f"M0 control (n={len(m0)})", edgecolor="white", linewidth=0.4)
    ax.scatter(m1["EPAS1"], m1["TOP2A"], s=52, alpha=0.85, color="tab:red",
               label=f"M1 metastatic (n={len(m1)})", edgecolor="black", linewidth=0.4)

    # Decision line: TOP2A - EPAS1 = 0 => TOP2A = EPAS1
    lo = min(df["EPAS1"].min(), df["TOP2A"].min())
    hi = max(df["EPAS1"].max(), df["TOP2A"].max())
    ax.plot([lo, hi], [lo, hi], color="black", linestyle="--", linewidth=1.0,
            label="TOP2A = EPAS1 (decision line)")

    ax.set_xlabel("EPAS1 (HIF-2α, log2 TPM)")
    ax.set_ylabel("TOP2A (proliferation, log2 TPM)")
    ax.set_title(
        "Surviving law: TOP2A − EPAS1\n"
        "M1 samples skew above the TOP2A = EPAS1 line (proliferation > HIF-2α)"
    )
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "survivor_scatter_top2a_vs_epas1.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def survivor_score_histogram() -> Path:
    df = pd.read_csv("data/kirc_metastasis_expanded.csv")
    scores = df["TOP2A"] - df["EPAS1"]
    m0_scores = scores[df["label"] == "control"]
    m1_scores = scores[df["label"] == "disease"]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    bins = np.linspace(scores.min(), scores.max(), 30)
    ax.hist(m0_scores, bins=bins, alpha=0.55, density=True, color="tab:blue",
            label=f"M0 control (n={len(m0_scores)})")
    ax.hist(m1_scores, bins=bins, alpha=0.55, density=True, color="tab:red",
            label=f"M1 metastatic (n={len(m1_scores)})")

    # Score mean line
    ax.axvline(m0_scores.mean(), color="tab:blue", linestyle="--", linewidth=1.2)
    ax.axvline(m1_scores.mean(), color="tab:red", linestyle="--", linewidth=1.2)

    pooled = np.sqrt((np.std(m1_scores, ddof=1) ** 2 + np.std(m0_scores, ddof=1) ** 2) / 2)
    cohens_d = (np.mean(m1_scores) - np.mean(m0_scores)) / pooled if pooled > 0 else 0.0

    ax.set_xlabel("TOP2A − EPAS1 (law score)")
    ax.set_ylabel("density")
    ax.set_title(
        "Score separation of the surviving law on TCGA-KIRC metastasis\n"
        f"AUROC 0.726 · ci_lower 0.658 · Cohen's d = {cohens_d:.2f}"
    )
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    out = OUT / "survivor_score_histogram.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def expanded_panel_comparison() -> Path:
    # For each task, read the best delta_baseline across candidates.
    task_specs = [
        ("Tumor vs Normal", RESULTS / "flagship_run" / "falsification_report.json", None, "CA9=0.965"),
        ("Stage", RESULTS / "tier2_run" / "falsification_report.json", None, "CUBN=0.610"),
        ("Survival", RESULTS / "track_a_task_landscape" / "survival" / "falsification_report.json",
                     RESULTS / "track_a_task_landscape" / "survival_expanded" / "falsification_report.json",
                     "CUBN=0.696"),
        ("Metastasis", RESULTS / "track_a_task_landscape" / "metastasis" / "falsification_report.json",
                       RESULTS / "track_a_task_landscape" / "metastasis_expanded" / "falsification_report.json",
                       "MKI67=0.645"),
    ]

    def best_delta(path: Path | None) -> float | None:
        if path is None or not path.exists():
            return None
        r = json.loads(path.read_text())
        valid = [e.get("delta_baseline", 0.0) for e in r if not e.get("numeric_error")]
        return max(valid) if valid else None

    names = []
    d11 = []
    d45 = []
    annos = []
    for name, p11, p45, anno in task_specs:
        names.append(name)
        d11.append(best_delta(p11))
        d45.append(best_delta(p45))
        annos.append(anno)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(names))
    w = 0.35
    b1 = ax.bar(x - w / 2, [d if d is not None else 0 for d in d11], w,
                color="tab:blue", label="11-gene panel", alpha=0.85)
    b2 = ax.bar(x + w / 2, [d if d is not None else 0 for d in d45], w,
                color="tab:orange", label="45-gene expanded", alpha=0.85)

    ax.axhline(y=0.05, color="red", linestyle="--", linewidth=1.5,
               label="pre-reg threshold (+0.05)")
    ax.axhline(y=0.0, color="gray", linestyle="-", linewidth=0.6)

    for i, (d11v, d45v, anno) in enumerate(zip(d11, d45, annos)):
        if d11v is not None:
            ax.text(i - w / 2, d11v + 0.003, f"{d11v:+.3f}", ha="center", fontsize=8)
        if d45v is not None:
            ax.text(i + w / 2, d45v + 0.003, f"{d45v:+.3f}", ha="center", fontsize=8,
                    color="black" if d45v > 0.05 else "black")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\n(top single: {a})" for n, a in zip(names, annos)],
                       fontsize=9)
    ax.set_ylabel("best Δbaseline across candidates")
    ax.set_ylim(-0.05, 0.12)
    ax.set_title(
        "Expanding from 11 to 45 genes flips the gate verdict on metastasis only\n"
        "(compound-law ceiling remains below the +0.05 bar on the other three tasks)"
    )
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    out = OUT / "expanded_panel_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    for fn in (survivor_scatter, survivor_score_histogram, expanded_panel_comparison):
        p = fn()
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
