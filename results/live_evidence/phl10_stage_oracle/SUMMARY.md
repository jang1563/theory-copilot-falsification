# PhL-10 — Stage Oracle: FAIL + PASS on ccRCC Staging

**Status:** COMPLETE — clean dual verdict.
**Run date:** 2026-04-26
**Session URL:** `https://claude.ai/code/session_01XGse8XYFtv3C1aKLZeMH9t`
**Routine:** lacuna-scientific-oracle (CLAUDE_ROUTINE_TRIG_ID fallback; same Instructions handle stage task)

## What this run shows

Second autonomous oracle session. Same gate, same pre-registered thresholds, new task
(Stage I-II vs III-IV, n=512). Instantiates the "new Routine per disease/question" architecture.

| Property | PhL-8d (metastasis) | PhL-10 (stage) |
|---|---|---|
| Task | tumor_vs_normal + metastasis_expanded | stage_expanded (Stage I-II vs III-IV) |
| n | 609 / 505 | 512 |
| Eq1 | CA9 − AGXT | CCNB1 / PGK1 |
| Eq2 | CDK1 − EPAS1 | CXCR4 / EPAS1 |
| Verdict | FAIL + PASS | FAIL + PASS |

## Gate results

### Eq1 — CCNB1 / PGK1 → GATE FAIL

```
===GATE VERDICT: eq1===
equation:       CCNB1 / PGK1
task:           stage_expanded (Stage I-II vs III-IV, n=512)
RESULT:         FAIL
fail_reason:    delta_baseline (0.007 < 0.05 threshold)
perm_p:         0.000000   ✓
ci_lower:       0.603456   ✓  (>0.6)
delta_baseline: 0.007110   ✗  (need >0.05 — only +0.007 over CUBN single-gene baseline)
delta_confound: null       (no covariates supplied)
decoy_p:        0.000000   ✓
===END VERDICT===
```

CCNB1 and PGK1 together add only +0.7 pp over CUBN alone — genuine signal (non-random,
non-decoy) but the gate correctly refuses the compound-discovery claim.

### Eq2 — CXCR4 / EPAS1 → GATE PASS

```
===GATE VERDICT: eq2===
equation:       CXCR4 / EPAS1
task:           stage_expanded (Stage I-II vs III-IV, n=512)
RESULT:         PASS
fail_reason:    none
perm_p:         0.000000   ✓
ci_lower:       0.648614   ✓  (>0.6)
delta_baseline: 0.051318   ✓  (+0.051 over best single-gene — just clears 0.05)
delta_confound: null       (no covariates supplied)
decoy_p:        0.000000   ✓
===END VERDICT===
```

CXCR4 (chemokine receptor; invasion/migration) / EPAS1 (HIF-2α; well-differentiated ccRCC)
reaches AUROC 0.696. Baseline (CUBN single-gene): 0.645.

**Honest caveat:** delta_baseline margin is razor-thin — 0.051318 vs 0.050000 threshold
(+0.001 above the bar). Independent-cohort replay warranted before elevation to survivor.

## Dual verdict summary

```
===DUAL VERDICT SUMMARY===
                  CCNB1 / PGK1    CXCR4 / EPAS1
RESULT:           FAIL            PASS
AUROC:            0.652           0.696
ci_lower:         0.603           0.649
perm_p:           <0.001          <0.001
delta_baseline:   +0.007 ✗        +0.051 ✓
decoy_p:          <0.001          <0.001
baseline (CUBN):  0.645           0.645
===END DUAL VERDICT SUMMARY===
```

## Architecture confirmed

Two sessions, two tasks, same gate, same pre-registered thresholds:
- PhL-8d: `session_01CgsJYAPdvhJJwTuBt7QZLZ` — metastasis/tumor_vs_normal
- PhL-10: `session_01XGse8XYFtv3C1aKLZeMH9t` — stage_expanded

One Routine per disease/question. Skills and gate are shared. No human decision after the fire call.
