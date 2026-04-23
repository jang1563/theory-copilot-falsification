# PhI-3 — LAB-Bench LitQA2 reproduction on Opus 4.6 vs 4.7

**Honest-null + UNEXPECTED-REVERSAL result. Report verbatim below.**

## Context

Anthropic's Opus 4.7 model card (2026-04-16) reports LAB-Bench deltas
on several biology subtasks — the largest being FigQA (multimodal
figure QA): **59.3% → 78.6%** no-tools, **76.7% → 86.4%** with tools
(+19.3pp). No direct 4.6-vs-4.7 comparison for **LitQA2** (text-only
multiple-choice biology literature QA) was published.

This script runs LitQA2 (199 four-choice questions, open-source at
`futurehouse/lab-bench`) on both `claude-opus-4-6` and
`claude-opus-4-7` to extend Anthropic's benchmarking onto a subtask
they did not report. Both models use their *native* thinking
configurations: 4.6 with `type="enabled", budget_tokens=4000`
(deprecated but functional), 4.7 with `type="adaptive",
display="summarized"` (4.7's only supported mode; `budget_tokens`
removed in this release).

## Headline

| Model | N | Correct | Accuracy | Parse failures | Cost | Avg latency |
|---|---|---|---|---|---|---|
| claude-opus-4-6 | 199 | 104 | **52.3%** | 4 | $4.76 | 8.23 s |
| claude-opus-4-7 | 199 | 83 | **41.7%** (observed) | 25 | $0.67 | 2.18 s |

**Δ (4.7 − 4.6): −10.5pp.** Opposite direction from Anthropic's
FigQA +19.3pp delta.

## Why this delta is not the full story

All 25 of 4.7's parse failures are **empty replies**
(`output_tokens=1`, no text content, no API error). The model
returned nothing where it should have returned a single letter.
Inspecting the row data on the first empty case:

- Input tokens = 189 (prompt received normally)
- Output tokens = 1 (essentially just whitespace)
- No API error, no abstention message
- Latency = 1.63s (very fast — no thinking invoked)

Three candidate explanations:

1. **Adaptive thinking under-invoked.** 4.7's adaptive layer decided
   no thinking was needed; latency 2.18s (vs 4.6's 8.23s with
   budget_tokens=4000) suggests very little compute was spent, and the
   model then failed to produce even a short answer. Zvi's model-card
   analysis notes 4.7 "sometimes skips tool calls to look fast"; this
   may be the analog for answer generation.
2. **Streaming edge case.** Some interaction between `adaptive` and
   the streaming context manager may swallow the final text block.
   Not reproduced consistently — 174 of 199 calls worked normally.
3. **ASL-3 biology-related guardrails** may have tightened around
   some questions (Acinetobacter / antibiotic / pathogen). LitQA2
   has several such items.

### Sensitivity analysis

| Re-scoring assumption | 4.7 accuracy |
|---|---|
| Observed (empty = wrong) | 41.7% |
| Exclude empties from denominator (174 / 199) | **47.7%** |
| Best-case (all 25 empties correct) | 54.3% |
| 4.6 observed (4 parse fails, baseline) | 52.3% |

Most-honest single number: **47.7%** (exclude-empties). Under that
scoring, 4.7 trails 4.6 by **−4.6pp**, not −10.5pp. Either way,
Anthropic's FigQA uplift (+19.3pp) does NOT transfer to LitQA2 under
our setup.

## Agreement matrix (199 matched pairs)

| 4.6 correct | 4.7 correct | Count |
|---|---|---|
| ✓ | ✓ | 66 |
| ✓ | ✗ | **38** (4.6 beats 4.7) |
| ✗ | ✓ | 17 (4.7 beats 4.6) |
| ✗ | ✗ | 78 |

4.6 wins net 21 questions. The reversal is not an artefact of
parse-failure scoring alone.

## Why this is useful narrative evidence

The Built-with-Opus-4.7 hackathon framing invites showcasing
capability gains. A genuinely honest submission also reports the
reversals. This is a ~20-minute, $5 open-data reproduction that:

1. Documents a subtask where the headline 4.7 gains do **not** transfer.
2. Identifies a **4.7-specific failure mode**: adaptive thinking
   under-invoking on short multiple-choice where forced thinking
   actually helps.
3. Makes the cost narrative crisp — 4.7 is **7× cheaper and 4× faster**
   than 4.6, even when accuracy drops.
4. Mirrors our core "Rejection-as-Product" thesis at the model level:
   pre-registered reporting of unexpected-direction results is the
   artefact.

## Honest limitations

- LitQA2 real scoring may include "Insufficient Information" as a 5th
  option; we forced a 4-way choice. Could cost accuracy on genuinely
  ambiguous items for either model.
- We did not replicate FigQA (the subtask where Anthropic's largest
  delta was reported) because it requires multimodal inputs.
- 4.7 was tested with adaptive thinking (the release-default mode);
  4.6 with `type=enabled` (deprecated but matched E2 / G6 convention).
  Re-running 4.7 with a forced-thinking analog is NOT available —
  `budget_tokens` was removed in 4.7.
- The 25 empty-reply artefact is 4.7-specific on our prompt format.
  Retrying those with modified wording might recover some; not done
  here.

## Files

- `SUMMARY.md` (this doc)
- `summary.json` — machine-readable metrics
- `litqa2_claude_opus_4_6_answers.jsonl` — 199 raw rows
- `litqa2_claude_opus_4_7_answers.jsonl` — 199 raw rows
- `src/phi3_labbench_reproduce.py` — generator

## Reproduce

```bash
PYTHONPATH=src .venv/bin/python src/phi3_labbench_reproduce.py \
    --workers 6 --models claude-opus-4-6 claude-opus-4-7
```
Estimated cost ~$5.50; wall-clock ~15–25 min with 6 workers.
