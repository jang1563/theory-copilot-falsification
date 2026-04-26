# Stage 1 — Self-audit against judging criteria

**Date:** 2026-04-25 (T-29h to submit)
**Method:** Walk every criterion from `docs/judging_criteria_audit.md` §7
against current repo state. Each row has ✅/⚠️/❌ + evidence file +
gap note. Two highest-weight axes (Demo 25%, Opus 4.7 Use 25%) get
deep-dive sections at the end.

---

## A. Compact axis-by-axis table

### A.1 Impact (30% — single largest axis)

| Sub-criterion | Status | Evidence | Gap |
|---|---|---|---|
| Real-world problem articulated | ✅ | `submission_form_draft.md` unified summary §1; README.md L9; `loom_narration_final_90s.md` 0:00 hook ("AI-for-science tools help you confirm almost anything. This one was built to say no.") | none — sharp framing |
| "Built from what you know" — domain-expert credible | ✅ | `submission_form_draft.md` "Problem statement alignment" → explicitly chooses `Build From What You Know`; user is biomedical postdoc | none — directly mapped |
| Wide-audience applicability | ⚠️ | DatasetCard abstraction + `lacuna plug-in-dataset` CLI; cross-disease validation (KIRC + DIPG + IPF, 3 structurally distant diseases) | minor — "wide audience" phrasing not explicit in unified summary; covered in §"Broader Program Context" optional |
| Time/cost saved (human-meaningful metric) | ⚠️ | IPF Run #1: "$58, 32 min" (a cost figure); KIRC: "194 of 203 rejected" (a rejection-rate figure, not time-saved) | **GAP**: 4.6 winners had "weeks→20 min" / "$30K saved" — we have rejection counts + dollar cost of API run. Not a "researcher time saved" metric. **Acceptable framing**: the time-saved metric is *implicit* — researchers spending months pursuing a non-survivor could redirect that time. Decide if explicit version needed in summary. |
| Comparison vs existing alternatives | ✅ | `docs/why_opus_4_7.md` §1 (POPPER, LLM-SR, Sakana v2, FIRE-Bench citations); `survivor_narrative.md` (Brannon 2010, ClearCode34, TOP2A 2024); 180-call cross-model ablation (Opus 4.7 vs 4.6 vs Sonnet 4.6 vs Haiku 4.5) | none — extensive prior-art context |

### A.2 Demo (25% — PRIMARY judging input per Ado 4/23)

| Sub-criterion | Status | Evidence | Gap |
|---|---|---|---|
| Demo ≤ 3:00 | ⚠️ | Script: 333w / 2:23 @ 140 WPM / 2:47 @ 120 WPM; budget tier 1/2/3 documented for fallback | **VIDEO NOT YET RECORDED** (Stage 7 = 4/26 AM) |
| Real product screen recording (not Remotion-replicated UI) | ✅ | `loom_visual_cue_map.md` uses real editor/image-viewer/terminal panes; verified by parallel-session audit 4/25 | none — 4.6 mistake #1 explicitly avoided |
| "Easier to demo than to explain" | ✅ | Hook frames problem in 21 words; opening shows actual `RESULTS.md`; closing terminal `make audit` → `OK` | none |
| Human → pain → before → after narrative arc | ⚠️ | Hook ("AI-for-science tools help you confirm almost anything") = pain; Architecture (0:10) = build; Survivor (0:45) = after-state; **but no explicit "researcher persona" cold-open** like 4.6 winners (Mike Brown showed ADU permit; Nedoszytko showed patient summary) | **GAP**: no named end-user persona in script. We open with abstract claim, not a named scientist with a specific disease question. **Consider**: 5-second persona insert ("Jin, postdoc, 3 weeks chasing a finding that won't replicate") OR accept current frame as the Loom is for an audience who already aligns with the abstract problem |
| Visible Claude Code / Opus 4.7 in action | ⚠️ | Loom 0:25-0:45 shows JSON outputs and (NEW) terminal jq cut; 1:20-1:30 shows browser with PhL-8 Routine session URL; `make audit` terminal | minor — Claude Code itself (the CLI window) doesn't appear; only its outputs. Decide if a 3-second cut to a Claude Code session is needed (Boris Cherny's heuristic) |

