# Parallel sub-agent skeptic consensus — metastasis_expanded

Three Claude sub-agents — Opus 4.7, Sonnet 4.6, Haiku 4.5 — reviewed the 9 survivors in parallel (DRY-RUN, synthetic votes).

> **Dry-run mode.** No API calls were made. Votes are deterministic functions of the gate metrics, encoding the expected cross-model behaviour (Opus stricter on marginals; Haiku rubber-stamps). For live results, set `ANTHROPIC_API_KEY` and run `make skeptic-review LIVE=1`.

## Per-candidate consensus

| # | equation | Δbase | perm p | ci_lower | consensus | breakdown |
|---|---|---|---|---|---|---|
| 0 | `-0.08599428 * ((EPAS1 + -1.5503553) - TOP2A)` | 0.069 | 0.0000 | 0.664 | PASS ✓ | PASS:3 |
| 1 | `log1p(log1p(exp(TOP2A - EPAS1)) * 0.21792223)` | 0.069 | 0.0000 | 0.670 | PASS ✓ | PASS:3 |
| 2 | `log1p(log1p(0.24403314) * log1p(exp(TOP2A - EPAS1)))` | 0.069 | 0.0000 | 0.661 | PASS ✓ | PASS:3 |
| 3 | `0.16861118 * log1p(exp(MKI67 - EPAS1))` | 0.051 | 0.0000 | 0.643 | NEEDS_MORE_TESTS  | NEEDS_MORE_TESTS:2, PASS:1 |
| 4 | `log1p(log1p(exp(MKI67 - exp(((EPAS1 - PTGER3) + LRP2) - R...` | 0.069 | 0.0000 | 0.654 | PASS  | NEEDS_MORE_TESTS:1, PASS:2 |
| 5 | `log1p(log1p(log1p(exp(MKI67 - exp((EPAS1 - (PTGER3 + RPL1...` | 0.069 | 0.0000 | 0.670 | PASS ✓ | PASS:3 |
| 6 | `log1p(log1p(exp(MKI67 - EPAS1)) * 0.2149816)` | 0.051 | 0.0000 | 0.652 | NEEDS_MORE_TESTS  | NEEDS_MORE_TESTS:2, PASS:1 |
| 7 | `(0.09855198 * (TOP2A - EPAS1)) + 0.16059029` | 0.069 | 0.0000 | 0.658 | PASS  | NEEDS_MORE_TESTS:1, PASS:2 |
| 8 | `log1p(log1p(exp(TOP2A - EPAS1)) * 0.21692236)` | 0.069 | 0.0000 | 0.665 | PASS ✓ | PASS:3 |

## Per-model verdict distribution

| model | PASS | FAIL | NEEDS_MORE_TESTS | UNCERTAIN | UNPARSED |
|---|---|---|---|---|---|
| `claude-opus-4-7` | 5 | 0 | 4 | 0 | 0 |
| `claude-sonnet-4-6` | 7 | 0 | 2 | 0 | 0 |
| `claude-haiku-4-5` | 9 | 0 | 0 | 0 | 0 |

## How to read this table

Each survivor is reviewed by three independent Claude sub-agents in the Skeptic role. A unanimous PASS is the strongest consensus signal; a majority-PASS with one dissent is still informative — the dissenting model's `reason` field in `consensus.json` names which metric triggered the dissent. A majority-NEEDS_MORE_TESTS indicates the gate-passing candidate is marginal enough that smaller downstream models are not satisfied.

Boris Cherny at the 2026-04-22 *Built with Opus 4.7* session flagged parallel sub-agent delegation as an Opus 4.7 strength. `make skeptic-review` is that pattern applied at the scientific falsification layer: three adversaries, one consensus, reconciled deterministically.

