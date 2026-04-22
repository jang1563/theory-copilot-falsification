# Track B — Progress Log

## B1 — Threshold sensitivity grid  `2026-04-22`

**Code:** `src/gate_sensitivity.py`
**Artifacts:**
- `results/track_b_gate_robustness/threshold_grid.csv` (1,809 rows, long format)
- `results/track_b_gate_robustness/threshold_heatmap.png` (67 candidates × 32 scenarios)
- `results/track_b_gate_robustness/threshold_grid_summary.json`

**Inputs loaded (4 sources, 67 candidates):**

| Source | N | Path |
|---|---|---|
| flagship_pysr | 26 | `results/flagship_run/falsification_report.json` |
| tier2_pysr | 27 | `results/tier2_run/falsification_report.json` |
| opus_exante_flagship | 7 | `results/opus_exante/kirc_flagship_report.json` |
| opus_exante_tier2 | 7 | `results/opus_exante/kirc_tier2_report.json` |

Total 67, not the 60 the brief anticipated — Opus ex-ante is evaluated on
both the tumor-vs-normal and stage tasks (7 laws × 2 tasks = 14), making
26 + 27 + 14 = 67. All have the five gate metrics present.

### Headline (current pre-registered thresholds)
- **current_all** → **0 survivors** across all 67 candidates — confirms the
  RESULTS.md verdict.

### delta_baseline flip curve (operative constraint)

| threshold | survivors | by-source breakdown |
|---|---|---|
| 0.000 | 15 | 14 flagship_pysr + 1 opus_exante_flagship |
| 0.010 | 15 | same |
| 0.020 | 11 | flagship_pysr only |
| 0.025 | 5 | flagship_pysr only |
| **0.030** | **0** | **cliff** |
| 0.035 | 0 | — |
| 0.040 | 0 | — |
| 0.050 (current) | 0 | — |
| 0.060 | 0 | — |
| 0.080 | 0 | — |

Cliff at 0.030 is the empirical +0.029 ceiling described in RESULTS.md.
The verdict flips **strictly below** the empirical ceiling — there is no
gray zone between 0.030 and 0.050.

### Other thresholds (held at current for non-operative test)

| Threshold | Grid values | Survivors across grid |
|---|---|---|
| ci_lower | 0.50 … 0.70 | 0 at every value |
| perm_p_fdr | 0.01 … 0.10 | 0 at every value |
| delta_confound | 0.00 … 0.05 | 0 at every value |
| decoy_p | 0.01 … 0.10 | 0 at every value |

Relaxing any of the other four thresholds in isolation does not yield a
single survivor — `delta_baseline` is the sole operative constraint.

### One-line finding

The 0-survivor verdict is robust to *any* reasonable relaxation of the
four non-baseline thresholds and is robust to a ~40% relaxation of
`delta_baseline` (0.05 → 0.030). Survivors appear only when
`delta_baseline` drops below the empirical +0.029 ceiling.

### What's next (B2 — baseline definition ablation)

B1 treats the current sign-invariant max as fixed. B2 will re-derive
`delta_baseline` under two stronger baselines (LR-single and LR-pair+
interaction) to test whether the verdict flips when the *definition*
of "best single-gene baseline" changes, independent of threshold.

---

## B2 — Baseline definition ablation  `2026-04-22`

**Code:** `src/track_b_baseline_ablation.py`
**Artifacts:**
- `results/track_b_gate_robustness/baseline_ablation.csv` (201 rows; 67 candidates × 3 baselines)
- `results/track_b_gate_robustness/baseline_ablation_summary.json`

### Per-task baseline AUCs

| Task | `sign_invariant_max` | `lr_single` | `lr_pair_interaction` |
|---|---|---|---|
| flagship (n=609) | **0.9655** (CA9) | 0.9658 | **0.9842** |
| tier2 (n=534) | **0.6098** (CUBN) | 0.6085 | **0.6434** |

### Max `delta_baseline` under each baseline

| Task | Baseline | Max Δ | Survivors |
|---|---|---|---|
| flagship | sign_invariant_max | +0.029 | 0 |
| flagship | lr_single | +0.029 | 0 |
| flagship | **lr_pair_interaction** | **+0.010** | 0 |
| tier2 | sign_invariant_max | +0.029 | 0 |
| tier2 | lr_single | +0.030 | 0 |
| tier2 | **lr_pair_interaction** | **−0.005** | 0 |

### Finding

- `lr_single` ≈ `sign_invariant_max` (a logistic regression on a single
  gene does not materially beat the simple AUC — the tails of the
  decision function already match what LR would learn).
- **`lr_pair_interaction` drops the max delta by ~65% on flagship
  (+0.029 → +0.010) and turns it negative on tier2 (−0.005)**. The
  strongest multi-gene compound law is essentially no better than a
  two-gene logistic regression with an interaction term.