### A.3 Opus 4.7 use (25% — equal weight to Demo)

| Sub-criterion | Status | Evidence | Gap |
|---|---|---|---|
| Beyond basic prompting | ✅ | 4 distinct roles (Proposer / Searcher / Skeptic / Interpreter); each with role-specific prompt; structured-JSON handoff between sessions | none — orchestration is the point of the project |
| Creative / surprising integration | ✅ | Falsification gate ENFORCED on the LLM's own proposals (the system kills its own H1 3-gene extension via PhL-1); 180-call cross-model ablation showing Opus 4.7 is the only model that holds dissent stance (10/60 vs Sonnet 0/60) | none |
| Adaptive thinking / 1M context / extended-thinking demonstrated | ✅ | `thinking={"type":"adaptive","display":"summarized"}` + `output_config={"effort":"high"}` documented in `why_opus_4_7.md`; PhL-15 thinking-mode confound resolution; 1M-context cross-reasoning synthesis (`opus_1m_synthesis.py` + `synthesis_1m.json`); PhL-17 210-turn adversarial-critique stance-decay | none — arguably the strongest axis |
| Managed Agents (Best-MA special prize candidacy) | ✅ | Path A live (PhL-9 + PhL-9v2 sequential 3-session), Path B live (`04_managed_agents_e2e.log`), Path C live (PhL-8 `/fire` HTTP 200 + session URL); Memory PhL-3 / PhL-10 / PhL-12; pin_version pattern; persist_session_events / replay_session_from_log durability | none — primary special-prize target |
| Skills / Memory / Routines used per documented pattern | ✅ | `.claude/skills/` (falsification-gate + pre-register-claim, both with proper SKILL.md); `.claude/agents/` (proposer / skeptic / interpreter / qa-validator); `.mcp.json` + `mcp_biology_validator.py`; Routines via `experimental-cc-routine-2026-04-01` beta header | none |

### A.4 Depth (20% — smallest axis)

| Sub-criterion | Status | Evidence | Gap |
|---|---|---|---|
| "Push past first idea" — multiple iterations visible | ✅ | Phase A → ... → G → I (G1/G2 + I2/I3/I4 = 5 pre-registered analyses just landed today); branding v1.0 → v1.6; Lacuna rename | none |
| Real craft (tests, audits, validation) | ✅ | 104/104 pytest pass; `make audit` clean; pre-registration discipline (24+ YAMLs); branch hygiene | none |
| Pre-registration discipline | ✅ | `preregistrations/` 25+ YAMLs all SHA-tagged; emitted_git_sha bound to repo state at commit; "gate_logic_changed: false" reporting-only flag pattern | none — load-bearing for the falsification claim |
| Honest negative results / self-falsification | ✅ | PhL-1 (own H1 extension killed by separately pre-registered IMmotion150 gate); G1 H1+H2 FAIL honestly documented; I3 P3 FAIL on screening sensitivity; I4 P2 bootstrap CI includes zero — flagged | none — strongest axis under "honest" framing |

### A.5 Submission requirements compliance

| Requirement | Status | Note |
|---|---|---|
| Demo video URL | ❌ | Stage 7 (4/26 AM) |
| GitHub repo URL | ⏳ | Lacuna rename committed (f5bb417 + 86abdfb); awaiting GitHub UI rename + push (Stage 9) |
| Written description (100-200w) | ✅ | unified summary 176/200w |
| Description 4-beat (what / problem / how-built / how-Claude) | ⚠️ | **GAP**: current summary leads with problem ("AI-for-Science tools accelerate hypothesis generation — not rejection"), then build ("Lacuna is the rejection step. Opus 4.7 plays..."), then validation ("On TCGA-KIRC..."). Missing explicit "what" header? Reads more as **problem → build/Claude → results**. **Stage 6 task: re-test against 4-beat structure (what / problem / how-built / how-Claude); reorder if needed** |
| Public repo during judging window | ⏳ | Stage 9 |
| OSS license on all code | ✅ | `LICENSE` (MIT) at repo root; pyproject.toml license metadata |
| 3rd-party API integration code public | ✅ | Anthropic SDK only |

