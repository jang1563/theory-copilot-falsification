"""Verifier-first RL readiness checks for Lacuna."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def verifier_reward(
    row: dict[str, Any],
    *,
    external_replay_pass: bool | None = None,
    complexity_weight: float = 0.01,
) -> dict[str, Any]:
    """Compute a conservative verifier reward with explicit components."""

    internal_gate = bool(row.get("passes"))
    complexity = float(row.get("complexity") or 0.0)
    internal_reward = 1.0 if internal_gate else 0.0
    if external_replay_pass is True:
        external_reward = 1.0
    elif external_replay_pass is False:
        external_reward = -1.0
    else:
        external_reward = 0.0
    complexity_penalty = complexity_weight * complexity
    reward = internal_reward + external_reward - complexity_penalty
    return {
        "reward": reward,
        "internal_gate_reward": internal_reward,
        "external_replay_reward": external_reward,
        "complexity_penalty": complexity_penalty,
        "reward_hacking_risk": internal_gate and external_replay_pass is False,
    }


def build_rl_readiness_report(
    bench_audit: dict[str, Any],
    atlas_summary: dict[str, Any],
    *,
    min_external_outcomes: int = 3,
    min_failure_records: int = 50,
) -> dict[str, Any]:
    """Report which RL stage is scientifically justified by current artifacts."""

    metrics = bench_audit.get("metrics", {})
    tasks = bench_audit.get("tasks", [])
    external_known = sum(task.get("external_replay_known_outcomes", 0) for task in tasks)
    external_fail = sum(task.get("external_replay_fail_count", 0) for task in tasks)
    failed_count = int(atlas_summary.get("failed_count", 0))
    label_coverage = float(atlas_summary.get("failure_label_coverage", 0.0))

    blockers: list[str] = []
    if external_known < min_external_outcomes:
        blockers.append(
            "Too few machine-readable external replay outcomes for robust reward calibration."
        )
    if failed_count < min_failure_records:
        blockers.append("Failure memory is too small for policy learning beyond retrieval.")
    if label_coverage < 0.5:
        blockers.append("Failure-label coverage is too narrow for general failure-aware reranking.")
    blockers.append("Verifier agreement across held-out gates is not yet instrumented.")
    blockers.append("Reward variance and reward-hacking stress tests are not yet logged.")

    if failed_count >= 20 and label_coverage > 0:
        recommended_stage = "Phase 2: failure-memory retrieval and reranking"
    else:
        recommended_stage = "Phase 1: deterministic verifier stabilization"

    return {
        "recommended_stage": recommended_stage,
        "ready_for_contextual_bandit": (
            failed_count >= min_failure_records
            and label_coverage >= 0.5
            and external_known >= 1
        ),
        "ready_for_offline_rl": False,
        "ready_for_rlvr": False,
        "blockers": blockers,
        "observed": {
            "rediscovery_f1": metrics.get("rediscovery_f1"),
            "false_survivor_rate": metrics.get("false_survivor_rate"),
            "external_replay_rate": metrics.get("external_replay_rate"),
            "strict_external_replay_rate": metrics.get("strict_external_replay_rate"),
            "interpretable_external_failure_rate": metrics.get(
                "interpretable_external_failure_rate"
            ),
            "underpowered_external_fail_rate": metrics.get("underpowered_external_fail_rate"),
            "endpoint_mismatch_rate": metrics.get("endpoint_mismatch_rate"),
            "missing_data_external_fail_rate": metrics.get(
                "missing_data_external_fail_rate"
            ),
            "direction_reversal_external_fail_rate": metrics.get(
                "direction_reversal_external_fail_rate"
            ),
            "external_replay_known_outcomes": external_known,
            "external_replay_fail_count": external_fail,
            "failure_records": failed_count,
            "failure_label_coverage": label_coverage,
        },
        "next_tests": [
            "Compare no-memory proposer vs failure-memory proposer at the same candidate budget.",
            "Run reward-hacking tests where candidates optimize internal gate pass only.",
            "Add held-out cohort/gate agreement logs before contextual bandit training.",
            "Require external replay plus complexity penalty before any RLVR reward is exposed.",
        ],
    }
