"""
Smoke probe — does `sessions.events.list` preserve Opus 4.7 adaptive-thinking
summaries across session retrieval?

This is the load-bearing question for the "durable reasoning-trace substrate"
capability claim. If `events.list` returns `agent.thinking` events with the
summarized thinking blocks intact, then a later Opus 4.7 call can ingest the
prior agent's REASONING (not just conclusions) as 1M-context input. That is a
UNIQUELY NEW combination (Opus 4.7 × Managed Agents) — plain Messages API gives
you thinking per call but no queryable durable log across sessions.

If `events.list` strips thinking content, the claim weakens to "durable
conclusions log" — still useful, not uniquely new.

Usage
-----
  ANTHROPIC_API_KEY=... .venv/bin/python src/phk_events_list_thinking_probe.py

The probe:
  1. Creates a minimal Managed Agent (Opus 4.7, no tools) that is asked a
     non-trivial question so adaptive thinking fires.
  2. Streams events, counts thinking tokens seen in the stream.
  3. Calls `client.beta.sessions.events.list` on the same session_id.
  4. Writes a diff report: stream-observed thinking vs list-observed thinking.
  5. Prints verdict: PRESERVED | STRIPPED | PARTIAL.

Cost: ~$0.05-0.15 (one short Opus 4.7 call).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic

OUT_DIR = Path("results/overhang/phk_events_list_probe")
PROBE_PROMPT = (
    "I need you to think carefully about whether the following two AUROCs are "
    "distinguishable at sample size n=505 with 95% confidence: "
    "AUROC_A = 0.726, AUROC_B = 0.722. Walk through the calculation step by "
    "step, then state a single numeric 95% confidence interval on the "
    "difference. Keep your final answer to one paragraph."
)


def _extract_event_thinking(block_list) -> str:
    chunks: list[str] = []
    for block in block_list or []:
        # Event content blocks are dict-like (from events.list) or objects.
        btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", "")
        if btype == "thinking":
            text = (block.get("thinking") if isinstance(block, dict)
                    else getattr(block, "thinking", "")) or ""
            chunks.append(text)
        elif btype == "summary":  # some SDKs label summarized thinking "summary"
            text = (block.get("text") if isinstance(block, dict)
                    else getattr(block, "text", "")) or ""
            chunks.append(text)
    return "".join(chunks)


def _event_to_dict(event) -> dict:
    for attr in ("model_dump", "dict", "to_dict"):
        fn = getattr(event, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                pass
    if isinstance(event, dict):
        return event
    return {
        "type": getattr(event, "type", ""),
        "content": getattr(event, "content", None),
        "id": getattr(event, "id", None),
    }


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()

    # 1) Create a minimal agent (Opus 4.7, no tools) so thinking is likely used.
    print(">>> Creating agent (claude-opus-4-7, no tools)...")
    agent = client.beta.agents.create(
        name="phk-thinking-probe",
        model="claude-opus-4-7",
        system=(
            "You are a statistically-rigorous reviewer. When asked to calculate, "
            "show each step and keep your final answer precise. Adaptive thinking "
            "is on; use it when the problem warrants it."
        ),
    )
    print(f"  agent.id = {agent.id}")

    # 2) Create an environment + session.
    print(">>> Creating environment + session...")
    env = client.beta.environments.create(
        name="phk-probe-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    session = client.beta.sessions.create(
        agent=agent.id, environment_id=env.id, title="phk thinking probe",
    )
    print(f"  session.id = {session.id}")

    # 3) Stream; count thinking chars observed in the stream.
    stream_thinking_chars = 0
    stream_events_seen: list[str] = []
    stream_events_full: list[dict] = []
    print(">>> Streaming...")
    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[{"type": "user.message",
                         "content": [{"type": "text", "text": PROBE_PROMPT}]}],
            )
            for event in stream:
                etype = getattr(event, "type", "")
                stream_events_seen.append(etype)
                ser = _event_to_dict(event)
                stream_events_full.append(ser)
                if etype == "agent.thinking":
                    stream_thinking_chars += len(
                        _extract_event_thinking(ser.get("content"))
                    )
                if etype in ("session.status_idle", "session.status_terminated"):
                    break
    except Exception as exc:
        print(f"  stream exception: {exc!r}")

    # 4) Re-fetch via events.list and count again.
    print(">>> Re-fetching via events.list...")
    list_thinking_chars = 0
    list_events_seen: list[str] = []
    list_events_full: list[dict] = []
    try:
        pager = client.beta.sessions.events.list(session.id, order="asc")
        for event in pager:
            ser = _event_to_dict(event)
            etype = ser.get("type", "")
            list_events_seen.append(etype)
            list_events_full.append(ser)
            if etype == "agent.thinking":
                list_thinking_chars += len(_extract_event_thinking(ser.get("content")))
    except Exception as exc:
        print(f"  list exception: {exc!r}")

    # 5) Verdict.
    if stream_thinking_chars == 0 and list_thinking_chars == 0:
        verdict = "NO_THINKING_OBSERVED"
        narrative = (
            "Adaptive thinking did not produce agent.thinking events on this "
            "prompt. Re-run with a longer / harder problem before concluding."
        )
    elif list_thinking_chars >= 0.9 * stream_thinking_chars:
        verdict = "PRESERVED"
        narrative = (
            "events.list returns agent.thinking content comparable to stream. "
            "This validates the 'durable reasoning-trace substrate' claim: a "
            "downstream Opus 4.7 call can ingest prior agent REASONING, not "
            "just conclusions, via events.list."
        )
    elif list_thinking_chars == 0:
        verdict = "STRIPPED"
        narrative = (
            "Stream emits thinking chars; events.list returns zero. The durable "
            "log preserves conclusions but not reasoning. Revise the submission "
            "narrative accordingly: event log = conclusions-as-data, not "
            "reasoning-as-data."
        )
    else:
        ratio = list_thinking_chars / max(stream_thinking_chars, 1)
        verdict = "PARTIAL"
        narrative = (
            f"Partial preservation (ratio={ratio:.2f}). Summarized thinking "
            "may be truncated or compacted. Inspect outputs before claiming "
            "full fidelity."
        )

    report = {
        "session_id": session.id,
        "agent_id": agent.id,
        "prompt_len_chars": len(PROBE_PROMPT),
        "stream_event_types": stream_events_seen,
        "list_event_types": list_events_seen,
        "stream_thinking_chars": stream_thinking_chars,
        "list_thinking_chars": list_thinking_chars,
        "verdict": verdict,
        "narrative": narrative,
    }

    (OUT_DIR / "verdict.json").write_text(json.dumps(report, indent=2))
    (OUT_DIR / "stream_events.jsonl").write_text(
        "\n".join(json.dumps(e, default=str) for e in stream_events_full)
    )
    (OUT_DIR / "list_events.jsonl").write_text(
        "\n".join(json.dumps(e, default=str) for e in list_events_full)
    )

    print(f"\n=== Verdict: {verdict} ===")
    print(narrative)
    print(f"Report: {OUT_DIR / 'verdict.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