### A.6 Special prize candidacy

| Prize | Claim status | Justification quality |
|---|---|---|
| **Best Use of Claude Managed Agents** ($5K) — primary | ✅ | 96/100w drafted; cites Path A live (PhL-9 + PhL-9v2 real TCGA-KIRC), Path B live (agent_toolset_20260401), Path C live (PhL-8 HTTP 200 fire), Memory public-beta day-of integration (PhL-3) |
| **Most Creative Opus 4.7 Exploration** ($5K) — secondary | ⚠️ | Not currently called out in submission_form. Strong candidate via 1M-context cross-reasoning synthesis on full failure history. **Stage 6 decide**: add a 1-sentence "Most Creative" pitch in the Opus 4.7 usage paragraph or skip |
| **Keep Thinking** ($5K) — secondary | ⚠️ | Not currently called out. Strong candidate via PhL-15 (adaptive thinking ablation) + PhL-17 (210-turn adversarial stance-decay) — "thinking persisted across 7 rounds of adversarial critique". **Stage 6 decide**: add 1-sentence pitch |

---

## B. Deep dive — Demo (25%)

### B.1 What's in the can right now

- Script: `loom_narration_final_90s.md` (333w, 8 segments, **2:23-2:47 at 140-120 WPM**, well under 3:00 hard cap)
- Visual cue map: `loom_visual_cue_map.md` (8 segments × multi-pane; terminal cut added at 0:25-0:45 by parallel session 4/25)
- Recording cheatsheet: `loom_recording_cheatsheet.md`
- Verbatim narration (longer 246w): `loom_narration_verbatim.md`

### B.2 Strengths against 4.6 winner pattern

1. **Real screen recording, not Remotion** ✅ verified
2. **Pain-stated-first hook** ✅ "AI-for-science tools help you confirm almost anything. This one was built to say no."
3. **Concrete numbers in dialogue** ✅ "194 of 203 rejected" (memorable)
4. **Demonstrates falsification on LLM's own output** ✅ PhL-1 segment shows the system killing its own H1 extension
5. **3-disease generalization** ✅ KIRC → DIPG → IPF closing tag

### B.3 Weaknesses against 4.6 winner pattern

| 4.6 winner did | We have | Risk |
|---|---|---|
| Named end-user (Mike Brown's lawyer; Nedoszytko's patient) | Abstract "AI-for-science tools" | **MEDIUM**: opens cold without a person; could feel "for researchers" not "for everyone" |
| Visible UI (CrossBeam web app; PostVisit.ai dashboard) | Editor panes + JSON files + terminal | **LOW**: our "UI" IS the terminal/editor; honest framing |
| Time/cost-saved before-after ("weeks→20 min") | "$58, 32 min" for one disease run | **LOW-MEDIUM**: dollar+time figure exists for IPF segment; could surface earlier in script |
| Live demo of working product | Static cuts of working product | **LOW**: product IS plain Python, deterministic; the artifacts ARE the demo |

### B.4 Demo verdict

- **Tier 1 ship-ready** (no further script changes required to record)
- **Optional improvements** (Stage 7 pre-record decision):
  - Add 5-second "Jin the postdoc, 3 weeks chasing a non-replicating finding" persona cold-open before the abstract hook
  - Re-record the 0:32-0:36 terminal cut with verified `jq` schema (per parallel-session note)
  - Show Claude Code session window briefly somewhere (Boris Cherny signal)
