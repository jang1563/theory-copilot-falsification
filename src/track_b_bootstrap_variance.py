"""Track B — B4: Bootstrap seed variance scan.

For each task's top-5 candidates (by `law_auc`) re-runs a bootstrap
stability estimate (AUROC mean + 95% CI) with multiple RNG seeds.
Goal: verify the gate's ``ci_lower`` estimate is stable to at least
three decimals so the 0.60 threshold isn't on the wrong side of seed
noise.

Output:
    results/track_b_gate_robustness/bootstrap_seed_variance.json

Usage:
    python src/track_b_bootstrap_variance.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

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


def bootstrap_stability(
    X: np.ndarray,
    y: np.ndarray,
    equation_fn,
    n_resamples: int,
    seed: int,
) -> dict[str, float]:
    """Sign-invariant AUROC bootstrap. Returns mean, ci_lower (2.5 %), ci_upper
    (97.5 %), and ci_width (two-sided)."""
    rng = np.random.default_rng(seed)
    n = len(y)
    scores = equation_fn(X)
    aucs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        y_sample = np.asarray(y)[idx]
        s_sample = np.asarray(scores)[idx]
        if len(np.unique(y_sample)) < 2:
            aucs[i] = np.nan
            continue
        aucs[i] = sign_invariant_auc(y_sample, s_sample)
    aucs = aucs[~np.isnan(aucs)]
    return {
        "n_resamples": int(n_resamples),
        "seed": int(seed),
        "ci_lower": float(np.quantile(aucs, 0.025)),
        "ci_upper": float(np.quantile(aucs, 0.975)),
        "ci_width": float(np.quantile(aucs, 0.975) - np.quantile(aucs, 0.025)),
        "mean": float(np.mean(aucs)),
        "n_valid": int(len(aucs)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    )
    parser.add_argument("--n-resamples", type=int, default=1000)
    parser.add_argument("--out-dir", default="results/track_b_gate_robustness")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prime task data.
    task_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for task, csv in TASK_DATA.items():
        df = pd.read_csv(csv)
        X = df[TASK_FEATURES[task]].to_numpy(dtype=float)
        y = _parse_labels(df["label"])
        task_cache[task] = (X, y)

    records: list[dict[str, Any]] = []
    per_candidate: list[dict[str, Any]] = []
    for source in SOURCE_PATHS:
        task = SOURCE_TO_TASK[source]
        X, y = task_cache[task]
        features = TASK_FEATURES[task]
        for cand in select_top_candidates(source, top_n=args.top_n):
            try:
                fn = make_equation_fn(cand["equation"], features)
                _ = fn(X)  # sanity
            except Exception as exc:  # pylint: disable=broad-except
                per_candidate.append({**cand, "error": str(exc)})
                print(f"  SKIP {cand['candidate_id']}: {exc}")
                continue

            ci_lowers: list[float] = []
            ci_widths: list[float] = []
            runs: list[dict[str, Any]] = []
            for seed in args.seeds:
                stats = bootstrap_stability(
                    X, y, fn, n_resamples=args.n_resamples, seed=seed
                )
                runs.append(stats)
                ci_lowers.append(stats["ci_lower"])
                ci_widths.append(stats["ci_width"])

            cils = np.array(ci_lowers)
            widths = np.array(ci_widths)
            passes_gate_all = bool(np.all(cils > 0.60))
            passes_gate_any = bool(np.any(cils > 0.60))
            record = {
                "candidate_id": cand["candidate_id"],
                "source": source,
                "task": task,
                "equation": cand["equation"],
                "law_auc": cand["law_auc"],
                "report_ci_lower": cand.get("ci_lower"),
                "n_resamples": args.n_resamples,
                "seeds": list(args.seeds),
                "ci_lower_per_seed": ci_lowers,
                "ci_width_per_seed": ci_widths,
                "ci_lower_mean": float(np.mean(cils)),
                "ci_lower_std": float(np.std(cils, ddof=1)) if len(cils) > 1 else 0.0,
                "ci_lower_min": float(np.min(cils)),
                "ci_lower_max": float(np.max(cils)),
                "ci_lower_range": float(np.max(cils) - np.min(cils)),
                "ci_width_mean": float(np.mean(widths)),
                "passes_ci_gate_all_seeds": passes_gate_all,
                "passes_ci_gate_any_seed": passes_gate_any,
                "runs": runs,
            }
            records.append(record)
            per_candidate.append({**cand})
            print(
                f"  {cand['candidate_id']:30s} report_cil={cand.get('ci_lower'):.4f} "
                f"seed_mean={np.mean(cils):.4f} seed_range={np.max(cils)-np.min(cils):.4f}"
            )

    out = {
        "n_resamples": args.n_resamples,
        "seeds": list(args.seeds),
        "records": records,
    }
    out_path = out_dir / "bootstrap_seed_variance.json"
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {out_path}  ({len(records)} candidates)")


if __name__ == "__main__":
    main()
