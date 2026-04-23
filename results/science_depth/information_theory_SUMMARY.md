# Information-theoretic analysis of TOP2A − EPAS1

TCGA-KIRC metastasis (M0 vs M1, n=505, prevalence 16%).

## Mutual information (sklearn k=5 NN estimator)

| Variable | I(X; Y) (nats) |
|---|---|
| TOP2A | 0.0324 |
| EPAS1 | 0.0278 |
| score = TOP2A − EPAS1 | **0.0450** |
| 2D joint (TOP2A, EPAS1) via histogram | 0.0203 |

## Synergy

Synergy = I(joint; Y) − I(TOP2A; Y) − I(EPAS1; Y)
- Via score: **-0.0151**
- Via 2D histogram: **-0.0398**

**Interpretation**: Synergy > 0 → the compound law carries information
about metastasis that neither single gene carries alone, i.e. the
2-gene form is *informationally necessary*, not redundant with either.

## MDL (equation token counts vs. AUROC)

| Equation | Tokens | AUROC | Tokens / AUROC |
|---|---|---|---|
| `TOP2A - EPAS1` | 3 | 0.726 | 4.13 |
| `log1p(CA9) + log1p(VEGFA) - log1p(AGXT)` | 9 | — | — |
| `log1p(LDHA) - log1p(ALB)` | 5 | — | — |
| `MKI67 - EPAS1` | 3 | 0.708 | 4.24 |
| `log1p(ACTB) - log1p(GAPDH)` | 5 | — | — |
| `CA9 (single gene)` | 1 | 0.521 | 1.92 |

**Token/AUROC** is a rough MDL-style efficiency. Lower = more
compact discrimination per equation symbol.

## Reproduce
```bash
PYTHONPATH=src .venv/bin/python src/i4_information_theory.py
```