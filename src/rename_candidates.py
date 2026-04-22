#!/usr/bin/env python3
"""Post-process PySR candidate equations.

PySR 0.19.x silently ignores `variable_names` when rendering equations
into the output DataFrame, so candidates come back in `x0..xN` form.
This utility substitutes those indices with the gene names in the order
they were passed to the sweep, so the saved candidate JSON is
human-readable and falsification_sweep can evaluate by gene name.

Also attempts a best-effort law_family match against the initial_guess
strings in law_proposals.json so that the demo narrative can say
"this equation matches the HIF/angiogenesis family proposed ex-ante".
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _rename_equation(equation: str, gene_order: list[str]) -> str:
    """Replace x0..xN with gene names in a PySR equation string."""
    # Longest-first so x10 is matched before x1.
    indexed = sorted(
        range(len(gene_order)),
        key=lambda i: -len(str(i)),
    )
    out = equation
    for i in indexed:
        pattern = rf"\bx{i}\b"
        out = re.sub(pattern, gene_order[i], out)
    return out


def _match_law_family(equation_named: str, proposals: list[dict]) -> str:
    """Best-effort law-family label from a named equation."""
    # Direct hit: the equation matches the initial_guess verbatim.
    eq_norm = equation_named.replace(" ", "")
    for p in proposals:
        ig = p.get("initial_guess", "").replace(" ", "")
        if ig and ig == eq_norm:
            return p.get("template_id", "") or p.get("name", "")

    # Soft hit: the equation uses the same target_features as a proposal.
    referenced = {g for g in re.findall(r"\b[A-Z][A-Z0-9]+\b", equation_named)}
    best: tuple[int, str] = (0, "")
    for p in proposals:
        tf = set(p.get("target_features", []))
        if not tf:
            continue
        overlap = len(tf & referenced)
        if overlap > best[0] and overlap >= 2:
            best = (overlap, p.get("template_id", "") or p.get("name", ""))
    return best[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename xi -> gene names in PySR candidates JSON")
    parser.add_argument("--input", required=True, help="Path to raw candidates JSON (xi form)")
    parser.add_argument("--genes", required=True, help="Comma-separated gene order used in the PySR sweep")
    parser.add_argument("--proposals", default=None, help="Optional law_proposals.json for family matching")
    parser.add_argument("--output", required=True, help="Output path for renamed candidates JSON")
    args = parser.parse_args()

    gene_order = [g.strip() for g in args.genes.split(",") if g.strip()]
    candidates = json.loads(Path(args.input).read_text())

    proposals: list[dict] = []
    if args.proposals:
        proposals = json.loads(Path(args.proposals).read_text())

    renamed: list[dict] = []
    for c in candidates:
        eq_named = _rename_equation(c["equation"], gene_order)
        family = c.get("law_family") or _match_law_family(eq_named, proposals)
        renamed.append({
            **c,
            "equation_original": c["equation"],
            "equation": eq_named,
            "law_family": family,
            "genes_used": [g for g in gene_order if re.search(rf"\b{re.escape(g)}\b", eq_named)],
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(renamed, indent=2))
    print(f"Renamed {len(renamed)} candidates -> {args.output}")


if __name__ == "__main__":
    main()
