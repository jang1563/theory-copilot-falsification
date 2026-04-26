# Track A — KIRC Stage I-II vs III-IV (45-gene panel)

**Run date:** 2026-04-26 (fixed PySR sweep)
**Data:** `data/kirc_stage_expanded.csv` (n=512; control=309 Stage I-II, disease=203 Stage III-IV)
**Panel:** 45-gene HIF/Warburg/tubule/proliferation/metastasis/ccRCC-lineage/housekeeping
**PySR:** 20 populations × 50 pop_size × 1000 iterations × 3 seeds (1, 7, 42), 20 CPUs

---

## Headline

**23 / 28 candidates survive** the pre-registered 5-test gate on KIRC Stage I-II vs III-IV
with the 45-gene expanded panel. Compare to 0/34 on the same task with the 11-gene HIF-axis
panel — the gate accepts when the panel contains features that can form an incremental compound.

Top surviving law: `(CXCR4 / EPAS1) + const` (AUROC 0.689, Δbaseline +0.051, perm_p < 0.0001).

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 28 |
| Survivors (all 5 tests pass + BH-FDR) | **23** |
| Rejected (any test fails) | 5 |
| Best AUROC among survivors | 0.689 |
| Best Δbaseline | +0.092 |
| Most common rejection reason | `delta_baseline` (4×) |

---

## Top survivors

| Rank | Equation | AUROC | Δbase | perm_p |
|---|---|---|---|---|
| 1 | `(CXCR4 / EPAS1) + const` | 0.689 | +0.051 | <0.001 |
| 2 | `(ANGPTL4 * (.../ EPAS1) / (PFKP + SLC22A8))` | 0.686 | +0.092 | <0.001 |
| 3 | `log1p((MKI67 - (ANGPTL4/EPAS1 × const)) / (SLC22A8 + PFKP))` | 0.684 | +0.091 | <0.001 |

Three themes in the survivor cluster:
- **CXCR4 / EPAS1** (migration receptor / HIF-2α ratio) — dominant axis
- **MKI67 + ANGPTL4 / EPAS1** (proliferation + angiogenesis over HIF-2α)
- Tubule-loss markers (SLC22A8, PFKP) in denominator

---

## Biological note

CXCR4 (C-X-C chemokine receptor type 4) is upregulated in advanced ccRCC and promotes metastatic
homing via the CXCL12/SDF-1 axis. EPAS1 (HIF-2α) is the canonical well-differentiated ccRCC
driver. The ratio `CXCR4 / EPAS1` — migration marker over hypoxia-differentiation marker —
predicts advanced stage (III-IV vs I-II), consistent with HIF-2α's role in maintaining the
differentiated phenotype that resists invasion.

This is **different** from the TOP2A-EPAS1 metastasis axis (proliferation over HIF-2α), despite
both being `[aggressiveness marker] / [HIF-2α]` in form. Stage task favors the
migration/invasion axis; metastasis task favors the proliferative axis. The gate distinguishes
them by selecting different laws on different tasks with identical thresholds.

---

## Platform comparison (same gate, same thresholds)

| Task | Panel | n | Dominant gene (AUC) | Survivors |
|---|---|---|---|---|
| Stage I-II vs III-IV | 11-gene | 534 | CUBN=0.610 | **0 / 34** |
| Stage I-II vs III-IV | 45-gene | 512 | ~0.638 (est.) | **23 / 28** ✅ |

The 11-gene panel could not clear +0.05 above CUBN; the 45-gene panel
(which adds CXCR4, MKI67, ANGPTL4, plus Warburg markers) crosses it with 23 laws.
The gate's +0.05 threshold is the same. The panel changed; the gate did not.

---

## Honest caveat

23/28 is a high survival rate (82%). This reflects:
1. The stage task has a moderate dominant-gene ceiling (~0.638 est.) — more room for compound laws
2. The 45-gene panel contains multiple features that co-vary with stage — many combinations satisfy +0.05
3. These 23 laws cluster into 2-3 biological axes; the effective "discovery count" is lower than the raw
   survivor count

The top survivors all clear the threshold by modest margins (Δbase ~0.05-0.09). The gate is not
reporting "strong" laws — it is reporting "incremental and statistically non-spurious" laws.
Cross-cohort replay on an independent stage-labeled ccRCC cohort would be the appropriate
next validation step.
