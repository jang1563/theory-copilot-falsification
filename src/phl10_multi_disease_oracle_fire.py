#!/usr/bin/env python3
"""PhL-10 — Multi-Disease Oracle: Stage + COAD, new Routine per disease.

Answers the PhL-8d question: "new Routine or update?"
Answer: NEW Routine per disease. Each Routine's Instructions encode the
disease-specific data contract; the Skills and gate are shared.

Fires a *second* Routine — `lacuna-stage-oracle` — pointing at the KIRC
staging task instead of the original metastasis/tumor task. Demonstrates
that `routines_client` is disease-agnostic: only trig_id + token change.

  Eq1 (expected FAIL): CCNB1 / PGK1 on stage_expanded
    delta_baseline = +0.007 < 0.05 threshold.
  Eq2 (expected PASS): CXCR4 / EPAS1 on stage_expanded
    delta_baseline = +0.051 > 0.05 threshold (AUROC 0.689).

Multi-cancer evidence already committed (gate already ran offline):
  KIRC Stage:  results/track_a_task_landscape/stage_expanded/  23/28 PASS
  COAD MSI:    results/track_a_task_landscape/coad_msi/         15/22 PASS
  LIHC:        results/track_a_task_landscape/lihc/              0/26 PASS (designed negative)

Pre-requisites:
  - Create a *new* Routine in claude.ai/code/routines named `lacuna-stage-oracle`.
    Use routines/2026_04_26/lacuna_stage_oracle_instructions.md as the Instructions.
    This is a *separate* Routine — NOT an edit of the original oracle's Instructions.
    The original Routine's Instructions are the provenance record for PhL-8d; editing
    them would break the audit chain. One disease = one Routine.
  - Set env vars:
      export CLAUDE_ROUTINE_STAGE_TRIG_ID=trig_01...   # new Routine
      export CLAUDE_ROUTINE_STAGE_TOKEN=sk-ant-...      # new bearer token

Usage:
    cd lacuna-falsification/
    export CLAUDE_ROUTINE_STAGE_TRIG_ID=trig_01XXXXX...
    export CLAUDE_ROUTINE_STAGE_TOKEN=sk-ant-...
    PYTHONPATH=src .venv/bin/python src/phl10_multi_disease_oracle_fire.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from lacuna.routines_client import fire_routine

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl10_stage_oracle"

# Eq1: staging — expected FAIL (CCNB1/PGK1, delta_baseline=+0.007)
# Eq2: staging — expected PASS (CXCR4/EPAS1, AUROC 0.689, delta=+0.051)
STAGE_TRIGGER = (
    "eq1: task=stage_expanded, data=kirc_stage_expanded.csv, "
    "equation=CCNB1 / PGK1\n"
    "eq2: task=stage_expanded, data=kirc_stage_expanded.csv, "
    "equation=CXCR4 / EPAS1"
)

# Multi-cancer results already committed (gate ran offline, used for narrative)
MULTI_CANCER_EVIDENCE = {
    "kirc_stage": {
        "disease": "ccRCC",
        "task": "stage_expanded (Stage I-II vs III-IV)",
        "n_samples": 512,
        "n_pass": 23,
        "n_total": 28,
        "top_law": "CXCR4 / EPAS1",
        "top_auroc": 0.6887,
        "top_delta_baseline": 0.0513,
        "results_dir": "results/track_a_task_landscape/stage_expanded/",
    },
    "coad_msi": {
        "disease": "Colon (MSI-high)",
        "task": "MSI-high vs MSS",
        "n_pass": 15,
        "n_total": 22,
        "top_law": "SLC2A1 + (PDCD1LG2 + VIM − MYC)",
        "top_auroc": 0.6584,
        "top_delta_baseline": 0.1001,
        "results_dir": "results/track_a_task_landscape/coad_msi/",
    },
    "lihc": {
        "disease": "Liver (HCC)",
        "task": "tumor_vs_normal",
        "n_pass": 0,
        "n_total": 26,
        "top_law": "TTR — saturates single-gene baseline",
        "note": "designed negative — gate correctly refuses",
        "results_dir": "results/track_a_task_landscape/lihc/",
    },
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Try STAGE-specific vars first; fall back to the standard vars used by phl8c/phl8d.
    trig_id = (
        os.environ.get("CLAUDE_ROUTINE_STAGE_TRIG_ID", "").strip()
        or os.environ.get("CLAUDE_ROUTINE_TRIG_ID", "").strip()
    )
    token = (
        os.environ.get("CLAUDE_ROUTINE_STAGE_TOKEN", "").strip()
        or os.environ.get("CLAUDE_ROUTINE_TOKEN", "").strip()
    )
    using_fallback = (
        not os.environ.get("CLAUDE_ROUTINE_STAGE_TRIG_ID", "").strip()
        and bool(trig_id)
    )

    if not trig_id or not token:
        print(
            "ERROR: No Routine credentials found.\n"
            "Set either the stage-specific vars:\n"
            "  export CLAUDE_ROUTINE_STAGE_TRIG_ID=trig_01...\n"
            "  export CLAUDE_ROUTINE_STAGE_TOKEN=sk-ant-...\n"
            "or the standard vars (will fire whichever Routine they point to):\n"
            "  export CLAUDE_ROUTINE_TRIG_ID=trig_01...\n"
            "  export CLAUDE_ROUTINE_TOKEN=sk-ant-...\n\n"
            "Multi-cancer results already committed (offline gate runs):\n"
            "  KIRC Stage: 23/28 PASS (CXCR4/EPAS1, Δ=+0.051)\n"
            "  COAD MSI:   15/22 PASS (SLC2A1+Warburg, Δ=+0.100)\n"
            "  LIHC:        0/26 PASS (designed negative — gate correctly refuses)",
            file=sys.stderr,
        )
        out_path = OUT_DIR / "multi_cancer_evidence.json"
        out_path.write_text(json.dumps(MULTI_CANCER_EVIDENCE, indent=2))
        print(f"\n[offline] Wrote multi-cancer evidence to {out_path}", file=sys.stderr)
        return 2

    if using_fallback:
        print(
            ">>> Note: CLAUDE_ROUTINE_STAGE_TRIG_ID not set — "
            "using CLAUDE_ROUTINE_TRIG_ID as fallback."
        )

    print(">>> Firing lacuna-stage-oracle (NEW Routine — separate from PhL-8d Routine)")
    print(">>> Eq1 (expected FAIL): CCNB1 / PGK1  [stage_expanded, delta=+0.007]")
    print(">>> Eq2 (expected PASS): CXCR4 / EPAS1  [stage_expanded, delta=+0.051]")
    print()

    t0 = time.time()
    result = fire_routine(trig_id=trig_id, token=token, text=STAGE_TRIGGER)
    elapsed = time.time() - t0

    print(f">>> Fire returned in {elapsed:.2f}s")
    print(f"    http_status  = {result.http_status}")
    print(f"    session_id   = {result.session_id}")
    print(f"    session_url  = {result.session_url}")
    print(f"    status       = {result.status}")

    artefact = {
        "hypothesis_id": "phl10_multi_disease_oracle",
        "fire_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "routine_name": "lacuna-stage-oracle",
        "routine_trig_id_prefix": trig_id[:12] + "...",
        "routine_trig_id_length": len(trig_id),
        "trigger_type": "api",
        "trigger_text": STAGE_TRIGGER,
        "http_status": result.http_status,
        "claude_code_session_id": result.session_id,
        "claude_code_session_url": result.session_url,
        "normalized_status": result.status,
        "fire_elapsed_seconds": round(elapsed, 3),
        "architecture_note": (
            "This is a SECOND Routine, not an update to the PhL-8d Routine. "
            "The PhL-8d Routine Instructions are frozen as the provenance record. "
            "One disease = one Routine. Skills (falsification-gate, pre-register-claim) "
            "are shared across all Routines. Only trig_id + token are disease-specific."
        ),
        "eq1": {
            "task": "stage_expanded",
            "data": "kirc_stage_expanded.csv",
            "equation": "CCNB1 / PGK1",
            "expected_gate": "FAIL",
            "expected_fail_reason": "delta_baseline (+0.007 < 0.05 threshold)",
        },
        "eq2": {
            "task": "stage_expanded",
            "data": "kirc_stage_expanded.csv",
            "equation": "CXCR4 / EPAS1",
            "expected_gate": "PASS",
            "expected_metrics": "auroc=0.689, delta_baseline=+0.051, perm_p≈0.0",
        },
        "multi_cancer_evidence_offline": MULTI_CANCER_EVIDENCE,
    }

    out_path = OUT_DIR / "fire_response.json"
    out_path.write_text(json.dumps(artefact, indent=2))
    print(f"\n>>> Wrote {out_path}")
    print(f"\n>>> Open session in browser (wait ~6-8 min for both gates to complete):")
    print(f"    {result.session_url}")
    print(f"\n>>> Routine architecture confirmed:")
    print(f"    lacuna-scientific-oracle (PhL-8d, frozen) → metastasis/tumor_vs_normal")
    print(f"    lacuna-stage-oracle      (PhL-10, live)  → stage_expanded")

    return 0 if result.status in ("completed", "running") else 1


if __name__ == "__main__":
    raise SystemExit(main())
