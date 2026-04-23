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
Verification-as-skill: Opus 4.7 rediscovers TOP2A-EPAS1, a gate kills 194/204 candidates — then kills our own H1-loop extension too.
```
(140 chars.)

---

## Project summary (150 words, 145 counted)

Theory Copilot is a verification-as-shipped-skill biological discovery
loop powered by Opus 4.7 + Managed Agents (public beta 2026-04-08).
Opus plays Proposer, Skeptic, Interpreter around a deterministic 5-test
Python gate that runs before any LLM judgement. The gate rejected 194
of 204 candidates (95.1%) across 11 task-panel combinations — including
two explicit negative controls. The simplest surviving law is `TOP2A −
EPAS1`, the published ccA-vs-ccB ccRCC subtype axis, rediscovered on
TCGA-KIRC (AUROC 0.726) and replicated on IMmotion150 Phase-2 (n=263,
log-rank p=0.00027, Cox HR 1.36, C-index 0.601, robust to 3-arm
treatment adjustment). When our own H1 LLM-SR loop later proposed a
3-gene extension adding SLC22A8, the same gate killed it on cross-cohort
replay (PhL-1, pre-reg committed before the analysis ran — C-index
dropped to 0.566, HR to 1.16). Pre-registrations are git-tracked YAMLs.
The 194 rejections are the product, not an appendix.

---

## Claude Opus 4.7 usage (150 words, 147 counted)

Four Opus 4.7 calls per loop, all with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. `budget_tokens` is removed on Opus
4.7 (400 error); `effort` is the control. (1) Scientist proposes
three-to-five compact law families and writes the ex-ante skeptic
test for each, before any fit. (2) The pre-registered test is then
executed by plain Python, not by Opus. (3) Skeptic reviews the
specific metric pattern (`perm_p = 0.049` is weaker than `0.001`;
`ci_lower = 0.61` is marginal) and emits PASS / FAIL /
NEEDS_MORE_TESTS with a written justification. (4) Interpreter
writes the mechanism hypothesis and, critically, the "what this is
not" paragraph. Extended thinking is what keeps the Skeptic turn
from collapsing into rubber-stamp agreement with the Proposer turn
— smaller models collapse; Opus 4.7 holds the tension.

---

## Claude Managed Agents usage (150 words, 141 counted)

Three-agent architecture. Proposer = Opus 4.7 with adaptive
thinking. Searcher = local PySR, no API. Falsifier = Opus 4.7 with
adaptive thinking. Clean role separation, structured
PASS / FAIL / NEEDS_MORE_TESTS output. Two delegation paths:

- **Path B — public beta, live-verified.** Single Managed Agent with
  `agent_toolset_20260401`; drives Night-2 sweep, Night-3
  falsification, Night-4 replay through structured tool calls. End-
  to-end trace committed at
  `results/live_evidence/04_managed_agents_e2e.log` (`agents.create`
  → `environments.create` → `sessions.create` → `stream` → `send`
  → `session.status_idle`).
- **Path A — sequential falsification chain (public-beta only).** Three
  Managed Agents sessions (Proposer / Searcher / Skeptic) in a shared
  environment with structured-JSON handoff. Per the 2026-04-23 hackathon
  fairness rule, Agent Teams (`callable_agents`) research-preview features
  are not used; the orchestrator-with-`callable_agents` code path is
  retained as an architectural reference guarded by an env flag.
- **Path C — Claude Code Routines (separate product; research preview).**
  `POST /v1/claude_code/routines/{trig_id}/fire` with per-routine bearer
  token (`src/theory_copilot/routines_client.py`). `--use-routine` flag
  swaps the local watch-dir loop for real cloud-triggered execution.
  GitHub triggers: `pull_request` + `release` (no `push`).

**Durability primitives:** `persist_session_events` pages through
`sessions.events.list` to JSONL; `replay_session_from_log` re-injects
user-origin events into a different session — concrete brain/body
decoupling, not just prose.

All paths expose `{session_id, agent_id, output, status}`. Path A adds
`delegation_mode`; Path C adds `routine_session_url`.

---

## Prize category justification (100 words, 98 counted)

**Keep Thinking ($5K).** Extended thinking is load-bearing on
the Skeptic turn: that role has to hold the proposal in context
and argue against it without the tokens that generated the proposal
collapsing the dissent. Smaller models collapse; Opus 4.7 holds.

**Best Claude Managed Agents ($5K).** Public-beta-only compliant per
the 2026-04-23 hackathon fairness rule. Three delegation paths: Path B
(single-agent `agent_toolset_20260401`, live), Path A (sequential
falsification chain across three Path B sessions — not Agent Teams),
Path C (Claude Code Routines `/fire` with local fallback). The Skeptic
runs with isolated subagent context (Boris's architecture pattern);
the 5-test gate is a shareable skill; `make audit` is the Stop hook
that refuses to mark a task complete without verification. We killed
our own H1 LLM-SR loop's 3-gene extension on cross-cohort replay
(PhL-1) — the verification loop Thariq Shihipar flagged as an open
problem, shipped as a skill. Brain/body decoupling as working
primitives, not prose. <60s demo-able.

---

## GitHub

```
https://github.com/jang1563/theory-copilot-falsification
```

Repo is currently private; flipped to public immediately before
submission cutoff per plan.

---

## Demo video

```
[to be pasted on 4/26 morning after Loom render]
```

Script: `docs/loom_script.md` (90 s, six cuts, single terminal +
browser, no overlays). Fallback GIF path documented in the same file
for upload failures.

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
