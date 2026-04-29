"""Failure Atlas v1 utilities.

The atlas converts rejection logs into structured memory. The labels are not a
replacement for biological review; they are machine-readable hooks for
retrieval, reranking, and later policy learning.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .bench import BenchmarkTask, load_manifest, load_report


FAILURE_LABELS = [
    "single_gene_saturation",
    "decoy_overfit",
    "bootstrap_unstable",
    "label_shuffle_fragile",
    "cohort_shift_fail",
    "endpoint_mismatch",
    "confound_only",
    "underpowered",
    "known_axis_triviality",
]


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _genes(row: dict[str, Any]) -> list[str]:
    genes = row.get("genes_used")
    if isinstance(genes, list):
        return [str(g).upper() for g in genes]
    if isinstance(genes, str):
        return [g.strip().upper() for g in genes.split(",") if g.strip()]
    return []


def _fail_parts(row: dict[str, Any]) -> set[str]:
    reason = row.get("fail_reason", "")
    if isinstance(reason, list):
        raw_parts = reason
    else:
        raw_parts = str(reason).replace(";", ",").split(",")
    parts = {str(part).strip() for part in raw_parts if str(part).strip()}

    fails = row.get("fails")
    if isinstance(fails, list):
        for item in fails:
            text = str(item)
            if "ci_lower" in text:
                parts.add("ci_lower")
            if "delta_baseline" in text:
                parts.add("delta_baseline")
            if "perm_p" in text:
                parts.add("perm_p")
    return parts


def classify_failure(row: dict[str, Any], context: dict[str, Any] | None = None) -> list[str]:
    """Assign one or more Failure Atlas labels to a candidate row."""

    context = context or {}
    labels: set[str] = set()
    passes = bool(row.get("passes"))
    parts = _fail_parts(row)

    external_status = context.get("external_status")
    if passes and external_status not in {"fail", "endpoint_fail"}:
        return []

    if "perm_p" in parts:
        labels.add("label_shuffle_fragile")
    if "decoy_p" in parts:
        labels.add("decoy_overfit")
    if "ci_lower" in parts:
        labels.add("bootstrap_unstable")
        ci_width = _as_float(row.get("ci_width"))
        ci_lower = _as_float(row.get("ci_lower"))
        if (ci_width is not None and ci_width >= 0.20) or (
            ci_lower is not None and ci_lower < 0.60
        ):
            labels.add("underpowered")
    if "delta_confound" in parts:
        labels.add("confound_only")
    if "delta_baseline" in parts:
        baseline_auc = _as_float(row.get("baseline_auc"))
        law_auc = _as_float(row.get("law_auc", row.get("auroc")))
        gene_count = len(_genes(row))
        if gene_count <= 1:
            labels.add("known_axis_triviality")
        elif baseline_auc is not None and law_auc is not None and baseline_auc >= law_auc:
            labels.add("single_gene_saturation")
        else:
            labels.add("known_axis_triviality")
    if "threshold_edge" in parts:
        labels.add("known_axis_triviality")

    if external_status == "fail":
        labels.add("cohort_shift_fail")
    if external_status == "endpoint_fail":
        labels.add("endpoint_mismatch")
    if row.get("transfer_dataset") and not passes:
        labels.add("cohort_shift_fail")

    if not passes and not labels:
        labels.add("known_axis_triviality")

    return [label for label in FAILURE_LABELS if label in labels]


def record_from_row(
    row: dict[str, Any],
    *,
    task_id: str = "",
    dataset_id: str = "",
    source_report: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    labels = classify_failure(row, context=context)
    metrics = {
        key: row.get(key)
        for key in (
            "law_auc",
            "auroc",
            "baseline_auc",
            "delta_baseline",
            "confound_auc",
            "delta_confound",
            "perm_p",
            "perm_p_fdr",
            "ci_width",
            "ci_lower",
            "decoy_p",
            "decoy_q95",
            "complexity",
        )
        if key in row
    }
    genes = _genes(row)
    return {
        "task_id": task_id,
        "dataset_id": dataset_id,
        "source_report": source_report,
        "equation": row.get("equation"),
        "equation_named": row.get("equation_named"),
        "genes_used": genes,
        "candidate_signature": "|".join(sorted(genes)) or str(row.get("equation", "")),
        "passes": bool(row.get("passes")),
        "fail_reason": row.get("fail_reason", ""),
        "failure_labels": labels,
        "metrics": metrics,
    }


def records_from_report(
    report_path: str | Path,
    *,
    task_id: str = "",
    dataset_id: str = "",
) -> list[dict[str, Any]]:
    rows = load_report(report_path)
    return [
        record_from_row(
            row,
            task_id=task_id,
            dataset_id=dataset_id,
            source_report=str(report_path),
        )
        for row in rows
    ]


def records_from_manifest(
    manifest_path: str | Path,
    *,
    root: str | Path = ".",
) -> list[dict[str, Any]]:
    root_path = Path(root)
    records: list[dict[str, Any]] = []
    for task in load_manifest(manifest_path):
        assert isinstance(task, BenchmarkTask)
        report_path = Path(task.report_path)
        if not report_path.is_absolute():
            report_path = root_path / report_path
        dataset_id = Path(task.dataset_card).stem
        records.extend(
            records_from_report(
                report_path,
                task_id=task.task_id,
                dataset_id=dataset_id,
            )
        )
    return records


def summarize_failure_memory(records: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts: Counter[str] = Counter()
    gene_sets: Counter[str] = Counter()
    failed_count = 0
    survivor_count = 0

    for record in records:
        if record.get("passes"):
            survivor_count += 1
            continue
        failed_count += 1
        label_counts.update(record.get("failure_labels", []))
        signature = record.get("candidate_signature") or ""
        if signature:
            gene_sets[signature] += 1

    return {
        "candidate_count": len(records),
        "failed_count": failed_count,
        "survivor_count": survivor_count,
        "failure_label_counts": {label: label_counts.get(label, 0) for label in FAILURE_LABELS},
        "failure_label_coverage": sum(1 for label in FAILURE_LABELS if label_counts.get(label, 0))
        / len(FAILURE_LABELS),
        "top_repeated_gene_sets": [
            {"candidate_signature": signature, "count": count}
            for signature, count in gene_sets.most_common(10)
        ],
    }


def retrieve_similar_failures(
    records: list[dict[str, Any]],
    genes: list[str],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    query = {gene.upper() for gene in genes}
    if not query:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        if record.get("passes"):
            continue
        candidate_genes = {gene.upper() for gene in record.get("genes_used", [])}
        if not candidate_genes:
            continue
        union = query | candidate_genes
        score = len(query & candidate_genes) / len(union)
        if score > 0:
            scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    output: list[dict[str, Any]] = []
    for score, record in scored[:limit]:
        output.append({**record, "similarity": score})
    return output
