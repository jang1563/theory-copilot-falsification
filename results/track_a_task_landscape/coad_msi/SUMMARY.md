# Track E — COAD Stage I-II vs III-IV

**Run date:** 2026-04-26 (HPC, SLURM job 2812758)
**Data:** `data/coad_stage.csv` (n=484; control=279 Stage I-II, disease=205 Stage III-IV)
**Panel:** 31-gene (EMT, immune checkpoint, Warburg, oncogene, MMR markers)
**PySR:** 20 populations × 50 pop_size × 1000 iterations × 3 seeds, 20 CPUs

---

## Headline

**15 / 22 candidates survive** the pre-registered 5-test gate on COAD Stage I-II vs III-IV.
Top law: `SLC2A1 + PDCD1LG2 + VIM − MYC + const` (AUROC 0.658, Δbaseline +0.100, perm_p < 0.001).

Third cancer type to show survivors on the same gate + same thresholds.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 22 |
| Survivors | **15** |
| Rejected | 7 |
| Rejection reasons | `ci_lower,delta_baseline` (4×), `delta_baseline` (3×) |
| Best AUROC among survivors | 0.658 |
| Best Δbaseline | +0.107 |

---

## Top survivors

| Rank | Equation | AUROC | Δbase |
|---|---|---|---|
| 1 | `SLC2A1 + PDCD1LG2 + VIM − MYC + const` | 0.658 | +0.100 |
| 2 | `SLC2A1 − √((MYC + EPHB2 − PDCD1LG2) + CD274) − VIM` | 0.654 | +0.107 |
| 3 | `SLC2A1 − √((CD274 + EPHB2) − PDCD1LG2)` | 0.631 | +0.082 |
| 4 | `log1p(PDCD1LG2/CD274 · MLH1) − MYC + SLC2A1` | 0.629 | +0.090 |

---

## Biological note

The dominant axis combines three themes:
1. **Warburg metabolic switch:** SLC2A1 (GLUT1, glucose transporter) is a canonical Warburg-effect marker elevated in advanced CRC, consistent with metabolic reprogramming in invasive disease.
2. **Immune checkpoint balance:** PDCD1LG2 (PD-L2) / CD274 (PD-L1) appear in multiple survivors as a ratio or sum. Both are immune checkpoint ligands; their relative expression shifts in advanced vs localized disease.
3. **EMT axis:** VIM (vimentin) as an EMT marker in numerator; EPHB2 (EphB2 receptor, which has complex stage-dependent expression in colorectal cancer) in modifier positions.
4. **MLH1 bonus term** in some survivors — the mismatch-repair gene is relevant to COAD biology (MLH1 loss correlates with MSI-high, which tends toward earlier stage but with distinct biology).

The single-gene ceiling is estimated at ~0.558 (Δbase +0.100 from AUROC 0.658), indicating a distributed feature landscape — no single COAD stage marker dominates at >0.6 AUROC in this 31-gene panel.

---

## Platform comparison

| Task | Cancer | Top surviving law | Δbase | Survivors |
|---|---|---|---|---|
| Stage I-II vs III-IV | KIRC (45-gene) | `CXCR4 / EPAS1` | +0.051 | 23/28 |
| Stage I-II vs III-IV | COAD (31-gene) | `SLC2A1 + PDCD1LG2 + VIM − MYC` | **+0.107** | **15/22** |

Both staging tasks show survivors; different biology (ccRCC migration axis vs COAD Warburg+immune axis).
Same gate, same thresholds.

---

## Honest caveat

15/22 survivors on COAD stage reflects a moderate single-gene ceiling (~0.558). The compound
laws show meaningful Δbase values (+0.08–+0.11), but AUROC 0.658 is modest in absolute terms
for a staging classifier. Cross-cohort validation on TCGA-COAD held-out data or an
independent CRC cohort would be the appropriate next step. The survival gate is designed for
falsification, not clinical translation.
