"""Lacuna-Bench manifest auditing utilities.

The benchmark layer deliberately reads existing falsification artifacts instead
of rerunning discovery. That keeps the first publishable target narrow:
rediscovery + rejection accounting + external replay traceability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any


EXTERNAL_PASS = "external_pass"
ENDPOINT_MISMATCH = "endpoint_mismatch"
UNDERPOWERED_EXTERNAL_FAIL = "underpowered_external_fail"
SINGLE_GENE_SATURATION_EXTERNAL = "single_gene_saturation_external"
DIRECTION_REVERSAL = "direction_reversal"
MISSING_DATA = "missing_data"
UNCLASSIFIED_EXTERNAL_FAIL = "unclassified_external_fail"


@dataclass(frozen=True)
class BenchmarkTask:
    """One preregistered rediscovery or replay task in Lacuna-Bench."""

    task_id: str
    disease: str
    task_type: str
    dataset_card: str
    report_path: str
    preregistration: str | None = None
    hidden_target: str = ""
    target_genes: list[str] = field(default_factory=list)
    positive_controls: list[str] = field(default_factory=list)
    negative_controls: list[str] = field(default_factory=list)
    external_replay: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "BenchmarkTask":
        known = {field.name for field in cls.__dataclass_fields__.values()}
        data = {key: value for key, value in raw.items() if key in known}
        return cls(**data)


def _resolve_path(root: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def load_manifest_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, list):
        return {"version": "legacy-list", "tasks": payload}
    if not isinstance(payload, dict):
        raise ValueError(f"Benchmark manifest must be a JSON object or list: {path}")
    return payload


def load_manifest(path: str | Path) -> list[BenchmarkTask]:
    payload = load_manifest_payload(path)
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("Benchmark manifest field `tasks` must be a list.")
    return [BenchmarkTask.from_mapping(task) for task in tasks]


def load_report(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "rows", "candidates", "report"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError(f"Falsification report is not a list-like JSON artifact: {path}")


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_genes(row: dict[str, Any]) -> list[str]:
    genes = row.get("genes_used")
    if isinstance(genes, list):
        return [str(g).upper() for g in genes]
    if isinstance(genes, str):
        return [g.strip().upper() for g in genes.split(",") if g.strip()]
    return []


def _row_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(row.get(key, ""))
        for key in ("equation_named", "equation", "law_family", "hypothesis_id")
    ).upper()


def _is_rediscovery_hit(row: dict[str, Any], target_genes: list[str]) -> bool:
    targets = [gene.upper() for gene in target_genes]
    if not targets or not row.get("passes"):
        return False
    row_genes = set(_row_genes(row))
    if row_genes and all(gene in row_genes for gene in targets):
        return True
    text = _row_text(row)
    return all(gene in text for gene in targets)


def _sort_metric(row: dict[str, Any]) -> float:
    for key in ("law_auc", "auroc", "original_auc", "mean_auc"):
        value = _as_float(row.get(key))
        if value is not None:
            return value
    return 0.0


def _top_survivors(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    survivors = [row for row in rows if bool(row.get("passes"))]
    survivors.sort(key=_sort_metric, reverse=True)
    compact: list[dict[str, Any]] = []
    for row in survivors[:limit]:
        compact.append(
            {
                "equation": row.get("equation"),
                "equation_named": row.get("equation_named"),
                "genes_used": row.get("genes_used", []),
                "law_auc": row.get("law_auc", row.get("auroc")),
                "baseline_auc": row.get("baseline_auc"),
                "delta_baseline": row.get("delta_baseline"),
                "complexity": row.get("complexity"),
            }
        )
    return compact


def _verdict_from_payload(payload: Any) -> bool | None:
    if not isinstance(payload, dict):
        return None

    for key in ("verdict", "verdict_primary", "outperforms_verdict"):
        value = payload.get(key)
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized == "PASS":
                return True
            if normalized in {"FAIL", "FAILED", "UNDERPERFORMS"}:
                return False

    for key in ("all_kill_tests_pass", "passed", "pass"):
        value = payload.get(key)
        if isinstance(value, bool):
            return value

    passes = payload.get("passes")
    if isinstance(passes, bool):
        return passes

    report = payload.get("report")
    if isinstance(report, dict) and isinstance(report.get("passes"), bool):
        return report["passes"]

    kill_tests = payload.get("kill_tests")
    if isinstance(kill_tests, list) and kill_tests:
        bools = [test.get("pass") for test in kill_tests if isinstance(test, dict)]
        if bools and all(isinstance(value, bool) for value in bools):
            return all(bools)

    return None


def _payload_text(payload: Any) -> str:
    if isinstance(payload, dict):
        return json.dumps(payload, sort_keys=True).lower()
    return str(payload).lower()


def _nested_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _infer_endpoint(label: str, payload: dict[str, Any]) -> str:
    text = f"{label} {_payload_text(payload)}"
    if any(token in text for token in ("pfs", "survival", "cox", "logrank")):
        return "survival"
    if any(token in text for token in ("tumor_normal", "tumor-vs-normal", "normal")):
        return "tumor_normal"
    if any(token in text for token in ("m_stage", "m-stage", " m1", " m0", "metastasis")):
        return "metastasis_m_stage"
    return "unknown"


def _infer_direction_preserved(payload: dict[str, Any]) -> bool | None:
    value = payload.get("direction_preserved")
    if isinstance(value, bool):
        return value
    diagnostics = _nested_dict(payload, "diagnostics")
    value = diagnostics.get("direction_preserved_both_genes")
    if isinstance(value, bool):
        return value
    return None


def _infer_sample_size(payload: dict[str, Any]) -> int | None:
    for key in ("n_total", "n"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return None


def _infer_positive_case_count(payload: dict[str, Any]) -> int | None:
    for key in ("n_m1", "n_positive", "events"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return None


def _infer_power_assessment(
    payload: dict[str, Any],
    *,
    direction_preserved: bool | None = None,
) -> dict[str, Any]:
    text = _payload_text(payload)
    basis: list[str] = []
    positive = _infer_positive_case_count(payload)
    if positive is not None and positive < 40:
        basis.append("positive_case_count_lt_40")
    if "underpowered" in text or "power limitation" in text or "insufficient" in text:
        basis.append("explicit_underpowered_language")
    if payload.get("ci_lower_pass") is False and direction_preserved is True:
        basis.append("direction_preserved_but_ci_lower_gate_failed")
    report = _nested_dict(payload, "report")
    ci_lower = _as_float(report.get("ci_lower"))
    if ci_lower is not None and ci_lower < 0.60 and direction_preserved is True:
        basis.append("direction_preserved_but_ci_lower_below_0_60")
    return {
        "flag": bool(basis),
        "basis": basis,
        "positive_case_count": positive,
        "threshold_note": (
            "Screening heuristic for external replay triage, not a universal "
            "sample-size rule. Interpret with endpoint, event count, CI width, "
            "and preregistered gate context."
        ),
    }


def _infer_power_flag(
    payload: dict[str, Any],
    *,
    direction_preserved: bool | None = None,
) -> bool:
    return bool(
        _infer_power_assessment(
            payload,
            direction_preserved=direction_preserved,
        )["flag"]
    )


def _infer_single_gene_saturation_flag(payload: dict[str, Any]) -> bool:
    report = _nested_dict(payload, "report") or payload
    baseline_auc = _as_float(report.get("baseline_auc"))
    law_auc = _as_float(report.get("law_auc", report.get("auroc")))
    delta_baseline = _as_float(report.get("delta_baseline"))
    if delta_baseline is not None and delta_baseline < 0:
        return True
    if baseline_auc is not None and law_auc is not None and baseline_auc >= law_auc:
        return True
    if payload.get("delta_baseline_pass") is False:
        return True
    best_single = _as_float(payload.get("best_single_gene_auroc"))
    auc = _as_float(payload.get("auroc"))
    return bool(best_single is not None and auc is not None and best_single >= auc)


def _infer_missingness_flag(payload: dict[str, Any]) -> bool:
    diagnostics = _nested_dict(payload, "diagnostics")
    staging_notes = _nested_dict(diagnostics, "m_staging_notes")
    for key in ("missing_mx_cases", "missing_cases", "missing_outcomes"):
        value = staging_notes.get(key, payload.get(key))
        if isinstance(value, int) and value > 0:
            return True
    text = _payload_text(staging_notes)
    return "missing" in text or "excluded" in text


def _external_failure_subtypes(
    label: str,
    payload: dict[str, Any],
    *,
    status: str,
    endpoint: str,
    endpoint_relation: str | None = None,
    direction_preserved: bool | None,
) -> list[str]:
    if status != "fail":
        return []

    subtypes: set[str] = set()
    if endpoint == "tumor_normal" or endpoint_relation == "endpoint_mismatch":
        subtypes.add(ENDPOINT_MISMATCH)
    if direction_preserved is False:
        subtypes.add(DIRECTION_REVERSAL)
    if _infer_power_flag(payload, direction_preserved=direction_preserved):
        subtypes.add(UNDERPOWERED_EXTERNAL_FAIL)
    if _infer_single_gene_saturation_flag(payload):
        subtypes.add(SINGLE_GENE_SATURATION_EXTERNAL)
    if _infer_missingness_flag(payload):
        subtypes.add(MISSING_DATA)
    if not subtypes:
        subtypes.add(UNCLASSIFIED_EXTERNAL_FAIL)

    order = [
        ENDPOINT_MISMATCH,
        UNDERPOWERED_EXTERNAL_FAIL,
        SINGLE_GENE_SATURATION_EXTERNAL,
        DIRECTION_REVERSAL,
        MISSING_DATA,
        UNCLASSIFIED_EXTERNAL_FAIL,
    ]
    return [subtype for subtype in order if subtype in subtypes]


def _primary_failure_subtype(failure_subtypes: list[str]) -> str | None:
    for subtype in (
        ENDPOINT_MISMATCH,
        DIRECTION_REVERSAL,
        UNDERPOWERED_EXTERNAL_FAIL,
        SINGLE_GENE_SATURATION_EXTERNAL,
        MISSING_DATA,
        UNCLASSIFIED_EXTERNAL_FAIL,
    ):
        if subtype in failure_subtypes:
            return subtype
    return None


def _external_outcome(root: Path, label: str, value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        path_value = value.get("path") or value.get("verdict_path")
        endpoint_metadata = value.get("endpoint")
        expected_endpoint = value.get("expected_endpoint")
        endpoint_relation = value.get("endpoint_relation")
        replay_role = value.get("replay_role")
        interpretation = value.get("interpretation")
    else:
        path_value = value
        endpoint_metadata = None
        expected_endpoint = None
        endpoint_relation = None
        replay_role = None
        interpretation = None

    path = _resolve_path(root, path_value) if isinstance(path_value, str) else None
    if path is None:
        return {
            "label": label,
            "status": "unknown",
            "endpoint": endpoint_metadata,
            "expected_endpoint": expected_endpoint,
            "endpoint_relation": endpoint_relation,
            "replay_role": replay_role,
            "interpretation": interpretation,
            "path": None,
        }
    if not path.exists():
        return {
            "label": label,
            "status": "missing",
            "endpoint": endpoint_metadata,
            "expected_endpoint": expected_endpoint,
            "endpoint_relation": endpoint_relation,
            "replay_role": replay_role,
            "interpretation": interpretation,
            "path": str(path),
        }

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"label": label, "status": "unreadable", "path": str(path)}

    verdict = _verdict_from_payload(payload)
    if verdict is True:
        status = "pass"
    elif verdict is False:
        status = "fail"
    else:
        status = "unknown"
    endpoint = str(endpoint_metadata) if endpoint_metadata else _infer_endpoint(label, payload)
    direction_preserved = _infer_direction_preserved(payload)
    failure_subtypes = _external_failure_subtypes(
        label,
        payload,
        status=status,
        endpoint=endpoint,
        endpoint_relation=endpoint_relation,
        direction_preserved=direction_preserved,
    )
    primary_failure_subtype = _primary_failure_subtype(failure_subtypes)
    outcome_subtype = EXTERNAL_PASS if status == "pass" else (
        primary_failure_subtype if primary_failure_subtype else status
    )
    power_assessment = _infer_power_assessment(
        payload,
        direction_preserved=direction_preserved,
    )
    return {
        "label": label,
        "status": status,
        "outcome_subtype": outcome_subtype,
        "primary_failure_subtype": primary_failure_subtype,
        "failure_subtypes": failure_subtypes,
        "endpoint": endpoint,
        "expected_endpoint": expected_endpoint,
        "endpoint_relation": endpoint_relation,
        "replay_role": replay_role,
        "interpretation": interpretation,
        "direction_preserved": direction_preserved,
        "sample_size": _infer_sample_size(payload),
        "positive_case_count": _infer_positive_case_count(payload),
        "power_assessment": power_assessment,
        "power_flag": power_assessment["flag"],
        "single_gene_saturation_flag": _infer_single_gene_saturation_flag(payload),
        "missingness_flag": _infer_missingness_flag(payload),
        "path": str(path),
    }


def _external_profile(external: list[dict[str, Any]]) -> dict[str, Any]:
    known = [item for item in external if item["status"] in {"pass", "fail"}]
    failures = [item for item in known if item["status"] == "fail"]
    subtype_counts = {
        subtype: sum(1 for item in failures if subtype in item.get("failure_subtypes", []))
        for subtype in (
            ENDPOINT_MISMATCH,
            UNDERPOWERED_EXTERNAL_FAIL,
            SINGLE_GENE_SATURATION_EXTERNAL,
            DIRECTION_REVERSAL,
            MISSING_DATA,
            UNCLASSIFIED_EXTERNAL_FAIL,
        )
    }
    primary_subtype_counts = {
        subtype: sum(1 for item in failures if item.get("primary_failure_subtype") == subtype)
        for subtype in (
            ENDPOINT_MISMATCH,
            UNDERPOWERED_EXTERNAL_FAIL,
            SINGLE_GENE_SATURATION_EXTERNAL,
            DIRECTION_REVERSAL,
            MISSING_DATA,
            UNCLASSIFIED_EXTERNAL_FAIL,
        )
    }
    strict_pass_count = sum(1 for item in known if item["status"] == "pass")
    interpretable_failures = sum(
        1
        for item in failures
        if item.get("failure_subtypes")
        and UNCLASSIFIED_EXTERNAL_FAIL not in item.get("failure_subtypes", [])
    )
    direction_preserved_failures = sum(
        1 for item in failures if item.get("direction_preserved") is True
    )

    def _rate(count: int, denominator: int) -> float | None:
        return count / denominator if denominator else None

    return {
        "known_outcomes": len(known),
        "strict_pass_count": strict_pass_count,
        "strict_fail_count": len(failures),
        "strict_external_replay_rate": _rate(strict_pass_count, len(known)),
        "interpretable_external_failure_rate": _rate(interpretable_failures, len(failures)),
        "direction_preserved_external_fail_rate": _rate(
            direction_preserved_failures, len(failures)
        ),
        "interpretable_external_failure_count": interpretable_failures,
        "direction_preserved_external_fail_count": direction_preserved_failures,
        "failure_subtype_counts": subtype_counts,
        "primary_failure_subtype_counts": primary_subtype_counts,
        "failure_subtype_rates": {
            subtype: _rate(count, len(failures))
            for subtype, count in subtype_counts.items()
        },
    }


def score_task(task: BenchmarkTask, root: str | Path = ".") -> dict[str, Any]:
    """Score a single benchmark task from an existing falsification report."""

    root_path = Path(root)
    report_path = _resolve_path(root_path, task.report_path)
    if report_path is None or not report_path.exists():
        raise FileNotFoundError(f"Missing falsification report for task {task.task_id}: {report_path}")

    rows = load_report(report_path)
    survivors = [row for row in rows if bool(row.get("passes"))]
    rediscovery_hits = [row for row in survivors if _is_rediscovery_hit(row, task.target_genes)]

    external = [
        _external_outcome(root_path, label, value)
        for label, value in sorted(task.external_replay.items())
    ]
    external_profile = _external_profile(external)
    external_known = [item for item in external if item["status"] in {"pass", "fail"}]
    external_pass_count = sum(1 for item in external_known if item["status"] == "pass")
    external_fail_count = sum(1 for item in external_known if item["status"] == "fail")

    rediscovery_f1 = 1.0 if rediscovery_hits else 0.0
    external_replay_rate = (
        external_pass_count / len(external_known) if external_known else None
    )
    false_survivor_rate = (
        external_fail_count / len(external_known)
        if survivors and external_known
        else None
    )

    return {
        "task_id": task.task_id,
        "disease": task.disease,
        "task_type": task.task_type,
        "dataset_card": task.dataset_card,
        "report_path": str(report_path),
        "preregistration": task.preregistration,
        "hidden_target": task.hidden_target,
        "target_genes": task.target_genes,
        "candidate_count": len(rows),
        "survivor_count": len(survivors),
        "reject_count": len(rows) - len(survivors),
        "rediscovery_hit": bool(rediscovery_hits),
        "rediscovery_f1": rediscovery_f1,
        "false_survivor_rate": false_survivor_rate,
        "external_replay_rate": external_replay_rate,
        "strict_external_replay_rate": external_profile["strict_external_replay_rate"],
        "external_replay_profile": external_profile,
        "external_replay_known_outcomes": len(external_known),
        "external_replay_pass_count": external_pass_count,
        "external_replay_fail_count": external_fail_count,
        "external_replay": external,
        "time_to_reject_seconds": None,
        "cost_per_surviving_claim_usd": None,
        "top_survivors": _top_survivors(rows),
        "notes": task.notes,
    }


def audit_manifest(manifest_path: str | Path, root: str | Path = ".") -> dict[str, Any]:
    """Audit all tasks in a Lacuna-Bench manifest."""

    payload = load_manifest_payload(manifest_path)
    tasks = load_manifest(manifest_path)
    task_scores = [score_task(task, root=root) for task in tasks]

    rediscovery_scores = [score["rediscovery_f1"] for score in task_scores]
    false_rates = [
        score["false_survivor_rate"]
        for score in task_scores
        if score["false_survivor_rate"] is not None
    ]
    external_known = sum(score["external_replay_known_outcomes"] for score in task_scores)
    external_pass = sum(score["external_replay_pass_count"] for score in task_scores)
    external_tasks = sum(1 for score in task_scores if score["external_replay"])
    external_failure_count = sum(
        score["external_replay_profile"]["strict_fail_count"] for score in task_scores
    )
    external_interpretable_failures = sum(
        score["external_replay_profile"]["interpretable_external_failure_count"]
        for score in task_scores
    )
    external_direction_preserved_failures = sum(
        score["external_replay_profile"]["direction_preserved_external_fail_count"]
        for score in task_scores
    )
    external_subtype_counts: dict[str, int] = {}
    external_primary_subtype_counts: dict[str, int] = {}
    for score in task_scores:
        for subtype, count in score["external_replay_profile"]["failure_subtype_counts"].items():
            external_subtype_counts[subtype] = external_subtype_counts.get(subtype, 0) + count
        for subtype, count in score["external_replay_profile"][
            "primary_failure_subtype_counts"
        ].items():
            external_primary_subtype_counts[subtype] = (
                external_primary_subtype_counts.get(subtype, 0) + count
            )

    def _external_failure_rate(subtype: str) -> float | None:
        if not external_failure_count:
            return None
        return external_subtype_counts.get(subtype, 0) / external_failure_count

    return {
        "manifest": str(manifest_path),
        "manifest_version": payload.get("version", "unknown"),
        "primary_scientific_goal": payload.get("primary_scientific_goal", ""),
        "task_count": len(task_scores),
        "candidate_count": sum(score["candidate_count"] for score in task_scores),
        "survivor_count": sum(score["survivor_count"] for score in task_scores),
        "reject_count": sum(score["reject_count"] for score in task_scores),
        "metrics": {
            "rediscovery_f1": mean(rediscovery_scores) if rediscovery_scores else None,
            "false_survivor_rate": mean(false_rates) if false_rates else None,
            "external_replay_rate": external_pass / external_known if external_known else None,
            "strict_external_replay_rate": external_pass / external_known if external_known else None,
            "interpretable_external_failure_rate": (
                external_interpretable_failures / external_failure_count
                if external_failure_count
                else None
            ),
            "direction_preserved_external_fail_rate": (
                external_direction_preserved_failures / external_failure_count
                if external_failure_count
                else None
            ),
            "underpowered_external_fail_rate": _external_failure_rate(
                UNDERPOWERED_EXTERNAL_FAIL
            ),
            "endpoint_mismatch_rate": _external_failure_rate(ENDPOINT_MISMATCH),
            "single_gene_saturation_external_rate": _external_failure_rate(
                SINGLE_GENE_SATURATION_EXTERNAL
            ),
            "missing_data_external_fail_rate": _external_failure_rate(MISSING_DATA),
            "direction_reversal_external_fail_rate": _external_failure_rate(
                DIRECTION_REVERSAL
            ),
            "external_replay_task_coverage": external_tasks / len(task_scores) if task_scores else None,
            "time_to_reject": None,
            "cost_per_surviving_claim": None,
        },
        "external_replay_profile": {
            "known_outcomes": external_known,
            "strict_pass_count": external_pass,
            "strict_fail_count": external_failure_count,
            "failure_subtype_counts": external_subtype_counts,
            "primary_failure_subtype_counts": external_primary_subtype_counts,
        },
        "tasks": task_scores,
        "expansion_candidates": payload.get("expansion_candidates", []),
    }
