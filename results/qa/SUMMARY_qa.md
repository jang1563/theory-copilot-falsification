# Phase Q — QA Summary

**Run:** 2026-04-22, Phase Q session
**Scope:** Q1–Q9 of the QA brief
**Codebase state at start:** commit `5e737de` (Sci-A TOP2A−EPAS1 survivor stress)
**Phase Q commits:** `32d69d9` (Q1+Q2), `5614c65` (Q1-rerun + Q3/Q4/Q5), and this commit (Q6/Q7/Q8 + handoff).

---

## Compact status table

| Step | Pass/Fail | Notes | Files |
|---|---|---|---|
| **Q1** `make test` | ✅ PASS | 47/47 under `.venv/bin/python`. Default `python3` = 3.9 breaks on `X \| Y` type hints; see low-priority note in HANDOFF. | `q1_test_run.txt` |
| **Q2** `make audit` | ✅ PASS | Zero tracked-file hits against `.audit-patterns`. Re-run after every subsequent change — still clean. | `q2_audit.txt` |
| **Q3** `make demo` | ❌ **FAIL — BLOCKER 1** | `opus_client._call` uses non-streaming `messages.create(max_tokens=32000)`; SDK rejects before network call. Documented fix in `api_validation_log.txt` Part 5 is missing from HEAD. | `q3_demo_stdout.log`, `HANDOFF_to_N.md` |
| **Q4** `make demo-kirc` | ❌ **FAIL — same BLOCKER** | Same `_call` path; same SDK rejection. | `q4_demo_kirc_stdout.log`, `HANDOFF_to_N.md` |
| **Q5** Re-run metastasis_expanded | ✅ PASS | 9 / 30 survivors matches committed report. Top Δ +0.069 via `log1p(log1p(exp(x31 − x4)) * k)` = TOP2A − EPAS1 (panel index x31/x4). | `q5_metastasis_expanded_rerun.json`, `q5_rerun_check.txt` |
| **Q6** Plot review | ⚠️ 4 HIGH findings | H1 `falsification_panel_all.png` pre-Option A6; H2 `delta_baseline_hist.png` "60" should be 67; H3 task_auroc + delta_by_task pre-Option A6; H4 `threshold_heatmap.png` title typo (Phase Q's own). | `q6_plot_review.txt`, `HANDOFF_to_N.md` |
| **Q7** Doc scan | ✅ PASS | 22 markdown links, all targets exist. No contradictory numbers across prose. Deadlines consistent. | `q7_doc_scan.txt` |
| **Q8** opus_client + prompts + live_evidence | ⚠️ 1 BLOCKER | Prompts all JSON-enforced ✓; fence-stripping parser sound ✓; Managed Agents Path B shape verified ✓; role tagging consistent ✓; **streaming fix missing (same BLOCKER 1)**. | `q8_opus_client_check.txt`, `HANDOFF_to_N.md` |

## Overall status

**1 BLOCKER, 4 HIGH, 0 MEDIUM, 1 LOW**, all passed to Phase N via
`HANDOFF_to_N.md` at repo root.

Pipeline reproduces (Q5). Tests pass (Q1). Audit clean (Q2). Docs
consistent (Q7). The only submission-blocking issue is the
`opus_client._call` streaming-fix regression, which is a ~10-line
edit documented in `api_validation_log.txt` Part 5.

## Phase Q standby

Phase Q will not touch any Phase N file directly. Once Phase N applies
BLOCKER 1 fix and commits, Phase Q will re-run `make demo` + `make
demo-kirc` to confirm green-path end-to-end and log the confirmation
under `results/qa/`.

## Files under results/qa/

```
SUMMARY_qa.md                        (this file)
q1_test_run.txt                      Q1 pytest output (sanitized)
q2_audit.txt                         Q2 audit output
q3_demo_stdout.log                   Q3 make demo crash log
q4_demo_kirc_stdout.log              Q4 make demo-kirc crash log
q5_metastasis_expanded_rerun.json    Q5 fresh falsification result
q5_rerun_check.txt                   Q5 vs committed comparison
q6_plot_review.txt                   Q6 13-plot review
q7_doc_scan.txt                      Q7 link + numeric consistency
q8_opus_client_check.txt             Q8 client + prompts + evidence check
```

Handoff at repo root: `HANDOFF_to_N.md` — severity-tagged fix list
for Phase N.
