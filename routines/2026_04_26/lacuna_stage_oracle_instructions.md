# Lacuna Stage Oracle — Routine Instructions

**Routine name**: `lacuna-stage-oracle`
**Created**: 2026-04-26
**Purpose**: Run the pre-registered 5-test falsification gate on ccRCC staging equations.
**Architecture note**: This is a SECOND Routine, separate from `lacuna-scientific-oracle`
(PhL-8d provenance record). One disease/question = one Routine. The Instructions encode
the disease-specific data contract; the Skills and gate logic are shared.

---

## What this Routine does

On each fire call, parse the trigger text for up to 2 equations in `DUAL_TRIGGER` format:

```
eq1: task=<task_name>, data=<csv_file>, equation=<expression>
eq2: task=<task_name>, data=<csv_file>, equation=<expression>
```

For each equation:
1. Load `data/<csv_file>` from the repo root.
2. Evaluate the equation as a Python expression over the CSV columns to produce a law score.
3. Run `passes_falsification(X, y, law_score)` from `src/lacuna/falsification.py`.
   The gate runs five pre-registered tests: permutation null, bootstrap CI lower bound,
   delta_baseline (law AUROC minus best sign-invariant single-gene), incremental confound,
   and decoy-feature null. Thresholds are committed — do not adjust them.
4. Print a `===GATE VERDICT===` block with all metric values and `PASS` / `FAIL`.

## Data contract — stage_expanded

- File: `data/kirc_stage_expanded.csv`
- Task: Stage I-II vs Stage III-IV (`label` column: 0 = Stage I-II, 1 = Stage III-IV)
- n = 512 samples
- Gene columns: 45-gene ccRCC panel (same as metastasis_expanded)
- Known pre-computed results:
  - `CCNB1 / PGK1`: AUROC 0.625, delta_baseline=+0.007 → expected FAIL
  - `CXCR4 / EPAS1`: AUROC 0.689, delta_baseline=+0.051 → expected PASS

## Output format (both equations)

```
===GATE VERDICT: eq1===
equation: CCNB1 / PGK1
task: stage_expanded
RESULT: FAIL
fail_reason: delta_baseline
perm_p: 0.000 (< 0.05 ✓)
ci_lower: 0.603 (> 0.60 ✓)
delta_baseline: +0.007 (threshold > 0.05 ✗)
delta_confound: null
decoy_p: 0.000 (< 0.05 ✓)
===END VERDICT===

===GATE VERDICT: eq2===
equation: CXCR4 / EPAS1
task: stage_expanded
RESULT: PASS
fail_reason: none
perm_p: 0.000 (< 0.05 ✓)
ci_lower: 0.662 (> 0.60 ✓)
delta_baseline: +0.051 (> 0.05 ✓)
delta_confound: null
decoy_p: 0.000 (< 0.05 ✓)
===END VERDICT===
```

## Multi-disease context

This Routine is part of a multi-disease expansion. Other committed results:
- `lacuna-scientific-oracle` (PhL-8d): ccRCC metastasis + tumor_vs_normal
- `coad_msi/`: Colon MSI-high (15/22 PASS, SLC2A1+Warburg)
- `lihc/`: Liver HCC (0/26, designed negative)
- `stage_expanded/`: ccRCC Stage (23/28 PASS, CXCR4/EPAS1) — this Routine

Same gate, same Skills, new Routine per disease/question.
