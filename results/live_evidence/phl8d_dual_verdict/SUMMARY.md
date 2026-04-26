# PhL-8d — Dual Verdict Oracle: FAIL + PASS in one autonomous session

**Status:** COMPLETE (v2) — clean dual verdict. FAIL reason = delta_baseline.  
**Run date:** 2026-04-26  
**Session URL (v2):** `https://claude.ai/code/session_01CgsJYAPdvhJJwTuBt7QZLZ`  
**Session URL (v1):** [not recorded]

## What this run shows (vs PhL-8c)

| Property | PhL-8c (Scientific Oracle) | PhL-8d (Dual Verdict Oracle) |
|---|---|---|
| Trigger text | `"equation: CDK1 - EPAS1"` | Two equations: FAIL + PASS |
| Equations run | 1 (expected PASS) | 2 (one expected FAIL, one expected PASS) |
| Gate outcomes | PASS only | FAIL + PASS |
| Lacuna narrative covered | Accept cycle only | **Full story: reject AND accept** |
| Session duration | ~4 min | ~6–8 min |

PhL-8c showed the oracle gate can accept a valid law. PhL-8d shows
the gate's **falsification power**: the same pre-registered thresholds, the
same infrastructure, the same session — one equation rejected, one accepted.

## Equations submitted

**Eq1 — expected FAIL** (HIF-axis linear, tumor vs normal):
```
CA9 - AGXT
```
Why it should fail: CA9 alone reaches AUROC 0.965 on the tumor_vs_normal task.
The compound adds only Δ ≈ +0.019 over the best single-gene baseline — below
the pre-registered +0.05 threshold. This is the same HIF-axis logic as the
Opus 4.7-proposed textbook law rejected in the original ccRCC sweep.
Note: `log1p(CA9) + log1p(VEGFA) - log1p(AGXT)` breaks under `--standardize`
(z-scores go negative → NaN in log1p). `CA9 - AGXT` is the clean linear
equivalent with identical FAIL reason (delta_baseline, not numeric error).

**Eq2 — expected PASS** (proliferation-minus-HIF2α, metastasis):
```
CDK1 - EPAS1
```
Why it should pass: Rashomon-set rank 2 (AUROC 0.7192), same
proliferation-minus-HIF-2α axis as canonical TOP2A − EPAS1 survivor.
Δ_baseline ≈ +0.062. Confirmed PASS in PhL-8c.

## Session output (v1 — log1p equation)

```
===GATE VERDICT 1===
task: tumor_vs_normal
equation: log1p(CA9) + log1p(VEGFA) - log1p(AGXT)
gate: FAIL
perm_p: 1.0  (degenerate — equation did not score)
ci_lower: 0.0
delta_baseline: 0.0
decoy_p: 1.0
fail_reason: perm_p, ci_lower, delta_baseline, decoy_p
numeric_error: non_finite_scores
====================
Note: log1p() applied to z-score standardized features produces NaN for
any z-score < −1. CA9 z-scores reach −2.38 in this cohort (130/609 samples
affected). The gate records all metrics as 0.5/degenerate and flags FAIL
before any statistical test runs. The equation is ill-specified on
standardized data.
===GATE VERDICT 2===
task: metastasis_expanded
equation: CDK1 - EPAS1
gate: PASS
perm_p: 0.0 (< 0.001, well below 0.05 threshold)
ci_lower: 0.663 (threshold: > 0.60) ✓
delta_baseline: +0.062 (threshold: > 0.05) ✓
delta_confound: null (no non-degenerate covariates; leg skipped — expected)
decoy_p: 0.0 (< 0.001, well below 0.05 threshold) ✓
law_auc: 0.719
fail_reason: none
====================
===DUAL VERDICT SUMMARY===
Eq1 (tumor_vs_normal): FAIL — log1p(z-score) produces NaN for 130/609
  samples (z_CA9 reaches −2.38); the equation is algebraically ill-specified
  on standardized data before any statistical test runs.
Eq2 (metastasis_expanded): PASS — CDK1 − EPAS1 clears all four active legs
  (perm_p < 0.001, ci_lower 0.663, Δbaseline +0.062, decoy_p < 0.001),
  placing it in the same proliferation-minus-HIF-2α cluster as the
  TOP2A − EPAS1 flagship survivor (AUROC 0.719 vs 0.726 for TOP2A).
Gate behaviour: the same pre-registered thresholds, same 45-gene panel,
  same 1000-permutation / 1000-resample run — one equation is rejected
  before statistics for algebraic reasons, one passes every active test
  decisively; the gate discriminates on the content of the equation, not
  the task or the runner.
===========================
Noteworthy: CDK1 − EPAS1 lands in the Rashomon tight set (within ε = 0.02
of TOP2A − EPAS1 = 0.726), consistent with the pre-registered finding that
100% of near-equivalent 2-gene pairs are of the form (proliferation marker
− EPAS1). This is a second independent member of that cluster surviving the gate.
```

