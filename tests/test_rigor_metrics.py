"""Tests for the G2 rigor-extension metrics (AUPRC + Brier + calibration)."""
from __future__ import annotations

import numpy as np
import pytest

from theory_copilot.rigor_metrics import rigor_metrics


@pytest.fixture
def synthetic_classification():
    rng = np.random.default_rng(seed=42)
    n = 300
    y = rng.binomial(n=1, p=0.16, size=n).astype(int)  # ~16% prevalence (matches KIRC M1)
    # Score correlated with y: y=1 ⇒ Normal(1.2, 1); y=0 ⇒ Normal(0, 1)
    score = rng.normal(loc=y * 1.2, scale=1.0)
    return score, y


def test_returns_expected_keys(synthetic_classification):
    score, y = synthetic_classification
    out = rigor_metrics(score, y, seed=0)
    expected = {
        "auprc",
        "auprc_baseline",
        "auprc_lift",
        "brier",
        "brier_uninformative_ref",
        "calibration_slope",
        "calibration_intercept",
        "cal_curve_predicted",
        "cal_curve_observed",
        "prevalence",
        "n_samples",
        "seed",
    }
    assert expected.issubset(out.keys())


def test_auprc_above_baseline(synthetic_classification):
    score, y = synthetic_classification
    out = rigor_metrics(score, y, seed=0)
    # The synthetic signal (Δμ=1.2) should yield AUPRC well above prevalence
    assert out["auprc"] > out["auprc_baseline"]
    assert out["auprc_lift"] > 1.5


def test_brier_below_uninformative_reference(synthetic_classification):
    score, y = synthetic_classification
    out = rigor_metrics(score, y, seed=0)
    # A signal that beats random should produce Brier < p(1-p)
    assert out["brier"] < out["brier_uninformative_ref"]


def test_calibration_slope_positive_for_signal(synthetic_classification):
    score, y = synthetic_classification
    out = rigor_metrics(score, y, seed=0)
    # On a positively-correlated score, slope b in logit(y) ~ a + b·score
    # must be > 0; an honest discrimination metric.
    assert out["calibration_slope"] > 0.0


def test_sign_invariant_auprc():
    """AUPRC is computed sign-invariantly (matches the gate's AUROC convention)."""
    rng = np.random.default_rng(seed=1)
    n = 300
    y = rng.binomial(1, 0.16, n).astype(int)
    score = rng.normal(loc=y * 1.2, scale=1.0)
    pos = rigor_metrics(score, y, seed=0)
    neg = rigor_metrics(-score, y, seed=0)
    # Sign-flipped score should produce the same AUPRC + Brier (Platt absorbs sign)
    assert pos["auprc"] == pytest.approx(neg["auprc"], abs=1e-9)
    assert pos["brier"] == pytest.approx(neg["brier"], abs=1e-9)


def test_deterministic_seed():
    rng = np.random.default_rng(seed=2)
    n = 200
    y = rng.binomial(1, 0.2, n).astype(int)
    score = rng.normal(loc=y, scale=1.0)
    a = rigor_metrics(score, y, seed=0)
    b = rigor_metrics(score, y, seed=0)
    assert a["brier"] == pytest.approx(b["brier"], abs=1e-12)
    assert a["auprc"] == pytest.approx(b["auprc"], abs=1e-12)


def test_attaches_to_falsification_suite():
    """run_falsification_suite returns a `rigor` dict by default."""
    from theory_copilot.falsification import run_falsification_suite

    rng = np.random.default_rng(seed=3)
    n = 200
    y = rng.binomial(1, 0.2, n).astype(int)
    X = rng.normal(loc=y[:, None] * 0.8, scale=1.0, size=(n, 3))

    def equation_fn(X_arr):
        return X_arr[:, 0] - X_arr[:, 1]

    out = run_falsification_suite(equation_fn, X, y, seed=0, include_decoy=False)
    assert "rigor" in out
    assert "auprc" in out["rigor"]
    assert "brier" in out["rigor"]
    assert "calibration_slope" in out["rigor"]
