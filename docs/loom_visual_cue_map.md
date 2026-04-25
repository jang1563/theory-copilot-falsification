# Loom visual cue map — segment ↔ asset

Companion to `docs/loom_narration_final_90s.md`. For each of the 7
narration segments, this file lists the **primary on-screen asset** to
display, the **fallback** if the primary isn't ready, and the **exact
file path** to keep open in the recording window.

Loom multi-pane setup (recommended): three side-by-side windows —
**Pane A** (editor), **Pane B** (image viewer / browser), **Pane C**
(terminal). Cue rows below say which pane.

---

## 0:00 – 0:10 — Hook (21 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A | `results/RESULTS.md` open at top with the "194/203 rejected" headline visible | `results/RESULTS.md` | `README.md` line 3 (the same headline blockquote) |

**Audio**: hook line. **No cuts during these 10 s.**

---

## 0:10 – 0:25 — Architecture (30 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A | **Architecture diagram** (4-role agent loop + gate + 3 paths) | ⚠️ **NOT YET CREATED** — needs `docs/architecture.png` | `CLAUDE.md` ASCII execution-flow block (visible if window scrolls there) |

**⚠️ ACTION REQUIRED before recording**: create `docs/architecture.png`
showing Proposer → Searcher (PySR) → Falsification gate → Skeptic →
Interpreter, with the three Managed Agents paths (A/B/C) on the side.
Source data: `CLAUDE.md` execution-flow ASCII + `docs/methodology.md
§4` Managed Agents architecture. Keynote 1 slide; export 1920×1080.

---

## 0:25 – 0:45 — Rejection surface (38 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A (cross-task matrix) | `task_auroc_comparison.png` | `results/track_a_task_landscape/plots/task_auroc_comparison.png` | `results/plots/falsification_panel_all.png` |
| Pane B (rejection log row) | `falsification_report.json` scrolled to a CA9-anchor failing row | `results/flagship_run/falsification_report.json` (or `track_a_task_landscape/tumor_normal/falsification_report.json`) | `delta_baseline_by_task.png` |

**Cut at**: "Even the textbook HIF-axis law Opus itself proposed —
log CA9 + log VEGFA − log AGXT — fails." — that's where the JSON row
should be visible.

---

## 0:45 – 1:05 — Survivor (52 words, with citation emphasis)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (survivor scatter) | `survivor_scatter_top2a_vs_epas1.png` | `results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png` | `results/plots/separation_top3_tier1.png` |
| Pane A (interpretation md) | Opus-authored mechanism doc | `results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md` | `docs/survivor_narrative.md` "One-minute version" |

**Cut at**: "The simplest — top-two-A minus EE-pass-one —" → scatter
appears. **Hold scatter through the Brannon/ClearCode citation.**

---

## 1:05 – 1:20 — External validation + own-output kill (34 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (KM curve) | IMmotion150 PFS Kaplan–Meier | `results/track_a_task_landscape/external_replay/immotion150_pfs/km_median_split.png` | `g4_anchor_regression/anchor_trajectory.png` |
| Pane A (PhL-1 verdict JSON) | 3-gene extension SLC22A8 verdict — must show `"verdict": "FAIL"` | `results/track_a_task_landscape/external_replay/immotion150_slc22a8/km_median_split.png` (KM) + the SUMMARY.md or verdict JSON in the same dir | `results/track_a_task_landscape/external_replay/immotion150_slc22a8/SUMMARY.md` |

**Cut at**: "Then our own three-gene extension. Same survival gate.
Killed it." — verdict JSON shown here.

---

## 1:20 – 1:30 — Routine + close (18 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (browser, Path C) | PhL-8 Routine session URL live in incognito tab | `https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM` | `results/live_evidence/04_managed_agents_e2e.log` opened in editor |
| Pane C (terminal) | `make audit` → wait for `OK` line | `make audit` | n/a (terminal always available) |

**Cut at**: "A Claude Code Routine fires this audit server-side." —
browser tab visible. **Last 2 s**: terminal `OK` flash.

---

## 1:30 – 2:00 — DIPG generalization (60 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A (RESULTS row) | `results/external_validation_dipg/RESULTS.md` with the 7-7-1 verdict distribution row highlighted | `results/external_validation_dipg/RESULTS.md` | `docs/headline_findings.md` DIPG paragraph |
| Pane B (top-lead JSON) | Panobinostat-CED-MTX110 verdict — must show aggregate score 13/15 | `results/external_validation_dipg/top_lead_panobinostat_CED_MTX110/04_panobinostat_CED_MTX110.verdict.json` | n/a — this asset is essential |

**Cut at**: "Top lead: CED-delivered MTX110 panobinostat" — JSON shown
with score 13/15 visible.

---

## Pre-flight checklist (before camera rolls)

1. **Architecture diagram** ready as `docs/architecture.png` (or
   accept ASCII-fallback in `CLAUDE.md`).
2. **Pane A editor** has `results/RESULTS.md`,
   `INTERPRETATION_top2a_epas1.md`,
   `external_validation_dipg/RESULTS.md` open in tabs.
3. **Pane B image viewer** has the four required PNGs preloaded:
   - `survivor_scatter_top2a_vs_epas1.png`
   - `task_auroc_comparison.png`
   - `immotion150_pfs/km_median_split.png`
   - `immotion150_slc22a8/km_median_split.png`
4. **Pane B incognito browser** preloaded to PhL-8 `claude.ai/code`
   session URL.
5. **Pane C terminal** in repo root with `make audit` typed but not
   pressed.
6. Trim 1 s leading silence; trim trailing silence aggressively;
   1080p / 30 fps single take preferred.

## What is NOT shown (intentional omissions)

- Live API call traces — too noisy on screen, log file path
  referenced instead.
- Cross-model ablation histogram (`results/ablation/plots/model_specificity_histogram.png`)
  — load-bearing for the *write-up* but slows the demo flow. Reviewers
  who care will click `docs/judge_faq.md` Q5.
- Robustness 6-axis heatmaps — same reason; reviewers find them via
  the `survivor_robustness/SUMMARY.md` link if they want.
- Manuscript / paper PDF — judge_faq.md and methodology.md cover the
  same ground in shorter form.

This file is the single source of truth for which assets matter at
recording time. If a Loom-time question is "should I show X?", the
answer is "only if it's listed above."
