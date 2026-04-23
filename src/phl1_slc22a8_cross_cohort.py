#!/usr/bin/env python3
"""PhL-1: external cross-cohort replay of the 3-gene H1-loop extension

    score = TOP2A − (EPAS1 + SLC22A8)

on IMmotion150 metastatic ccRCC.

Pre-registration:
  preregistrations/20260423T181322Z_phl1_immotion150_slc22a8_extension.yaml
  (committed 2026-04-23 as commit d2352a9 BEFORE this script was run).

Three pre-registered kill tests (same shape as PhF-3):
  1. Log-rank median-split p < 0.05
  2. Cox HR per z: |log(HR)| > log(1.3) AND 95% CI excludes 1
  3. Harrell C-index > 0.55

Plus a pre-registered comparison gate vs the 2-gene PhF-3 form:
  3-gene outperforms 2-gene ⇔ C-index (3gene) > C-index (2gene) + 0.01
                              AND HR (3gene) > HR (2gene).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "data" / "immotion150_ccrcc.csv"
    out_dir = (
        repo_root / "results" / "track_a_task_landscape"
        / "external_replay" / "immotion150_slc22a8"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load + clean -----------------------------------------------------
    df = pd.read_csv(csv_path)
    for col in ("TOP2A", "EPAS1", "SLC22A8", "PFS_MONTHS"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    raw_status = df["PFS_STATUS"].astype(str)
    df["pfs_event"] = raw_status.str.startswith("1").astype(int)

    df = df.dropna(
        subset=["TOP2A", "EPAS1", "SLC22A8", "PFS_MONTHS", "pfs_event"]
    ).copy()

    # --- 3-gene score (the H1 v2 finding) --------------------------------
    df["score_3gene"] = df["TOP2A"] - (df["EPAS1"] + df["SLC22A8"])
    df["score_3gene_z"] = (df["score_3gene"] - df["score_3gene"].mean()) / df["score_3gene"].std()
    # Reference 2-gene score for comparison-gate calculation on this same cohort.
    df["score_2gene"] = df["TOP2A"] - df["EPAS1"]
    df["score_2gene_z"] = (df["score_2gene"] - df["score_2gene"].mean()) / df["score_2gene"].std()

    # --- 1) Log-rank median split ---------------------------------------
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    median_3 = df["score_3gene"].median()
    df["group_3"] = np.where(df["score_3gene"] >= median_3, "high", "low")
    high_3 = df[df["group_3"] == "high"]
    low_3 = df[df["group_3"] == "low"]
    lr_3 = logrank_test(
        high_3["PFS_MONTHS"], low_3["PFS_MONTHS"],
        event_observed_A=high_3["pfs_event"], event_observed_B=low_3["pfs_event"],
    )
    lr_p_3 = float(lr_3.p_value)
    lr_chi2_3 = float(lr_3.test_statistic)

    kmf_high = KaplanMeierFitter().fit(
        high_3["PFS_MONTHS"], high_3["pfs_event"],
        label=f"high 3-gene (n={len(high_3)})",
    )
    kmf_low = KaplanMeierFitter().fit(
        low_3["PFS_MONTHS"], low_3["pfs_event"],
        label=f"low 3-gene (n={len(low_3)})",
    )
    median_pfs_high = float(kmf_high.median_survival_time_)
    median_pfs_low = float(kmf_low.median_survival_time_)

    # --- 2) Cox HR per z ------------------------------------------------
    from lifelines import CoxPHFitter
    cox_df_3 = df[["PFS_MONTHS", "pfs_event", "score_3gene_z"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    )
    cph_3 = CoxPHFitter()
    cph_3.fit(cox_df_3, duration_col="T", event_col="E")
    hr_3 = float(np.exp(cph_3.params_["score_3gene_z"]))
    hr3_ci_low = float(np.exp(cph_3.confidence_intervals_.loc["score_3gene_z", "95% lower-bound"]))
    hr3_ci_high = float(np.exp(cph_3.confidence_intervals_.loc["score_3gene_z", "95% upper-bound"]))
    cox_p_3 = float(cph_3.summary.loc["score_3gene_z", "p"])

    # Also fit 2-gene on SAME dropped-sample set for apples-to-apples comparison.
    cox_df_2 = df[["PFS_MONTHS", "pfs_event", "score_2gene_z"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    )
    cph_2 = CoxPHFitter()
    cph_2.fit(cox_df_2, duration_col="T", event_col="E")
    hr_2 = float(np.exp(cph_2.params_["score_2gene_z"]))
    hr2_ci_low = float(np.exp(cph_2.confidence_intervals_.loc["score_2gene_z", "95% lower-bound"]))
    hr2_ci_high = float(np.exp(cph_2.confidence_intervals_.loc["score_2gene_z", "95% upper-bound"]))

    # --- 3) Harrell C-index ---------------------------------------------
    from lifelines.utils import concordance_index
    c_idx_3_risk = float(concordance_index(
        df["PFS_MONTHS"], -df["score_3gene"], df["pfs_event"]
    ))
    c_idx_3_inv = float(concordance_index(
        df["PFS_MONTHS"], df["score_3gene"], df["pfs_event"]
    ))
    c_idx_3 = max(c_idx_3_risk, c_idx_3_inv)

    c_idx_2_risk = float(concordance_index(
        df["PFS_MONTHS"], -df["score_2gene"], df["pfs_event"]
    ))
    c_idx_2_inv = float(concordance_index(
        df["PFS_MONTHS"], df["score_2gene"], df["pfs_event"]
    ))
    c_idx_2 = max(c_idx_2_risk, c_idx_2_inv)

    # --- Kill-test verdicts ---------------------------------------------
    test1 = {
        "name": "logrank_median_split",
        "p": lr_p_3, "chi2": lr_chi2_3,
        "threshold": "p < 0.05", "pass": bool(lr_p_3 < 0.05),
    }
    test2 = {
        "name": "cox_hazard_ratio",
        "hr": hr_3, "hr_ci_95": [hr3_ci_low, hr3_ci_high], "p": cox_p_3,
        "threshold": "abs(log(HR)) > log(1.3) AND 95%CI excludes 1",
        "pass": bool(abs(np.log(hr_3)) > np.log(1.3) and not (hr3_ci_low <= 1 <= hr3_ci_high)),
    }
    test3 = {
        "name": "concordance_index",
        "c_index_risk_direction": c_idx_3_risk,
        "c_index_inverse_direction": c_idx_3_inv,
        "c_index_best": c_idx_3,
        "threshold": "> 0.55", "pass": bool(c_idx_3 > 0.55),
    }

    all_pass = bool(test1["pass"] and test2["pass"] and test3["pass"])

    # --- Comparison gate (pre-registered) -------------------------------
    # Must beat 2-gene on BOTH C-index (+0.01 floor) AND HR.
    c_outperforms = bool(c_idx_3 > c_idx_2 + 0.01)
    hr_outperforms = bool(hr_3 > hr_2)
    comparison = {
        "criterion": "3-gene outperforms 2-gene iff C(3) > C(2)+0.01 AND HR(3) > HR(2)",
        "c_index_3gene": c_idx_3,
        "c_index_2gene_same_samples": c_idx_2,
        "c_delta": c_idx_3 - c_idx_2,
        "c_outperforms": c_outperforms,
        "hr_3gene": hr_3,
        "hr_2gene_same_samples": hr_2,
        "hr_delta": hr_3 - hr_2,
        "hr_outperforms": hr_outperforms,
        "outperforms_verdict": (
            "OUTPERFORMS"
            if (c_outperforms and hr_outperforms)
            else (
                "MATCHES"
                if all_pass
                else "UNDERPERFORMS"
            )
        ),
    }

    verdict = {
        "hypothesis_id": "phl1_immotion150_slc22a8_extension",
        "prereg_file": "preregistrations/20260423T181322Z_phl1_immotion150_slc22a8_extension.yaml",
        "cohort": "IMmotion150 (rcc_iatlas_immotion150_2018)",
        "n": int(len(df)),
        "events": int(df["pfs_event"].sum()),
        "score_formula": "TOP2A - (EPAS1 + SLC22A8)",
        "median_score": float(median_3),
        "median_pfs_high_group": median_pfs_high,
        "median_pfs_low_group": median_pfs_low,
        "kill_tests": [test1, test2, test3],
        "all_kill_tests_pass": all_pass,
        "verdict": "PASS" if all_pass else "FAIL",
        "direction": (
            "high 3-gene score → worse PFS"
            if c_idx_3_risk > c_idx_3_inv
            else "high 3-gene score → better PFS"
        ),
        "comparison_vs_2gene": comparison,
    }
    (out_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))

    # --- KM plot --------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4.5))
    kmf_high.plot_survival_function(ax=ax, color="tab:red")
    kmf_low.plot_survival_function(ax=ax, color="tab:blue")
    ax.set_title(
        f"IMmotion150 (n={len(df)}): TOP2A − (EPAS1 + SLC22A8) "
        f"median split\nlog-rank p = {lr_p_3:.4f}  |  "
        f"Cox HR per z = {hr_3:.2f} "
        f"(95% CI {hr3_ci_low:.2f}–{hr3_ci_high:.2f})  |  "
        f"C-index = {c_idx_3:.3f}",
        fontsize=9,
    )
    ax.set_xlabel("Months since start of therapy")
    ax.set_ylabel("Progression-free survival")
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "km_median_split.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
