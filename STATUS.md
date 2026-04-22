# STATUS — theory-copilot-falsification

**Last updated:** 2026-04-22 14:35 ET (Phase N kickoff)
**Days to submit:** T-4d 5h25m
**Submit window:** 2026-04-26 20:00 ET
**Judging:** 2026-04-28 12:00 ET

---

## 🎯 Headline artifact state

Scientific payload is complete and committed to `origin/main`. Narrative +
QA phases now run in parallel toward the 2026-04-26 submit window.

- **Flagship (11-gene panel, 4 ccRCC tasks):** 0 / 100+ candidates
  survive the pre-registered 5-test gate. `delta_baseline` ceiling at
  +0.029.
- **45-gene expanded panel:** 9 / 30 candidates pass on the metastasis
  task; simplest surviving law is `TOP2A − EPAS1` (proliferation minus
  HIF-2α) at AUROC 0.726, `delta_baseline = +0.069`.
- **Survivor robustness (6 axes + 5-fold CV):** passes 5 / 6 axes;
  single honest caveat is the LR pair-with-interaction baseline
  (`Δ = +0.004`, indicating the survivor is a compact monotone form
  of the `(TOP2A, EPAS1)` interaction rather than a multi-gene
  discovery beyond that pair).
- **Track B gate robustness (flagship 0-survivor verdict):** robust to
  threshold grid, baseline definition, permutation count, bootstrap
  seed, and cohort size; soft along feature-scaling (1/34 crosses a
  reduced-gate threshold).

---

## 🟢🟡🔴 Deliverable Dashboard

| # | Deliverable | Owner | Status | Last artifact | Notes |
|---|---|---|---|---|---|
| D1 | E2E `make demo` + flagship_run artifacts | N | 🟢 | results/flagship_run/, results/tier2_run/, results/track_a_task_landscape/, results/track_b_gate_robustness/ | Phase Q validates E2E via `make demo` / `make demo-kirc` |
| D2 | 90s Loom demo | N | 🔴 | — | N7 pending; 4/25 녹화 예정 |
| D3 | README (quickstart + persona) | N | 🟡 | 7a70919 | N5 pending (persona section) |
| D4 | methodology.md (5-test pre-reg + survivor section) | N | 🟡 | 7a70919 | N2 pending (positive-survivor section) |
| D5 | Managed Agents evidence | N | 🟢 | results/live_evidence/04_managed_agents_e2e.log | Path B end-to-end verified |
| D6 | Extended-thinking transcript | N | 🟢 | results/live_evidence/{01_opus_raw_smoke, 02_proposer_kirc, 03_skeptic}.log | all live, $0.20 cost |
| D7 | Survivor finding + interpretation | N | 🟢 | results/track_a_task_landscape/survivor_robustness/{SUMMARY.md, INTERPRETATION_top2a_epas1.md} | Sci-A phase output |
| D8 | Gate robustness finding | N | 🟢 | results/track_b_gate_robustness/SUMMARY.md | Sci-B phase output |
| D9 | Submission form draft (≤150 w) | N | 🔴 | — | N8 |

## 🛡️ Backup Plan Dashboard

| BP | State | Trigger status | 비고 |
|---|---|---|---|
| BP-1 Template fallback | 🟢 pre-built | not triggered | 7+ KIRC law families |
| BP-2 Scaffold excision | 🟢 done | .gitignore로 pre-hackathon scaffold 제외, cli.py rewritten institutional-name-free | `make audit` pass |
| BP-3 Freeze artifacts | 🟢 done | results/ under version control | flagship + tier2 + track_a + track_b + plots |
| BP-5 Cost ledger | 🟡 in progress | 누적 spend ≈ $0.20 | hard cap $350, well under |
| BP-6 ND2 audit | 🟢 clean | — | prompts/docs 0 matches |
| BP-7 HPC naming | 🟢 clean | — | `make audit` via .audit-patterns external pattern file |
| BP-8 Live smoke | 🟢 done | 4/22 early; api_validation_log.txt recorded | transcripts in results/live_evidence/ |
| BP-9 Loom backup | ⚪ pending | 4/26 12:00 ET cutoff | Phase N7 |
| BP-10 Judge personas | ⚪ pending | — | Phase N5 |
| BP-11 Leakage audit | 🟡 deferred | — | implicit in train/test split + CV replay; doc N-task TBD |
| BP-12 Scope freeze | 🟢 held | **4/24 24:00 ET 강제** | research additions stopped; Phase N/Q is narrative + QA only |
| BP-NULL Honest null | 🟢 morphed | converted to "accept+reject narrative" after 9-survivor finding | survivor_narrative.md (N6) replaces null_narrative |
| ~~BP-4 MA de-scope~~ | 해제 | Claude 팀 공식 답변 | Path B verified |

