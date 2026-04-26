# I2 Rashomon set analysis — TOP2A − EPAS1 in context

**Pre-registration:** `preregistrations/20260425T185717Z_i2_rashomon_set.yaml`
(`gate_logic_changed: false`, `extension_type: descriptive_enumeration`)

## Question

How many other compact two-gene differences in the 45-gene
metastasis_expanded panel reach AUROC comparable to TOP2A − EPAS1?
The "Rashomon set" (Breiman 2001) is the set of models that
achieve near-equivalent predictive performance — its size is a
direct measure of how unique the headline survivor is.

## Method

- All `C(45, 2) = 990` unordered gene pairs.
- Score = `g_i − g_j` after per-gene z-score; sign-invariant
  AUROC = `max(AUROC, 1 − AUROC)`.
- No fitting, no FDR, no permutation — pure enumeration.
- Tight set ε = 0.02 (within 0.02 of TOP2A − EPAS1 = 0.726 → AUROC ≥ 0.706).
- Loose set ε = 0.05 (AUROC ≥ 0.676).

## Result

| Quantity | Value |
|---|---|
| Pairs evaluated | 990 |
| **TOP2A − EPAS1 rank** | **1 / 990** (AUROC 0.7275) |
| Tight Rashomon set (ε=0.02) | **3 pairs** |
| Loose Rashomon set (ε=0.05) | 19 pairs |

### Tight Rashomon set (the only laws within 0.02 of the survivor)

The enumeration is over **unordered** pairs `{g_i, g_j}`; AUROC is
computed sign-invariantly (`max(AUROC, 1 − AUROC)`), so each row below
is sign-equivalent to its swap (e.g., `EPAS1 − TOP2A` ≡ `TOP2A − EPAS1`).
Below the rows are presented in **biological orientation**
(proliferation marker − EPAS1) for narrative consistency:

| Rank | Pair (biological orientation) | Pair (CSV row order) | Sign-inv AUROC |
|---|---|---|---|
| 1 | **TOP2A − EPAS1** | EPAS1 − TOP2A | **0.7275** |
| 2 | CDK1 − EPAS1 | CDK1 − EPAS1 | 0.7192 |
| 3 | MKI67 − EPAS1 | EPAS1 − MKI67 | 0.7100 |

All three pairs are **`proliferation marker − EPAS1`** — TOP2A, CDK1,
and MKI67 are canonical proliferation drivers; EPAS1 is HIF-2α. The
ccA/ccB axis is the same biology in three slightly different gene
proxies; parsimony preference picks `TOP2A − EPAS1`.

## Pre-registered prediction verdicts

| Prediction | Outcome | Status |
|---|---|---|
| **P1** TOP2A−EPAS1 in top 5 by AUROC | rank **1** | ✅ PASS |
| **P2** Tight Rashomon set has ≤ 20 pairs | **3** pairs | ✅ PASS |
| **P3** Tight set ≥ 80% pairs containing EPAS1 OR a proliferation marker | **100%** | ✅ PASS |

All three predictions, locked before computation, pass.

## What this strengthens in the narrative

- The compactness claim was previously: *"the survivor's distinctive
  contribution is interpretable compactness + pre-registered falsification,
  not an AUROC ceiling that no other 2-gene model can reach."* The
  Rashomon evidence sharpens this: among all 990 candidate 2-gene
  differences, **TOP2A − EPAS1 IS the AUROC ceiling** (rank 1/990) and
  the entire tight Rashomon set is a 3-pair cluster of equivalent
  compactified ccA/ccB-axis representations.
- The previous "2-gene LR with interaction reaches 0.722" caveat
  remains — the interaction-augmented baseline is a *parametric*
  model, not a 2-gene difference, so it does not appear in this
  enumeration. The compactness comparison applies to like-with-like.
- The 19-pair loose Rashomon set (ε=0.05) widens the cluster but
  stays inside the proliferation-vs-HIF-axis biology.

## Honest caveat

This enumeration only covers `g_i − g_j` linear differences. It does
not cover ratios, log-transforms, or 3+ gene compounds, which is
why the headline 5-gene compound from the v1 gate
(`MKI67 / EPAS1 / LRP2 / PTGER3 / RPL13A`, AUROC 0.726) is absent
here — it is in a different model class. The Rashomon claim
applies *within* the 2-gene-linear-difference class.

## Reproducibility

- Source: `src/track_a_rashomon_set.py`
- Full enumeration: `all_pairs.csv` (990 rows, sorted by AUROC desc)
- JSON snapshot: `rashomon_tight.json`
- Pre-reg: `preregistrations/20260425T185717Z_i2_rashomon_set.yaml`

## Citations

- Breiman L. (2001). *Statistical Modeling: The Two Cultures*.
  Statistical Science, 16(3):199-231 — coined "Rashomon set".
- Semenova, Rudin, Parr (2022). *On the Existence of Simpler Machine
  Learning Models*. arXiv:1908.01755.
- Marx, Calmon, Ustun (2020). *Predictive Multiplicity in
  Classification*. arXiv:1909.06677.
