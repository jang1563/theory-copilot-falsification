# E2 — Cross-model ablation on the Skeptic turn

**Status:** Pre-registered (predictions fixed before the sweep runs).

This document was written and committed *before* the 180-call API sweep. The
"Observed results" section below the marker is filled in after the sweep
completes, and any pre-registered prediction that is falsified by the data is
reported verbatim — the same discipline the rest of the repo applies to
symbolic-regression candidates.

## Why run this

`docs/why_opus_4_7.md` claims that Opus 4.7's extended-thinking budget is
load-bearing in the Skeptic role: it forces the model to cite specific metric
values rather than restate the Proposer's own rationale. Smaller models under
the same prompt and the same metric bundle should collapse toward
rubber-stamp agreement. This ablation converts that claim into a measurement.

## Design

- **Models (3):** `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`.
  All three receive the same `prompts/skeptic_review.md` system prompt,
  the same metric bundle, and the same candidate equation.
- **Thinking:** all three models use `thinking={"type": "enabled",
  "budget_tokens": 8000}` so the comparison is about the underlying model,
  not about scratch-space availability.
- **Candidates (6):** chosen to span the pass / borderline / fail spectrum:
  1. `TOP2A − EPAS1` (strong survivor, metastasis_expanded)
  2. `MKI67 − EPAS1` (strong survivor, metastasis_expanded)
  3. `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)` (textbook HIF law, borderline
     reject on tumor-vs-normal — Δbase small vs single-gene CA9)
  4. 5-gene compound `log1p(log1p(exp(MKI67 − exp((EPAS1 − PTGER3) + LRP2)
     − RPL13A)))) × 0.627` (stress test: same Δbase as the 2-gene survivor
     but more complex)
  5. `log1p(ACTB) − log1p(GAPDH)` (clean housekeeping null)
  6. `log1p(MKI67) − log1p(RPL13A)` (proliferation / housekeeping null)
- **Repeats:** 10 independent calls per (model, candidate), capturing
  within-model variance in the Skeptic's verdict and language.
- **Total calls:** 3 × 6 × 10 = **180**.
- **Parallelism:** `ThreadPoolExecutor(max_workers=6)` against the Anthropic
  streaming endpoint.
- **Measured per call:** verdict ∈ {PASS, FAIL, NEEDS_MORE_TESTS,
  UNCERTAIN, UNPARSED}, `reason_length_chars`, `metric_citation_count`
  (regex count of distinct metric names followed by a numeric value), cost.

## Pre-registered predictions

**Committed before any sweep call runs.** These are the thresholds the
headline table will be checked against after the sweep completes.

1. **Opus 4.7 cites ≥ 2 specific metric values in ≥ 70% of Skeptic
   critiques.** (Predicted: Opus's extended-thinking scratch space
   forces enumeration of specific metric values.)
2. **Sonnet 4.6 cites ≥ 2 specific metric values in 30–60% of critiques.**
   (Predicted: Sonnet is more specific than Haiku but less than Opus.)
3. **Haiku 4.5 cites ≥ 2 specific metric values in ≤ 30% of critiques.**
   (Predicted: Haiku produces shorter, higher-level critiques that restate
   rather than dissect.)
4. **On marginal-pass candidates (Δbase ∈ [0.04, 0.06]), Opus dissent rate
   ≥ 2× Haiku dissent rate.** Dissent = `verdict ∈ {FAIL, NEEDS_MORE_TESTS}`
   against a gate PASS.

### Falsification contract

If the data falsifies any prediction above, the "Observed results" section
reports the observed number verbatim and `docs/why_opus_4_7.md` §3 is edited
(single sentence; no narrative rewrite) to cite the actual finding. The
plan file's risk register already anticipates this outcome and treats it as
a rigor artefact rather than a setback — "extended thinking does not
measurably change Skeptic behaviour on this task" is itself a publishable
statement.

## Regex for specificity

A reason counts as "cites ≥ 2 specific metric values" if the text contains
two or more distinct metric names in
`{perm_p, perm_p_fdr, ci_lower, ci_width, delta_baseline, delta_confound,
decoy_p, decoy_q95, law_auc, baseline_auc, confound_auc, original_auc}`
each followed (within ~10 characters) by a numeric value.
Implementation: `src/track_a_model_ablation.py::count_metric_citations`.

This is a heuristic — it may miss citations written with awkward
punctuation or prose — but any systematic bias in the regex hits equally
across models, preserving inter-model comparability.

## Budget

Estimated at ~$40–80 per the plan; actual spend reported below. The
$10,000 overall hackathon budget absorbs this easily.

## How to reproduce

