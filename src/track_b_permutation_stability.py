"""Track B — B3: Permutation stability scan.

For the top 5 candidates (by law_auc) of each source, re-run the
label-shuffle permutation null at ``n_permutations ∈ {200, 500, 1000,
2000, 5000}``. Records permutation p-values and their dispersion across
multiple RNG seeds, so we can see whether the gate's p estimate is
stable enough to support the pre-registered ``perm_p_fdr < 0.05`` rule.

Output:
    results/track_b_gate_robustness/permutation_stability.json

Usage:
    python src/track_b_permutation_stability.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}

# Full feature panel: 11 KIRC biology genes + 4 controls (ACTB/GAPDH/RPL13A
# as housekeeping nulls, MKI67 as proliferation null). Opus ex-ante negative
# controls reference the controls; the PySR sweep used the 11-gene subset.
# Both data CSVs carry all 15 columns, so a single shared panel is safe.
_FULL_PANEL = [
    "CA9", "VEGFA", "LDHA", "NDUFA4L2", "SLC2A1", "ENO2", "AGXT", "ALB",
    "CUBN", "PTGER3", "SLC12A3",
    "ACTB", "GAPDH", "RPL13A", "MKI67",
]
TASK_FEATURES: dict[str, list[str]] = {
    "flagship": _FULL_PANEL,
    "tier2": _FULL_PANEL,
}
TASK_DATA: dict[str, str] = {
    "flagship": "data/kirc_tumor_normal.csv",
    "tier2": "data/kirc_stage.csv",
}
SOURCE_TO_TASK: dict[str, str] = {
    "flagship_pysr": "flagship",
    "tier2_pysr": "tier2",
    "opus_exante_flagship": "flagship",
    "opus_exante_tier2": "tier2",
}

# The original gate uses named equations where possible. For PySR we use
# the gene-name-rewritten variants.
SOURCE_PATHS: dict[str, dict[str, str]] = {
    "flagship_pysr": {
        "report": "results/flagship_run/falsification_report.json",
        "named": "results/flagship_run/candidates_named.json",
    },
    "tier2_pysr": {
        "report": "results/tier2_run/falsification_report.json",
        "named": "results/tier2_run/candidates_named.json",
    },
    "opus_exante_flagship": {
        "report": "results/opus_exante/kirc_flagship_report.json",
        "named": None,  # equations already use gene names
    },
    "opus_exante_tier2": {
        "report": "results/opus_exante/kirc_tier2_report.json",
        "named": None,
    },
}

# Allowed numpy functions in the equation expression.
_SAFE_NAMES = {
    "log": np.log,
    "log1p": np.log1p,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "sin": np.sin,
    "cos": np.cos,
}


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def make_equation_fn(equation: str, feature_names: list[str]):
    """Build a vectorised callable from a symbolic equation. Returns a
    function ``fn(X: np.ndarray) -> np.ndarray``."""

    def fn(X: np.ndarray) -> np.ndarray:
        ns = dict(_SAFE_NAMES)
        for i, name in enumerate(feature_names):
            ns[name] = X[:, i]
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            values = eval(equation, {"__builtins__": {}}, ns)  # noqa: S307
        values = np.asarray(values, dtype=float)
        # Replace non-finite values with zeros so downstream AUC remains defined.
        values = np.where(np.isfinite(values), values, 0.0)
        return values

    return fn


def sign_invariant_auc(y: np.ndarray, scores: np.ndarray) -> float:
    """Return AUROC treating the score as direction-free."""
    try:
        a = roc_auc_score(y, scores)
    except ValueError:
        return float("nan")
    return float(max(a, 1.0 - a))


def label_shuffle_null(
    X: np.ndarray,
    y: np.ndarray,
    equation_fn,
    n_permutations: int,
    seed: int,
) -> tuple[float, float]:
    """Return (permutation_p, observed_auc). ``permutation_p`` is the
    fraction of shuffles with AUC ≥ observed."""
    rng = np.random.default_rng(seed)
    observed_scores = equation_fn(X)
    obs_auc = sign_invariant_auc(y, observed_scores)
    if np.isnan(obs_auc):
        return float("nan"), float("nan")
    shuffled = np.empty(n_permutations, dtype=float)
    y_arr = np.asarray(y)
    for i in range(n_permutations):
        y_perm = rng.permutation(y_arr)
        shuffled[i] = sign_invariant_auc(y_perm, observed_scores)
    p = float(np.mean(shuffled >= obs_auc))
    return p, obs_auc


def select_top_candidates(source: str, top_n: int = 5) -> list[dict[str, Any]]:
    """Select top ``top_n`` candidates by law_auc from a given source."""
    report_path = Path(SOURCE_PATHS[source]["report"])
    named_path = Path(SOURCE_PATHS[source]["named"]) if SOURCE_PATHS[source]["named"] else None
    report = json.loads(report_path.read_text())

    # Align named equations where available.
    named_eqs: list[str] | None = None
    if named_path and named_path.exists():
        named_raw = json.loads(named_path.read_text())
        named_eqs = [entry.get("equation", "") for entry in named_raw]

    ranked = sorted(
        enumerate(report),
        key=lambda t: t[1].get("law_auc") or 0.0,
        reverse=True,
    )[:top_n]

    result: list[dict[str, Any]] = []
    for idx, entry in ranked:
        eq = entry.get("equation", "")
        if named_eqs is not None and idx < len(named_eqs) and named_eqs[idx]:
            eq = named_eqs[idx]
        result.append(
            {
                "candidate_id": f"{source}::{idx:03d}",
                "source": source,
                "task": SOURCE_TO_TASK[source],
                "equation": eq,
                "original_equation": entry.get("equation", ""),
                "law_auc": float(entry.get("law_auc", float("nan"))),
                "baseline_auc": float(entry.get("baseline_auc", float("nan"))),
                "ci_lower": float(entry.get("ci_lower", float("nan"))),
                "perm_p_fdr": float(entry.get("perm_p_fdr", float("nan"))),
                "perm_p": float(entry.get("perm_p", float("nan"))),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--n-grid", type=int, nargs="+", default=[200, 500, 1000, 2000, 5000])
    parser.add_argument("--out-dir", default="results/track_b_gate_robustness")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cache loaded task data to avoid repeat I/O.
    task_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for task, csv in TASK_DATA.items():
        df = pd.read_csv(csv)
        features = TASK_FEATURES[task]
        X = df[features].to_numpy(dtype=float)
        y = _parse_labels(df["label"])
        task_cache[task] = (X, y)

    records: list[dict[str, Any]] = []
    per_candidate: list[dict[str, Any]] = []

    sources = list(SOURCE_PATHS.keys())
    for source in sources:
        top = select_top_candidates(source, top_n=args.top_n)
        task = SOURCE_TO_TASK[source]
        X, y = task_cache[task]
        features = TASK_FEATURES[task]
        print(f"\n=== {source} (task={task}) — top {len(top)} by law_auc ===")
        for cand in top:
            try:
                fn = make_equation_fn(cand["equation"], features)
            except SyntaxError as exc:
                print(f"  SKIP {cand['candidate_id']}: {exc}")
                per_candidate.append({**cand, "error": f"syntax: {exc}"})
                continue

            # Quick viability check: observed score finite and law_auc close
            # to the report's law_auc.
            scores = fn(X)
            obs_auc_check = sign_invariant_auc(y, scores)
            print(
                f"  {cand['candidate_id']} law_auc_report={cand['law_auc']:.4f} "
                f"law_auc_replayed={obs_auc_check:.4f} eq={cand['equation'][:80]}"
            )
            per_candidate.append({**cand, "law_auc_replayed": obs_auc_check})

            for n in args.n_grid:
                p_values: list[float] = []
                for seed in args.seeds:
                    p, _ = label_shuffle_null(X, y, fn, n_permutations=n, seed=seed)
                    p_values.append(p)
                records.append(
                    {
                        "candidate_id": cand["candidate_id"],
                        "source": source,
                        "task": task,
                        "equation": cand["equation"],
                        "n_permutations": n,
                        "seeds": args.seeds,
                        "p_values": p_values,
                        "p_mean": float(np.mean(p_values)),
                        "p_min": float(np.min(p_values)),
                        "p_max": float(np.max(p_values)),
                        "p_std": float(np.std(p_values, ddof=1)) if len(p_values) > 1 else 0.0,
                    }
                )

    summary = {
        "top_n": args.top_n,
        "seeds": args.seeds,
        "n_grid": args.n_grid,
        "candidates": per_candidate,
        "records": records,
    }
    out_path = out_dir / "permutation_stability.json"
    out_path.write_text(json.dumps(summary, indent=2, default=float))
    print(f"\nWrote {out_path}")

    # Compact summary table.
    df = pd.DataFrame(records)
    if not df.empty:
        pivot = df.pivot_table(
            index="candidate_id",
            columns="n_permutations",
            values="p_mean",
            aggfunc="first",
        ).sort_index()
        print("\n=== perm_p (mean over seeds) by candidate × n_permutations ===")
        print(pivot.to_string())


if __name__ == "__main__":
    main()
