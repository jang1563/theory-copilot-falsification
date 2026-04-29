from __future__ import annotations

import json

from lacuna.bench import audit_manifest, load_manifest, score_task


def test_score_task_detects_rediscovery_and_external_replay(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            [
                {
                    "equation": "TOP2A - EPAS1",
                    "equation_named": "TOP2A - EPAS1",
                    "genes_used": ["TOP2A", "EPAS1"],
                    "passes": True,
                    "law_auc": 0.72,
                    "baseline_auc": 0.65,
                    "delta_baseline": 0.07,
                },
                {
                    "equation": "CA9",
                    "equation_named": "CA9",
                    "genes_used": ["CA9"],
                    "passes": False,
                    "fail_reason": "delta_baseline",
                },
            ]
        )
    )
    external = tmp_path / "external.json"
    external.write_text(json.dumps({"verdict": "PASS"}))
    manifest = tmp_path / "bench.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test",
                "tasks": [
                    {
                        "task_id": "kirc",
                        "disease": "ccRCC",
                        "task_type": "blind_rediscovery",
                        "dataset_card": "cards/kirc.json",
                        "report_path": str(report),
                        "target_genes": ["TOP2A", "EPAS1"],
                        "external_replay": {"external": str(external)},
                    }
                ],
            }
        )
    )

    task = load_manifest(manifest)[0]
    score = score_task(task, root=tmp_path)

    assert score["rediscovery_hit"] is True
    assert score["rediscovery_f1"] == 1.0
    assert score["candidate_count"] == 2
    assert score["survivor_count"] == 1
    assert score["external_replay_rate"] == 1.0


def test_audit_manifest_aggregates_metrics(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            [
                {
                    "equation_named": "TOP2A - EPAS1",
                    "genes_used": ["TOP2A", "EPAS1"],
                    "passes": True,
                }
            ]
        )
    )
    external = tmp_path / "external.json"
    external.write_text(json.dumps({"verdict_primary": "FAIL"}))
    manifest = tmp_path / "bench.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test",
                "tasks": [
                    {
                        "task_id": "kirc",
                        "disease": "ccRCC",
                        "task_type": "blind_rediscovery",
                        "dataset_card": "cards/kirc.json",
                        "report_path": str(report),
                        "target_genes": ["TOP2A", "EPAS1"],
                        "external_replay": {"external": str(external)},
                    }
                ],
            }
        )
    )

    audit = audit_manifest(manifest, root=tmp_path)

    assert audit["task_count"] == 1
    assert audit["metrics"]["rediscovery_f1"] == 1.0
    assert audit["metrics"]["external_replay_rate"] == 0.0
    assert audit["metrics"]["false_survivor_rate"] == 1.0


def test_external_replay_subtypes_separate_endpoint_and_underpowered_failures(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            [
                {
                    "equation_named": "TOP2A - EPAS1",
                    "genes_used": ["TOP2A", "EPAS1"],
                    "passes": True,
                }
            ]
        )
    )
    cptac = tmp_path / "cptac.json"
    cptac.write_text(
        json.dumps(
            {
                "verdict": "FAIL",
                "n_total": 155,
                "n_m1": 20,
                "direction_preserved": True,
                "ci_lower_pass": False,
                "delta_baseline_pass": False,
                "auroc": 0.6833,
                "best_single_gene_auroc": 0.6907,
                "diagnostics": {
                    "m_staging_notes": {
                        "missing_mx_cases": 23,
                    }
                },
            }
        )
    )
    gse = tmp_path / "gse.json"
    gse.write_text(
        json.dumps(
            {
                "verdict_primary": "FAIL",
                "cohort_csv": "data/gse53757_ccrcc.csv",
                "n": 144,
                "n_positive": 72,
                "report": {
                    "passes": False,
                    "law_auc": 0.27,
                    "baseline_auc": 0.99,
                    "delta_baseline": -0.72,
                },
            }
        )
    )
    manifest = tmp_path / "bench.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test",
                "tasks": [
                    {
                        "task_id": "kirc",
                        "disease": "ccRCC",
                        "task_type": "blind_rediscovery",
                        "dataset_card": "cards/kirc.json",
                        "report_path": str(report),
                        "target_genes": ["TOP2A", "EPAS1"],
                        "external_replay": {
                            "cptac3_m_stage": str(cptac),
                            "gse53757_tumor_normal": str(gse),
                        },
                    }
                ],
            }
        )
    )

    audit = audit_manifest(manifest, root=tmp_path)
    external = audit["tasks"][0]["external_replay"]
    cptac_result = next(item for item in external if item["label"] == "cptac3_m_stage")
    gse_result = next(item for item in external if item["label"] == "gse53757_tumor_normal")

    assert cptac_result["direction_preserved"] is True
    assert cptac_result["primary_failure_subtype"] == "underpowered_external_fail"
    assert "underpowered_external_fail" in cptac_result["failure_subtypes"]
    assert "single_gene_saturation_external" in cptac_result["failure_subtypes"]
    assert "missing_data" in cptac_result["failure_subtypes"]
    assert cptac_result["power_assessment"]["flag"] is True
    assert "positive_case_count_lt_40" in cptac_result["power_assessment"]["basis"]
    assert gse_result["primary_failure_subtype"] == "endpoint_mismatch"
    assert "endpoint_mismatch" in gse_result["failure_subtypes"]
    assert audit["metrics"]["strict_external_replay_rate"] == 0.0
    assert audit["metrics"]["interpretable_external_failure_rate"] == 1.0
    assert audit["metrics"]["underpowered_external_fail_rate"] == 0.5
    assert audit["metrics"]["endpoint_mismatch_rate"] == 0.5
    assert audit["metrics"]["missing_data_external_fail_rate"] == 0.5
    assert audit["external_replay_profile"]["failure_subtype_counts"]["missing_data"] == 1


def test_external_replay_metadata_controls_endpoint_classification(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            [
                {
                    "equation_named": "TOP2A - EPAS1",
                    "genes_used": ["TOP2A", "EPAS1"],
                    "passes": True,
                }
            ]
        )
    )
    external = tmp_path / "external.json"
    external.write_text(json.dumps({"verdict": "FAIL", "n_total": 144}))
    manifest = tmp_path / "bench.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test",
                "tasks": [
                    {
                        "task_id": "kirc",
                        "disease": "ccRCC",
                        "task_type": "blind_rediscovery",
                        "dataset_card": "cards/kirc.json",
                        "report_path": str(report),
                        "target_genes": ["TOP2A", "EPAS1"],
                        "external_replay": {
                            "generic_external_label": {
                                "path": str(external),
                                "endpoint": "tumor_normal",
                                "expected_endpoint": "metastasis_m_stage",
                                "endpoint_relation": "endpoint_mismatch",
                                "replay_role": "tumor_normal_specificity_probe",
                            }
                        },
                    }
                ],
            }
        )
    )

    audit = audit_manifest(manifest, root=tmp_path)
    result = audit["tasks"][0]["external_replay"][0]

    assert result["endpoint"] == "tumor_normal"
    assert result["expected_endpoint"] == "metastasis_m_stage"
    assert result["endpoint_relation"] == "endpoint_mismatch"
    assert result["primary_failure_subtype"] == "endpoint_mismatch"
    assert result["failure_subtypes"] == ["endpoint_mismatch"]
