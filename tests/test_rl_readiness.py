from __future__ import annotations

from lacuna.rl_readiness import build_rl_readiness_report, verifier_reward


def test_verifier_reward_penalizes_external_replay_failure_and_complexity():
    reward = verifier_reward(
        {"passes": True, "complexity": 5},
        external_replay_pass=False,
        complexity_weight=0.01,
    )

    assert reward["reward"] == -0.05
    assert reward["reward_hacking_risk"] is True


def test_rl_readiness_keeps_rlvr_blocked_until_verifier_is_stable():
    bench_audit = {
        "metrics": {
            "rediscovery_f1": 1.0,
            "external_replay_rate": 0.5,
            "strict_external_replay_rate": 0.5,
        },
        "tasks": [
            {
                "external_replay_known_outcomes": 2,
                "external_replay_fail_count": 1,
            }
        ],
    }
    atlas_summary = {
        "failed_count": 30,
        "failure_label_coverage": 0.4,
    }

    report = build_rl_readiness_report(bench_audit, atlas_summary)

    assert report["recommended_stage"] == "Phase 2: failure-memory retrieval and reranking"
    assert report["ready_for_contextual_bandit"] is False
    assert report["ready_for_rlvr"] is False
    assert report["blockers"]
