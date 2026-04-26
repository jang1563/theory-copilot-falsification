# PhL-15v2 — Thinking causal ablation on Opus 4.7 (rerun 2026-04-24)

**Question:** is a thinking budget the *mechanism* behind Opus 4.7's Skeptic calibration,
or does Opus remain calibrated even without any thinking?

## Original v1 confound (honest)

The original PhL-15 (v1) used `thinking={'type':'adaptive'}` which lets the model
**skip thinking** for simple queries. All 120 v1 calls: thinking_length_chars=0, latency ~7s
for BOTH modes — compared 'no thinking vs no thinking.' An intermediate v2a attempt used
`thinking={'type':'enabled','budget_tokens':8000}` which returns 400 on Opus 4.7 (not supported).
**Key E2 finding (critical context):** E2's Opus 4.7 calls also received 400 errors on
`enabled` thinking and silently fell back to NO thinking — so E2's 10/60 PASS was achieved
WITHOUT thinking. Sonnet 4.6 and Haiku 4.5 DID run with thinking (23s vs 16s latency).
E2 comparison was: Opus 4.7 (no thinking) vs Sonnet/Haiku (with thinking). Opus won.
This final v2 design compares Opus 4.7 WITH vs WITHOUT thinking to isolate the mechanism.

## Design (v2 final)

- Opus 4.7 only (single model isolates mechanism)
- 6 candidates (same as E2 ablation, pass/borderline/fail spread)
- 10 repeats × 2 modes = **120 API calls**
- Modes:
  - `adaptive_max`: `thinking={'type':'adaptive'}` + `output_config={'effort':'max'}`
    (Opus 4.7 correct thinking API; effort=max forces allocation even for simpler queries)
  - `no_thinking`: no thinking parameter (mirrors E2 Opus 4.7 fallback: 10/60 PASS baseline)
- Thinking verification: `usage.thinking_tokens` (API-attested)

## Result

| Mode | PASS | FAIL | NEEDS_MORE_TESTS | UNPARSED |
|---|---|---|---|---|
| `adaptive_max` | 0 | 30 | 30 | 0 |
| `no_thinking` | 0 | 30 | 30 | 0 |

**Dissent rate on gate-PASS candidates** (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound):

- `adaptive_max`: 100.0% dissent (30 gate-PASS calls)
- `no_thinking`: 100.0% dissent (30 gate-PASS calls)

**Mean metric citations per response**:

- `adaptive_max`: 6.30
- `no_thinking`: 6.35

**Mean thinking tokens (API-attested, `usage.thinking_tokens`)**:

- `adaptive_max`: 0
- `no_thinking`: 0

## Interpretation

**INSTRUMENTATION WARNING**: adaptive_max mode shows only 0 mean thinking tokens — thinking may not have activated despite effort=max. Results below may not represent a clean with-vs-without-thinking comparison.

## Run history comparison (honest instrumentation log)

| Run | Mode pair | Thinking status | Latency | PASS count |
|---|---|---|---|---|
| v1 (2026-04-24) | adaptive vs disabled | adaptive silently skipped (0 tokens, 7.1s) | 7.1s ≈ 7.7s | 0/60 vs 0/60 |
| v2a (2026-04-24) | enabled vs disabled | enabled→400 error on Opus 4.7 (not supported) | N/A | 0/60 UNPARSED |
| v2 final (2026-04-24) | adaptive_max vs no_thinking | 0 tokens vs 0 tokens | see jsonl | 0/60 vs 0/60 |
| **E2 context** | Opus 4.7 in E2 (enabled→fallback) | enabled→400→fallback NO thinking | 8.0s | **10/60 PASS** |

**Raw data**: `sweep.jsonl` (120 v2 rows, modes: adaptive_max/no_thinking)
**v1 archive**: `sweep_v1_adaptive_disabled.jsonl` (120 rows, adaptive/disabled)

**Reproduce**:
```bash
export ANTHROPIC_API_KEY=<your-key>
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py run
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py analyze
```