#!/usr/bin/env python3
"""PhF-3b: external replay of TOP2A − EPAS1 on IMmotion150 metastatic ccRCC.

Pre-registration: preregistrations/*phf3_immotion150_pfs_replay.yaml
(written and committed BEFORE this script was run).

Kill tests (from that pre-reg):
  1. Log-rank median-split p < 0.05 (two-sided).
  2. Cox HR per z-score: |log(HR)| > log(1.3) AND 95% CI excludes 1.
  3. Harrell C-index > 0.55.

Direction of effect NOT pre-specified (two-sided test). The biological
prediction is "high TOP2A-EPAS1 → worse PFS" but the pre-reg does not
assume it.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "data" / "immotion150_ccrcc.csv"
    out_dir = repo_root / "results" / "track_a_task_landscape" / "external_replay" / "immotion150_pfs"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df["TOP2A"] = pd.to_numeric(df["TOP2A"], errors="coerce")
    df["EPAS1"] = pd.to_numeric(df["EPAS1"], errors="coerce")
    df["PFS_MONTHS"] = pd.to_numeric(df["PFS_MONTHS"], errors="coerce")
    # PFS_STATUS is encoded as e.g. "1:Progressed" or "0:Censored" — normalise.
    raw_status = df["PFS_STATUS"].astype(str)
    df["pfs_event"] = raw_status.str.startswith("1").astype(int)

    df = df.dropna(subset=["TOP2A", "EPAS1", "PFS_MONTHS", "pfs_event"]).copy()
    df["score"] = df["TOP2A"] - df["EPAS1"]
    df["score_z"] = (df["score"] - df["score"].mean()) / df["score"].std()

    # --- 1) Log-rank on median split --------------------------------------
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    median = df["score"].median()
    df["group"] = np.where(df["score"] >= median, "high", "low")
    high = df[df["group"] == "high"]
    low = df[df["group"] == "low"]
    lr = logrank_test(
        high["PFS_MONTHS"], low["PFS_MONTHS"],
        event_observed_A=high["pfs_event"], event_observed_B=low["pfs_event"],
    )
    lr_p = float(lr.p_value)
    lr_chi2 = float(lr.test_statistic)

    kmf_high = KaplanMeierFitter().fit(high["PFS_MONTHS"], high["pfs_event"], label=f"high (n={len(high)})")
    kmf_low = KaplanMeierFitter().fit(low["PFS_MONTHS"], low["pfs_event"], label=f"low (n={len(low)})")
    median_pfs_high = float(kmf_high.median_survival_time_)
    median_pfs_low = float(kmf_low.median_survival_time_)

    # --- 2) Cox HR per z-score --------------------------------------------
    from lifelines import CoxPHFitter
    cox_df = df[["PFS_MONTHS", "pfs_event", "score_z"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    )
    cph = CoxPHFitter()
    cph.fit(cox_df, duration_col="T", event_col="E")
    hr = float(np.exp(cph.params_["score_z"]))
    hr_ci_low = float(np.exp(cph.confidence_intervals_.loc["score_z", "95% lower-bound"]))
    hr_ci_high = float(np.exp(cph.confidence_intervals_.loc["score_z", "95% upper-bound"]))
    cox_p = float(cph.summary.loc["score_z", "p"])

    # --- 3) Harrell C-index -----------------------------------------------
    from lifelines.utils import concordance_index
    # Higher score → shorter PFS expected. concordance_index expects higher
    # predicted survival time → higher concordance; so negate the score when
    # predicting survival time (equivalent to predicting risk directly).
    c_index_risk = float(concordance_index(
        df["PFS_MONTHS"], -df["score"], df["pfs_event"]
    ))
    # Also compute the score-as-survival-time direction (if biology were
    # inverse).
    c_index_inverse = float(concordance_index(
        df["PFS_MONTHS"], df["score"], df["pfs_event"]
    ))
    c_index = max(c_index_risk, c_index_inverse)

    # --- Kill-test verdicts -----------------------------------------------
    test1 = {"name": "logrank_median_split", "p": lr_p, "chi2": lr_chi2,
             "threshold": "p < 0.05", "pass": lr_p < 0.05}
    test2 = {"name": "cox_hazard_ratio", "hr": hr,
             "hr_ci_95": [hr_ci_low, hr_ci_high], "p": cox_p,
             "threshold": "abs(log(HR)) > log(1.3) AND 95%CI excludes 1",
             "pass": abs(np.log(hr)) > np.log(1.3) and not (hr_ci_low <= 1 <= hr_ci_high)}
    test3 = {"name": "concordance_index", "c_index_risk_direction": c_index_risk,
             "c_index_inverse_direction": c_index_inverse, "c_index_best": c_index,
             "threshold": "> 0.55", "pass": c_index > 0.55}

    all_pass = test1["pass"] and test2["pass"] and test3["pass"]

    verdict = {
        "hypothesis_id": "phf3_immotion150_pfs_replay",
        "cohort": "IMmotion150 (rcc_iatlas_immotion150_2018)",
        "n": int(len(df)),
        "events": int(df["pfs_event"].sum()),
        "median_score": float(median),
        "median_pfs_high_group": median_pfs_high,
        "median_pfs_low_group": median_pfs_low,
        "kill_tests": [test1, test2, test3],
        "verdict": "PASS" if all_pass else "FAIL",
        "direction": ("high score → worse PFS" if c_index_risk > c_index_inverse
                      else "high score → better PFS"),
        "prereg_file": "preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml",
    }
    (out_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))

    # Plot KM curves.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4.5))
    kmf_high.plot_survival_function(ax=ax, color="tab:red")
    kmf_low.plot_survival_function(ax=ax, color="tab:blue")
    ax.set_title(
        f"IMmotion150 (n={len(df)} metastatic ccRCC): TOP2A − EPAS1 "
        f"median split\nlog-rank p = {lr_p:.4f}  |  Cox HR per z = "
        f"{hr:.2f} (95% CI {hr_ci_low:.2f}–{hr_ci_high:.2f})  |  "
        f"C-index = {c_index:.3f}",
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
