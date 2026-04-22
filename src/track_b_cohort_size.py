"""Track B — B6: Cohort-size subsampling curve.

Subsample TCGA-KIRC tumor-vs-normal to ``n ∈ {100, 200, 400, 600}`` and
re-apply the five-test gate to the Opus ex-ante HIF/angiogenesis law
``log1p(CA9) + log1p(VEGFA) - log1p(AGXT)``. Records the ``law_auc``,
``baseline_auc`` (sign-invariant max), ``ci_lower``, ``perm_p``, and
the verdict at each n for multiple RNG seeds. Shows whether the
0-survivor verdict is robust to cohort-size reduction.

Output:
    results/track_b_gate_robustness/cohort_size_curve.json

Usage:
    python src/track_b_cohort_size.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from track_b_permutation_stability import (
    TASK_FEATURES,
    _parse_labels,
    make_equation_fn,
    sign_invariant_auc,
)


FLAGSHIP_CSV = "data/kirc_tumor_normal.csv"
# The canonical ex-ante HIF/angiogenesis law from the Opus ex-ante set.
DEFAULT_LAW = "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)"


def single_feature_baseline(X: np.ndarray, y: np.ndarray) -> float:
    best = -1.0
    for j in range(X.shape[1]):
        a = sign_invariant_auc(y, X[:, j])
        best = max(best, a)
    return float(best)


def bootstrap_ci(
    y: np.ndarray,
    scores: np.ndarray,
    n_resamples: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(y)
    aucs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        y_s = y[idx]
        s_s = scores[idx]
        if len(np.unique(y_s)) < 2:
            aucs[i] = np.nan
            continue
        aucs[i] = sign_invariant_auc(y_s, s_s)
    aucs = aucs[~np.isnan(aucs)]
    return float(np.quantile(aucs, 0.025)), float(np.quantile(aucs, 0.975))


def permutation_p(
    y: np.ndarray,
    scores: np.ndarray,
    n_permutations: int,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed)
    obs = sign_invariant_auc(y, scores)
    shuffled = np.empty(n_permutations, dtype=float)
    for i in range(n_permutations):
        shuffled[i] = sign_invariant_auc(rng.permutation(y), scores)
    return float(np.mean(shuffled >= obs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ns", type=int, nargs="+", default=[100, 200, 400, 600])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--equation", default=DEFAULT_LAW)
    parser.add_argument("--n-resamples", type=int, default=1000)
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--out-dir", default="results/track_b_gate_robustness")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(FLAGSHIP_CSV)
    features = TASK_FEATURES["flagship"]
    X_all = df[features].to_numpy(dtype=float)
    y_all = _parse_labels(df["label"])
    n_total = len(y_all)
    print(f"Full cohort: n={n_total}, pos rate={y_all.mean():.3f}")

    fn = make_equation_fn(args.equation, features)
    records: list[dict[str, Any]] = []
    for n in args.ns:
        if n > n_total:
            continue
        for seed in args.seeds:
            rng = np.random.default_rng(seed * 1000 + n)
            idx = rng.choice(n_total, size=n, replace=False)
            X = X_all[idx]
            y = y_all[idx]
            if len(np.unique(y)) < 2:
                records.append({"n": n, "seed": seed, "error": "single-class subsample"})
                continue
            scores = fn(X)
            law_auc = sign_invariant_auc(y, scores)
            baseline_auc = single_feature_baseline(X, y)
            ci_lower, ci_upper = bootstrap_ci(y, scores, args.n_resamples, seed)
            p = permutation_p(y, scores, args.n_permutations, seed)
            delta = law_auc - baseline_auc
            passes = (
                p < 0.05
                and ci_lower > 0.6
                and delta > 0.05
            )
            records.append(
                {
                    "n": int(n),
                    "seed": int(seed),
                    "law_auc": law_auc,
                    "baseline_auc": baseline_auc,
                    "delta_baseline": float(delta),
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "perm_p": p,
                    "pass_reduced_gate": bool(passes),
                    "pos_rate": float(np.mean(y)),
                }
            )
            print(
                f"  n={n:4d} seed={seed} law_auc={law_auc:.4f} "
                f"baseline={baseline_auc:.4f} ci_lower={ci_lower:.4f} "
                f"delta={delta:+.4f} p={p:.4f} pass={passes}"
            )

    out = {
        "equation": args.equation,
        "full_n": n_total,
        "ns": args.ns,
        "seeds": args.seeds,
        "records": records,
    }
    out_path = out_dir / "cohort_size_curve.json"
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {out_path}  ({len(records)} rows)")


if __name__ == "__main__":
    main()
