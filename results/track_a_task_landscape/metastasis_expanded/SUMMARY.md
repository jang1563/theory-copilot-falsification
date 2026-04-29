# TCGA-KIRC Metastasis Expanded Panel Summary

This directory contains the central repaired-panel TCGA-KIRC M0-vs-M1 classification run used by the FMAI manuscript.

## Task and Scope

| Field | Value |
|---|---|
| Cohort/task | TCGA-KIRC M0 vs M1 |
| n | 505 |
| Panel | 45-gene expanded metastasis panel |
| Repair target | Panel absence in the original 11-gene HIF-axis panel |
| Gate | Same classification gate as the original rejection layer |
| Candidate report | `falsification_report.json` |

## Accounting

| Evaluated | Passed | Rejected |
|---:|---:|---:|
| 30 | 9 | 21 |

Passing families:

| Family | Passing rows |
|---|---:|
| `TOP2A - EPAS1` variants | 5 |
| `MKI67 - EPAS1` variants | 2 |
| Larger `EPAS1/MKI67/LRP2/PTGER3/RPL13A` compounds | 2 |

## Central Simple Survivor

The simplest reported survivor is:

```text
(0.09855198 * (TOP2A - EPAS1)) + 0.16059029
```

Metrics for the simple `TOP2A - EPAS1` family:

| Metric | Value | Interpretation |
|---|---:|---|
| `law_auc` | 0.7255601117252035 | Discovery-cohort gate metric; sign-invariant law AUROC |
| `train_auroc` | 0.7666870042708969 | PySR search split training diagnostic |
| `test_auroc` | 0.6311848958333333 | PySR 70/30 search split diagnostic |
| train-test gap | 0.1355021084375636 | Search diagnostic; not a gate leg |
| `baseline_auc` | 0.6569501396565044 | Best sign-invariant single-feature baseline |
| `delta_baseline` | 0.06860997206869912 | Passes the required `> 0.05` increment |
| `ci_lower` | 0.6579767149658812 to 0.6699004989833176 | Bootstrap lower 95% AUROC bound across simple variants |
| `perm_p_fdr` | 0.0 | Gate diagnostic after proposal/search |
| `decoy_p` | 0.0 | Gate diagnostic against decoy features |
| `fail_reason` | empty | Passing row |

`delta_confound` is `null` for these rows because this M0-vs-M1 task had no non-degenerate covariates available after cohort filtering; the active gate legs are permutation, bootstrap lower bound, sign-invariant single-feature baseline comparison, decoy null, and FDR adjustment.

## Internal Replay

Five-fold internal replay for the simple `TOP2A - EPAS1` score is stored at:

```text
results/track_a_task_landscape/survivor_robustness/replay_5foldcv.json
```

Key result:

| Replay | Value |
|---|---:|
| Folds | 5 |
| Sign-invariant AUROC mean | 0.7223347013223894 |
| Sign-invariant AUROC std | 0.07818814807986145 |
| Fold AUROCs | 0.641, 0.659, 0.679, 0.801, 0.832 |
| Permutation-null mean AUROC | 0.5085444140446876 |

## Claim Boundary

This run supports a repaired-panel discovery-cohort gate acceptance, not independent clinical validation. The reported `law_auc=0.726` is the locked gate metric; the lower `test_auroc=0.631` is retained as a search split diagnostic; the 5-fold AUROC is an internal robustness replay.
