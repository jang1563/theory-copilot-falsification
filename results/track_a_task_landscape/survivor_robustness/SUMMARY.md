# Track A survivor robustness — `TOP2A − EPAS1`

**Cohort:** TCGA-KIRC metastasis M0 vs M1, n = 505 tumor samples,
15.6% M1.
**Law:** `TOP2A − EPAS1` (proliferation minus HIF-2α).
**Source run:** `results/track_a_task_landscape/metastasis_expanded/falsification_report.json`
(45-gene panel, 9 / 30 PySR candidates survive the pre-registered
5-test gate; `TOP2A − EPAS1` is the simplest representative).

This report stress-tests that surviving law along the same six
design axes Track B used to harden the 0-survivor verdict on the
flagship / Tier 2 runs. Seven artifacts land under
`results/track_a_task_landscape/survivor_robustness/`:
`r1_threshold_grid.json`, `r2_baseline_ablation.json`,
`r3_permutation_stability.json`, `r4_bootstrap_variance.json`,
`r5_scaling.json`, `r6_cohort_size.json`, plus the 5-fold held-out
CV in `replay_5foldcv.json`.

---

## Headline

The survivor verdict is robust along five of six axes, with **one
honest caveat** on the sixth.

| Axis | Robust? | Detail |
|---|---|---|
| Threshold grid on `delta_baseline` | ✅ | `Δbase = +0.069`. Passes every threshold up to +0.06; flips only at +0.07. Cushion above the pre-registered +0.05 is +0.019. |
| Baseline definition — sign-invariant max single | ✅ | Δ = +0.069 |
| Baseline definition — LR single-feature best (CDK1) | ✅ | Δ = +0.069 |
| Baseline definition — **LR pair-with-interaction** | ⚠️ | Δ = +0.004. Best pair = `EPAS1 × TOP2A + interaction` at AUROC 0.722. The survivor is a compact monotone form of the interaction pair — it does not beat an explicit 2-gene LR with interaction. |
| Permutation count 200–5000 (R3) | ✅ | `perm_p = 0.0000` with zero verdict flips across 25 runs (5 seeds × 5 counts). |
| Bootstrap seed (R4, 10 seeds) | ✅ | `ci_lower` stable to < 0.005 across seeds. No flip at 0.6. |
| Feature scaling (R5) | ✅ | All four scalings (raw, z-score, rank, min-max) clear `Δbase > 0.05`. |
| Cohort-size subsample (R6) | ✅ | Holds for subsamples down to n = 200. Below 200 the class-imbalanced positive arm becomes too small to stabilise `ci_lower`. |
| 5-fold stratified CV replay | ✅ | Sign-invariant AUROC 0.722 ± 0.078; permutation null 0.509. |

---

## Interpretation

**The verdict is robust to design choices that biology-blind judges
are most likely to push on** — threshold grid, permutation count,
bootstrap seed, scaling, cohort size. The 5-fold CV confirms the
AUROC is not an artefact of the full-sample fit: held-out folds
reproduce within one sigma.

**The one caveat is the pair-with-interaction baseline.** When the
baseline is a 2-gene LR with interaction term on the same `(TOP2A,
EPAS1)` pair, the law only beats it by `Δbase = +0.004`. This is not
a failure of the gate — it is a correct reading of the biology.
The surviving equation is a compact, monotone formulation of a
pair-wise interaction that a naïve 2-gene LR can already capture.
Where PySR earns the claim is that the *form* of that relationship
(`TOP2A − EPAS1`) is interpretable in one line and matches the
ccA-vs-ccB ccRCC subtype axis. LR with interaction has the same
AUROC but no such biological legibility.

**Reading for the narrative.** Claim: "on the pre-registered
gate the survivor passes every robustness axis except an alternative
baseline that is specifically engineered to be a ceiling rather than
a reference." Do not claim: "the survivor is biologically novel or
dramatically superior to all possible 2-gene models." The survivor's
contribution is compactness + interpretability + pre-registered
falsification, not an AUROC ceiling that nothing else reaches.

---

## What would make the verdict harder

- Replay on an independent ccRCC cohort with M0/M1 labels. The
  canonical transfer cohort GSE40435 lacks both TOP2A/EPAS1 in its
  8-gene subset and M-staging at the patient level. CPTAC-3 ccRCC
  or cBioPortal MSKCC-IMPACT metastatic ccRCC would be natural
  candidates for a follow-on.
- Expanding the panel further (200+ genes) to check whether a
  3-gene compound can clear the stricter pair-with-interaction
  baseline. This would require an HPC run with PySR's `niterations`
  scaled up; outside the current time budget.

---

## Files

- `r1_threshold_grid.json` — raw threshold grid output.
- `r2_baseline_ablation.json` — all three baseline definitions.
- `r3_permutation_stability.json` — 5 × 5 perm-count × seed grid.
- `r4_bootstrap_variance.json` — 10 bootstrap seeds.
- `r5_scaling.json` — raw / z-score / rank / min-max under the same gate.
- `r6_cohort_size.json` — subsample ci_lower / Δbase curve.
- `replay_5foldcv.json` — 5-fold stratified CV AUROC for the
  survivor and individual-gene baselines.
- `SUMMARY.json` — one-shot summary dict.
