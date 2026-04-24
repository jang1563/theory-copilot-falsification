#!/usr/bin/env python3
"""PhL-10 — extend the Skeptic Memory chain with 2 more candidates.

Builds on PhL-3 (initial 2-session write/read demo) + PhL-7 (compound
orchestrator that added the 3rd lesson). Adds two more sessions so
the chain demonstrates "memory accumulating across 5 sessions" rather
than just 3 — the visceral version of the Rakuten "agents distill
lessons from every session" pattern.

Each new session evaluates a different candidate that tests a
DIFFERENT axis of the prior accumulated lessons:

  Session 4 (this script's first call): MKI67 - EPAS1 on TCGA-KIRC
  metastasis (same axis as TOP2A-EPAS1, different proliferation
  marker). Predicted: PASS. Tests whether the memory recognises
  "same proliferation-vs-HIF-2α axis" as a generalisable PASS pattern.

  Session 5 (this script's second call): A LUAD tumor-vs-normal
  candidate (`SFTPC - log1p(MKI67)`) where best-single is saturated.
  Predicted: FAIL on delta_baseline. Tests whether the memory's
  "stop proposing T-vs-N when best-single >= 0.95" lesson
  generalises across cancers (cross-cancer transfer of the rule).

Each session:
  1. Reads `/mnt/memory/skeptic-lessons/lessons.md` (now ~3 entries)
  2. Quotes the prior lesson that applies (or notes none applies)
  3. Applies the gate thresholds
  4. Emits PASS/FAIL/NEEDS_MORE_TESTS with reasoning
  5. Appends a new lesson capturing what this candidate added

Cost: ~$0.40 across 2 Opus 4.7 sessions.
Usage:
    PYTHONPATH=src .venv/bin/python src/phl10_memory_chain_extended.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import anthropic
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
PHL3_STATE = REPO_ROOT / "results" / "live_evidence" / "phl3_state.json"
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl10_memory_chain_extended"

API_BASE = "https://api.anthropic.com"
BETA_HEADER = "managed-agents-2026-04-01"


def _headers() -> dict[str, str]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    return {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": BETA_HEADER,
        "content-type": "application/json",
    }


def _drain_session_text(client, session_id) -> tuple[str, list[dict]]:
    parts: list[str] = []
    transcript: list[dict] = []
    with client.beta.sessions.events.stream(session_id) as stream:
        for event in stream:
            etype = getattr(event, "type", "")
            try:
                dump = event.model_dump()
            except Exception:
                dump = {"type": etype}
            transcript.append(dump)
            if etype == "agent.message":
                for block in getattr(event, "content", []) or []:
                    text = getattr(block, "text", "") or ""
                    if text:
                        parts.append(text)
            elif etype in ("session.status_idle",
                           "session.status_terminated",
                           "session.error"):
                break
    return "".join(parts).strip(), transcript


def _judge_candidate(
    client: anthropic.Anthropic,
    state: dict,
    session_label: str,
    candidate_eq: str,
    metrics: dict,
    cohort: str,
    extra_context: str = "",
) -> dict:
    prompt = (
        "## Candidate to judge (session " + session_label + ")\n\n"
        f"**Equation:** `{candidate_eq}`\n"
        f"**Cohort:** {cohort}\n\n"
        "**Pre-computed metrics:**\n```json\n"
        f"{json.dumps(metrics, indent=2)}\n```\n\n"
        "## Pre-registered gate thresholds (DO NOT re-negotiate)\n\n"
        "- `perm_p < 0.05`\n"
        "- `ci_lower > 0.6`\n"
        "- `delta_baseline > 0.05`\n"
        "- `delta_confound > 0.03` (may be null when cohort lacks "
        "non-degenerate covariates — null is allowed, not a failure)\n"
        "- `decoy_p < 0.05`\n\n"
        "## Your job\n\n"
        "1. **Read** `/mnt/memory/skeptic-lessons/lessons.md` first. "
        "Quote any prior lesson that applies, OR explicitly note "
        "'no prior lesson applies' if none does.\n"
        "2. **Apply** the gate thresholds to the supplied metrics.\n"
        "3. **Return verdict**: PASS / FAIL / NEEDS_MORE_TESTS with "
        "the failing gates listed.\n"
        "4. **Append** a 1-2 line lesson to "
        "`/mnt/memory/skeptic-lessons/lessons.md` capturing what "
        "this candidate added that prior lessons did NOT capture. "
        "If this candidate just reaffirms existing lessons, write "
        "a one-line confirmation note.\n\n"
    )
    if extra_context:
        prompt += "## Extra context\n\n" + extra_context + "\n"

    session = client.beta.sessions.create(
        agent=state["agent_id"],
        environment_id=state["env_id"],
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": state["store_id"],
                "access": "read_write",
                "instructions": (
                    "Persistent Skeptic lessons accumulated across "
                    "PhL-3 + PhL-7 + PhL-10 sessions. ALWAYS read "
                    "/mnt/memory/skeptic-lessons/lessons.md BEFORE "
                    "judging; ALWAYS append a new lesson AFTER "
                    "judging."
                ),
            }
        ],
        title=f"PhL-10 {session_label}",
    )
    print(f">>> {session_label}: session={session.id}")

    client.beta.sessions.events.send(
        session.id,
        events=[{"type": "user.message",
                 "content": [{"type": "text", "text": prompt}]}],
    )
    text, transcript = _drain_session_text(client, session.id)

    return {
        "session_label": session_label,
        "session_id": session.id,
        "candidate_eq": candidate_eq,
        "cohort": cohort,
        "metrics_supplied": metrics,
        "agent_text": text,
        "event_count": len(transcript),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not PHL3_STATE.exists():
        raise SystemExit(
            f"PhL-3 state cache missing at {PHL3_STATE}. "
            "Run src/phl3_memory_smoke.py write first."
        )
    state = json.loads(PHL3_STATE.read_text())
    print(f">>> Reusing PhL-3/7 agent + memory store:")
    print(f"    agent_id    = {state['agent_id']}")
    print(f"    env_id      = {state['env_id']}")
    print(f"    store_id    = {state['store_id']}")

    client = anthropic.Anthropic()

    # Session 4 — MKI67 - EPAS1 on TCGA-KIRC metastasis (same axis as
    # TOP2A-EPAS1, different proliferation marker). Real numbers from
    # results/track_a_task_landscape/metastasis_expanded/falsification_report.json.
    session4 = _judge_candidate(
        client, state,
        session_label="session4_mki67_epas1",
        candidate_eq="MKI67 - EPAS1",
        cohort="TCGA-KIRC metastasis_expanded (n=505, 16% M1)",
        metrics={
            "perm_p": 0.0,
            "ci_lower": 0.642,
            "delta_baseline": 0.063,
            "delta_confound": None,
            "decoy_p": 0.0,
            "law_auc": 0.708,
            "baseline_auc_best_single_gene": 0.645,
        },
        extra_context=(
            "MKI67 is a proliferation marker, like TOP2A in the prior "
            "TOP2A-EPAS1 survivor (PhL-7 session)."
        ),
    )
    print(f"   text len = {len(session4['agent_text'])}, "
          f"events = {session4['event_count']}")

    # Brief pause to ensure memory writes commit before next session.
    time.sleep(2)

    # Session 5 — LUAD tumor-vs-normal saturated single gene.
    # Real-world analog: SFTPC alone reaches AUC ~0.998 on LUAD T-vs-N
    # (per existing analysis); compound cannot clear delta_baseline.
    session5 = _judge_candidate(
        client, state,
        session_label="session5_luad_sftpc_mki67",
        candidate_eq="SFTPC - log1p(MKI67)",
        cohort="TCGA-LUAD tumor-vs-normal (n=540)",
        metrics={
            "perm_p": 0.001,
            "ci_lower": 0.95,
            "delta_baseline": 0.011,
            "delta_confound": 0.005,
            "decoy_p": 0.0,
            "law_auc": 0.991,
            "baseline_auc_best_single_gene": 0.980,
        },
        extra_context=(
            "LUAD (lung adenocarcinoma), DIFFERENT cancer than ccRCC. "
            "SFTPC (surfactant protein C) is the canonical lung "
            "epithelial marker — saturated for tumor-vs-normal. "
            "MKI67 is the proliferation marker. Test whether the "
            "prior lesson 'stop proposing T-vs-N compounds when "
            "best-single >= 0.95' generalises across cancers."
        ),
    )
    print(f"   text len = {len(session5['agent_text'])}, "
          f"events = {session5['event_count']}")

    # Server-side memory dump (tamper-evidence)
    print("\n>>> Server-side memory dump after 2 new sessions ...")
    with httpx.Client(timeout=30.0) as cli:
        r = cli.get(
            f"{API_BASE}/v1/memory_stores/{state['store_id']}/memories",
            headers=_headers(),
            params={"path_prefix": "/"},
        )
        listing = r.json().get("data", [])
        memories = []
        for entry in listing:
            r2 = cli.get(
                f"{API_BASE}/v1/memory_stores/{state['store_id']}"
                f"/memories/{entry['id']}",
                headers=_headers(),
            )
            memories.append(r2.json())

    # Count the lesson entries (rough — one per "- [VERDICT]" prefix
    # in the lessons.md content)
    lesson_count = 0
    if memories:
        content = memories[0].get("content", "")
        lesson_count = content.count("\n- [")

    print(f"    Memory store contains {len(memories)} file(s); "
          f"~{lesson_count} lesson entries.")

    artefact = {
        "hypothesis_id": "phl10_memory_chain_extended",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent_id": state["agent_id"],
        "store_id": state["store_id"],
        "sessions": [session4, session5],
        "memory_file_count_after": len(memories),
        "lesson_entries_after_estimate": lesson_count,
        "memory_snapshot_after": [
            {"path": m.get("path"),
             "content_sha256": m.get("content_sha256"),
             "content_len": len(m.get("content") or "")}
            for m in memories
        ],
    }
    (OUT_DIR / "verdict.json").write_text(json.dumps(artefact, indent=2, default=str))
    (OUT_DIR / "memory_snapshot_after.jsonl").write_text(
        "\n".join(json.dumps(m, default=str) for m in memories)
    )
    print(f"\n>>> Artefacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
