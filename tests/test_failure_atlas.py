from __future__ import annotations

from lacuna.failure_atlas import (
    classify_failure,
    record_from_row,
    retrieve_similar_failures,
    summarize_failure_memory,
)


def test_classify_failure_maps_gate_reasons_to_failure_labels():
    row = {
        "passes": False,
        "fail_reason": "perm_p,ci_lower,delta_baseline,decoy_p",
        "ci_width": 0.24,
        "ci_lower": 0.52,
        "baseline_auc": 0.90,
        "law_auc": 0.62,
        "genes_used": ["TOP2A", "EPAS1"],
    }

    labels = classify_failure(row)

    assert "label_shuffle_fragile" in labels
    assert "bootstrap_unstable" in labels
    assert "underpowered" in labels
    assert "single_gene_saturation" in labels
    assert "decoy_overfit" in labels


def test_failure_memory_summary_and_retrieval():
    records = [
        record_from_row(
            {
                "passes": False,
                "fail_reason": "delta_baseline",
                "genes_used": ["TOP2A", "EPAS1"],
                "baseline_auc": 0.95,
                "law_auc": 0.60,
            },
            task_id="kirc",
        ),
        record_from_row(
            {
                "passes": False,
                "fail_reason": "delta_confound",
                "genes_used": ["CA9", "VEGFA"],
            },
            task_id="kirc",
        ),
        record_from_row(
            {
                "passes": True,
                "genes_used": ["TOP2A", "EPAS1"],
            },
            task_id="kirc",
        ),
    ]

    summary = summarize_failure_memory(records)
    similar = retrieve_similar_failures(records, ["TOP2A"], limit=1)

    assert summary["candidate_count"] == 3
    assert summary["failed_count"] == 2
    assert summary["survivor_count"] == 1
    assert summary["failure_label_counts"]["single_gene_saturation"] == 1
    assert similar[0]["candidate_signature"] == "EPAS1|TOP2A"
