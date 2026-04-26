# Track D — LIHC Tumor vs Normal

**Run date:** 2026-04-26 (HPC, SLURM job 2812758)
**Data:** `data/lihc_tumor_normal.csv` (n=424; disease=374 tumor, control=50 normal)
**Panel:** 31-gene (hepatic function + oncofetal + proliferation)
**PySR:** 20 populations × 50 pop_size × 1000 iterations × 3 seeds, 20 CPUs

---

## Headline

**0 / 26 candidates survive** the pre-registered 5-test gate on LIHC Tumor vs Normal.
All 26 rejections on `delta_baseline`. The gate correctly refuses: a normal hepatic function
marker (likely ALB or TTR) saturates classification at AUROC ~0.985, making the required
+0.05 compound increment effectively unreachable (best compound reaches AUROC 1.000, Δbase = +0.015).

Same rejection pattern as KIRC Tumor vs Normal (CA9 = 0.965) and LUAD Tumor vs Normal
(SFTPC saturation). A multi-gene law is not a discovery when one gene already saturates.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 26 |
| Survivors | **0** |
| Rejected | 26 |
| Rejection reason | `delta_baseline` (26/26) |
| Best compound AUROC | 1.000 |
| Best Δbaseline | +0.015 (threshold: +0.05) |

---

## Saturation diagnosis

The equations reaching AUROC 1.000 combine CA9, TTR (transthyretin), NDUFA4L2, CDK1 —
all consistent with a liver functional marker (TTR or ALB) near-saturating AUROC 0.985.

TTR and ALB are highly expressed in normal hepatocytes and near-absent in tumor, forming
a clean binary discriminator. This is the LIHC analog of the ccRCC CA9 signal: a cell-type
identity marker so specific that no compound adds incremental information within this panel.

---

## Platform comparison

| Task | Cancer | Dominant signal | Best Δbase | Survivors |
|---|---|---|---|---|
| Tumor vs Normal | KIRC | CA9 (single gene, AUC 0.965) | +0.019 | 0 / 26 |
| Tumor vs Normal | LUAD | SFTPC saturation | — | 0 / 4 |
| Tumor vs Normal | LIHC | ALB/TTR (est. AUC ~0.985) | **+0.015** | **0 / 26** |

All three "Tumor vs Normal" tasks produce 0 survivors with the same threshold.
The biology is consistent: tissue-identity markers dominate normal-vs-tumor classification.

---

## Honest framing

0/26 is the expected outcome for a tissue-identity marker problem. The gate is correct
to reject: a claim that a multi-gene compound predicts tumor vs normal in LIHC would require
showing incremental AUROC over a single hepatic function marker that already discriminates at ~0.985.
This is a designed negative result — the same gate that accepted 23/28 on KIRC Stage refuses
to accept a compound here. The gate is bi-directional.
