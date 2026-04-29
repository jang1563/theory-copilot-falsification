# Submission Form Draft

## ⚡ Final submission checklist (fill at form open time)

- [ ] Open the submission form: https://cerebralvalley.ai/e/built-with-4-7-hackathon/hackathon/submit
- [x] Demo video URL: **https://youtu.be/eB-gREA4zGI?si=8hjo-BhMtKqtN_lV** (YouTube, ≤3 min) — paste into submission form's "Demo video" field
- [ ] Select problem statement: **"Build From What You Know"**
- [ ] Select prize category (if field exists): **"Best Use of Claude Managed Agents"**
- [ ] Copy unified 200-word summary below into the description field
- [ ] Verify repo is public for review: `https://github.com/jang1563/lacuna-falsification` (can be made private after the event)
- [ ] Verify click-through demo does not require judges to enter their own Anthropic API key
- [ ] If the video uses free/stock assets, mention the source/license in README when linking the video; avoid unlicensed copyrighted assets/fonts
- [ ] Submit before **2026-04-26 20:00 ET**

---

**Verified 2026-04-24** against the official Cerebral Valley × Anthropic
[Built with Opus 4.7 participant resources page](https://cerebralvalley.ai/e/built-with-4-7-hackathon/details).
**Updated 2026-04-26 from Discord announcements / mod answers.**
**Submission form URL saved 2026-04-26**:
https://cerebralvalley.ai/e/built-with-4-7-hackathon/hackathon/submit
Per official rules, the actual submission requires **only three items**:

| Required item | Cap |
|---|---|
| Demo video link (YouTube / Loom / Google Drive) | **https://youtu.be/eB-gREA4zGI?si=8hjo-BhMtKqtN_lV** · 3 min max |
| Public GitHub repository | URL; public for review, may be private after event |
| Written description / summary | **100–200 words** |

Latest Discord clarifications:
- Submissions are due **2026-04-26 20:00 ET**.
- Demo video should show what was built and must not exceed 3 minutes.
- Judges should not need to enter their own Anthropic API key to test a click-through demo; set up a capped/limited demo environment if needed.
- Non-copyrighted / properly licensed stock or free assets are fine in the demo video. If the README includes the video link, mention the asset source/license there.
- Commercial fonts/assets should only be used when licensed / permitted; do not include copyrighted content without rights.

The actual submission form may include additional sub-fields (e.g.
prize-category select, problem-statement select, project name, team
info). The detailed sub-section drafts below (one-line pitch, Opus 4.7
usage, Managed Agents usage, prize-category justification) are
**inferred from the 4.6 hackathon precedent** and should be adapted at
submit time once the live form fields are visible:

| Inferred sub-section | Length cap (4.6 precedent) |
|---|---|
| Project name | 60 characters |
| One-line pitch | 140 characters |
| Project summary | 150 words |
| Claude Opus 4.7 usage | 150 words |
| Claude Managed Agents usage | 150 words |
| Prize category justification | 100 words |
| Team | name / role / contact |

**Problem statement alignment.** Per the official rules, two problem
statements are offered: *Build From What You Know* (domain expertise →
real-world workflow acceleration) and *Build For What's Next* (a
workflow that doesn't have a name yet). This submission targets
**Build From What You Know**: a biomedical postdoc's domain question
about confirmation bias in AI-for-Science → a verification harness
that any researcher can re-run on any disease CSV in 30 minutes.

**Judging criteria mapping** (Stage 1 async, 4/26-27, weights from
Discord update; Top 6 advance to final panel review on **2026-04-28
12:00 ET**):

| Criterion | Weight | Our load-bearing evidence |
|---|---|---|
| Impact (problem-statement fit, real-world potential) | 30% | **Platform generalization (2026-04-26, same classification-gate family + thresholds):** COAD (colon) 15/22 survivors (Δ+0.107 — highest of any run); LGG (brain glioma) 2/25 survivors (**AUROC 0.840** — TWIST1×MKI67 interaction term); LIHC (liver) 0/26 (designed negative, gate refuses correctly); KIRC (kidney) Stage 23/28 survivors. 7 disease contexts total. DIPG (pediatric brain cancer) generalization (7/15 Tier-2 supported, panobinostat-CED-MTX110 lead); Tier-1 prognostic-substrate gate on PBTA v15 (pediatric brain tumor atlas, n=192, 182 events) refuses to mint substrate-PASS on 0/4 — cross-disease falsification consistent with the original KIRC rejection layer; **IPF (lung fibrosis) Run #1 (2026-04-25): same engine, 1/5 SUPPORTED + 4 INSUFFICIENT, Skeptic caught two Advocate fabrications about prior trial design (RAINIER + Raghu 2017) — runtime demonstration of dual-role context isolation; $58.28, 32 min**; DatasetCard CLI = 30-min plug-in for any disease cohort |
| Demo (working, holds up live, cool to watch) | 25% | **[▶ YouTube demo](https://youtu.be/eB-gREA4zGI?si=8hjo-BhMtKqtN_lV)** (KIRC + DIPG + IPF tags), 24 reproducible plots, `make smoke` no-API health check + `make demo` guided Opus handoff, **2 Routine sessions with FAIL+PASS dual verdict** (static evidence in `results/live_evidence/`) |
| Opus 4.7 use (creative, beyond basic, surprises) | 25% | 180-call cross-model ablation (10/60 vs 0/60 PASS gap); **Opus 4.6 vs 4.7: 53.3%→66.7% (+13.3pp)** — 4.7 PASS 10/10 clean survivors, NEEDS_MORE_TESTS 10/10 stress-test, zero over-commitment; **prospective meta-calibration (PhI-1): Opus proposed 5 skeletons; 2 were testable on the current panel, 0/2 passed, and 2/2 failure modes were anticipated before the gate ran**; PhL-15 thinking-mode confound resolution; PhL-13 memorization audit (0/10 zero-shot retrieval); 1M-context cross-reasoning synthesis on full failure history |
| Depth & execution (push past first idea, real craft) | 20% | Self-killed our own H1 3-gene extension (PhL-1) on a separately pre-registered survival gate; ICP causal-invariance + anchor regression + Knockoffs + Westfall-Young + AUPRC stack; 107/107 current `make test` target + audit clean on package review; **IMmotion150 treatment-arm confound control: HR 1.361 (unadjusted) → 1.365 after controlling for immunotherapy vs VEGF-inhibitor arm — treatment-arm-adjusted prognostic signal persists** |

---

## Project name (60 char)

```
Lacuna: Falsification-First Biological Law Discovery
```
(52 chars)

---

## One-line pitch (140 char)

```
AI for Science that says no: 203 initial rejects, 9/30 after panel repair, and an own-output extension killed externally.
```
(124 chars.)

---

## Project Description (recommended final)

Lacuna is an AI-for-science system built to say no.

Most discovery tools are optimized to generate more hypotheses.
Lacuna focuses on the harder scientific step: rejecting weak ones
before they become convincing stories.

Built with Claude Code, Opus 4.7, and Claude Managed Agents, Lacuna
proposes candidate biological laws, then sends them through a fixed
five-test Python gate. The AI cannot change the rules after seeing the
result. Failed candidates are saved as useful scientific evidence, not
treated as wasted work.

On a public kidney cancer dataset with 505 patients, Lacuna rejected
203 of 203 initial candidate evaluations. After the loop diagnosed
panel absence and repaired only that cause, the same five-test gate
accepted 9 of 30 expanded-panel metastasis candidates. One simple
survivor, TOP2A - EPAS1, matched a known kidney-cancer growth program.
That was the point: this is not presented as a new biological discovery,
but as positive-control evidence that the system can rediscover known
truth under strict rules.

That survivor also passed a cross-endpoint prognostic replay in a
kidney cancer clinical-trial dataset. A later three-gene extension
proposed by the system failed the same external survival gate.

The broader goal is a repeatable scientific discipline: propose, test,
reject, remember, and only then interpret.

---

## Thoughts and feedback on building with Opus 4.7 (recommended final)

Opus 4.7 became most useful when I stopped using it as one general
answer engine and instead gave it separate scientific roles.

In each loop, Opus acts as:
1. Proposer: suggests compact candidate laws and writes down how they
   might fail before seeing results.
2. Skeptic: reviews only the test output, in a separate context, and
   decides whether the evidence is strong enough.
3. Interpreter: explains only the candidates that survive.

The most valuable behavior was not just creativity. It was restraint.
Opus 4.7 could propose ideas, accept strong evidence, reject weak
evidence, and write careful "what this does not mean" caveats.

I also ran repeated model comparisons. In one ablation, Sonnet 4.6
rejected every gate-passing candidate, while Opus 4.7 was better
aligned with the evidence. I would not frame that as a universal model
ranking, but for this workflow it mattered: the Skeptic role needs
calibrated judgment, not permanent doubt.

The biggest surprise was a lung fibrosis run where an isolated Skeptic
caught two false claims made by another agent. That made the
architecture feel real.

---

## Claude Managed Agents usage (recommended final)

Yes. Lacuna uses Claude Managed Agents to separate roles that should
not share the same reasoning context.

The Proposer suggests candidate biological laws. The Skeptic reviews
the evidence in a separate session and never sees the Proposer's
reasoning. The Interpreter explains only what survived. This separation
matters because science needs adversarial review, not one continuous
chain rationalizing its own ideas.

A deterministic Python gate sits between the agents. It runs the
actual tests and decides pass or fail. Managed Agents provide the
structure around that gate: separate sessions, structured handoffs,
durable event logs, and memory across runs.

I also used Claude Code Routines as the persistence layer. A routine
can receive a new equation, run the audit and falsification scripts,
and emit a structured verdict automatically.

The goal is not "AI discovers everything." The goal is a repeatable
discipline where hypotheses are proposed, tested, rejected, remembered,
and only then interpreted.

---

## Prize category justification (100 words, **106 counted** — ~6 over inferred cap; trim at paste time)

**Best use of Claude Managed Agents ($5K).** Public-beta-only Managed
Agents orchestration with isolated sessions: three live paths — B
(single-agent with full built-in toolset), A (sequential
three-session chain on real kidney cancer data, structured-JSON handoff), C
(metastasis FAIL+PASS dual verdict + stage FAIL+PASS — static evidence in
`results/live_evidence/`). Plus Memory public beta (integrated
2026-04-23 day-of): Skeptic writes rejection lessons; fresh sessions
read, quote, refine them; server-side persistence verified via raw
`/v1/memory_stores/*` API. Our own 3-gene extension was killed by
the separately pre-registered IMmotion150 survival replay.
**IPF Run #1: Skeptic caught two Advocate fabrications about prior
trial design — single-harness pipelines cannot catch this.**
Verification as working code.

---

## GitHub

```
https://github.com/jang1563/lacuna-falsification
```

Repo has been public since 2026-04-23 19:32 ET. Per Discord update,
public GitHub is required for review, but the repo may be made private
after the event.

---

## Demo video

```
Paste the final Loom / YouTube / Google Drive URL into the external submission form.
README links the interactive demo companion and discovery story for reviewers who click through from GitHub.
```

Discord constraints: upload to Loom, YouTube, or Google Drive; show
what was built; keep the video at or under **3:00**. A 1:37 video is
fine per mod answer as long as it does not exceed 3 minutes.

Canonical narration: `docs/loom_narration_final_90s.md` (333 words,
~143 s at 140 WPM / ~167 s at 120 WPM, **eight segments** incl. DIPG
+ IPF generalization tags, opens with problem-first "AI-for-science...
built to say no" hook and closes with the IPF dual-fabrication-catch
demonstration of four-role context isolation). Shot-list / rehearsal
assets: `docs/loom_script.md` (pre-narration shot list) +
`docs/loom_visual_cue_map.md` (8-segment asset cue map).

---

## Broader Program Context (optional, 90 words, 89 counted)

Opus 4.7 prototype of a larger program (NegBioDB + failure
network + rescue engine for prematurely-rejected clinical hypotheses).
Same four-role engine re-run on 15 H3 K27M DMG (pediatric brainstem cancer) rescue hypotheses
(locked-before-output git SHA 8a4ecc5): 7 supported, 7 mixed, 1
insufficient; top lead: panobinostat via CED (direct brain tumor drug delivery, 13/15
delivery class). Tier-1 prognostic-substrate gate then re-tested 4
candidates on PBTA v15 (pediatric brain tumor atlas, n=192 survival-evaluable, 182 events): 0
PASS, 2 FAIL, 2 UNDERPOWERED — intended falsifier output. **IPF (lung fibrosis) Run
#1: 1/5 supported, two Advocate fabrications caught (2026-04-25).**
Research-grade hypotheses; prospective validation required.