- Under any of the three baseline definitions, zero candidates pass the
  gate. The verdict hardens, not softens, when the baseline is
  strengthened.

### Interpretation

Had we pre-registered "beat pair+interaction LR" instead of "beat
best single gene", the incremental ceiling on flagship would be
**+0.010 AUROC**, not +0.029. The apparent +0.029 gap is substantially
explained by pairwise gene-gene interactions that a compound
symbolic law can also capture, but not amplify beyond them. On tier2
the compound laws are measurably *worse* than pair+interaction.

### What's next (B3 — permutation stability)

Holding the gate's baseline fixed, vary n_permutations to see whether
the `perm_p_fdr` estimate is seed-stable. If a candidate's p flips
across permutation counts, the gate's verdict at the margin may be
noisy even if the +0.029 ceiling is solid.

---

## B5 — Feature-scaling ablation  `2026-04-22`

**Code:** `src/track_b_scaling_ablation.py`
**Artifacts:**
- `results/track_b_gate_robustness/scaling_ablation.csv` (268 rows)
- `results/track_b_gate_robustness/scaling_ablation_summary.json`

Re-evaluates the 67 candidates under four scalings on real TCGA-KIRC,
recomputing `law_auc`, `baseline_auc` (sign-invariant max), and
`delta_baseline`. Applies a reduced gate (`delta_baseline > 0.05`) per
B1's finding that delta is the sole operative constraint.

### Per (task, scaling) summary

| Task | Scaling | Baseline AUC | Max `law_auc` | Max Δ | Survivors (reduced gate) |
|---|---|---|---|---|---|
| flagship | raw | 0.9655 (CA9) | 0.9946 | +0.0291 | 0 / 33 |
| flagship | zscore | 0.9655 (CA9) | 0.9949 | +0.0294 | 0 / 33 |
| flagship | rank | 0.9655 (CA9) | 0.9907 | +0.0252 | 0 / 33 |
| flagship | minmax | 0.9655 (CA9) | 0.9953 | +0.0298 | 0 / 33 |
| tier2 | raw | 0.6098 (CUBN) | 0.6385 | +0.0287 | 0 / 34 |
| tier2 | **zscore** | 0.6098 (CUBN) | **0.6648** | **+0.0550** | **1 / 34** |
| tier2 | rank | 0.6098 (CUBN) | 0.6506 | +0.0408 | 0 / 34 |
| tier2 | minmax | 0.6098 (CUBN) | 0.6405 | +0.0307 | 0 / 34 |

### Finding

Flagship verdict (0 survivors) is **scaling-invariant** — max delta
ranges from 0.025 to 0.030 across all four scalings.

**Tier2 × zscore** flips the reduced-gate verdict for one candidate
(max Δ = +0.055 > 0.05). Under the **full** 5-test gate the other
four tests (permutation, CI, confound, decoy) still apply and would
need separate verification; the scaling effect on tier2 is the one
place where the artifact's design choice (z-score standardization
inside the gate) may matter operationally.

### Interpretation

The flagship headline (0 survivors, +0.029 ceiling) is robust to
scaling choice. The tier2 finding reveals a mild design sensitivity:
the 0.06-AUROC ceiling on tier2 depends on the scaling. Z-score
strengthens the compound-law advantage by ~0.02 AUROC relative to
raw. Whether that still passes the full gate is checked in B7.

---

## B6 — Cohort-size subsampling  `2026-04-22`

**Code:** `src/track_b_cohort_size.py`
**Law:** `log1p(CA9) + log1p(VEGFA) - log1p(AGXT)` (Opus ex-ante)
**Artifacts:** `results/track_b_gate_robustness/cohort_size_curve.json`

Subsamples TCGA-KIRC (full n=609) to n ∈ {100, 200, 400, 600} with five
RNG seeds per n, re-computes law_auc / baseline_auc / ci_lower /
perm_p / delta_baseline.

### Per n (mean over seeds)

| n | law_auc | ci_lower (min / mean) | perm_p | Δ baseline | Pass (reduced) |
|---|---|---|---|---|---|
| 100 | 0.985 | 0.927 / 0.955 | 0.000 | +0.010 | 0/5 |
| 200 | 0.985 | 0.953 / 0.966 | 0.000 | +0.012 | 0/5 |
| 400 | 0.985 | 0.965 / 0.970 | 0.000 | +0.021 | 0/5 |
| 600 | 0.984 | 0.971 / 0.972 | 0.000 | +0.019 | 0/5 |

### Finding