## 💰 Cost Ledger

| Date | Opus 4.7 USD | Sonnet USD | Cumulative | % of $500 |
|---|---|---|---|---|
| 4/22 | $0.20 | — | $0.20 | 0.04% |

**Kill-switch trigger:** ≥$350 (70%) OR 24h 윈도우 $150

## 🔄 Session Ownership (current phase)

- **Phase N (this session, formerly Sci-A)** — Narrative:
  STATUS / README / docs / prompts / submission form.
- **Phase Q (other session, formerly Sci-B)** — QA:
  `make test` / `make audit` / `make demo*` / plot sanity / doc
  consistency / live-transcript coherence.

Cross-phase handoffs: `HANDOFF_to_N.md` and `HANDOFF_to_Q.md` at repo
root (gitignored). Read before committing.

**Branch state:** `main` is the only branch. Latest origin/main
commit: `7a70919 [N] Restamp coordination contract header`.

## 🚦 Go/No-Go Gates

- [x] **G1** 4/23 22:00 — flagship_run ≥ 1 artifact (met early: flagship + tier2 + track_a + track_b)
- [x] **G2** 4/24 22:00 — full E2E + replay done (5-fold CV stands in for GSE40435; documented limitation)
- [x] **G3** 4/25 18:00 — ≥ 1 survivor OR null-narrative swap-ready (9 survivors on metastasis_expanded)
- [x] **G4** 4/25 22:00 — live-API smoke pass (done 4/22)
- [ ] **G5** 4/26 12:00 — Loom rendered (Phase N7)
- [ ] **G6** 4/26 18:00 — public push-ready, `make audit` pass (Phase Q validates)
- [ ] **G7** 4/26 20:00 — SUBMIT

## 📝 Decision Log (latest on top)

- 2026-04-22 14:35 ET · [N] · Phase transition from Sci-A/B to Phase N/Q. N queue = narrative docs; Q queue = E2E tests + audit + plot sanity. SESSION_COORDINATION.md updated.
- 2026-04-22 ~14:00 ET · [Sci-A] · 🎯 9 survivors on metastasis_expanded with 45-gene panel. TOP2A − EPAS1 passes 6-axis robustness (5 / 6 axes; honest caveat on pair+interaction baseline). 5-fold CV AUROC 0.722 ± 0.078.
- 2026-04-22 ~13:00 ET · [Sci-B] · Track B B1-B7 complete. Flagship 0-survivor verdict robust along 5 of 6 axes; feature scaling is soft.
- 2026-04-22 12:30 ET · [S2] · Phase A 실행 시작. `make audit` target 추가, `.gitignore` 가 이미 scaffold 제외 중이라 BP-2 pre-hackathon excision 불필요 확인.
- 2026-04-22 12:00 ET · [S2] · HPC compute approved for heavy PySR sweeps; Managed Agents public-beta confirmed usable (Claude team reply).
- 2026-04-22 (earlier) · [planning] · soft-sniffing-starlight backup plan 작성 완료.

## 🧭 What's left (Phase N queue)

1. **N1** STATUS.md refresh ← this commit
2. **N2** docs/methodology.md: add positive-survivor section after §5
3. **N3** docs/why_opus_4_7.md: update §4 demo moment with the survivor
4. **N4** docs/submission_description.md: rewrite for accept+reject
5. **N5** README persona section (Boris / Lydia / Jason / domain view)
6. **N6** docs/survivor_narrative.md (replaces the null_narrative draft)
7. **N7** docs/loom_script.md: 90-second demo script
8. **N8** submission form draft ≤ 150 words
