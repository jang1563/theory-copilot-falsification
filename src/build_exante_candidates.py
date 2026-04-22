#!/usr/bin/env python3
"""Construct a candidates JSON from Opus's ex-ante law_proposals.json.

Each entry with an `initial_guess` string becomes one candidate; this
bypasses PySR and lets the falsification sweep evaluate Opus 4.7's
hand-written templates directly against real data. Use this alongside
the PySR sweep output to compare ex-ante domain knowledge against
unconstrained symbolic search on the same gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build candidate JSON from law_proposals.json initial_guess fields")
    parser.add_argument("--proposals", required=True, help="Path to law_proposals.json")
    parser.add_argument("--dataset", default=None, help="Filter to this dataset_id (e.g. kirc)")
    parser.add_argument("--output", required=True, help="Output candidates JSON path")
    args = parser.parse_args()

    proposals = json.loads(Path(args.proposals).read_text())

    candidates: list[dict] = []
    for p in proposals:
        ig = p.get("initial_guess", "")
        if not ig:
            continue
        if args.dataset and p.get("dataset") not in (args.dataset, None):
            continue
        candidates.append({
            "equation": ig,
            "complexity": len(ig.split()),
            "auroc": None,
            "seed": None,
            "law_family": p.get("template_id", "") or p.get("name", ""),
            "source": "opus_exante",
            "expected_verdict": p.get("expected_verdict", "UNKNOWN"),
            "biological_rationale": p.get("biological_rationale", ""),
            "target_features": p.get("target_features", []),
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(candidates, indent=2))
    print(f"Wrote {len(candidates)} ex-ante candidates from {args.proposals} -> {args.output}")


if __name__ == "__main__":
    main()
