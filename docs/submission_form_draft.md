# Submission Form Draft

Target constraints per the Cerebral Valley × Anthropic submission form
(inferred from the 4.6 hackathon form structure; confirm at submit time):

| Field | Length cap |
|---|---|
| Project name | 60 characters |
| One-line pitch | 140 characters |
| Project summary | 150 words |
| Claude Opus 4.7 usage | 150 words |
| Claude Managed Agents usage | 150 words |
| Prize category justification | 100 words |
| GitHub link | URL |
| Demo video link | URL |
| Team | name / role / contact |

---

## Project name (60 char)

```
Theory Copilot: Falsification-Aware Biological Law Discovery
```
(60 chars exactly.)

---

## One-line pitch (140 char)

```
Opus 4.7 rediscovers TOP2A-EPAS1; 5-test gate kills 194/203; separately-preregistered survival replay then kills our own H1 extension.
```
(140 chars.)

---

## Project summary (150 words, 145 counted)

Theory Copilot is a verification-first biological discovery loop
powered by Opus 4.7 + Managed Agents (public beta 2026-04-08). Opus
plays Proposer, Skeptic, Interpreter around a deterministic 5-test
Python gate that runs before any LLM judgement. The 5-test
classification gate rejected 194 of 203 candidate evaluations across
11 task-panel combinations — 9 survivors on metastasis_expanded
(confound leg null for this task; 4 active legs + FDR/decoy). The
simplest surviving law is `TOP2A − EPAS1`, the published ccA-vs-ccB
ccRCC subtype axis, rediscovered on TCGA-KIRC (AUROC 0.726). Under
three separately pre-registered survival kill tests on IMmotion150
Phase-2 (n=263), the 2-gene form passes (log-rank p=0.0003, Cox
HR=1.36, C-index 0.601, robust to treatment adjustment). Our own H1
LLM-SR loop then proposed a 3-gene extension (adding SLC22A8); the
same IMmotion150 survival gate killed it (PhL-1, C-index dropped to
0.566). Pre-registrations are git-tracked YAMLs.

---

## Claude Opus 4.7 usage (150 words, 125 counted)

Four Opus 4.7 calls per loop with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. (1) Proposer emits 3-5 compact law
families and the ex-ante skeptic test for each, before any fit. (2)
The test is executed by plain Python, not Opus. (3) Skeptic reviews
the specific metric pattern (`perm_p=0.049` is weaker than `0.001`;
`ci_lower=0.61` is marginal) and emits PASS / FAIL / NEEDS_MORE_TESTS.
(4) Interpreter writes the mechanism hypothesis and the "what this is
not" paragraph. Adaptive thinking keeps the Skeptic turn from
collapsing across the dual-role prompt: in our 180-call ablation,
Sonnet 4.6 emits **0 PASS of 60** on gate-PASS candidates (full dissent
collapse); Opus 4.7 emits **10 of 60**. **PhL-13 memorization audit:
Opus 4.7 does not retrieve TOP2A−EPAS1 zero-shot (0/10 repeats) —
refutes the LLM-SRBench memorization concern.**

---

## Claude Managed Agents usage (150 words, 119 counted)

**Verification-isolated Managed Agents orchestration.** Three separate
public-beta sessions (Proposer / Skeptic / Interpreter = Opus 4.7;
Searcher = local PySR) with separate context windows and structured-
JSON handoff — the Skeptic never sees the Proposer's reasoning tokens,
so it cannot rationalise its own proposal into passing. Public-beta
compliant per the 2026-04-23 hackathon fairness rule; research-preview
`callable_agents` disabled.

- **Path B (live).** Single-agent `agent_toolset_20260401`; end-to-end
  `agents.create → environments.create → sessions.create → stream →
  send → status_idle` at `04_managed_agents_e2e.log`.
- **Path A (live, PhL-9 + PhL-9v2 on real TCGA-KIRC).** Sequential
  three-session chain, structured-JSON handoff,
  `delegation_mode=sequential_fallback`, 706 s wall.
- **Path C (live, PhL-8).** `/fire` HTTP 200 +
  https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM

**Durability.** `persist_session_events` pages `sessions.events.list`
to JSONL; `replay_session_from_log` re-injects user-origin events into
a different session.

---

## Prize category justification (100 words, 98 counted)

**Best Claude Managed Agents ($5K).** Public-beta-only. Three paths:
B (live), A (live PhL-9 sequential 3-session + **v2 on real TCGA-KIRC**
PhL-9v2), C (live PhL-8 `/fire` 200 OK).
Plus **Memory public beta (integrated 2026-04-23, day-of)**: Skeptic
writes rejection lessons to a memory store; fresh sessions read,
quote, and **refine** prior lessons verbatim. PhL-10 + PhL-12 grow
the chain to 8 entries and show the ceiling-effect rule generalizing
across cancers (KIRC→LUAD→PRAD/KLK3). Server-side persistence verified
via raw `/v1/memory_stores/*` API. Our own H1 LLM-SR extension was
killed by the separately-pre-registered IMmotion150 survival replay
gate (PhL-1, NOT the TCGA classification gate). Verification as working
code.

---

## GitHub

```
https://github.com/jang1563/theory-copilot-falsification
```

Repo has been public since 2026-04-23 19:32 ET.

---

## Demo video

```
[to be pasted on 4/26 morning after Loom render]
```

Canonical narration: `docs/loom_narration_final_90s.md` (178 words,
76-89 s, six segments, opens with biomedical-researcher confirmation-
bias hook). Shot-list / rehearsal assets: `docs/loom_script.md`
(pre-narration shot list, 6 cuts, single terminal + browser, no
overlays). Fallback GIF path documented for upload failures.

---

## Broader Program Context (optional, 90 words)

This hackathon artefact is the Opus 4.7-centered proof-of-concept of
a larger research program — **NegBioDB**, a structured database
aggregating ~32.8 million confirmed negative biomedical results
(drug-target inactives, failed clinical trials, protein non-
interactions, non-essential genes, benign variants) paired with
benchmarks for how publication bias propagates into ML/LLM
predictions. Theory Copilot operationalises NegBioDB's core thesis
— that falsification is the expensive, neglected half of
scientific inference — as a runnable Opus 4.7 loop on real
cancer-genomics data.
