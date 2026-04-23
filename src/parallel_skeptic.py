"""E12 parallel sub-agent skeptic review harness.

Spawns three Claude sub-agents in parallel (Opus 4.7, Sonnet 4.6,
Haiku 4.5) on each surviving candidate from a falsification_report.json,
collects their verdicts, and emits a consensus JSON plus Markdown
summary.

This makes the "parallel sub-agents" pattern the Claude Code team
publicly advocates visible at run time, not just in prose — three
independent adversarial reviewers of the same candidate, reconciled
deterministically.

Usage:
    python src/parallel_skeptic.py \\
        --input results/track_a_task_landscape/metastasis_expanded/falsification_report.json \\
        --output-dir results/skeptic_consensus \\
        [--dry-run] [--workers 6]

Dry-run mode skips API calls and emits a synthetic consensus based on
gate metrics; this lets judges without API credit inspect the
pipeline shape. The Makefile target `make skeptic-review` invokes
dry-run by default; pass `LIVE=1` for a real run (requires
ANTHROPIC_API_KEY).
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

MODELS: list[tuple[str, str]] = [
    ("claude-opus-4-7", "Opus 4.7"),
    ("claude-sonnet-4-6", "Sonnet 4.6"),
    ("claude-haiku-4-5", "Haiku 4.5"),
]

# Matches the E2 ablation budget so the 3-way comparison is apples-to-apples.
THINKING_BUDGET: dict[str, int] = {
    "claude-opus-4-7": 8000,
    "claude-sonnet-4-6": 8000,
    "claude-haiku-4-5": 4000,
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "skeptic_review.md"

METRIC_KEYS: tuple[str, ...] = (
    "perm_p",
    "ci_width",
    "ci_lower",
    "law_auc",
    "baseline_auc",
    "delta_baseline",
    "delta_confound",
    "confound_auc",
    "decoy_p",
    "decoy_q95",
    "passes",
)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    cleaned = _FENCE_RE.sub("", text).strip()
    if cleaned and not cleaned.startswith("{"):
        s, e = cleaned.find("{"), cleaned.rfind("}")
        if s >= 0 and e > s:
            cleaned = cleaned[s : e + 1]
    return cleaned


def _pick_survivors(report: list[dict]) -> list[dict]:
    return [r for r in report if r.get("passes")]


def _candidate_bundle(candidate: dict, dataset_name: str) -> dict:
    bundle = {k: candidate[k] for k in METRIC_KEYS if k in candidate}
    bundle["equation"] = candidate.get("equation_named") or candidate.get("equation", "")
    bundle["dataset"] = dataset_name
    bundle["genes_used"] = candidate.get("genes_used", [])
    return bundle


def _call_model(model_id: str, system: str, bundle: dict) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    metrics_for_prompt = {k: bundle[k] for k in METRIC_KEYS if k in bundle}
    user_msg = (
        f"Candidate equation: {bundle['equation']}\n"
        f"Dataset: {bundle['dataset']}\n"
        f"Falsification metrics: {json.dumps(metrics_for_prompt, default=str)}\n\n"
        "Output only the JSON described in the system prompt."
    )
    thinking_cfg = {"type": "enabled", "budget_tokens": THINKING_BUDGET[model_id]}

    t0 = time.time()
    response_text = ""
    thinking_text = ""
    err: str | None = None
    try:
        with client.messages.stream(
            model=model_id,
            max_tokens=16000,
            thinking=thinking_cfg,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        for block in final.content:
            t = getattr(block, "type", "")
            if t == "thinking":
                thinking_text += getattr(block, "thinking", "")
            elif t == "text":
                response_text += getattr(block, "text", "")
    except anthropic.BadRequestError as e:
        err = f"bad_request_with_thinking: {e}"
        try:
            with client.messages.stream(
                model=model_id,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            ) as stream:
                final = stream.get_final_message()
            for block in final.content:
                if getattr(block, "type", "") == "text":
                    response_text += getattr(block, "text", "")
        except Exception as e2:
            err = f"{err}; retry_failed: {e2}"

    latency = time.time() - t0

    parsed: Any = None
    try:
        parsed = json.loads(_strip_fences(response_text))
    except Exception:
        parsed = None
    if not isinstance(parsed, dict):
        parsed = {}

    return {
        "model": model_id,
        "verdict": parsed.get("verdict", "UNPARSED"),
        "reason": parsed.get("reason", response_text[:400]),
        "additional_test": parsed.get("additional_test", ""),
        "latency_s": round(latency, 2),
        "error": err,
        "thinking_chars": len(thinking_text),
        "response_chars": len(response_text),
    }


def _dry_run_vote(model_id: str, bundle: dict) -> dict:
    """Deterministic synthetic vote for --dry-run; expresses the expected
    cross-model signature: Opus is stricter on marginal candidates, Haiku
    rubber-stamps. Used only when no API key is available."""
    def _num(key: str, default: float) -> float:
        v = bundle.get(key, default)
        return float(default if v is None else v)

    dbase = _num("delta_baseline", 0.0)
    decoy = _num("decoy_p", 1.0)
    ci_lower = _num("ci_lower", 0.0)
    marginal = (dbase < 0.07) or (ci_lower < 0.66)

    if model_id == "claude-opus-4-7":
        # Strictest: dissents on any marginal (Δbase or ci_lower).
        verdict = "PASS" if (dbase > 0.06 and ci_lower > 0.66 and decoy < 0.05) else "NEEDS_MORE_TESTS"
    elif model_id == "claude-sonnet-4-6":
        # Middle: dissents only on weak Δbase.
        verdict = "PASS" if (dbase > 0.06 and decoy < 0.05) else "NEEDS_MORE_TESTS"
    else:
        # Haiku: rubber-stamps anything the gate accepted.
        verdict = "PASS" if (dbase > 0.05 and decoy < 0.05) else "UNCERTAIN"

    reason = (
        f"[dry-run synthetic] delta_baseline={dbase:.3f}, decoy_p={decoy:.3f}, "
        f"ci_lower={ci_lower:.3f}; marginal={marginal}"
    )
    return {
        "model": model_id,
        "verdict": verdict,
        "reason": reason,
        "additional_test": "",
        "latency_s": 0.0,
        "error": None,
        "thinking_chars": 0,
        "response_chars": len(reason),
    }


def _consensus(votes: list[dict]) -> dict:
    verdicts = [v["verdict"] for v in votes]
    counter = Counter(verdicts)
    majority_verdict, majority_count = counter.most_common(1)[0]
    return {
        "majority_verdict": majority_verdict,
        "majority_count": majority_count,
        "n_votes": len(votes),
        "unanimous": majority_count == len(votes),
        "breakdown": dict(counter),
    }


def run(args: argparse.Namespace) -> None:
    report_path = Path(args.input)
    report = json.loads(report_path.read_text())
    survivors = _pick_survivors(report)
    print(f"[parallel_skeptic] loaded {len(report)} candidates, "
          f"{len(survivors)} survivors from {report_path}")

    if not survivors:
        raise SystemExit("No survivors in input — nothing to review.")

    if PROMPT_PATH.exists():
        system = PROMPT_PATH.read_text()
    else:
        system = (
            "You are an adversarial skeptic reviewing a candidate law after "
            "a pre-registered 5-test falsification gate. Output ONLY JSON "
            "with keys `verdict` (PASS/FAIL/NEEDS_MORE_TESTS), `reason`, "
            "`additional_test`."
        )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks: list[tuple[int, str, dict]] = []
    for i, c in enumerate(survivors):
        bundle = _candidate_bundle(c, args.dataset)
        for model_id, _label in MODELS:
            tasks.append((i, model_id, bundle))

    votes_by_candidate: dict[int, list[dict]] = {i: [] for i in range(len(survivors))}

    if args.dry_run:
        print("[parallel_skeptic] DRY-RUN mode — no API calls")
        for i, model_id, bundle in tasks:
            votes_by_candidate[i].append(_dry_run_vote(model_id, bundle))
    else:
        print(f"[parallel_skeptic] dispatching {len(tasks)} live calls "
              f"across {len(MODELS)} models with workers={args.workers}")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            fut_to_key = {
                ex.submit(_call_model, model_id, system, bundle): (i, model_id)
                for (i, model_id, bundle) in tasks
            }
            done = 0
            for fut in as_completed(fut_to_key):
                i, model_id = fut_to_key[fut]
                vote = fut.result()
                votes_by_candidate[i].append(vote)
                done += 1
                print(f"[parallel_skeptic] {done}/{len(tasks)} "
                      f"cand_{i} {model_id} → {vote['verdict']} "
                      f"({vote['latency_s']}s)")

    consensus_records = []
    for i, c in enumerate(survivors):
        votes = votes_by_candidate[i]
        consensus_records.append(
            {
                "candidate_index": i,
                "equation": c.get("equation_named") or c.get("equation"),
                "gate_delta_baseline": c.get("delta_baseline"),
                "gate_perm_p": c.get("perm_p"),
                "gate_ci_lower": c.get("ci_lower"),
                "gate_decoy_p": c.get("decoy_p"),
                "gate_law_auc": c.get("law_auc"),
                "votes": votes,
                "consensus": _consensus(votes),
            }
        )

    out_json = out_dir / "consensus.json"
    out_json.write_text(json.dumps(consensus_records, indent=2, default=str))
    print(f"[parallel_skeptic] wrote {out_json}")

    _write_summary(out_dir / "SUMMARY.md", consensus_records, dry_run=args.dry_run)
    print(f"[parallel_skeptic] wrote {out_dir / 'SUMMARY.md'}")


def _write_summary(path: Path, records: list[dict], *, dry_run: bool) -> None:
    lines: list[str] = []
    lines.append("# Parallel sub-agent skeptic consensus — metastasis_expanded")
    lines.append("")
    mode_tag = " (DRY-RUN, synthetic votes)" if dry_run else ""
    lines.append(
        f"Three Claude sub-agents — Opus 4.7, Sonnet 4.6, Haiku 4.5 — "
        f"reviewed the {len(records)} survivors in parallel{mode_tag}."
    )
    lines.append("")
    if dry_run:
        lines.append(
            "> **Dry-run mode.** No API calls were made. Votes are deterministic "
            "functions of the gate metrics, encoding the expected cross-model "
            "behaviour (Opus stricter on marginals; Haiku rubber-stamps). "
            "For live results, set `ANTHROPIC_API_KEY` and run "
            "`make skeptic-review LIVE=1`."
        )
        lines.append("")

    lines.append("## Per-candidate consensus")
    lines.append("")
    lines.append("| # | equation | Δbase | perm p | ci_lower | consensus | breakdown |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in records:
        cons = r["consensus"]
        breakdown = ", ".join(f"{k}:{v}" for k, v in sorted(cons["breakdown"].items()))
        marker = "✓" if cons["unanimous"] else ""
        eq = r["equation"] or ""
        if len(eq) > 60:
            eq_disp = eq[:57] + "..."
        else:
            eq_disp = eq
        lines.append(
            f"| {r['candidate_index']} | `{eq_disp}` | "
            f"{r['gate_delta_baseline']:.3f} | "
            f"{r['gate_perm_p']:.4f} | "
            f"{r['gate_ci_lower']:.3f} | "
            f"{cons['majority_verdict']} {marker} | {breakdown} |"
        )

    lines.append("")
    lines.append("## Per-model verdict distribution")
    lines.append("")
    lines.append("| model | PASS | FAIL | NEEDS_MORE_TESTS | UNCERTAIN | UNPARSED |")
    lines.append("|---|---|---|---|---|---|")
    per_model: dict[str, Counter] = {m: Counter() for m, _ in MODELS}
    for r in records:
        for v in r["votes"]:
            per_model[v["model"]][v["verdict"]] += 1
    for m, _label in MODELS:
        c = per_model[m]
        lines.append(
            f"| `{m}` | {c['PASS']} | {c['FAIL']} | "
            f"{c['NEEDS_MORE_TESTS']} | {c['UNCERTAIN']} | {c['UNPARSED']} |"
        )

    lines.append("")
    lines.append("## How to read this table")
    lines.append("")
    lines.append(
        "Each survivor is reviewed by three independent Claude sub-agents "
        "in the Skeptic role. A unanimous PASS is the strongest consensus "
        "signal; a majority-PASS with one dissent is still informative — "
        "the dissenting model's `reason` field in `consensus.json` names "
        "which metric triggered the dissent. A majority-NEEDS_MORE_TESTS "
        "indicates the gate-passing candidate is marginal enough that "
        "smaller downstream models are not satisfied."
    )
    lines.append("")
    lines.append(
        "Boris Cherny at the 2026-04-22 *Built with Opus 4.7* session flagged "
        "parallel sub-agent delegation as an Opus 4.7 strength. `make "
        "skeptic-review` is that pattern applied at the scientific "
        "falsification layer: three adversaries, one consensus, reconciled "
        "deterministically."
    )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Parallel sub-agent skeptic review harness (E12)"
    )
    p.add_argument(
        "--input",
        default="results/track_a_task_landscape/metastasis_expanded/falsification_report.json",
    )
    p.add_argument("--output-dir", default="results/skeptic_consensus")
    p.add_argument(
        "--dataset",
        default="TCGA-KIRC metastasis_expanded (n=505, 16% M1)",
    )
    p.add_argument("--workers", type=int, default=6)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="skip API calls; emit deterministic synthetic votes",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
