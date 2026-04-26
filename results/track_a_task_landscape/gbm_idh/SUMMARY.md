# Track I — LGG Grade II vs III

**Run date:** 2026-04-26 (fixed PySR sweep)
**Data:** `data/lgg_grade.csv` (n=384; control=176 Grade II, disease=208 Grade III)
**Panel:** 30-gene (EMT, proliferation, stem cell, Warburg, HIF markers)
**PySR:** 20 populations × 50 pop_size × 1000 iterations × 3 seeds, 20 CPUs

---

## Headline

**2 / 25 candidates survive** the pre-registered 5-test gate on LGG Grade II vs III.
Top law: `log1p(TWIST1 × MKI67 + VIM) − CDH2/NES` (AUROC 0.840, Δbaseline +0.051).

Sparse survival (2/25, 8%) reflects a high single-gene ceiling (~0.789 estimated) and
a narrow panel — MKI67 alone likely discriminates Grade II vs III near-effectively.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 25 |
| Survivors | **2** |
| Rejected | 23 |
| Rejection reason | `delta_baseline` (23/25) |
| Best AUROC among survivors | 0.840 |
| Best Δbaseline | +0.058 |
| Estimated dominant single-gene AUROC | ~0.789 |

---

## Surviving laws

| Rank | Equation | AUROC | Δbase |
|---|---|---|---|
| 1 | `log1p(TWIST1 × MKI67 + VIM) − CDH2/NES` | 0.840 | +0.051 |
| 2 | `(log1p(MKI67 × TWIST1 + LDHA) × (NES/CDH2)) − EPAS1/SLC2A1` | 0.840 | +0.058 |

---

## Biological note

Both survivors share a core structure: **TWIST1 × MKI67** (an interaction product) in a log1p term,
with VIM or LDHA as additive co-features. This captures:

- **Proliferation × EMT plasticity:** MKI67 (Grade III tumors actively proliferate) × TWIST1
  (an EMT/stem transcription factor upregulated in high-grade glioma) creates a compound
  feature that is more grade-specific than either alone.
- **CDH2/NES normalization:** N-cadherin (CDH2) and Nestin (NES) are neural stem cell markers.
  Their ratio appears in the denominator — potentially capturing the neural differentiation
  state that is retained more in Grade II (lower grade, more differentiated).
- **Warburg/HIF complement (Survivor 2):** LDHA and SLC2A1/EPAS1 add metabolic context,
  consistent with the more hypoxic and glycolytic environment of Grade III gliomas.

---

## Platform comparison

| Task | Cancer | Top surviving law | AUROC | Δbase | Survivors |
|---|---|---|---|---|---|
| Stage I-II vs III-IV | KIRC (45-gene) | `CXCR4 / EPAS1` | 0.689 | +0.051 | 23/28 |
| Tumor vs Normal | LIHC (31-gene) | — (ALB/TTR saturates) | — | +0.015 | 0/26 |
| Stage I-II vs III-IV | COAD (31-gene) | `SLC2A1 + PDCD1LG2 + VIM − MYC` | 0.658 | +0.107 | 15/22 |
| Grade II vs III | LGG (30-gene) | `log1p(TWIST1×MKI67+VIM) − CDH2/NES` | 0.840 | +0.051 | **2/25** |

LGG has the highest survivor AUROC (0.840) but lowest survivor count (2/25), consistent with
a high single-gene ceiling that allows few compounds to clear +0.05 incrementally.

---

## Honest caveat

2/25 survivors in LGG is a marginally sparse result. The two laws are essentially
the same biological axis (TWIST1 × MKI67 as core, with different auxiliary features), so
the effective discovery count is 1 distinct axis. The grade II vs III task has a high
single-gene ceiling (MKI67 likely ~0.789), which limits the incremental opportunity.
The AUROC 0.840 is notable but the panel is narrow (30 genes); a broader panel might
reveal additional axes or confirm the uniqueness of this one.
