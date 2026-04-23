# G6 pre-registration — Opus 4.6 vs 4.7 calibration transfer test

**Written 2026-04-23, BEFORE viewing the sweep analysis output.**

## Setting

60 Opus 4.6 calls completed (6 candidates × 10 repeats) matching the
existing E2 60 Opus 4.7 calls on the same candidates and prompt.
Miscalibration = (FAIL on gate=PASS) + (PASS on gate=FAIL). `NEEDS_MORE_TESTS`
treated as non-miscalibrated abstention.

Anthropic published delta (Opus 4.7 model card, 2026-04-16):
**abstention on unknowns 61% → 36% incorrect** (adaptive thinking).

## Decision rule (committed before analyze step runs)

```
IF |miscal(4.6) - miscal(4.7)| >= 5pp AND 95% CIs do not overlap:
    → CONFIRMED: Anthropic's published delta detectable on this
      biology skeptic task at n=60.
ELIF difference < 5pp OR 95% CIs overlap:
    → EXPLORATORY NULL: At n=60 on 6 candidates (2 true borderline cases),
      we do not have statistical power to detect a 25pp published delta.
      Null here does NOT disprove Anthropic's claim; it confines our
      demonstrable claim to "pipeline-level external verification works
      regardless of which frontier model powers the Skeptic role".
ELIF miscal(4.6) < miscal(4.7):
    → REVERSAL: 4.7 shows *worse* calibration than 4.6 on this task.
      Report verbatim; investigate whether ASL-3 biology de-emphasis
      (Mythos civilian framing) is a contributing factor.
```

## Sample size caveat (explicit)

Anthropic's 61→36% is measured across many thousands of
unknown-answer questions in MMLU-style benchmarks. Our test uses
60 calls per model on 6 candidates, with only 2 borderline/stress
candidates × 10 repeats = 20 differentiating data points per model.
A 25pp effect is in principle detectable at this n, but 95% CIs
will be wide (~±20pp). This is an exploratory transfer test, not a
confirmatory powered trial.

## Narrative impact per outcome

| Outcome | Primary narrative ("Rejection-as-Product") | Secondary narrative ("4.7 overhang") |
|---|---|---|
| Confirmed | Unchanged | Strengthened — Anthropic's claim shown to transfer |
| Exploratory null | Unchanged | Softened to "complementary": model-level calibration and pipeline-level external verification are independent contributions |
| Reversal | Unchanged | Used as honest caveat: biology task may not exercise the same capability Anthropic benchmarked |

In all three cases the primary "Rejection-as-Product" thesis
(the 5-test gate rejects 194/204 regardless of which frontier
model is in the Skeptic seat) is independent of the outcome.

## Commit discipline

This PREREG.md is committed before `python src/g6_calibration_4_6_vs_4_7.py analyze`
runs. Any edit to this file after commit is visible in `git log -p`.
