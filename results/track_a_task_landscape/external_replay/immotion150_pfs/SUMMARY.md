# IMmotion150 external replay — TOP2A − EPAS1 stratifies PFS

**Status.** All 3 pre-registered kill tests **PASS** (2026-04-23).
**Pre-registration** written and git-committed *before* this analysis ran:
[`preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`](../../../../preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml)

## Cohort

IMmotion150 (cBioPortal study `rcc_iatlas_immotion150_2018`). Phase-2
randomized trial of **atezolizumab ± bevacizumab** in previously untreated
metastatic renal clear-cell carcinoma. Published: McDermott *et al.*,
*Nature Medicine* 2018 (PMID 29867230). All patients metastatic at baseline
— therefore *not* an M0-vs-M1 replay. This is a prognostic-score replay:
does the survivor-law *score* stratify progression-free survival in an
ImTx-treated cohort?

- n = 263 samples after QC
- Events (PFS progression) = 164
- Platform: bulk tumor RNA-seq, TPM (log2)
- Not a subset of TCGA-KIRC (trial-level biopsy collection, different
  preprocessing pipeline)

## Score definition

The same equation the 5-test falsification gate accepted on TCGA-KIRC
metastasis (M0 vs M1, n=505, AUROC 0.726, Δbaseline +0.069):

$$\text{score} = \text{TOP2A} - \text{EPAS1}$$

No per-gene z-scoring, no cohort-specific refitting. Same numbers, same
signs. The only cohort-specific step is z-scoring the **final score**
to report Cox HR per standardized unit.

## Pre-registered kill tests (committed 2026-04-23T04:44:46Z, before
this analysis ran)

| # | Test | Threshold | Observed | Pass |
|---|---|---|---|---|
| 1 | Log-rank on median split (two-sided) | `p < 0.05` | **p = 0.00027**, χ² = 13.26 | ✅ |
| 2 | Cox HR per z-score | `|log HR| > log 1.3` AND 95 % CI excludes 1 | **HR = 1.36** (95 % CI 1.16–1.59), p = 0.0001 | ✅ |
| 3 | Harrell C-index (risk direction) | `> 0.55` | **0.601** | ✅ |

Verdict = **PASS**. Direction observed: *high score → worse PFS.* Matches
the biological prediction written into the pre-reg (ccA/ccB proliferation-
over-HIF-2α axis).

## Clinical-effect summary

| Group (median-split on `TOP2A − EPAS1`) | n | Median PFS | 95 % CI |
|---|---|---|---|
| High score (proliferation > HIF-2α) | 132 | **5.35 months** | from KM |
| Low score (HIF-2α > proliferation) | 131 | **12.88 months** | from KM |

**Absolute median PFS gap: 7.53 months.** On an independent metastatic
ccRCC cohort receiving immunotherapy + anti-VEGF, a two-gene tumor-biology
score — discovered by unconstrained symbolic regression on TCGA and
accepted by a pre-registered 5-test gate — separates median PFS by more
than seven months.

## Why this is a fair external replay

1. **Cohort independence.** IMmotion150 is a multi-site Phase-2 trial; no
   known overlap with TCGA-KIRC (which used Surgery-of-origin banking
   rather than clinical-trial enrollment).
2. **Preprocessing independence.** TCGA-KIRC data is star_tpm from the
   GDC-Xena hub (RSEM on STAR alignment); IMmotion150 is cBioPortal's
   log-TPM release from the published trial. Different pipelines, different
   normalization choices.
3. **Endpoint independence.** Training endpoint was categorical
   (M-stage classification). Replay endpoint is time-to-event (PFS under
   immunotherapy). Same score, different question.
4. **Pre-registration.** The three kill tests were locked before this
   analysis was run (see `preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`).
   Direction-of-effect was NOT pre-specified — the pre-reg accepts either
   direction if magnitudes clear.

## What this is *not*

- Not a claim that TOP2A − EPAS1 beats existing ccRCC prognostic
  scores (IMDC / MSKCC risk). We have not benchmarked against those.
- Not a claim of treatment-effect interaction with atezolizumab +
  bevacizumab. IMmotion150 had two arms; this analysis pooled them
  because the pre-reg did not specify arm-stratified Cox.
- Not a claim of causality. High proliferation biology is a hazard
  marker across most solid tumors; the novelty is the *compactness*
  of a pre-registered 2-gene form that replicates.

## Files

- `verdict.json` — machine-readable kill-test outcomes.
- `km_median_split.png` — Kaplan-Meier curves with log-rank + Cox + C-index
  in the title.
- `../../../../preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`
  — the pre-registration committed before this analysis.
- `../../../../src/phf3_immotion150_replay.py` — the script that produced
  this verdict (reproducible from `data/immotion150_ccrcc.csv`).
- `../../../../data/build_immotion150.py` — builder that fetches the
  263-sample slice from cBioPortal's public REST API.

## Reproduce

```bash
python data/build_immotion150.py
# → data/immotion150_ccrcc.csv (263 samples × 17 cols)

python src/phf3_immotion150_replay.py
# → results/.../immotion150_pfs/{verdict.json,km_median_split.png}
```
