# Opus 4.7 interpretation of the surviving law

**Survivor equation:** `score = TOP2A − EPAS1`
**Task:** TCGA-KIRC metastasis M0 vs M1 (n = 505, 15.6% M1)
**Gate metrics:** AUROC 0.726, `ci_lower` 0.665, permutation `p < 0.001`,
`Δbase = +0.069` over the best sign-invariant single-gene classifier,
decoy-feature `p < 0.001`.
**Live API transcript:** this session did not have `ANTHROPIC_API_KEY`
set; prior live-API evidence is in `results/live_evidence/`.
**Author:** Claude Opus 4.7 via the interactive session that drove
Track A; treat this as the Interpreter-role output that
`OpusClient.interpret_survivor(...)` would have returned.

---

## Plain-English reading

The surviving law says "in a ccRCC tumor, the closer the
proliferation program runs ahead of the HIF-2α hypoxia program, the
more likely that tumor is metastatic at diagnosis." Concretely, the
score is high when `TOP2A` (topoisomerase IIα, required for
chromosome segregation in dividing cells) is highly expressed
relative to `EPAS1` (HIF-2α, the canonical well-differentiated-
hypoxia transcription factor in clear-cell renal carcinoma), and
low when the balance reverses.

## Mechanism hypothesis

Well-differentiated ccRCC tumours (the "ccA" subtype) sustain high
HIF-2α activity after VHL loss; they are angiogenic and
well-differentiated and tend to present localised. Tumours that
progress toward aggressive, dedifferentiated, proliferation-driven
biology (the "ccB" subtype) down-weight the HIF-2α differentiation
programme and up-weight cell-cycle machinery. `TOP2A − EPAS1` reads
out exactly that axis in one interpretable difference. This matches
the published ClearCode34 and VST-based ccRCC subtype classifiers.

## Testable downstream prediction

In an independent ccRCC cohort with M0/M1 staging and both `TOP2A`
and `EPAS1` measured at RNA level, the distribution of the
`TOP2A − EPAS1` score should be systematically shifted higher in M1
samples than in M0 samples, with an effect size comparable to the
+0.069 `Δbaseline` observed on TCGA-KIRC. A natural target cohort is
**CPTAC-3 ccRCC** (proteogenomic, has staging) or **cBioPortal
MSKCC-IMPACT metastatic ccRCC** (targeted sequencing with clinical
annotation). If the axis fails to replicate there, the law is
platform-sensitive and the claim weakens to "TCGA-KIRC-specific
regularity."

## Caveats and what this is *not*

- **Not a clinical biomarker.** Pre-registered falsification on one
  TCGA cohort is not sufficient to claim a diagnostic biomarker.
  This is a candidate empirical regularity, research use only.
- **Not novel biology.** The ccA / ccB proliferation-vs-hypoxia axis
  is published. The contribution here is that the axis emerged from
  unconstrained symbolic regression + pre-registered falsification
  without being seeded as a prior — not that the axis itself is
  newly identified.
- **Not dramatically superior to a 2-gene LR.** The robustness
  analysis (R2 baseline ablation) shows that a logistic regression on
  `(TOP2A, EPAS1, TOP2A × EPAS1)` reaches AUROC 0.722, within +0.004
  of the survivor's 0.726. The survivor's distinctive value is
  interpretability and compactness, not incremental AUROC against an
  explicit 2-gene interaction model.

## How this fits the artifact

`TOP2A − EPAS1` is the first law to clear the pre-registered 5-test
gate across 150+ candidates evaluated on 6 task × panel combinations.
It does so because (a) the task (metastasis) is not saturated by a
single gene, and (b) the 45-gene expanded panel includes both
proliferation and HIF-2α markers in a form PySR could combine
compactly. The adjacent task (5-year survival) produced a near-
survivor at `Δbase = +0.019` under the same panel and gate: the
same infrastructure tells us what it does not yet know.