## v2 results — clean dual verdict (CA9 - AGXT)

```
===GATE VERDICT 1===
task: tumor_vs_normal
equation: CA9 - AGXT
gate: FAIL
perm_p: 0.0
ci_lower: 0.9646
delta_baseline: 0.0145
decoy_p: 0.0
fail_reason: delta_baseline
====================
===GATE VERDICT 2===
task: metastasis_expanded
equation: CDK1 - EPAS1
gate: PASS
perm_p: 0.0
ci_lower: 0.6621
delta_baseline: 0.0622
decoy_p: 0.0
fail_reason: none
====================
===DUAL VERDICT SUMMARY===
Eq1 (tumor_vs_normal): FAIL — delta_baseline = 0.0145 (threshold > 0.05);
  CA9 alone reaches AUROC 0.965, so CA9 − AGXT (law AUROC 0.980) cannot
  clear the +0.05 incremental bar over the best single sign-invariant
  classifier.
Eq2 (metastasis_expanded): PASS — delta_baseline = 0.0622 clears the
  +0.05 threshold; all other legs also pass (perm_p = 0.0, ci_lower =
  0.662 > 0.6, decoy_p = 0.0). CDK1 − EPAS1 joins the
  proliferation-minus-HIF-2α survivor cluster alongside TOP2A − EPAS1
  and MKI67 − EPAS1.
Gate behaviour: same pre-registered thresholds, same pipeline — rejects
  the compound that can't beat CA9 on an easy task, accepts the compound
  that genuinely outperforms any single proliferation or HIF-2α gene on
  metastasis prediction.
===========================
```

**Execution notes:**
- `make audit` passed cleanly.
- Session patched `falsification_sweep.py` locally to exclude metadata
  columns (age, batch_index) from inferred gene feature set (commit 7ce6723
  on server-side branch). This fix is NOT merged to main — the Routine's
  local edit does not affect the committed repo. The push failed with 403
  (expected: Routine has no push credentials to main).
- Git push 403 is normal for Routine sessions. Results documented here.

## v1 caveat (log1p equation — superseded)

v1 used `log1p(CA9) + log1p(VEGFA) - log1p(AGXT)` which broke under
`--standardize` (z-scores go negative → NaN). v2 uses `CA9 - AGXT`
(linear equivalent) and produces the intended `fail_reason=delta_baseline`.

## Why this matters

The Lacuna thesis is: **a pre-registered gate that genuinely rejects**.
Showing only a PASS (PhL-8c) proves the oracle works for valid laws.
Showing FAIL + PASS in one session proves the gate is symmetric —
it doesn't optimise for acceptance.

One click, one session URL, ~6 minutes of autonomous runtime:
1. Routine clones repo, runs `make venv && make audit`
2. Parses both equations from trigger text
3. Runs the 5-test gate on tumor_vs_normal → Eq1 FAILS (delta_baseline gate)
4. Runs the 5-test gate on metastasis_expanded → Eq2 PASSES
5. Emits dual verdict summary: "same gate, textbook law rejected, novel contrast accepted"

No human decision after the API fire call.

## Cross-reference

| Run | Trigger | Equations | Gate outcomes |
|---|---|---|---|
| PhL-8 (2026-04-23) | API | `make audit` only | CI pulse |
| PhL-8b (2026-04-26T00:39Z) | Schedule | N/A | Mechanism attested (quota gate) |
| PhL-8c (2026-04-26T15:05Z) | API | CDK1-EPAS1 | PASS |
| **PhL-8d** | **API** | **HIF-axis (FAIL) + CDK1-EPAS1 (PASS)** | ✅ **FAIL + PASS** |
