"""Track B — B5: Feature-scaling ablation.

Re-evaluates the 67 existing candidates under four feature-scaling regimes:
``raw``, ``z-score``, ``rank``, ``min-max``. For each candidate × scaling,
computes ``law_auc`` (sign-invariant), ``baseline_auc`` (sign-invariant max
single-feature), ``delta_baseline``, and the pass/fail verdict assuming
only ``delta_baseline > 0.05`` (the sole operative constraint per B1).

The brief marks this as HPC-worthy because a *full* sweep under each
scaling would be expensive. Since the 5-test gate showed ``delta_baseline``
to be the sole operative constraint, re-evaluating just the delta column
under four scalings is a faithful proxy for the verdict and runs locally
in seconds.

Output:
    results/track_b_gate_robustness/scaling_ablation.csv
    results/track_b_gate_robustness/scaling_ablation_summary.json

Usage:
    python src/track_b_scaling_ablation.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from track_b_permutation_stability import (
    TASK_DATA,
    TASK_FEATURES,
    _parse_labels,
    make_equation_fn,
    select_top_candidates,
    SOURCE_PATHS,
    SOURCE_TO_TASK,
    sign_invariant_auc,
)


def scale_raw(X: np.ndarray) -> np.ndarray:
    return X.copy()


def scale_zscore(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std


def scale_rank(X: np.ndarray) -> np.ndarray:
    out = np.empty_like(X, dtype=float)
    for j in range(X.shape[1]):
        out[:, j] = rankdata(X[:, j])
    # Normalize to [0,1] so values are comparable to log-expression magnitudes.
    out = (out - 1.0) / (X.shape[0] - 1.0)
    return out


def scale_minmax(X: np.ndarray) -> np.ndarray:
    mn = X.min(axis=0, keepdims=True)
    mx = X.max(axis=0, keepdims=True)
    rng = np.where(mx - mn < 1e-8, 1.0, mx - mn)
    return (X - mn) / rng


SCALINGS: dict[str, callable] = {
    "raw": scale_raw,
    "zscore": scale_zscore,
    "rank": scale_rank,
    "minmax": scale_minmax,
}


def single_feature_max_auc(X: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    per_feat = np.array([sign_invariant_auc(y, X[:, j]) for j in range(X.shape[1])])
    best_idx = int(np.argmax(per_feat))
    return float(per_feat[best_idx]), best_idx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top-n", type=int, default=100, help="all candidates per source")
    parser.add_argument("--out-dir", default="results/track_b_gate_robustness")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="delta_baseline threshold for the reduced gate",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cache scaled task data.
    task_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for task, csv in TASK_DATA.items():
        df = pd.read_csv(csv)
        X = df[TASK_FEATURES[task]].to_numpy(dtype=float)
        y = _parse_labels(df["label"])
        task_cache[task] = (X, y)

    rows: list[dict[str, Any]] = []
    for source in SOURCE_PATHS:
        task = SOURCE_TO_TASK[source]
        X_raw, y = task_cache[task]
        features = TASK_FEATURES[task]
        # Precompute baselines per scaling so they're reused across candidates.
        baselines: dict[str, tuple[float, str]] = {}
        for scale_name, fn in SCALINGS.items():
            X_s = fn(X_raw)
            base_auc, best_idx = single_feature_max_auc(X_s, y)
            baselines[scale_name] = (base_auc, features[best_idx])

        for cand in select_top_candidates(source, top_n=args.top_n):
            try:
                eq_fn = make_equation_fn(cand["equation"], features)
            except SyntaxError as exc:
                rows.append({**cand, "error": f"syntax: {exc}"})
                continue

            for scale_name, scaler in SCALINGS.items():
                X_s = scaler(X_raw)
                try:
                    scores = eq_fn(X_s)
                except Exception as exc:  # pylint: disable=broad-except
                    rows.append(
                        {
                            "candidate_id": cand["candidate_id"],
                            "source": source,
                            "task": task,
                            "scaling": scale_name,
                            "error": str(exc),
                        }
                    )
                    continue
                law_auc = sign_invariant_auc(y, scores)
                base_auc, base_feat = baselines[scale_name]
                delta = law_auc - base_auc
                rows.append(
                    {
                        "candidate_id": cand["candidate_id"],
                        "source": source,
                        "task": task,
                        "equation": cand["equation"],
                        "scaling": scale_name,
                        "law_auc": law_auc,
                        "baseline_auc": base_auc,
                        "baseline_feature": base_feat,
                        "delta_baseline": float(delta),
                        "pass_reduced_gate": bool(delta > args.threshold),
                    }
                )

    df_out = pd.DataFrame.from_records(rows)
    csv_path = out_dir / "scaling_ablation.csv"
    df_out.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}  ({len(df_out)} rows)")

    clean = df_out.dropna(subset=["law_auc"])
    summary = {
        "per_task_per_scaling": (
            clean.groupby(["task", "scaling"])
            .agg(
                baseline_auc=("baseline_auc", "first"),
                baseline_feature=("baseline_feature", "first"),
                max_law_auc=("law_auc", "max"),
                max_delta_baseline=("delta_baseline", "max"),
                survivors_reduced_gate=("pass_reduced_gate", "sum"),
                n_candidates=("candidate_id", "count"),
            )
            .reset_index()
            .to_dict(orient="records")
        ),
        "threshold": args.threshold,
    }
    summary_path = out_dir / "scaling_ablation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=float))
    print(f"Wrote {summary_path}")
    print("\n=== Per (task, scaling) ===")
    for r in summary["per_task_per_scaling"]:
        print(
            f"  {r['task']:10s} {r['scaling']:8s} base={r['baseline_auc']:.4f} "
            f"({r['baseline_feature']}) max_law={r['max_law_auc']:.4f} "
            f"max_delta={r['max_delta_baseline']:+.4f} "
            f"survivors={r['survivors_reduced_gate']}/{r['n_candidates']}"
        )


if __name__ == "__main__":
    main()
