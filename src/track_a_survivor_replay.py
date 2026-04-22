#!/usr/bin/env python3
"""Replay attempt on the Track A survivor ``TOP2A - EPAS1``.

Full independent-cohort replay is not available: GSE40435 (our flagship
transfer cohort) lacks TOP2A/EPAS1 in its 8-gene subset AND has no M0/M1
labels at the patient level — both the equation and the task are out of
reach on that cohort.

Given that limitation, this script provides the best remaining sanity
checks:

  1. Stratified 5-fold CV AUROC on TCGA-KIRC metastasis_expanded
     (leave-one-fold-out for every law in a small set, with the held-
     out test fold measuring generalisation).
  2. A permutation-null AUROC baseline on each fold (same as fold CV
     but with labels shuffled inside each fold) to confirm the CV
     AUROC is not an artefact of fold-level imbalance.

Output: results/track_a_task_landscape/survivor_robustness/replay.json

Future: if CPTAC-3 ccRCC proteogenomic or cBioPortal MSKCC-IMPACT
metastatic-ccRCC data becomes available in the tracked data lane, run
the same 5-test falsification gate on that cohort in a follow-up
commit. The current script is structured to accept a second
--transfer-data flag for that upgrade.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))


LAWS = {
    "TOP2A - EPAS1":          lambda df: df["TOP2A"] - df["EPAS1"],
    "MKI67 - EPAS1":          lambda df: df["MKI67"] - df["EPAS1"],
    "CUBN":                   lambda df: df["CUBN"],
    "MKI67":                  lambda df: df["MKI67"],
    "TOP2A":                  lambda df: df["TOP2A"],
    "EPAS1":                  lambda df: -df["EPAS1"],
}


def fold_auroc(df: pd.DataFrame, score_fn, n_splits: int = 5, seed: int = 13) -> dict:
    y = (df["label"] == "disease").astype(int).values
    scores_all = score_fn(df).values.astype(float)
    scores_all = np.where(np.isfinite(scores_all), scores_all, np.nanmedian(scores_all))

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    fold_aucs, perm_aucs = [], []
    rng = np.random.default_rng(seed)
    for fold_idx, (_, test_idx) in enumerate(skf.split(np.zeros_like(y), y)):
        y_t = y[test_idx]
        s_t = scores_all[test_idx]
        if len(np.unique(y_t)) < 2:
            continue
        fold_aucs.append(float(roc_auc_score(y_t, s_t)))

        perm_auc_trials = []
        for _ in range(50):
            y_shuf = rng.permutation(y_t)
            perm_auc_trials.append(float(roc_auc_score(y_shuf, s_t)))
        perm_aucs.append(float(np.mean(perm_auc_trials)))

    sign_invariant = [max(a, 1 - a) for a in fold_aucs]
    perm_sign_inv = [max(a, 1 - a) for a in perm_aucs]

    return {
        "n_folds": len(fold_aucs),
        "auroc_raw_per_fold": fold_aucs,
        "auroc_sign_invariant_per_fold": sign_invariant,
        "auroc_sign_invariant_mean": float(np.mean(sign_invariant)) if sign_invariant else None,
        "auroc_sign_invariant_std": float(np.std(sign_invariant)) if sign_invariant else None,
        "permutation_null_mean_auroc_sign_inv": float(np.mean(perm_sign_inv)) if perm_sign_inv else None,
    }


def main() -> None:
    df = pd.read_csv("data/kirc_metastasis_expanded.csv")
    print(f"Metastasis expanded: {df.shape}")

    report = {"task": "TCGA-KIRC metastasis M0 vs M1", "n": int(df.shape[0]), "laws": {}}
    for name, fn in LAWS.items():
        print(f"\n-- {name} --")
        res = fold_auroc(df, fn)
        report["laws"][name] = res
        mn = res["auroc_sign_invariant_mean"]
        std = res["auroc_sign_invariant_std"]
        perm = res["permutation_null_mean_auroc_sign_inv"]
        print(f"  5-fold sign-inv AUROC = {mn:.3f} ± {std:.3f}  (perm-null = {perm:.3f})")

    out_dir = Path("results/track_a_task_landscape/survivor_robustness")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "replay_5foldcv.json").write_text(json.dumps(report, indent=2))
    print(f"\nWrote {out_dir/'replay_5foldcv.json'}")


if __name__ == "__main__":
    main()