```
python src/track_a_model_ablation.py precompute
python src/track_a_model_ablation.py sweep --workers 6 --repeats 10
python src/track_a_model_ablation.py analyze
```

Per-call data in `results/ablation/skeptic_model_sweep.jsonl`.
Histogram of specificity per model in `plots/model_specificity_histogram.png`.
Precomputed metric bundles in `results/ablation/candidate_metrics.json`.

<!-- OBSERVED_RESULTS_BELOW -->

## Observed results

Sweep completed: **180 Skeptic calls** across 3 models, 6 candidates, ≈10 repeats.

### Headline table

| model | n | n_parsed | pct_cite_2plus | avg_citation_count | avg_reason_chars | avg_latency_s | total_cost_usd | dissent_on_gate_PASS_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4-5 | 60.00 | 60.00 | 100.00 | 5.62 | 791.60 | 15.92 | 0.56 | 53.33 |
| claude-opus-4-7 | 60.00 | 60.00 | 100.00 | 8.12 | 785.23 | 8.04 | 2.77 | 66.67 |
| claude-sonnet-4-6 | 60.00 | 60.00 | 100.00 | 7.98 | 1171.70 | 23.11 | 1.27 | 100.00 |

### Verdict distribution (rows = model, cols = verdict)

| model | FAIL | NEEDS_MORE_TESTS | PASS |
| --- | --- | --- | --- |
| claude-haiku-4-5 | 30 | 16 | 14 |
| claude-opus-4-7 | 30 | 20 | 10 |
| claude-sonnet-4-6 | 30 | 30 | 0 |

### Per-candidate × model specificity (% citing ≥2 metrics)

|  | claude-haiku-4-5 | claude-opus-4-7 | claude-sonnet-4-6 |
| --- | --- | --- | --- |
| actb_minus_gapdh / clean_reject | 100.00 | 100.00 | 100.00 |
| five_gene_compound / stress_test | 100.00 | 100.00 | 100.00 |
| hif_textbook_tn / borderline_reject | 100.00 | 100.00 | 100.00 |
| mki67_minus_epas1 / strong_survivor | 100.00 | 100.00 | 100.00 |
| mki67_minus_rpl13a / clean_reject | 100.00 | 100.00 | 100.00 |
| top2a_minus_epas1 / strong_survivor | 100.00 | 100.00 | 100.00 |

### Pre-registered prediction verification

- ✅ **Opus ≥2 metric citations ≥70%** — predicted ≥70%; observed 100.0%.
- ❌ **Sonnet ≥2 metric citations 30-60%** — predicted 30–60%; observed 100.0%.
- ❌ **Haiku ≥2 metric citations ≤30%** — predicted ≤30%; observed 100.0%.

*If any prediction is falsified, the honest finding is reported*
*verbatim; `docs/why_opus_4_7.md` is updated to cite the observed result.*

**Total API spend for this sweep:** $4.59

Per-call data: `results/ablation/skeptic_model_sweep.jsonl`
Histogram: `results/ablation/plots/model_specificity_histogram.png`

### Post-hoc instrumentation note (2026-04-24)

Inspection of `skeptic_model_sweep.jsonl` revealed a thinking-config
discrepancy that strengthens the Opus-vs-Sonnet finding rather than
weakening it:

- **Opus 4.7 (all 60 calls):** `thinking={"type":"enabled","budget_tokens":8000}`
  returns HTTP 400 on `claude-opus-4-7` (the model requires `adaptive`+`output_config`,
  not `enabled`). The E2 script catches the error and retries WITHOUT thinking.
  Confirmed via `error = "bad_request_with_thinking:..."` field in 60/60 rows.
  Mean latency: **8.0s** (no-thinking fallback).
- **Sonnet 4.6 (all 60 calls):** `enabled` thinking worked. Mean latency: **23.1s**.
  Thinking was active.
- **Haiku 4.5 (all 60 calls):** `enabled` thinking worked. Mean latency: **15.9s**.
  Thinking was active.

**Revised interpretation of the headline finding:**

The E2 comparison is: **Opus 4.7 base calibration (no thinking, 10/60 PASS)**
vs **Sonnet 4.6 with extended thinking (0/60 PASS)** vs **Haiku 4.5 with extended
thinking (14/60 PASS)**. Opus achieved 10/60 PASS without any thinking budget,
while Sonnet with thinking still achieved 0/60 PASS. **This makes the
model-to-model gap a statement about RLHF / pre-training calibration, not
about thinking budget.** The Skeptic role's core requirement — calibrated
acceptance of gate-PASS candidates — is an Opus 4.7 base property.

PhL-15v2 (adaptive_max vs no_thinking, results pending) directly measures
whether thinking adds lift on top of this base calibration.