`ci_lower > 0.60` at every cohort size tested, including n=100 (mean
0.955, min 0.927). The cohort would need to drop much smaller than 100
for `ci_lower` to approach 0.60. `delta_baseline` stays in the
+0.01…+0.02 band across all sizes — the compound advantage does not
materially change with sample size. `perm_p = 0.0` at every n.

### Interpretation

The 0-survivor verdict is robust to cohort-size reduction down to
n=100. The gate's stability floor (ci_lower > 0.60) is not the
limiting factor — delta_baseline is, at every size.

---

## B4 — Bootstrap seed variance  `2026-04-22`

**Code:** `src/track_b_bootstrap_variance.py`
**Artifacts:** `results/track_b_gate_robustness/bootstrap_seed_variance.json`
**Run:** top 5 × 4 sources = 20 candidates, 5 seeds × n_resamples=1000.

### Per-source seed variance of `ci_lower`

| Source | ci_lower_mean | ci_lower_std (max) | ci_lower_range (max) | Passes 0.60 gate (all seeds) |
|---|---|---|---|---|
| flagship_pysr (5) | 0.985–0.988 | 0.0007 | 0.0017 | 5/5 ✓ |
| opus_exante_flagship (5) | 0.858–0.973 | 0.0021 | 0.0052 | 5/5 ✓ |
| tier2_pysr (5) | 0.590 (all) | 0.0019 | 0.0052 | 0/5 ✗ (below) |
| opus_exante_tier2 (5) | 0.500–0.536 | 0.0031 | 0.0079 | 0/5 ✗ (below) |

### Finding

`ci_lower` is **stable to the third decimal** across 5 RNG seeds on
every candidate: the maximum range is 0.008, the maximum std is
0.003. No candidate's verdict flips across seeds. The gate's pass /
fail boundary for `ci_lower` (0.60) is nowhere near the measurement
noise for any of the 20 tested candidates — flagship candidates sit
~0.35 above the line, tier2 candidates sit ~0.01–0.10 below.

### Interpretation

The 0-survivor verdict is not a bootstrap-seed artifact. The tier2
PySR cluster genuinely fails the `ci_lower > 0.60` criterion — not
because the bootstrap happened to land on unlucky resamples, but
because the real data do not support a confident lower bound at 0.60.

---

## B3 — Permutation stability  `2026-04-22`

**Code:** `src/track_b_permutation_stability.py`
**Artifacts:** `results/track_b_gate_robustness/permutation_stability.json`
**Run:** 20 candidates (top 5 × 4 sources) × n ∈ {200, 500, 1000, 2000, 5000}
× 3 seeds = 300 permutation runs.

### Per-candidate cross-n stability

15 of 20 candidates have `perm_p = 0.000` at every n and every seed
(both zero std and zero cross-n range):

  - flagship_pysr (5): all 0.000
  - opus_exante_flagship (5): all 0.000
  - tier2_pysr (5): all 0.000

The remaining 5 candidates are the **opus_exante_tier2** set (the weak
stage-classification laws):

| Candidate | p_mean 200 | p_mean 500 | p_mean 1000 | p_mean 2000 | p_mean 5000 | max p_std (seeds) |
|---|---|---|---|---|---|---|
| opus_exante_tier2::000 | 0.597 | 0.603 | 0.593 | 0.598 | 0.594 | 0.048 |
| opus_exante_tier2::001 | 0.010 | 0.021 | 0.018 | 0.020 | 0.020 | 0.003 |
| opus_exante_tier2::002 | 0.135 | 0.167 | 0.164 | 0.165 | 0.169 | 0.024 |
| opus_exante_tier2::003 | 0.022 | 0.042 | 0.042 | 0.043 | 0.045 | 0.010 |
| opus_exante_tier2::006 | 0.002 | 0.001 | 0.001 | 0.000 | 0.001 | 0.003 |

### Finding

**Zero candidates flip the 0.05 pass / fail verdict** across any
combination of n_permutations and seed. Candidates with
`p_mean < 0.05` (`::001`, `::003`, `::006`) stay below 0.05 at every
n; candidates with `p_mean > 0.05` (`::000`, `::002`) stay above at
every n.

The closest-to-flip candidate is `opus_exante_tier2::003` with
p_mean running 0.022 → 0.045 across n. At n=5000 seeds, p_mean =
0.045 and max seed-std = 0.010, so a 1σ tail still lands at ≈ 0.055
— a hair above threshold, but the point estimate is stable below.
That's the only borderline case; every other candidate is far from
the boundary.

### Interpretation

Permutation count choice does **not** drive the pass / fail verdict
anywhere in the tested grid. The gate's `perm_p_fdr < 0.05` boundary
is stable to the two freedoms (how many shuffles, which seed). This
completes the robustness story — the permutation side contributes no
flips to the 0-survivor verdict.
