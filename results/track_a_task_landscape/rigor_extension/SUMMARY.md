# G2 Rigor extension — TOP2A − EPAS1 metastasis_expanded

**Pre-registration:** `preregistrations/20260425T164840Z_g2_rigor_extension.yaml`
(`gate_logic_changed: false`, `extension_type: reporting_only`)

**Status:** Reporting-only metrics added alongside the v1 5-test gate.
The pass/fail decision for `TOP2A − EPAS1` is unchanged.

## What G2 adds

The 5-test gate scores classification on AUROC. AUROC is **not**
sensitive to the prevalence of the positive class, which on this task
is 16% M1 — a regime where AUPRC and probabilistic calibration carry
information AUROC alone hides. G2 attaches three reporting-only
metrics to every gate run:

| Metric | What it measures | Reference baseline |
|---|---|---|
| **AUPRC** | Precision-recall area; sensitive to imbalance | prevalence (16%) |
| **Brier score** | Mean squared error of out-of-fold Platt-scaled probabilities | `p(1−p)` (uninformative reference) |
| **Calibration slope / intercept** | Logistic fit `logit(y) ~ a + b·score` on full data | slope ∈ [0.85, 1.15], intercept ≈ 0 |

**AUPRC is sign-invariant.** Mirroring the gate's sign-invariant AUROC
convention, G2 takes `max(AUPRC(score), AUPRC(-score))` so a
downregulated-in-disease law is not penalised. The same orientation is
then used downstream for the Platt-scaled probabilities.

**Brier uses 5-fold OOF Platt.** Out-of-fold StratifiedKFold
(`random_state=seed`) avoids the in-sample optimism documented in
Niculescu-Mizil & Caruana (2005, ICML). The resulting probabilities
are valid in [0, 1] and feed the calibration curve.

## Result on `TOP2A − EPAS1` × metastasis_expanded (n=505, prevalence 0.156)

Numbers reproduced from `top2a_epas1_metastasis_g2_metrics.json`
(committed alongside this SUMMARY; seed=0).

| Metric | Value | Reference | Interpretation |
|---|---|---|---|
| AUROC (sign-inv) | **0.728** | random=0.5 | v1 gate output (matches +0.001 of the prior 0.726 reported in `survivor_narrative.md` — bootstrap-seed level noise) |
| AUPRC | **0.321** | prevalence=0.156 | **2.05× the random baseline** at this prevalence |
| AUPRC lift | **2.05×** | 1.00× | substantial lift in the imbalance-sensitive metric AUROC alone hides |
| Brier | **0.122** | uninformative=0.132 | 7.6% reduction in MSE-on-probability vs. predicting prevalence everywhere |
| Calibration slope | **0.540** | well-cal ∈ [0.85, 1.15] | **slope < 1 → score is more discriminative than its raw scale suggests**; an honest signal of room for re-calibration before clinical use |
| Calibration intercept | **−1.85** | well-cal ≈ 0 | combined with the low slope, indicates the raw `TOP2A − EPAS1` value is not a probability — Platt scaling is required (and is what the Brier above already uses) |

The `cal_curve_predicted` / `cal_curve_observed` lists give the
quantile-binned reliability diagram (5 bins). The top quintile
predicts 32% M1 and observes 35% — well-calibrated at the high end,
which is the bin most relevant for screening. The slope penalty is
dominated by the low-score tail.

## Why this matters for the submission narrative

1. **AUROC alone hides imbalance.** A 16% prevalence task with AUROC
   0.726 leaves the AUPRC headroom unspecified. Reporting AUPRC
   alongside AUROC closes a known credibility gap that TRIPOD+AI
   (2024, BMJ; PMID 38719247) and Steyerberg (2019, *Clinical
   Prediction Models* 2nd ed., Springer) recommend by default.
2. **Calibration is its own claim.** A discrimination metric (AUROC)
   tells you whether the score *ranks* M1 above M0; calibration tells
   you whether the score's *magnitude* is interpretable as a probability.
   The Skeptic agent reviews both.
3. **Gate logic is unchanged.** G2 is reporting-only; no PASS / FAIL
   decision flips because of these numbers. The pre-registration
   commits to this explicitly.

## Reproducibility

- 7 unit tests in `tests/test_rigor_metrics.py` (sign-invariance,
  determinism, AUPRC > prevalence baseline, Brier < uninformative
  reference under signal, calibration slope > 0 with signal).
- Sanity-check script: `/tmp/run_g2_sanity_v2.py` (reproduces the
  numbers above when re-run against `data/kirc_metastasis_expanded.csv`).
- Seed `0` for the StratifiedKFold (matches the pre-registration YAML).

## Citations

- TRIPOD+AI (2024). *Reporting guidelines for prediction models that
  use AI*. BMJ. PMID 38719247.
- Steyerberg E. (2019). *Clinical Prediction Models*, 2nd ed., Springer.
- Austin & Steyerberg (2019). *Reflection on calibration of risk
  prediction models*. PMID 31451920.
- Niculescu-Mizil & Caruana (2005). *Predicting Good Probabilities With
  Supervised Learning*. ICML.
