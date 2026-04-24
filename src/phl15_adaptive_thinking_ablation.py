#!/usr/bin/env python3
"""PhL-15v2 — Thinking causal ablation on Opus 4.7 (RERUN, 2026-04-24).

Question: Is the thinking budget the MECHANISM behind Opus 4.7's Skeptic
calibration, or does Opus 4.7 remain calibrated even without any thinking?

Design: Opus 4.7 ONLY (single model isolates mechanism), 6 candidates,
10 repeats, 2 thinking modes:
  - Enabled: thinking={"type":"enabled","budget_tokens":8000}  ← same as E2
  - Disabled: thinking={"type":"disabled"}
= 2 × 6 × 10 = 120 API calls total (~$15-20).

RERUN RATIONALE (honest instrumentation fix):
  The original PhL-15 used thinking={"type":"adaptive"} which lets the model
  SKIP thinking when it deems the query simple. Inspection of sweep.jsonl v1
  shows thinking_length_chars=0 in ALL 120 calls and latency ~7s for BOTH
  modes — meaning adaptive mode silently fell back to no-thinking. The
  original experiment compared "no thinking vs no thinking" not
  "adaptive vs disabled." This rerun uses thinking={"type":"enabled",
  "budget_tokens":8000} — the same config E2 used — which forces thinking
  allocation and gives a clean comparison.

  The correct instrumentation also extracts thinking_tokens from
  usage.thinking_tokens (API-attested) rather than counting chars
  from block.thinking (unreliable with display="summarized").

Hypothesis: if thinking IS the mechanism, disabled Opus drops toward
Sonnet-like collapse (0/60 PASS in E2). If thinking is decorative, both
modes should look similar (still ~10/60 PASS).

Outputs:
  results/live_evidence/phl15_adaptive_thinking/sweep.jsonl  (per-call rows, APPENDED)
  results/live_evidence/phl15_adaptive_thinking/verdict.json (summary)
  results/live_evidence/phl15_adaptive_thinking/SUMMARY.md
  results/live_evidence/phl15_adaptive_thinking/mode_comparison.png
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "live_evidence" / "phl15_adaptive_thinking"
OUT.mkdir(parents=True, exist_ok=True)

SWEEP_PATH = OUT / "sweep.jsonl"
VERDICT_PATH = OUT / "verdict.json"
SUMMARY_PATH = OUT / "SUMMARY.md"
PLOT_PATH = OUT / "mode_comparison.png"

MODEL = "claude-opus-4-7"
# Opus 4.7 does NOT support thinking.type="enabled" (returns 400 error).
# The correct API for Opus 4.7 extended thinking is:
#   thinking={"type":"adaptive"} + output_config={"effort":"max"}
#
# v1 confound: adaptive without effort=max → model skips thinking (0 chars, 7s latency)
# v2 fix: two modes that differ only in thinking:
#   - "adaptive_max": adaptive + effort=max → forces thinking allocation
#   - "no_thinking": no thinking parameter → mirrors E2 Opus 4.7 fallback
#     (E2's Opus 4.7 calls all hit 400 on "enabled", retried without thinking)
MODES = {
    "adaptive_max": "adaptive_max",  # handled specially in _one_call
    "no_thinking": "no_thinking",    # no thinking parameter
}

# Reuse same 6 candidates from E2 ablation (pass/borderline/fail spread).
# These metrics are pre-computed by `track_a_model_ablation.py precompute`.
# If that file doesn't exist, fall back to embedded reference metrics.
METRICS_FILE = REPO / "results" / "ablation" / "candidate_metrics.json"
FALLBACK_METRICS = [
    {"id": "top2a_minus_epas1", "equation": "TOP2A - EPAS1",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.665, "ci_width": 0.122,
     "delta_baseline": 0.069, "delta_confound": None, "decoy_p": 0.001,
     "law_auc": 0.726, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "mki67_minus_epas1", "equation": "MKI67 - EPAS1",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.643, "ci_width": 0.130,
     "delta_baseline": 0.051, "delta_confound": None, "decoy_p": 0.003,
     "law_auc": 0.708, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "ca9_vegfa_minus_agxt", "equation": "log1p(CA9)+log1p(VEGFA)-log1p(AGXT)",
     "dataset": "TCGA-KIRC tumor_normal (n=609)", "passes": False,
     "perm_p": 0.0, "ci_lower": 0.975, "ci_width": 0.022,
     "delta_baseline": 0.019, "delta_confound": 0.008, "decoy_p": 0.0,
     "law_auc": 0.984, "baseline_auc": 0.965, "n_samples": 609, "n_disease": 537},
    {"id": "five_gene_stress", "equation": "MKI67 - (EPAS1 + LRP2 + PTGER3 + RPL13A)/4",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.654, "ci_width": 0.148,
     "delta_baseline": 0.069, "delta_confound": None, "decoy_p": 0.0,
     "law_auc": 0.726, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "actb_gapdh_null", "equation": "log1p(ACTB) - log1p(GAPDH)",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": False,
     "perm_p": 0.412, "ci_lower": 0.487, "ci_width": 0.095,
     "delta_baseline": -0.071, "delta_confound": None, "decoy_p": 0.538,
     "law_auc": 0.528, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "mki67_rpl13a_null", "equation": "log1p(MKI67) - log1p(RPL13A)",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": False,
     "perm_p": 0.0, "ci_lower": 0.592, "ci_width": 0.110,
     "delta_baseline": 0.021, "delta_confound": None, "decoy_p": 0.002,
     "law_auc": 0.647, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
]

SYSTEM = (REPO / "prompts" / "skeptic_review.md").read_text()

METRIC_RE = re.compile(
    r"(perm_p|perm_p_fdr|ci_lower|ci_width|delta_baseline|delta_confound|"
    r"decoy_p|law_auc|baseline_auc)\s*[=:≈]\s*[-+]?\d+\.\d+"
)


def _load_metrics() -> list[dict[str, Any]]:
    if METRICS_FILE.exists():
        data = json.loads(METRICS_FILE.read_text())
        if isinstance(data, list) and len(data) >= 6:
            return data[:6]
    return FALLBACK_METRICS


def _strip_json_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines)
    return s


def _one_call(client: Any, mode: str, thinking: Any, cand: dict,
              repeat: int) -> dict[str, Any]:
    import anthropic  # noqa: F401
    metrics_clean = {k: v for k, v in cand.items()
                     if k in ("perm_p", "ci_lower", "ci_width",
                              "delta_baseline", "delta_confound", "decoy_p",
                              "law_auc", "baseline_auc", "passes")}
    user_msg = (
        f"Candidate equation: {cand['equation']}\n"
        f"Dataset: {cand['dataset']}\n"
        f"Falsification metrics: {json.dumps(metrics_clean, default=str)}\n\n"
        "Output only the JSON described in the system prompt."
    )
    t0 = time.time()
    response_text = ""
    thinking_text = ""
    thinking_tokens = 0
    err = None
    usage = None
    try:
        # Build stream kwargs based on mode
        stream_kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": 16000,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": user_msg}],
        }
        if mode == "adaptive_max":
            stream_kwargs["thinking"] = {"type": "adaptive"}
            stream_kwargs["output_config"] = {"effort": "max"}
        # no_thinking mode: no thinking parameter at all
        with client.messages.stream(**stream_kwargs) as stream:
            final = stream.get_final_message()
        usage = getattr(final, "usage", None)
        # thinking_tokens is the authoritative signal (API-attested)
        thinking_tokens = int(getattr(usage, "thinking_tokens", 0) or 0) if usage else 0
        for block in final.content:
            t = getattr(block, "type", "")
            if t == "thinking":
                thinking_text += getattr(block, "thinking", "")
            elif t == "text":
                response_text += getattr(block, "text", "")
    except Exception as e:
        err = str(e)

    latency = time.time() - t0
    parsed = None
    try:
        parsed = json.loads(_strip_json_fences(response_text))
    except Exception:
        parsed = None

    if isinstance(parsed, dict):
        verdict = parsed.get("verdict", "UNPARSED")
        reason = parsed.get("reason", "")
    else:
        verdict = "UNPARSED"
        reason = response_text

    metric_cites = len(METRIC_RE.findall(reason))
    return {
        "mode": mode,
        "candidate_id": cand["id"],
        "repeat": repeat,
        "verdict": verdict,
        "reason_length_chars": len(reason),
        "thinking_length_chars": len(thinking_text),  # kept for compat
        "thinking_tokens": thinking_tokens,            # authoritative
        "metric_citations": metric_cites,
        "latency_sec": round(latency, 2),
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
        "err": err,
        "reason_snippet": reason[:240],
    }


def run_sweep(repeats: int = 10, workers: int = 6) -> None:
    import anthropic  # noqa
    client = anthropic.Anthropic()
    # Archive v1 data (adaptive/disabled) if present
    v1_archive = OUT / "sweep_v1_adaptive_disabled.jsonl"
    if SWEEP_PATH.exists() and not v1_archive.exists():
        existing = SWEEP_PATH.read_text()
        existing_rows = [json.loads(l) for l in existing.splitlines() if l]
        v1_rows = [r for r in existing_rows if r.get("mode") in ("adaptive",)]
        if v1_rows:
            v1_archive.write_text("\n".join(json.dumps(r) for r in existing_rows) + "\n")
            print(f"[PhL-15] archived v1 data to {v1_archive} ({len(existing_rows)} rows)")
        SWEEP_PATH.unlink()
    metrics = _load_metrics()
    tasks = []
    for mode_name in MODES:
        for cand in metrics:
            for r in range(repeats):
                tasks.append((mode_name, None, cand, r))  # thinking built in _one_call
    print(f"[PhL-15v2] {len(tasks)} calls: 2 modes × 6 candidates × {repeats} repeats")
    print(f"[PhL-15v2] Modes: {list(MODES.keys())}")
    print(f"[PhL-15v2] adaptive_max → thinking=adaptive + output_config.effort=max")
    print(f"[PhL-15v2] no_thinking → no thinking param (mirrors E2 Opus 4.7 fallback)")
    rows: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_one_call, client, m, th, c, r): (m, c['id'], r)
                   for (m, th, c, r) in tasks}
        for fut in as_completed(futures):
            row = fut.result()
            rows.append(row)
            done += 1
            if done % 10 == 0:
                think_tok = row.get("thinking_tokens", 0)
                print(f"  {done}/{len(tasks)} done (last: mode={row['mode']}, "
                      f"verdict={row['verdict']}, thinking_tokens={think_tok})", flush=True)
    with SWEEP_PATH.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-15v2] saved {SWEEP_PATH}")
    # Quick verification
    e_tok = [r.get("thinking_tokens", 0) for r in rows if r["mode"] == "enabled"]
    d_tok = [r.get("thinking_tokens", 0) for r in rows if r["mode"] == "disabled"]
    print(f"[PhL-15v2] enabled mean_thinking_tokens={sum(e_tok)/max(len(e_tok),1):.0f}")
    print(f"[PhL-15v2] disabled mean_thinking_tokens={sum(d_tok)/max(len(d_tok),1):.0f}")


def analyze() -> None:
    if not SWEEP_PATH.exists():
        print(f"ERROR: {SWEEP_PATH} not found. Run `run` first.", file=sys.stderr)
        sys.exit(1)
    rows = [json.loads(line) for line in SWEEP_PATH.read_text().splitlines() if line]
    # Filter to latest v2 rows (adaptive_max/no_thinking); skip v1 (adaptive/disabled) and v2a (enabled/disabled)
    v2_rows = [r for r in rows if r.get("mode") in ("adaptive_max", "no_thinking")]
    if not v2_rows:
        print("WARNING: no v2 rows found. Checking for earlier formats...")
        v2_rows = [r for r in rows if r.get("mode") in ("enabled", "disabled")]
    if not v2_rows:
        print("WARNING: falling back to all rows.")
        v2_rows = rows
    rows = v2_rows
    modes_present = sorted({r["mode"] for r in rows})
    # Tally per mode × candidate → verdict counts
    by_mode: dict[str, dict[str, int]] = {}
    gate_pass_ids = {"top2a_minus_epas1", "mki67_minus_epas1", "five_gene_stress"}
    dissent_by_mode: dict[str, dict] = {}
    citations_by_mode: dict[str, list[int]] = {m: [] for m in modes_present}
    thinking_tokens_by_mode: dict[str, list[int]] = {m: [] for m in modes_present}
    thinking_lens: dict[str, list[int]] = {m: [] for m in modes_present}
    for r in rows:
        m = r["mode"]
        v = r["verdict"]
        by_mode.setdefault(m, {"PASS": 0, "FAIL": 0, "NEEDS_MORE_TESTS": 0, "UNPARSED": 0, "total": 0})
        by_mode[m][v] = by_mode[m].get(v, 0) + 1
        by_mode[m]["total"] += 1
        citations_by_mode.setdefault(m, []).append(r.get("metric_citations", 0))
        thinking_tokens_by_mode.setdefault(m, []).append(r.get("thinking_tokens", 0))
        thinking_lens.setdefault(m, []).append(r.get("thinking_length_chars", 0))
        if r["candidate_id"] in gate_pass_ids:
            dissent_by_mode.setdefault(m, {"gate_pass_calls": 0, "dissent": 0})
            dissent_by_mode[m]["gate_pass_calls"] += 1
            if v in ("FAIL", "NEEDS_MORE_TESTS"):
                dissent_by_mode[m]["dissent"] += 1
    # Summary dict
    summary = {
        "model": MODEL,
        "version": "v2",
        "total_calls": len(rows),
        "by_mode": by_mode,
        "dissent_on_gate_pass": {
            m: {
                "rate": round(d["dissent"] / max(d["gate_pass_calls"], 1), 3),
                "n": d["gate_pass_calls"],
            } for m, d in dissent_by_mode.items()
        },
        "citations_mean_by_mode": {
            m: round(sum(v)/max(len(v),1), 2) for m, v in citations_by_mode.items()
        },
        "thinking_tokens_mean_by_mode": {
            m: round(sum(v)/max(len(v),1), 0) for m, v in thinking_tokens_by_mode.items()
        },
        "thinking_chars_mean_by_mode": {
            m: round(sum(v)/max(len(v),1), 0) for m, v in thinking_lens.items()
        },
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    VERDICT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"[PhL-15] verdict saved to {VERDICT_PATH}")
    print(json.dumps(summary, indent=2))
    _make_plot(summary)
    _write_summary_md(summary)


def _make_plot(summary: dict) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable — skipping plot")
        return
    modes = [m for m in ["enabled", "disabled"] if m in summary.get("by_mode", {})]
    if not modes:
        modes = list(summary.get("by_mode", {}).keys())[:2]
    verdicts = ["PASS", "FAIL", "NEEDS_MORE_TESTS", "UNPARSED"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    # Panel 1: verdict distribution per mode
    import numpy as np
    x = np.arange(len(verdicts))
    w = 0.35
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    for i, m in enumerate(modes):
        counts = [summary["by_mode"].get(m, {}).get(v, 0) for v in verdicts]
        ax1.bar(x + i*w - w/2, counts, w, label=f"thinking={m}",
                color=colors[i % len(colors)])
    ax1.set_xticks(x)
    ax1.set_xticklabels(verdicts)
    ax1.set_ylabel("Count (out of 60 per mode)")
    ax1.set_title("Opus 4.7 Skeptic verdict distribution by thinking mode")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)
    # Panel 2: dissent rate on gate-PASS + citation specificity
    dissent = summary["dissent_on_gate_pass"]
    cites = summary["citations_mean_by_mode"]
    labels = ["Dissent rate\n(on gate-PASS)", "Mean metric\ncitations"]
    m0, m1 = modes[0], modes[1] if len(modes) > 1 else "disabled"
    adaptive_vals = [dissent.get(m0, {}).get("rate", 0), cites.get(m0, 0)]
    disabled_vals = [dissent.get(m1, {}).get("rate", 0), cites.get(m1, 0)]
    x2 = np.arange(len(labels))
    ax2.bar(x2 - w/2, adaptive_vals, w, label="adaptive", color="#1f77b4")
    ax2.bar(x2 + w/2, disabled_vals, w, label="disabled", color="#ff7f0e")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels)
    ax2.set_title("Calibration proxies by thinking mode")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    fig.suptitle("PhL-15 · Thinking causal ablation (Opus 4.7: adaptive_max vs no_thinking)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PhL-15] plot saved: {PLOT_PATH}")


def _write_summary_md(summary: dict) -> None:
    md = ["# PhL-15v2 — Thinking causal ablation on Opus 4.7 (rerun 2026-04-24)",
          "",
          "**Question:** is a thinking budget the *mechanism* behind Opus 4.7's Skeptic calibration,",
          "or does Opus remain calibrated even without any thinking?",
          "",
          "## Original v1 confound (honest)",
          "",
          "The original PhL-15 (v1) used `thinking={'type':'adaptive'}` which lets the model",
          "**skip thinking** for simple queries. All 120 v1 calls: thinking_length_chars=0, latency ~7s",
          "for BOTH modes — compared 'no thinking vs no thinking.' An intermediate v2a attempt used",
          "`thinking={'type':'enabled','budget_tokens':8000}` which returns 400 on Opus 4.7 (not supported).",
          "**Key E2 finding (critical context):** E2's Opus 4.7 calls also received 400 errors on",
          "`enabled` thinking and silently fell back to NO thinking — so E2's 10/60 PASS was achieved",
          "WITHOUT thinking. Sonnet 4.6 and Haiku 4.5 DID run with thinking (23s vs 16s latency).",
          "E2 comparison was: Opus 4.7 (no thinking) vs Sonnet/Haiku (with thinking). Opus won.",
          "This final v2 design compares Opus 4.7 WITH vs WITHOUT thinking to isolate the mechanism.",
          "",
          "## Design (v2 final)",
          "", "- Opus 4.7 only (single model isolates mechanism)",
          "- 6 candidates (same as E2 ablation, pass/borderline/fail spread)",
          "- 10 repeats × 2 modes = **120 API calls**",
          "- Modes:",
          "  - `adaptive_max`: `thinking={'type':'adaptive'}` + `output_config={'effort':'max'}`",
          "    (Opus 4.7 correct thinking API; effort=max forces allocation even for simpler queries)",
          "  - `no_thinking`: no thinking parameter (mirrors E2 Opus 4.7 fallback: 10/60 PASS baseline)",
          "- Thinking verification: `usage.thinking_tokens` (API-attested)",
          "", "## Result",
          ""]
    md.append("| Mode | PASS | FAIL | NEEDS_MORE_TESTS | UNPARSED |")
    md.append("|---|---|---|---|---|")
    for m in ("adaptive_max", "no_thinking"):
        by = summary["by_mode"].get(m, {})
        md.append(f"| `{m}` | {by.get('PASS',0)} | {by.get('FAIL',0)} | "
                  f"{by.get('NEEDS_MORE_TESTS',0)} | {by.get('UNPARSED',0)} |")
    md.append("")
    md.append("**Dissent rate on gate-PASS candidates** (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound):")
    md.append("")
    for m, d in summary["dissent_on_gate_pass"].items():
        md.append(f"- `{m}`: {d['rate']*100:.1f}% dissent ({d['n']} gate-PASS calls)")
    md.append("")
    md.append("**Mean metric citations per response**:")
    md.append("")
    for m, c in summary["citations_mean_by_mode"].items():
        md.append(f"- `{m}`: {c:.2f}")
    md.append("")
    md.append("**Mean thinking tokens (API-attested, `usage.thinking_tokens`)**:")
    md.append("")
    for m, c in summary.get("thinking_tokens_mean_by_mode", {}).items():
        md.append(f"- `{m}`: {int(c):,}")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    e_pass = summary["by_mode"].get("adaptive_max", {}).get("PASS", 0)
    d_pass = summary["by_mode"].get("no_thinking", {}).get("PASS", 0)
    e_diss = summary["dissent_on_gate_pass"].get("adaptive_max", {}).get("rate", 0)
    d_diss = summary["dissent_on_gate_pass"].get("no_thinking", {}).get("rate", 0)
    e_think = summary.get("thinking_tokens_mean_by_mode", {}).get("adaptive_max", 0)
    d_think = summary.get("thinking_tokens_mean_by_mode", {}).get("no_thinking", 0)
    # Verify thinking actually ran
    think_ran = e_think > 100  # >100 thinking tokens = thinking was active
    if not think_ran:
        interp = (f"**INSTRUMENTATION WARNING**: adaptive_max mode shows only {int(e_think)} "
                  "mean thinking tokens — thinking may not have activated despite effort=max. "
                  "Results below may not represent a clean with-vs-without-thinking comparison.")
    elif abs(e_pass - d_pass) <= 2 and abs(e_diss - d_diss) < 0.1:
        interp = (f"**Honest null on thinking as mechanism.** Verdict distribution is similar "
                  f"with (adaptive_max: {e_pass}/60 PASS, {e_diss:.1%} dissent) and without "
                  f"(no_thinking: {d_pass}/60 PASS, {d_diss:.1%} dissent) thinking. "
                  "Combined with E2 finding (Opus 4.7 ran WITHOUT thinking due to enabled→400 "
                  "error fallback, achieving 10/60 PASS vs Sonnet 0/60 PASS WITH thinking): "
                  "**Opus 4.7's Skeptic calibration is a pre-training/RLHF property, not a "
                  "thinking-budget effect.** The model-vs-model gap is the primary finding. "
                  "why_opus_4_7.md framing: 'Opus 4.7 base calibration holds the stance' "
                  "(accurate regardless of thinking mode).")
    elif e_pass > d_pass + 2:
        interp = (f"**Thinking augments base calibration.** Opus 4.7 with adaptive_max thinking "
                  f"achieves {e_pass}/60 PASS vs {d_pass}/60 without thinking. "
                  "Note: E2 baseline (Opus without thinking) was 10/60 — so adaptive_max adds "
                  f"{e_pass - 10} additional PASSes. Thinking enhances but is not the sole source "
                  "of Opus's Skeptic calibration advantage.")
    else:
        interp = (f"**Unexpected direction.** No-thinking ({d_pass}/60 PASS) ≥ "
                  f"adaptive_max ({e_pass}/60 PASS). Report both numbers honestly; "
                  "thinking may be introducing overcaution.")
    md.append(interp)
    md.append("")
    md.append("## Run history comparison (honest instrumentation log)")
    md.append("")
    md.append("| Run | Mode pair | Thinking status | Latency | PASS count |")
    md.append("|---|---|---|---|---|")
    md.append("| v1 (2026-04-24) | adaptive vs disabled | adaptive silently skipped (0 tokens, 7.1s) | 7.1s ≈ 7.7s | 0/60 vs 0/60 |")
    md.append("| v2a (2026-04-24) | enabled vs disabled | enabled→400 error on Opus 4.7 (not supported) | N/A | 0/60 UNPARSED |")
    md.append(f"| v2 final (2026-04-24) | adaptive_max vs no_thinking | {int(e_think)} tokens vs {int(d_think)} tokens | see jsonl | {e_pass}/60 vs {d_pass}/60 |")
    md.append("| **E2 context** | Opus 4.7 in E2 (enabled→fallback) | enabled→400→fallback NO thinking | 8.0s | **10/60 PASS** |")
    md.append("")
    md.append(f"**Raw data**: `sweep.jsonl` ({summary['total_calls']} v2 rows, modes: adaptive_max/no_thinking)")
    md.append(f"**v1 archive**: `sweep_v1_adaptive_disabled.jsonl` (120 rows, adaptive/disabled)")
    md.append("")
    md.append("**Reproduce**:")
    md.append("```bash")
    md.append("source ~/.api_keys")
    md.append("PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py run")
    md.append("PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py analyze")
    md.append("```")
    SUMMARY_PATH.write_text("\n".join(md))
    print(f"[PhL-15] SUMMARY.md saved: {SUMMARY_PATH}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").add_argument("--repeats", type=int, default=10)
    sub.add_parser("analyze")
    args, extra = p.parse_known_args()
    if args.cmd == "run":
        repeats = 10
        for i, a in enumerate(extra):
            if a == "--repeats" and i+1 < len(extra):
                repeats = int(extra[i+1])
        run_sweep(repeats=repeats)
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
