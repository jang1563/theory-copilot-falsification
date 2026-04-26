# PhL-1 — SLC22A8 3-gene extension cross-cohort verdict

**Pre-registered, committed 2026-04-23 18:13 UTC (git d2352a9) BEFORE the
analysis ran.** YAML:
`preregistrations/20260423T181322Z_phl1_immotion150_slc22a8_extension.yaml`.

**Outcome: FAIL + UNDERPERFORMS.** Our own H1 LLM-SR loop's proposed
3-gene extension does not survive the independent-cohort replay. This
is exactly the result the falsification-first architecture is designed
to surface.

## Question

The H1 LLM-SR loop (commit e5b96e5) converged on
iteration 1 with 5 TOP2A − EPAS1 variants. The highest-AUC member
added SLC22A8 inside the subtraction, reaching AUC 0.739 on TCGA-KIRC
metastasis vs 0.726 for the 2-gene linear form — a +0.013 Δ-lift
within one cohort.

Does that +0.013 lift cross to the independent IMmotion150
metastatic ccRCC cohort (n=263, Phase-2 atezolizumab ± bevacizumab)?

## Three pre-registered kill tests

Score on IMmotion150:

    score = TOP2A − (EPAS1 + SLC22A8)

| Test | Result | Threshold | Pass |
|---|---|---|---|
| Log-rank (median split) | p = 0.117 | p < 0.05 | ❌ |
| Cox HR per z | 1.16 (95% CI 0.99–1.37, p=0.074) | \|log HR\| > log 1.3 AND CI excludes 1 | ❌ |
| Harrell C-index | 0.566 | > 0.55 | ✅ |

**2 of 3 kill tests fail. Verdict: FAIL.**

## Pre-registered comparison against the 2-gene form (PhF-3)

The prereg specified that the 3-gene form outperforms the 2-gene form
iff C-index(3) > C-index(2) + 0.01 AND HR(3) > HR(2). Both fitted on
the same sample set for apples-to-apples comparison:

| Metric | 2-gene (TOP2A − EPAS1) | 3-gene (+ SLC22A8) | Δ |
|---|---|---|---|
| C-index | 0.601 | 0.566 | **−0.035** |
| HR per z | 1.36 | 1.16 | **−0.20** |
| Log-rank p | 0.0003 | 0.117 | worse |
| Outperforms? | — | no (both directions wrong) | **UNDERPERFORMS** |

## Interpretation

H1 v2's SLC22A8 extension was **TCGA-KIRC cohort-specific**, not a
generalisable law. The +0.013 AUC lift on TCGA-KIRC does not cross to
the IMmotion150 PFS endpoint; it reverses direction, losing 0.035
C-index and 0.20 HR per z-score.

This matches what the pre-hackathon-committed `docs/methodology.md`
predicts will happen to candidates that clear one cohort and not
another: the gate rejects them. The 2-gene TOP2A − EPAS1 form remains
the canonical survivor — it is the one that passes both TCGA-KIRC
(AUROC 0.726, Δbase +0.069) and IMmotion150 (log-rank p=0.0003, HR=1.36,
C=0.601).

Concretely, this result:

1. **Falsifies H1 v2's SLC22A8 claim as a generalisable finding.** The
   headline_findings and submission narrative must say "the H1 loop
   proposed a 3-gene extension; our own pre-registered cross-cohort
   gate rejected it." Not "H1 found a 3-gene extension."
2. **Confirms the gate architecture bites on our own outputs.** The
   gate is not an ornament for Opus's proposals only; it kills
   downstream derivative claims the discovery loop itself produces.
   This is the single strongest pre-emptive response to any
   Sakana-AI-Scientist-v2-style critique of LLM-as-judge circularity.
3. **Strengthens the parsimony preference for the 2-gene survivor.**
   Occam + cross-cohort replication + pre-registered gate all point
   at the 2-gene form.

## What this means for the submission

- `docs/headline_findings.md` — already mentions SLC22A8 in the H1
  section; needs an update to report the cross-cohort FAIL.
- `docs/why_opus_4_7.md` — already pre-empts LLM-as-judge circularity;
  cite this PhL-1 FAIL as concrete evidence: we killed our own model's
  extension.
- `plans/claude_design_slide_specs_v1.md` — Slide 2 "Headline findings"
  draft currently claims "H1 loop found +0.013 lift with SLC22A8";
  revise to "H1 loop proposed SLC22A8 extension; cross-cohort gate
  rejected it (PhL-1); 2-gene law remains the survivor."
- Loom narration at 1:10-1:25 must NOT claim the 3-gene finding as
  cross-cohort robust.

## Files

- `km_median_split.png` — IMmotion150 KM curves for the 3-gene
  median split.
- `verdict.json` — machine-readable full verdict (kill-test values,
  comparison-gate numbers).

## Tamper-evidence chain

- Pre-registration: `preregistrations/20260423T181322Z_phl1_immotion150_slc22a8_extension.yaml`
  committed at git d2352a9.
- Analysis script: `src/phl1_slc22a8_cross_cohort.py` committed
  AFTER the prereg, referenced in the prereg YAML.
- Data: `data/immotion150_ccrcc.csv` (cBioPortal REST,
  `rcc_iatlas_immotion150_2018`), rebuilt 2026-04-23 18:10 UTC with
  SLC22A8 column added. Build script `data/build_immotion150.py`
  committed in d2352a9 alongside the prereg.
- Verdict freeze: this SUMMARY.md committed together with
  `verdict.json` and `km_median_split.png` in a single commit, with
  no subsequent edit of the kill-test thresholds.
