#!/usr/bin/env python3
"""PhL-7 — Compound orchestrator demo: MCP + Memory + 5-test gate in one session.

This is the Best-Managed-Agents flagship integration. A single Managed
Agents session exercises THREE durability primitives at once, all chained
through one agent's reasoning:

  1. Pre-fetched MCP evidence (biology_validator) — PubMed co-mention search
     for the candidate genes on ccRCC.
  2. Memory store (public beta, 2026-04-23) — `/mnt/memory/skeptic-lessons/`
     carries prior Skeptic lessons accumulated across PhL-3 sessions.
  3. 5-test gate verdict — computed locally and injected as a pre-evaluated
     rubric; the agent applies the pre-registered thresholds, does NOT
     re-negotiate them, and appends a compound-reasoning lesson to memory.

Why not run the gate IN the Managed Agents environment?
  The gate is 6 Python files + numpy/sklearn stack. Installing and running
  it inside a cloud container per-session is feasible but adds overhead
  without narrative value. The cleaner demo is: gate runs locally (it is
  a deterministic Python script — same as on the flagship TCGA-KIRC run),
  agent receives the verdict + metrics, applies the pre-registered rubric,
  and integrates with the other two durability primitives.

  This matches exactly the Michael Cohen 2026-04-23 `outcomes` framing:
  the rubric ("these things have to be true") and the computation are
  OUTSIDE the model. The agent's job is to integrate evidence across
  substrates (prior memory + MCP literature + gate metrics) and commit
  the reasoning to memory for the next session.

Pre-requisites:
  - ANTHROPIC_API_KEY set.
  - Existing PhL-3 agent + memory store cached in
    results/live_evidence/phl3_state.json. This script INTENTIONALLY
    reuses the PhL-3 skeptic to extend the same memory chain.
  - `src/mcp_biology_validator.py` runnable locally (no MCP SDK needed).

Cost: ~$0.30 for one Opus 4.7 session.
Usage:
    PYTHONPATH=src .venv/bin/python src/phl7_compound_orchestrator.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import anthropic
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
PHL3_STATE = REPO_ROOT / "results" / "live_evidence" / "phl3_state.json"
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl7_compound_orchestrator"

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


def mcp_validate_law(genes: list[str], disease: str) -> dict:
    """Run the MCP biology_validator tool directly (local subprocess)."""
    cmd = [
        ".venv/bin/python",
        "src/mcp_biology_validator.py",
        "--tool", "validate_law",
        "--genes", ",".join(genes),
        "--disease", disease,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=30
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "non-JSON output", "raw": result.stdout}


def fetch_gate_metrics_for_top2a_epas1() -> dict:
    """Load the pre-computed 5-test gate metrics for TOP2A − EPAS1 on
    TCGA-KIRC metastasis_expanded from the committed falsification report.

    The flagship report uses positional variables (earlier PySR pass), so
    we fetch the H1 v2 canonical result which has gene-name equations.
    """
    h1_path = REPO_ROOT / "results" / "overhang" / "sr_loop_run.json"
    report = json.loads(h1_path.read_text())
    # First survivor is the simplest TOP2A − EPAS1 linear form
    survivors = report.get("survivors", [])
    if not survivors:
        return {"error": "no survivors in sr_loop_run.json"}
    s = survivors[0]
    return {
        "cohort": "TCGA-KIRC metastasis_expanded (n=505, 16% M1)",
        "equation": s.get("equation"),
        "passes": s.get("passes"),
        "law_auc": s.get("law_auc"),
        "baseline_auc_best_single_gene": s.get("baseline_auc"),
        "delta_baseline": s.get("delta_baseline"),
        "perm_p": s.get("perm_p"),
        "ci_lower": s.get("ci_lower"),
        "decoy_p": s.get("decoy_p"),
        "delta_confound": s.get("delta_confound"),
        "origin_skeleton": s.get("origin_skeleton"),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not PHL3_STATE.exists():
        raise SystemExit(
            f"PhL-3 state missing at {PHL3_STATE}. Run src/phl3_memory_smoke.py "
            "write first to create the skeptic agent + memory store."
        )
    state = json.loads(PHL3_STATE.read_text())
    print(f">>> Reusing PhL-3 skeptic agent + memory store:")
    print(f"    agent_id = {state['agent_id']}")
    print(f"    env_id   = {state['env_id']}")
    print(f"    store_id = {state['store_id']}")

    # ------------------------------------------------------------------
    # Pre-step 1: MCP biology validator (live)
    # ------------------------------------------------------------------
    print("\n>>> [1/3] MCP biology_validator: TOP2A + EPAS1 in ccRCC ...")
    mcp_result = mcp_validate_law(["TOP2A", "EPAS1"], "ccRCC")
    print(f"    PubMed co-mention results: {mcp_result.get('total_results')}")

    # ------------------------------------------------------------------
    # Pre-step 2: fetch pre-computed gate metrics for TOP2A − EPAS1
    # ------------------------------------------------------------------
    print("\n>>> [2/3] 5-test gate metrics for TOP2A − EPAS1 on TCGA-KIRC metastasis ...")
    gate = fetch_gate_metrics_for_top2a_epas1()
    print(f"    equation:       {gate.get('equation')}")
    print(f"    passes:         {gate.get('passes')}")
    print(f"    delta_baseline: {gate.get('delta_baseline')}")
    print(f"    perm_p:         {gate.get('perm_p')}")

    # ------------------------------------------------------------------
    # Session: agent integrates MCP evidence + memory + gate verdict
    # ------------------------------------------------------------------
    client = anthropic.Anthropic()

    prompt = (
        "## Compound Skeptic review — cross-substrate integration\n\n"
        "You are judging the 2-gene law `TOP2A − EPAS1` on TCGA-KIRC\n"
        "metastasis_expanded (the flagship survivor). BEFORE writing\n"
        "your verdict you must integrate THREE substrates of evidence:\n\n"
        "1. **Prior Skeptic memory** at `/mnt/memory/skeptic-lessons/lessons.md`.\n"
        "   Read it first. Quote any prior lesson that applies or\n"
        "   conflicts with the current candidate.\n\n"
        "2. **MCP biology_validator live result** (PubMed co-mention\n"
        "   search on the gene pair in ccRCC):\n"
        f"```json\n{json.dumps(mcp_result, indent=2)}\n```\n\n"
        "3. **Pre-computed 5-test gate metrics** for this candidate:\n"
        f"```json\n{json.dumps(gate, indent=2)}\n```\n\n"
        "## Pre-registered gate thresholds (DO NOT re-negotiate)\n\n"
        "- perm_p < 0.05\n"
        "- ci_lower > 0.6\n"
        "- delta_baseline > 0.05\n"
        "- delta_confound > 0.03 (may be null if cohort lacks covariates)\n"
        "- decoy_p < 0.05\n\n"
        "## Your job\n\n"
        "Return PASS / FAIL / NEEDS_MORE_TESTS. Cite each substrate in\n"
        "your reasoning. After the verdict, APPEND a 1-2 line lesson to\n"
        "`/mnt/memory/skeptic-lessons/lessons.md` titled\n"
        "'Compound-substrate integration' capturing how cross-evidence\n"
        "reasoning changed (or failed to change) your conclusion vs\n"
        "single-substrate reasoning."
    )

    print(f"\n>>> [3/3] Opening Managed Agents session with memory mount ...")
    session = client.beta.sessions.create(
        agent=state["agent_id"],
        environment_id=state["env_id"],
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": state["store_id"],
                "access": "read_write",
                "instructions": (
                    "Persistent Skeptic lessons. Read "
                    "/mnt/memory/skeptic-lessons/lessons.md BEFORE judging "
                    "this compound-substrate candidate; APPEND a new lesson "
                    "AFTER judging, titled 'Compound-substrate integration'."
                ),
            }
        ],
        title="PhL-7 compound orchestrator session",
    )
    print(f"    session_id = {session.id}")

    agent_text: list[str] = []
    tool_uses: list[dict] = []
    transcript: list[dict] = []

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message",
                     "content": [{"type": "text", "text": prompt}]}],
        )
        for event in stream:
            etype = getattr(event, "type", "")
            try:
                dump = event.model_dump()
            except Exception:
                dump = {"type": etype}
            transcript.append(dump)
            if etype == "agent.message":
                for block in getattr(event, "content", []) or []:
                    t = getattr(block, "text", "") or ""
                    if t:
                        agent_text.append(t)
            elif etype == "agent.tool_use":
                tool_uses.append(dump)
            elif etype in ("session.status_idle",
                           "session.status_terminated",
                           "session.error"):
                break

    final_text = "".join(agent_text).strip()
    print(f"\n>>> Session complete. {len(transcript)} events, "
          f"{len(tool_uses)} tool uses.")
    print(f"\n=== Agent verdict (first 2000 chars) ===\n{final_text[:2000]}")

    # Dump memory store after session for server-side verification.
    print("\n>>> Server-side memory dump after session ...")
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
    print(f"    Memory store now contains {len(memories)} memory file(s).")

    verdict = {
        "hypothesis_id": "phl7_compound_orchestrator",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent_id": state["agent_id"],
        "session_id": session.id,
        "substrates": {
            "memory_store_id": state["store_id"],
            "mcp_biology_validator_result": mcp_result,
            "gate_metrics": gate,
        },
        "agent_final_text": final_text,
        "tool_use_count": len(tool_uses),
        "total_event_count": len(transcript),
        "memory_file_count_after": len(memories),
        "memory_snapshot_after": [
            {"path": m.get("path"),
             "content_sha256": m.get("content_sha256"),
             "content_len": len(m.get("content") or "")}
            for m in memories
        ],
    }
    (OUT_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2, default=str))
    (OUT_DIR / "memory_snapshot_after.jsonl").write_text(
        "\n".join(json.dumps(m, default=str) for m in memories)
    )
    (OUT_DIR / "session_transcript.jsonl").write_text(
        "\n".join(json.dumps(e, default=str) for e in transcript)
    )
    print(f"\n>>> Artefacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
