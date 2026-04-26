"""I4 Information-theoretic analysis of TOP2A−EPAS1 compound.

Pre-registered in preregistrations/20260425T190552Z_i4_information_theory.yaml.

Histogram-based mutual information on quartile-discretized features +
Miller-Madow bias correction. Reports:
  I(TOP2A; y), I(EPAS1; y), I(TOP2A, EPAS1; y), I(TOP2A − EPAS1; y),
  synergy, compactness ratio.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/kirc_metastasis_expanded.csv"
RESULTS = REPO / "results/track_a_task_landscape/information_theory"
RESULTS.mkdir(parents=True, exist_ok=True)


def quantile_bin(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Quantile discretization: returns integer bin index in [0, n_bins-1]."""
    quantiles = np.quantile(x, np.linspace(0.0, 1.0, n_bins + 1))
    quantiles[0] = -np.inf
    quantiles[-1] = np.inf
    return np.digitize(x, quantiles[1:-1])


def mi_discrete(x_bins: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    """MI between discrete x and binary y using counts (in nats).

    Returns (mi_nats, k_used) where k_used = number of joint cells with
    nonzero count, used for Miller-Madow bias correction.
    """
    n = len(y)
    # Joint (x, y) counts
    joint = np.zeros((int(x_bins.max()) + 1, 2), dtype=float)
    for xi, yi in zip(x_bins, y):
        joint[int(xi), int(yi)] += 1
    px = joint.sum(axis=1) / n
    py = joint.sum(axis=0) / n
    pxy = joint / n
    mi = 0.0
    k_used = 0
    for i in range(joint.shape[0]):
        for j in range(joint.shape[1]):
            if pxy[i, j] > 0 and px[i] > 0 and py[j] > 0:
                mi += pxy[i, j] * np.log(pxy[i, j] / (px[i] * py[j]))
                k_used += 1
    return mi, k_used


def miller_madow_correction(mi_nats: float, k_used: int, n: int) -> float:
    """Subtract (k-1) / (2n) bias term."""
    return mi_nats - (k_used - 1) / (2.0 * n)


def compute_mi_set(top2a, epas1, y, n_bins_indiv: int = 4, n_bins_compound: int = 8):
    """Compute the four MI quantities + synergy + compactness.

    Returns a dict with corrected and uncorrected variants. Used both
    on the full sample and inside the bootstrap loop.
    """
    n = len(y)
    top2a_bins = quantile_bin(top2a, n_bins_indiv)
    epas1_bins = quantile_bin(epas1, n_bins_indiv)

    mi_t, k_t = mi_discrete(top2a_bins, y)
    mi_e, k_e = mi_discrete(epas1_bins, y)
    joint_bins = top2a_bins * n_bins_indiv + epas1_bins
    mi_j, k_j = mi_discrete(joint_bins, y)

    top2a_z = (top2a - top2a.mean()) / (top2a.std() + 1e-9)
    epas1_z = (epas1 - epas1.mean()) / (epas1.std() + 1e-9)
    score = top2a_z - epas1_z
    score_bins = quantile_bin(score, n_bins_compound)
    mi_c, k_c = mi_discrete(score_bins, y)

    # Same-binning fairness check: re-bin the compound at n_bins_indiv²
    # so it has the same total bin count as the joint (16 cells for 4×4).
    score_bins_eq = quantile_bin(score, n_bins_indiv * n_bins_indiv)
    mi_c_eq, k_c_eq = mi_discrete(score_bins_eq, y)

    mi_t_c = miller_madow_correction(mi_t, k_t, n)
    mi_e_c = miller_madow_correction(mi_e, k_e, n)
    mi_j_c = miller_madow_correction(mi_j, k_j, n)
    mi_c_c = miller_madow_correction(mi_c, k_c, n)
    mi_c_eq_c = miller_madow_correction(mi_c_eq, k_c_eq, n)

    synergy = mi_j_c - mi_t_c - mi_e_c
    compactness = mi_c_c / mi_j_c if mi_j_c > 0 else float("nan")
    compactness_eq = mi_c_eq_c / mi_j_c if mi_j_c > 0 else float("nan")
    return {
        "I_TOP2A_y": mi_t_c,
        "I_EPAS1_y": mi_e_c,
        "I_joint_y": mi_j_c,
        "I_compound_y_8bin": mi_c_c,
        "I_compound_y_16bin_same_as_joint": mi_c_eq_c,
        "synergy": synergy,
        "compactness_8bin": compactness,
        "compactness_same_binning": compactness_eq,
    }


def main():
    df = pd.read_csv(DATA)
    y = (df["label"] == "disease").astype(int).to_numpy()
    n = len(y)
    print(f"n={n}, prevalence={y.mean():.3f}")

    top2a = df["TOP2A"].to_numpy()
    epas1 = df["EPAS1"].to_numpy()

    # Point-estimate MI quantities on the full sample
    full = compute_mi_set(top2a, epas1, y, n_bins_indiv=4, n_bins_compound=8)
    mi_t = full["I_TOP2A_y"]
    mi_e = full["I_EPAS1_y"]
    mi_j = full["I_joint_y"]
    mi_c = full["I_compound_y_8bin"]
    mi_c_eq = full["I_compound_y_16bin_same_as_joint"]
    synergy = full["synergy"]
    compactness = full["compactness_8bin"]
    compactness_eq = full["compactness_same_binning"]

    print(f"\nI(TOP2A; y)              = {mi_t:.4f} nats")
    print(f"I(EPAS1; y)              = {mi_e:.4f} nats")
    print(f"I(joint; y) [4×4=16 cells] = {mi_j:.4f} nats")
    print(f"I(TOP2A−EPAS1; y) [8 bins]  = {mi_c:.4f} nats")
    print(f"I(TOP2A−EPAS1; y) [16 bins, fairness] = {mi_c_eq:.4f} nats")
    print(f"Synergy                  = {synergy:+.4f} nats")
    print(f"Compactness (8-bin)      = {compactness:.3f}")
    print(f"Compactness (same-bin 16) = {compactness_eq:.3f}")

    # Bootstrap CI on synergy + compactness (1000 resamples).
    # Addresses the concern that synergy ≈ +0.0014 nats sits inside
    # the sampling-noise band at this n. Reports 95 % percentile CI.
    print("\nBootstrapping synergy + compactness (1000 resamples)...")
    rng = np.random.default_rng(seed=0)
    boot_synergy = np.empty(1000, dtype=float)
    boot_compactness = np.empty(1000, dtype=float)
    boot_compactness_eq = np.empty(1000, dtype=float)
    for b in range(1000):
        idx = rng.integers(0, n, size=n)
        boot = compute_mi_set(top2a[idx], epas1[idx], y[idx], n_bins_indiv=4, n_bins_compound=8)
        boot_synergy[b] = boot["synergy"]
        boot_compactness[b] = boot["compactness_8bin"]
        boot_compactness_eq[b] = boot["compactness_same_binning"]
    syn_ci = (float(np.quantile(boot_synergy, 0.025)), float(np.quantile(boot_synergy, 0.975)))
    syn_lo_one_sided = float(np.quantile(boot_synergy, 0.05))
    syn_p_pos = float(np.mean(boot_synergy > 0))  # bootstrap probability synergy > 0
    cmp_ci = (float(np.quantile(boot_compactness, 0.025)), float(np.quantile(boot_compactness, 0.975)))
    cmp_eq_ci = (float(np.quantile(boot_compactness_eq, 0.025)), float(np.quantile(boot_compactness_eq, 0.975)))

    print(f"\n  Synergy            point={synergy:+.4f}   95% CI=({syn_ci[0]:+.4f}, {syn_ci[1]:+.4f})   P(syn>0)={syn_p_pos:.3f}")
    print(f"  Compactness 8-bin  point={compactness:.3f}    95% CI=({cmp_ci[0]:.3f}, {cmp_ci[1]:.3f})")
    print(f"  Compactness 16-bin point={compactness_eq:.3f}    95% CI=({cmp_eq_ci[0]:.3f}, {cmp_eq_ci[1]:.3f})")

    # Pre-registered predictions (point estimates as locked)
    max_indiv = max(mi_t, mi_e)
    p1 = mi_j > 1.25 * max_indiv
    p2 = synergy > 0
    p3 = compactness >= 0.70

    out = {
        "n_samples": n,
        "prevalence": float(y.mean()),
        "n_bins_individual": 4,
        "n_bins_compound": 8,
        "bias_correction": "miller_madow",
        "units": "nats",
        "mi": {
            "I_TOP2A_y_nats": mi_t,
            "I_EPAS1_y_nats": mi_e,
            "I_joint_y_nats": mi_j,
            "I_compound_y_nats_8bin": mi_c,
            "I_compound_y_nats_16bin_same_as_joint": mi_c_eq,
        },
        "synergy_nats": synergy,
        "synergy_bootstrap_ci_95": list(syn_ci),
        "synergy_bootstrap_p_positive": syn_p_pos,
        "compactness_ratio_8bin": compactness,
        "compactness_ratio_8bin_ci_95": list(cmp_ci),
        "compactness_ratio_same_binning_16bin": compactness_eq,
        "compactness_ratio_same_binning_ci_95": list(cmp_eq_ci),
        "predictions": {
            "p1_joint_gt_1p25x_max_individual": {
                "pass": bool(p1),
                "joint_nats": mi_j,
                "max_individual_nats": max_indiv,
                "ratio": mi_j / max_indiv if max_indiv > 0 else float("nan"),
                "threshold_ratio": 1.25,
            },
            "p2_synergy_positive": {
                "pass": bool(p2),
                "synergy_nats": synergy,
                "bootstrap_ci_95": list(syn_ci),
                "bootstrap_p_positive": syn_p_pos,
                "honest_caveat": (
                    "Synergy point estimate is positive but small relative to "
                    "sampling noise; bootstrap 95% CI may include zero. P(syn>0) "
                    "in the bootstrap distribution quantifies confidence."
                ),
            },
            "p3_compactness_ge_0p70": {
                "pass": bool(p3),
                "compactness_8bin": compactness,
                "compactness_8bin_ci_95": list(cmp_ci),
                "compactness_same_binning_16bin": compactness_eq,
                "compactness_same_binning_ci_95": list(cmp_eq_ci),
                "threshold": 0.70,
            },
        },
    }

    out_path = RESULTS / "info_metrics.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n=== Pre-registered prediction verdicts ===")
    print(f"  P1 (joint > 1.25× max individual): {'PASS' if p1 else 'FAIL'}  ({mi_j/max_indiv:.2f}×)")
    print(f"  P2 (synergy > 0):                  {'PASS' if p2 else 'FAIL'}  ({synergy:+.4f} nats; P(syn>0)={syn_p_pos:.2f})")
    print(f"  P3 (compactness ≥ 0.70):           {'PASS' if p3 else 'FAIL'}  ({compactness:.3f}, same-bin {compactness_eq:.3f})")
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
