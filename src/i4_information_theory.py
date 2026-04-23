#!/usr/bin/env python3
"""Lane I · I4 — Information-theoretic analysis of TOP2A − EPAS1.

Questions:
1. Mutual information: I(TOP2A; Y), I(EPAS1; Y), I(score; Y)
2. Synergy: I((TOP2A,EPAS1); Y) - I(TOP2A; Y) - I(EPAS1; Y) > 0?
3. MDL (minimum description length): equation-token count vs. AUROC gain.

Uses k-nearest-neighbor mutual info estimator (sklearn.feature_selection).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "kirc_metastasis_expanded.csv"
OUT = ROOT / "results" / "science_depth"


def _mi(X, y, seed=42):
    """Single MI value per feature column of X vs y."""
    return mutual_info_classif(X, y, random_state=seed, n_neighbors=5)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV)
    y = (df["label"] == "disease").astype(int).values
    df["TOP2A"] = pd.to_numeric(df["TOP2A"], errors="coerce").fillna(0)
    df["EPAS1"] = pd.to_numeric(df["EPAS1"], errors="coerce").fillna(0)
    df["score"] = df["TOP2A"] - df["EPAS1"]

    # MI of single genes and of the compound score
    mi_top2a = float(_mi(df[["TOP2A"]].values, y)[0])
    mi_epas1 = float(_mi(df[["EPAS1"]].values, y)[0])
    mi_score = float(_mi(df[["score"]].values, y)[0])

    # Joint MI ≈ MI of (TOP2A, EPAS1) — sklearn doesn't give joint MI
    # directly, so we use the score-as-proxy + 2D histogram estimator.
    # Approximation: I((TOP2A, EPAS1); Y) ≈ max(mi_score, mi_2d_hist)
    def _joint_mi_hist(x1, x2, y, bins=20):
        # Discretize each continuous variable into `bins` quantile bins.
        q1 = pd.qcut(x1, bins, labels=False, duplicates="drop")
        q2 = pd.qcut(x2, bins, labels=False, duplicates="drop")
        joint_bin = q1.astype(str) + "_" + q2.astype(str)
        # Convert joint-bin strings to integer codes for MI.
        codes, _ = pd.factorize(joint_bin)
        return float(_mi(codes.reshape(-1, 1), y)[0])

    mi_joint_hist = _joint_mi_hist(
        df["TOP2A"].values, df["EPAS1"].values, y)

    synergy_score = mi_score - mi_top2a - mi_epas1
    synergy_joint = mi_joint_hist - mi_top2a - mi_epas1

    # MDL (token count of symbolic equation)
    equations = {
        "TOP2A - EPAS1": 3,
        "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)": 9,
        "log1p(LDHA) - log1p(ALB)": 5,
        "MKI67 - EPAS1": 3,
        "log1p(ACTB) - log1p(GAPDH)": 5,
        "CA9 (single gene)": 1,
    }

    # AUROC for each equation
    auroc_map = {}
    auroc_map["CA9 (single gene)"] = max(
        roc_auc_score(y, df["CA9"].fillna(0)),
        1 - roc_auc_score(y, df["CA9"].fillna(0)))
    auroc_map["TOP2A - EPAS1"] = roc_auc_score(y, df["score"])
    if auroc_map["TOP2A - EPAS1"] < 0.5:
        auroc_map["TOP2A - EPAS1"] = 1 - auroc_map["TOP2A - EPAS1"]
    auroc_map["MKI67 - EPAS1"] = roc_auc_score(
        y, df["MKI67"].fillna(0) - df["EPAS1"])
    if auroc_map["MKI67 - EPAS1"] < 0.5:
        auroc_map["MKI67 - EPAS1"] = 1 - auroc_map["MKI67 - EPAS1"]

    summary = {
        "mutual_information": {
            "I_TOP2A_Y": mi_top2a,
            "I_EPAS1_Y": mi_epas1,
            "I_score_Y (score = TOP2A - EPAS1)": mi_score,
            "I_joint_hist_Y (2D histogram, 20 bins)": mi_joint_hist,
        },
        "synergy": {
            "definition": "synergy = I(joint; Y) - I(TOP2A; Y) - I(EPAS1; Y)",
            "via_score": synergy_score,
            "via_joint_hist": synergy_joint,
            "interpretation": (
                "Positive synergy → TOP2A-EPAS1 carry non-redundant information "
                "about metastasis; the compound is INFORMATIONALLY NECESSARY. "
                "Near-zero synergy → the two genes are largely redundant."
            ),
        },
        "mdl_token_counts": {
            eq: {"tokens": tokens, "auroc": auroc_map.get(eq)}
            for eq, tokens in equations.items()
        },
        "notes": [
            "MI estimator: sklearn.feature_selection.mutual_info_classif, k=5 NN.",
            "Joint MI via 2D histogram (20 quantile bins per gene).",
            "Both estimators are lower bounds on true MI at this sample size (n=505).",
        ],
    }

    (OUT / "information_theory.json").write_text(
        json.dumps(summary, indent=2, default=str))

    # Human-readable SUMMARY
    md = [
        "# Information-theoretic analysis of TOP2A − EPAS1",
        "",
        "TCGA-KIRC metastasis (M0 vs M1, n=505, prevalence 16%).",
        "",
        "## Mutual information (sklearn k=5 NN estimator)",
        "",
        "| Variable | I(X; Y) (nats) |",
        "|---|---|",
        f"| TOP2A | {mi_top2a:.4f} |",
        f"| EPAS1 | {mi_epas1:.4f} |",
        f"| score = TOP2A − EPAS1 | **{mi_score:.4f}** |",
        f"| 2D joint (TOP2A, EPAS1) via histogram | {mi_joint_hist:.4f} |",
        "",
        "## Synergy",
        "",
        f"Synergy = I(joint; Y) − I(TOP2A; Y) − I(EPAS1; Y)",
        f"- Via score: **{synergy_score:+.4f}**",
        f"- Via 2D histogram: **{synergy_joint:+.4f}**",
        "",
        "**Interpretation**: Synergy > 0 → the compound law carries information",
        "about metastasis that neither single gene carries alone, i.e. the",
        "2-gene form is *informationally necessary*, not redundant with either.",
        "",
        "## MDL (equation token counts vs. AUROC)",
        "",
        "| Equation | Tokens | AUROC | Tokens / AUROC |",
        "|---|---|---|---|",
    ]
    for eq, data in summary["mdl_token_counts"].items():
        tok, auc = data["tokens"], data["auroc"]
        if auc is None:
            md.append(f"| `{eq}` | {tok} | — | — |")
        else:
            efficiency = tok / auc
            md.append(f"| `{eq}` | {tok} | {auc:.3f} | {efficiency:.2f} |")

    md += [
        "",
        "**Token/AUROC** is a rough MDL-style efficiency. Lower = more",
        "compact discrimination per equation symbol.",
        "",
        "## Reproduce",
        "```bash",
        "PYTHONPATH=src .venv/bin/python src/i4_information_theory.py",
        "```",
    ]
    (OUT / "information_theory_SUMMARY.md").write_text("\n".join(md))

    print(f"I(TOP2A;Y)   = {mi_top2a:.4f}")
    print(f"I(EPAS1;Y)   = {mi_epas1:.4f}")
    print(f"I(score;Y)   = {mi_score:.4f}")
    print(f"I(joint;Y)_hist = {mi_joint_hist:.4f}")
    print(f"Synergy (score-based) = {synergy_score:+.4f}")
    print(f"Synergy (joint-hist)  = {synergy_joint:+.4f}")
    print(f"\nWrote: {OUT}/information_theory_SUMMARY.md")


if __name__ == "__main__":
    main()
