#!/usr/bin/env python3
"""PhI-3 — LAB-Bench LitQA2 reproduction on Opus 4.7 vs 4.6.

Anthropic's Opus 4.7 model card (2026-04-16) reports LAB-Bench FigQA
deltas 59.3% → 78.6% (no-tools) and 76.7% → 86.4% (with tools) —
a +19.3pp jump on the figure-reasoning subtask. LAB-Bench is open
(Future-House, https://github.com/Future-House/LAB-Bench) but no
public third-party reproduction of the 4.7 delta exists, on FigQA
or any text subtask.

This script runs a text-only subtask (LitQA2, 199 multiple-choice
biology literature questions) on BOTH Opus 4.6 and Opus 4.7 and
reports the accuracy delta. Budget: ~$15–25, wall clock ~15–25 min
with 4 parallel workers.

Outputs:
  results/overhang/phi3_labbench/litqa2_{4_6,4_7}_answers.jsonl
  results/overhang/phi3_labbench/SUMMARY.md
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "overhang" / "phi3_labbench"
OUT.mkdir(parents=True, exist_ok=True)

# Model IDs
MODEL_46 = "claude-opus-4-6"
MODEL_47 = "claude-opus-4-7"

SYSTEM_PROMPT = (
    "You are an expert biology researcher answering multiple-choice "
    "questions from scientific literature. Read the question carefully, "
    "consider each option, and respond with ONLY the letter (A, B, C, or D) "
    "of the most likely correct answer. Do not add explanation or other text."
)


def _load_litqa2():
    from datasets import load_dataset
    ds = load_dataset("futurehouse/lab-bench", "LitQA2", split="train")
    return list(ds)


def _make_prompt(row, rng: random.Random) -> tuple[str, str]:
    """Build a 4-choice prompt, return (user_msg, correct_letter)."""
    q = row["question"]
    ideal = row["ideal"]
    distractors = row["distractors"]
    # Pick 3 distractors at random (many have 3 to 4)
    ds = list(distractors)
    if len(ds) > 3:
        ds = rng.sample(ds, 3)
    choices = [("correct", ideal)] + [("wrong", d) for d in ds]
    # Pad with placeholders if somehow less than 4 options
    while len(choices) < 4:
        choices.append(("wrong", f"None of the above ({len(choices)})"))
    rng.shuffle(choices)
    letters = ["A", "B", "C", "D"]
    correct_letter = letters[next(i for i, (tag, _) in enumerate(choices) if tag == "correct")]
    options_text = "\n".join(f"{letters[i]}) {text}" for i, (_, text) in enumerate(choices))
    user = (
        f"Question: {q}\n\n"
        f"Options:\n{options_text}\n\n"
        f"Respond with only the letter (A, B, C, or D)."
    )
    return user, correct_letter


def _parse_answer(text: str) -> str | None:
    """Extract the first A/B/C/D letter from the model's reply."""
    # Strict: first standalone A/B/C/D (avoid matching 'A' inside words)
    m = re.search(r"\b([ABCD])\b", text.strip()[:20].upper())
    if m:
        return m.group(1)
    m = re.search(r"([ABCD])", text.strip()[:20].upper())
    return m.group(1) if m else None