- **Risk if no improvements**: still strong demo, just not 4.6-winner-shaped. Acceptable for a research-driven submission.

---

## C. Deep dive — Opus 4.7 use (25%, equal weight to Demo)

### C.1 What we use Opus 4.7 for (4 distinct roles + 3 paths)

**Roles:**
1. **Proposer** — emits 3-5 compact law families + ex-ante kill-test per family, BEFORE any fit. Pre-registration is the bite. (`prompts/law_family_proposal.md`, `src/lacuna/managed_agent_runner.py::run_path_*`)
2. **Skeptic** — reviews gate output JSON only (never the Proposer's reasoning tokens). Emits per-candidate verdict + dissent flag. (`prompts/skeptic_review.md`)
3. **Interpreter** — for survivors only, emits mechanism hypothesis + downstream prediction + "what this is *not*" caveat paragraph. (`prompts/final_explanation.md`)
4. **Searcher** (Sonnet 4.6 actually, not Opus) — runs PySR via bash. No judgement.

**Paths (Managed Agents architecture):**
- **Path A**: Sequential 3-session falsification chain (Proposer → Searcher → Skeptic). PhL-9 + PhL-9v2 ran on real TCGA-KIRC, 706s wall, structured-JSON handoff. `delegation_mode=sequential_fallback` (callable_agents disabled per fairness rule).
- **Path B**: Single agent + `agent_toolset_20260401` public beta. End-to-end `agents.create → environments.create → sessions.create → stream → send → status_idle` at `04_managed_agents_e2e.log`.
- **Path C**: Claude Code Routine driver. PhL-8 `/fire` HTTP 200 + live session URL at `claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM`. `theory-copilot-falsification-gate` (renamed `lacuna-falsification-gate`) Routine.

### C.2 Opus 4.7-specific configurations and their evidence

| Feature | How we use it | Evidence file |
|---|---|---|
| `thinking={"type":"adaptive","display":"summarized"}` | All 4 Opus roles run adaptive thinking | `src/lacuna/opus_client.py`; `why_opus_4_7.md` §2 |
| `output_config={"effort":"high"}` | All 4 roles | same |
| 1M-context window | Cross-reasoning synthesis on entire failure history (3553 tokens actual; 1M cap not hit) | `src/opus_1m_synthesis.py`; `results/overhang/synthesis_1m.json` |
| Streaming `.messages.stream()` | Required for 32K max_tokens + adaptive + summarized; non-streaming trips SDK 10-min guard | `opus_client.py::_call`; CLAUDE.md Lessons |
| `pin_version=True` (V1/V2 versioned-resource) | Path B `sessions.create(agent={"type":"agent","id":..,"version":N})` | `managed_agent_runner.py::run_path_b` |

### C.3 Empirical Opus 4.7 capability claims (evidence)

1. **Cross-model ablation (180 calls)**: Opus 4.7 = 10/60 PASS on gate-PASS candidates; Sonnet 4.6 = 0/60 (full dissent collapse); Haiku 4.5 = 14/60. Sonnet's 100% dissent rate is the case for why a smaller model can't replace Opus 4.7 in the Skeptic role. (`results/ablation/SUMMARY.md`)

2. **Opus 4.6 vs 4.7 (60 calls each)**: 4.7 commits PASS 10/10 on clean survivors where 4.6 commits 7/10; 4.7 abstains `NEEDS_MORE_TESTS` 10/10 on a stress-test 5-gene compound where 4.6 over-commits PASS 2/10. Strict miscalibration 0% for both. (`results/ablation/opus_46_vs_47/`)

3. **Thinking-mode ablation (PhL-15 v2 final)**: adaptive_max vs no_thinking on Opus 4.7 = both 0/60 PASS in narrow context. Conclusion: **context richness, not thinking budget, is the capability-extraction lever** on this task. (`results/live_evidence/phl15_adaptive_thinking/SUMMARY.md`)

4. **Stance decay (PhL-17, 210-turn 7-round adversarial)**: Opus 4.7 holds PASS verdict 78.6% on TOP2A-EPAS1 across 7 rounds of adversarial critique; concedes twice on legitimate arguments (T4 Rashomon multiplicity) — calibrated updating. Sonnet holds PASS 100% regardless of argument quality (no concession even on valid arguments). Haiku 4.5 errored 10/10 on multi-turn + adaptive thinking. Interpretation: **Opus 4.7's specific capability is *knowing when to concede on valid arguments*, not unconditional stance-holding**. (`docs/why_opus_4_7.md` §0 — "gate-as-authority-substrate result")

5. **Memorization audit (PhL-13)**: Opus 4.7 zero-shot retrieval of TOP2A−EPAS1 = 0/10 (rebuts LLM-SRBench memorization concern). The discovery is data-driven, not memorized. (`results/live_evidence/phl13_memorization_audit/`)

### C.4 Where Opus 4.7 use shows up in current submission

- **submission_form_draft.md "Claude Opus 4.7 usage" (134/150w)**: 4 calls per loop, thinking config, ablation gap, memorization audit, IPF runtime context-isolation
- **submission_form_draft.md "Claude Managed Agents usage" (149/150w)**: 3 paths + durability + Memory + IPF
- **Loom narration**: Opus 4.7 mentioned 0:10-0:25 ("Opus four-point-seven proposes seven compact law families")
- **why_opus_4_7.md**: 6-section deep-dive (~600 lines)

### C.5 Opus 4.7 verdict

- **Strongest axis** under the rigor lens. 4 roles × 3 paths × empirically validated by 5 distinct PhL ablations.
- **Possible risk**: not surfaced strongly enough in the LOOM narration — the script mentions Opus 4.7 once. If a judge watches only the video and reads only the form, the form does the heavy lifting; the video frames it as architecture, not as "what 4.7 specifically enables."
- **Stage 6 candidate change**: 1-sentence Loom narration enhancement OR keep video light and let form carry it. (Decide based on Stage 7 timing.)

---

## D. Top 3 gaps (priority by axis weight × gap size)

| Rank | Gap | Axis impact | Action | Cost |
|---|---|---|---|---|
| **1** | **Description 4-beat structure not explicit** (Discord 4/25 spec: what / problem / how-built / how-Claude) — current summary reads more as problem→build→results | Demo + Impact (description complements video pre-shortlist) | Stage 6 — restructure unified summary into 4-beat order; verify each beat is identifiable | 30-45 min |
| **2** | **Loom video not yet recorded** (Demo PRIMARY input per Ado 4/23) | Demo (25%) | Stage 7 — record 4/26 AM | 90-120 min |
| **3** | **Missing time/cost-saved metric in summary headline** (4.6 winner pattern: "weeks→20 min", "$30K saved"); we have "$58 / 32 min" buried in IPF segment | Impact (30%) — 4.6 winner shape | Stage 6 — surface "before / after" pair in opening of summary if natural; OR explicitly accept that rejection-rate IS our metric | 15-30 min |

**Honest non-priorities (not fixing):**
- Named end-user persona cold-open in Loom (could improve Demo, but cost = re-script; risk = stumble at recording 4/26 AM). Decision: skip.
- Most Creative / Keep Thinking secondary special-prize 1-sentence pitch. Decision: include in Stage 6 if word budget allows; otherwise skip — primary target is Best-MA.
- Wide-audience phrasing in unified summary (already in optional Broader Program Context paragraph). Decision: keep as-is.
- Claude Code window cut in Loom (Boris Cherny signal). Decision: skip — current cuts already show real CLI/terminal output.

---

## E. Submission scope freeze (no new analyses past this point)

T-29h. Scope is frozen. Stages 3-9 are **purely about packaging existing
evidence into the 3 submission deliverables** (video, repo URL, 100-200w
description). No new science added.

The single exception is Stage 6 task #1 (4-beat restructure), which is
*re-arranging existing words*, not new analysis.
