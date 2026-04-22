#!/usr/bin/env python3
"""Track-A–specific plots: 4-task cross-comparison of AUROC + Δbase.

Outputs (into results/track_a_task_landscape/plots/):
  task_auroc_comparison.png  – side-by-side per-task AUROC distributions
                                (PySR + Opus ex-ante) with dominant single-gene
                                AUROC marked as horizontal line.
  delta_baseline_by_task.png – grouped histogram of Δbase per task +
                                pre-registered +0.05 threshold line.

Generator script; re-run after any Track A falsification re-run.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


RESULTS = Path("results")
PLOTS = RESULTS / "track_a_task_landscape" / "plots"

TASK_SPECS = [
    ("tumor_vs_normal",
     RESULTS / "flagship_run" / "falsification_report.json",
     RESULTS / "opus_exante" / "kirc_flagship_report.json",
     "CA9", 0.965, 609, "Tumor vs Normal (Tier 1)"),
    ("stage",
     RESULTS / "tier2_run" / "falsification_report.json",
     RESULTS / "opus_exante" / "kirc_tier2_report.json",
     "CUBN", 0.610, 534, "Stage I-II vs III-IV (Tier 2)"),
    ("survival",
     RESULTS / "track_a_task_landscape" / "survival" / "falsification_report.json",
     RESULTS / "track_a_task_landscape" / "survival" / "opus_exante_report.json",
     "CUBN", 0.696, 301, "5-year Survival"),
    ("metastasis",
     RESULTS / "track_a_task_landscape" / "metastasis" / "falsification_report.json",
     RESULTS / "track_a_task_landscape" / "metastasis" / "opus_exante_report.json",
     "MKI67", 0.645, 505, "Metastasis M0 vs M1"),
]


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def plot_task_auroc_comparison() -> Path:
    fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)

    for ax, (tid, pysr_path, opus_path, top_gene, top_auc, n, title) in zip(axes, TASK_SPECS):
        pysr = _load(pysr_path)
        opus = _load(opus_path)

        pysr_aucs = [e.get("law_auc", 0.5) for e in pysr
                     if not e.get("numeric_error")]
        opus_aucs = [e.get("law_auc", 0.5) for e in opus
                     if not e.get("numeric_error")]

        # Scatter with jitter
        rng = np.random.default_rng(42)
        if pysr_aucs:
            x = rng.normal(1.0, 0.04, size=len(pysr_aucs))
            ax.scatter(x, pysr_aucs, s=35, alpha=0.7, color="tab:blue",
                       label=f"PySR (n={len(pysr_aucs)})", edgecolor="white")
        if opus_aucs:
            x = rng.normal(2.0, 0.04, size=len(opus_aucs))
            ax.scatter(x, opus_aucs, s=65, alpha=0.85, color="tab:orange",
                       marker="s", label=f"Opus ex-ante (n={len(opus_aucs)})",
                       edgecolor="black")

        ax.axhline(y=top_auc, color="black", linestyle="--", linewidth=1.2,
                   label=f"{top_gene} alone = {top_auc:.3f}")
        ax.axhline(y=top_auc + 0.05, color="red", linestyle=":", linewidth=1.2,
                   label=f"gate threshold = {top_auc + 0.05:.3f}")
        ax.axhline(y=0.5, color="gray", linestyle="-", linewidth=0.6, alpha=0.6)

        ax.set_xlim(0.5, 2.5)
        ax.set_xticks([1.0, 2.0])
        ax.set_xticklabels(["PySR", "Opus"], rotation=0)
        ax.set_ylim(0.0, 1.05)
        ax.set_title(f"{title}\nn={n}", fontsize=10)
        if ax is axes[0]:
            ax.set_ylabel("law AUROC")
        ax.legend(fontsize=7, loc="lower left")

    fig.suptitle(
        "Four ccRCC tasks — the pre-registered +0.05 threshold (red) is "
        "never cleared\n(every task is dominated by one gene; compound laws "
        "cannot close the gap)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = PLOTS / "task_auroc_comparison.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_delta_baseline_by_task() -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    x_base = 0
    width = 0.35
    labels = []
    centers = []

    colors = ["tab:blue", "tab:orange"]

    for i, (tid, pysr_path, opus_path, top_gene, top_auc, n, title) in enumerate(TASK_SPECS):
        pysr = _load(pysr_path)
        opus = _load(opus_path)
        pysr_d = [e.get("delta_baseline", 0.0) for e in pysr
                  if not e.get("numeric_error")]
        opus_d = [e.get("delta_baseline", 0.0) for e in opus
                  if not e.get("numeric_error")]

        pysr_x = x_base + 0
        opus_x = x_base + width
        # Box-ish: scatter + max line
        rng = np.random.default_rng(i + 1)
        if pysr_d:
            jx = rng.normal(pysr_x, 0.04, size=len(pysr_d))
            ax.scatter(jx, pysr_d, s=24, color=colors[0], alpha=0.7, edgecolor="white")
            ax.hlines(max(pysr_d), pysr_x - 0.08, pysr_x + 0.08,
                      color=colors[0], linewidth=2)
        if opus_d:
            jx = rng.normal(opus_x, 0.04, size=len(opus_d))
            ax.scatter(jx, opus_d, s=40, color=colors[1], alpha=0.85,
                       marker="s", edgecolor="black")
            ax.hlines(max(opus_d), opus_x - 0.08, opus_x + 0.08,
                      color=colors[1], linewidth=2)

        centers.append(x_base + width / 2)
        labels.append(f"{title[:22]}\n(top single = {top_gene} {top_auc:.3f})")
        x_base += 1.1

    ax.axhline(y=0.05, color="red", linestyle="--", linewidth=1.5,
               label="pre-registered threshold (+0.05)")
    ax.axhline(y=0.0, color="gray", linestyle="-", linewidth=0.6)
    ax.set_xticks(centers)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Δbaseline (law AUROC − best single-gene AUROC)")
    ax.set_title(
        "Compound-law incremental AUROC ceiling across 4 ccRCC tasks\n"
        "PySR (blue) and Opus ex-ante (orange) both stay below +0.05"
    )
    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(color=colors[0], label="PySR candidates"),
            Patch(color=colors[1], label="Opus ex-ante laws"),
            plt.Line2D([0], [0], color="red", linestyle="--",
                       label="pre-reg threshold +0.05"),
        ],
        fontsize=9,
        loc="lower left",
    )
    fig.tight_layout()
    out = PLOTS / "delta_baseline_by_task.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    p1 = plot_task_auroc_comparison()
    print(f"wrote {p1}")
    p2 = plot_delta_baseline_by_task()
    print(f"wrote {p2}")


if __name__ == "__main__":
    main()