def _one_call(client, model: str, user_msg: str, correct: str, row_id: str,
              thinking_cfg: dict) -> dict:
    import anthropic
    t0 = time.time()
    reply = ""
    err = None
    in_tok = out_tok = 0
    # max_tokens must exceed thinking.budget_tokens for 4.6; keep generous
    max_out = max(6000, int(thinking_cfg.get("budget_tokens", 0) or 0) + 2000)
    try:
        kwargs = dict(
            model=model,
            max_tokens=max_out,
            thinking=thinking_cfg,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        with client.messages.stream(**kwargs) as stream:
            final = stream.get_final_message()
        for block in final.content:
            if block.type == "text":
                reply += block.text
        u = getattr(final, "usage", None)
        if u:
            in_tok = int(getattr(u, "input_tokens", 0) or 0)
            out_tok = int(getattr(u, "output_tokens", 0) or 0)
    except anthropic.BadRequestError as e:
        # Fallback without thinking
        err = f"bad_request: {e}"
        try:
            with client.messages.stream(
                model=model, max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            ) as stream:
                final = stream.get_final_message()
            for block in final.content:
                if block.type == "text":
                    reply += block.text
            u = getattr(final, "usage", None)
            if u:
                in_tok = int(getattr(u, "input_tokens", 0) or 0)
                out_tok = int(getattr(u, "output_tokens", 0) or 0)
        except Exception as e2:
            err = f"{err} | fallback also failed: {e2}"
    except Exception as e:
        err = f"other: {e}"

    answer = _parse_answer(reply) if reply else None
    correct_flag = (answer == correct)
    # Rough cost estimate for Opus (input $15/M, output $75/M as of 2026-04)
    cost = in_tok * 15e-6 + out_tok * 75e-6
    return {
        "row_id": row_id,
        "model": model,
        "reply": reply[:200],
        "parsed_answer": answer,
        "correct_answer": correct,
        "is_correct": correct_flag,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": cost,
        "latency_sec": round(time.time() - t0, 2),
        "error": err,
    }


def run_for_model(model: str, rows: list, workers: int,
                  thinking_cfg: dict, seed: int = 42) -> list[dict]:
    import anthropic
    client = anthropic.Anthropic()
    rng = random.Random(seed)
    # Pre-build prompts (shuffled deterministically by seed)
    jobs = []
    for row in rows:
        # Each row gets its own rng with id-based seed for reproducibility
        row_rng = random.Random(f"{seed}-{row['id']}")
        user_msg, correct = _make_prompt(row, row_rng)
        jobs.append((row["id"], user_msg, correct))

    out_rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_one_call, client, model, u, c, rid, thinking_cfg): rid
            for (rid, u, c) in jobs
        }
        for i, f in enumerate(as_completed(futures), 1):
            r = f.result()
            out_rows.append(r)
            if i % 20 == 0 or i == len(jobs):
                correct_so_far = sum(1 for x in out_rows if x["is_correct"])
                print(f"  [{model}] {i}/{len(jobs)} — accuracy-so-far {correct_so_far}/{i} = {100*correct_so_far/i:.1f}%")
    return out_rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=0, help="0 = all 199 questions; else limit")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--models", nargs="+", default=[MODEL_46, MODEL_47])
    args = p.parse_args()

    print("[PhI-3] loading LitQA2 dataset ...")
    rows = _load_litqa2()
    if args.n > 0:
        rows = rows[: args.n]
    print(f"[PhI-3] {len(rows)} questions, models: {args.models}, workers: {args.workers}")

    thinking_cfgs = {
        MODEL_46: {"type": "enabled", "budget_tokens": 4000},
        MODEL_47: {"type": "adaptive", "display": "summarized"},
    }

    for m in args.models:
        out_path = OUT / f"litqa2_{m.replace('-','_').replace('.','_')}_answers.jsonl"
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"[PhI-3] {m}: skipping, {out_path} already exists (remove to rerun)")
            continue
        print(f"[PhI-3] running {m} ...")
        results = run_for_model(
            m, rows, workers=args.workers,
            thinking_cfg=thinking_cfgs.get(m, {"type": "adaptive", "display": "summarized"}),
        )
        with out_path.open("w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        n = len(results)
        correct = sum(1 for r in results if r["is_correct"])
        cost = sum(r["cost_usd"] for r in results)
        print(f"[PhI-3] {m} done: {correct}/{n} = {100*correct/n:.1f}% accuracy, ~${cost:.2f}")

    # Analyse
    summary = {}
    for m in args.models:
        path = OUT / f"litqa2_{m.replace('-','_').replace('.','_')}_answers.jsonl"
        if not path.exists():
            continue
        rs = [json.loads(l) for l in path.open()]
        n = len(rs)
        correct = sum(1 for r in rs if r["is_correct"])
        errors = [r for r in rs if r["error"]]
        summary[m] = {
            "n": n,
            "correct": correct,
            "accuracy_pct": 100 * correct / n if n else 0,
            "parse_failures": sum(1 for r in rs if r["parsed_answer"] is None),
            "api_errors": len(errors),
            "total_cost_usd": sum(r["cost_usd"] for r in rs),
            "avg_latency_sec": sum(r["latency_sec"] for r in rs) / n if n else 0,
        }

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))

    # Human-readable SUMMARY
    lines = [
        "# PhI-3 — LAB-Bench LitQA2 reproduction on Opus 4.6 vs 4.7",
        "",
        "Subtask: LitQA2 (199 multiple-choice biology literature questions).",
        "Dataset: https://huggingface.co/datasets/futurehouse/lab-bench",
        "",
        "## Accuracy",
        "",
        "| Model | N | Correct | Accuracy | Parse fails | Cost |",
        "|---|---|---|---|---|---|",
    ]
    for m, d in summary.items():
        lines.append(
            f"| {m} | {d['n']} | {d['correct']} | {d['accuracy_pct']:.1f}% | "
            f"{d['parse_failures']} | ${d['total_cost_usd']:.2f} |"
        )

    if len(summary) == 2:
        models = list(summary.keys())
        d = summary[models[-1]]["accuracy_pct"] - summary[models[0]]["accuracy_pct"]
        lines += [
            "",
            f"**Delta ({models[-1]} vs {models[0]}): {d:+.1f}pp**",
            "",
            "## Context",
            "",
            "Anthropic's Opus 4.7 model card (2026-04-16) reports LAB-Bench",
            "FigQA accuracy going from 59.3% → 78.6% (no-tools) and 76.7% →",
            "86.4% (with tools) — a ~+19pp jump on figure reasoning. FigQA",
            "requires multimodal input (figure images) and is not included",
            "in this first reproduction pass.",
            "",
            "For LitQA2 specifically, Anthropic has not published a direct",
            "Opus 4.6 vs 4.7 number (it's not in the surfaced eval subset).",
            "This is therefore a novel public reproduction of the 4.6→4.7",
            "accuracy delta on an open-data-access LAB-Bench subtask.",
        ]
    lines += [
        "",
        "## Reproduce",
        "",
        "```bash",
        "PYTHONPATH=src .venv/bin/python src/phi3_labbench_reproduce.py \\",
        "    --workers 4 --models claude-opus-4-6 claude-opus-4-7",
        "```",
    ]
    (OUT / "SUMMARY.md").write_text("\n".join(lines))
    print(f"\n[PhI-3] wrote {OUT}/SUMMARY.md")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
