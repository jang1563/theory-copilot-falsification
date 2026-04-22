"""Tests for the MCP biology-validator module (E8).

All HTTP is mocked — these tests never touch the network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# src/ is on PYTHONPATH via pytest invocation; if not, fall back gracefully.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import mcp_biology_validator as mbv  # noqa: E402


@pytest.fixture
def fake_http():
    http = MagicMock(spec=mbv.HttpClient)
    return http


# --- validate_law ---------------------------------------------------------


def test_validate_law_happy_path(fake_http):
    fake_http.get_json.side_effect = [
        {"esearchresult": {"count": "42", "idlist": ["38730293", "20871783"]}},
        {
            "result": {
                "38730293": {
                    "title": "TOP2A in ccRCC",
                    "pubdate": "2024 May 8",
                },
                "20871783": {
                    "title": "Brannon ccRCC subtype",
                    "pubdate": "2010 Oct",
                },
            }
        },
    ]
    payload = mbv.validate_law(["TOP2A", "EPAS1"], disease="ccRCC", http=fake_http)

    assert payload["total_results"] == 42
    assert len(payload["top_results"]) == 2
    assert payload["top_results"][0]["pmid"] == "38730293"
    assert payload["top_results"][0]["title"] == "TOP2A in ccRCC"
    assert "query" in payload
    assert "ccRCC" in payload["query"]
    assert "heuristic" in payload["note"]


def test_validate_law_empty_input():
    out = mbv.validate_law([])
    assert "error" in out


def test_validate_law_no_disease_builds_plain_query(fake_http):
    fake_http.get_json.return_value = {
        "esearchresult": {"count": "0", "idlist": []},
    }
    payload = mbv.validate_law(["CA9"], http=fake_http)
    assert payload["total_results"] == 0
    assert payload["top_results"] == []
    assert "AND" not in payload["query"]  # single gene -> no AND


def test_validate_law_esearch_failure_reports_error(fake_http):
    fake_http.get_json.side_effect = RuntimeError("timeout")
    payload = mbv.validate_law(["TOP2A"], http=fake_http)
    assert "error" in payload
    assert "timeout" in payload["error"]


# --- fetch_cohort_summary -------------------------------------------------


def test_fetch_cohort_summary_happy_path(fake_http):
    fake_http.get_json.return_value = {
        "data": {
            "project_id": "TCGA-KIRC",
            "name": "Kidney Renal Clear Cell Carcinoma",
            "disease_type": ["Adenomas and Adenocarcinomas"],
            "primary_site": ["Kidney"],
            "summary": {
                "case_count": 537,
                "file_count": 5432,
                "data_categories": [
                    {"data_category": "Transcriptome Profiling", "file_count": 1000},
                    {"data_category": "Copy Number Variation", "file_count": 500},
                ],
            },
        }
    }
    out = mbv.fetch_cohort_summary("TCGA-KIRC", http=fake_http)
    assert out["project_id"] == "TCGA-KIRC"
    assert out["case_count"] == 537
    assert "Transcriptome Profiling" in out["data_categories"]


def test_fetch_cohort_summary_empty_id():
    out = mbv.fetch_cohort_summary("")
    assert "error" in out


def test_fetch_cohort_summary_gdc_failure(fake_http):
    fake_http.get_json.side_effect = Exception("500")
    out = mbv.fetch_cohort_summary("TCGA-NOPE", http=fake_http)
    assert "error" in out


# --- CLI ------------------------------------------------------------------


def test_cli_validate_law_prints_json(monkeypatch, capsys):
    calls = {}

    def fake_validate(**kwargs):
        calls.update(kwargs)
        return {"total_results": 7, "query": "stub", "top_results": [], "note": "x"}

    monkeypatch.setattr(mbv, "validate_law", fake_validate)
    monkeypatch.setattr(
        sys, "argv",
        ["mcp_biology_validator.py", "--tool", "validate_law",
         "--genes", "TOP2A,EPAS1", "--disease", "ccRCC"],
    )
    rc = mbv.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["total_results"] == 7
    assert calls["gene_symbols"] == ["TOP2A", "EPAS1"]
    assert calls["disease"] == "ccRCC"


def test_cli_fetch_cohort_summary(monkeypatch, capsys):
    monkeypatch.setattr(
        mbv, "fetch_cohort_summary",
        lambda **kw: {"project_id": kw["project_id"], "case_count": 1},
    )
    monkeypatch.setattr(
        sys, "argv",
        ["mcp_biology_validator.py", "--tool", "fetch_cohort_summary",
         "--project-id", "TCGA-KIRC"],
    )
    rc = mbv.main()
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert data["project_id"] == "TCGA-KIRC"
