"""G2 rigor-extension metrics.

Reporting-only additions to the falsification suite output: AUPRC,
Brier score (on 5-fold out-of-fold Platt-scaled probabilities), and
calibration slope/intercept. Pre-registered as gate-logic-unchanged
in preregistrations/20260425T164840Z_g2_rigor_extension.yaml.

These metrics do NOT change any pass/fail decision. The 5-test gate
in falsification.py remains the canonical decision surface.
"""
from __future__ import annotations

import warnings

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold


def rigor_metrics(
    score: np.ndarray,
    y: np.ndarray,
    n_cal_bins: int = 5,
    seed: int = 0,
) -> dict:
    """Compute AUPRC + Brier + calibration on a continuous score.

    Returns reporting-only metrics; no pass/fail thresholds are imposed.
    The Brier score uses out-of-fold Platt-scaled probabilities to avoid
    in-sample optimism (Niculescu-Mizil & Caruana 2005, ICML).

    Parameters
    ----------
    score : (n,) array
        Raw law score per sample. May be sign-flipped relative to y;
        Platt scaling absorbs the sign.
    y : (n,) array
        Binary outcome (0/1).
    n_cal_bins : int, default 5
        Quantile bins for the reliability diagram (Austin & Steyerberg
        2019 prefer equal-frequency at low prevalence).
    seed : int, default 0
        Deterministic seed for StratifiedKFold (matches the
        pre-registered seed in the YAML).

    Returns
    -------
    dict with keys:
      - auprc, auprc_baseline, auprc_lift
      - brier, brier_uninformative_ref
      - calibration_slope, calibration_intercept (raw-logit fit on full data)
      - cal_curve_predicted, cal_curve_observed (lists for plotting)
      - prevalence
      - seed (for reproducibility)
    """
    score = np.asarray(score, dtype=float).reshape(-1)
    y = np.asarray(y).astype(int).reshape(-1)
    n = y.shape[0]
    prevalence = float(y.mean())

    # ── AUPRC ────────────────────────────────────────────────────────────
    # Sign-handling: AUPRC is not sign-invariant. Use whichever sign
    # produces the higher AUPRC, mirroring the gate's sign-invariant
    # AUROC convention so a downregulated-in-disease law is not penalised.
    auprc_pos = float(average_precision_score(y, score))
    auprc_neg = float(average_precision_score(y, -score))
    auprc = max(auprc_pos, auprc_neg)
    score_oriented = score if auprc_pos >= auprc_neg else -score

    auprc_baseline = prevalence
    auprc_lift = auprc / auprc_baseline if auprc_baseline > 0 else float("nan")

    # ── 5-fold out-of-fold Platt-scaled probabilities ────────────────────
    prob = np.zeros(n, dtype=float)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for tr, te in skf.split(score_oriented, y):
            lr = LogisticRegression(max_iter=1000)
            lr.fit(score_oriented[tr].reshape(-1, 1), y[tr])
            prob[te] = lr.predict_proba(score_oriented[te].reshape(-1, 1))[:, 1]

    brier = float(brier_score_loss(y, prob))
    brier_uninformative_ref = prevalence * (1.0 - prevalence)

    # ── Calibration slope/intercept on full-data logistic fit ────────────
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        full = LogisticRegression(max_iter=1000).fit(
            score_oriented.reshape(-1, 1), y
        )
    slope = float(full.coef_[0, 0])
    intercept = float(full.intercept_[0])

    # ── Reliability curve for plotting ───────────────────────────────────
    # `calibration_curve` requires probabilities in [0, 1]; we pass the
    # 5-fold Platt-scaled probs which are valid probabilities.
    try:
        observed, predicted = calibration_curve(
            y, prob, n_bins=n_cal_bins, strategy="quantile"
        )
        cal_curve_predicted = predicted.tolist()
        cal_curve_observed = observed.tolist()
    except ValueError:
        # Degenerate case (e.g., all probs identical); skip the curve
        cal_curve_predicted = []
        cal_curve_observed = []

    return {
        "auprc": auprc,
        "auprc_baseline": auprc_baseline,
        "auprc_lift": auprc_lift,
        "brier": brier,
        "brier_uninformative_ref": brier_uninformative_ref,
        "calibration_slope": slope,
        "calibration_intercept": intercept,
        "cal_curve_predicted": cal_curve_predicted,
        "cal_curve_observed": cal_curve_observed,
        "prevalence": prevalence,
        "n_samples": n,
        "seed": seed,
    }
