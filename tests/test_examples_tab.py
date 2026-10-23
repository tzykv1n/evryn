"""
Tests for EVRYN Phase 2 Real-Paper Causal Evaluation Examples Tab.
Validates:
1. 3 distinct sections (PDF, Text, Multipage) with real-paper data.
2. Authentic PubMed Central Open Access and BioCause grounding (zero synthetic demo graphs).
3. Strict paper split separation (Train, Dev, Locked Test, External Generalization).
4. Direct and cross-page P/R/F1 with explicit denominators.
5. Workspace integration via /api/examples/load.
"""

import os
import json
import pytest
from starlette.testclient import TestClient

from evryn.web.server import app, store
from evryn.web.real_examples_service import RealExamplesService


@pytest.fixture
def client():
    return TestClient(app)


def test_examples_summary(client):
    res = client.get("/api/examples/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["synthetic_examples_active"] is False
    assert data["total_papers"] == 20
    assert data["split_counts"]["train"] == 4
    assert data["split_counts"]["dev"] == 8
    assert data["split_counts"]["locked_test"] == 4
    assert data["split_counts"]["external"] == 4

    assert data["sections"]["pdf_examples_count"] == 20
    assert data["sections"]["text_examples_count"] >= 10
    assert data["sections"]["multipage_examples_count"] >= 10


def test_pdf_examples_section(client):
    # Test all splits
    res = client.get("/api/examples/pdf")
    assert res.status_code == 200
    papers = res.json()
    assert len(papers) == 20

    # Verify real provenance and fields
    for p in papers:
        assert p["pmcid"].startswith("PMC")
        assert len(p["title"]) > 10
        assert p["page_count"] >= 2
        assert p["pdf_url"].endswith(f"/api/examples/paper/{p['pmcid']}/pdf")
        assert "direct_metrics" in p
        assert "cross_page_metrics" in p

        # Verify explicit denominators
        dm = p["direct_metrics"]
        assert "tp" in dm and "fp" in dm and "fn" in dm
        assert "precision" in dm and "recall" in dm and "f1" in dm
        assert "denominator_explanation" in dm

    # Test filtering by split
    dev_res = client.get("/api/examples/pdf?split=dev")
    assert dev_res.status_code == 200
    dev_papers = dev_res.json()
    assert len(dev_papers) == 8
    assert all(p["split"] == "dev" for p in dev_papers)

    test_res = client.get("/api/examples/pdf?split=locked_test")
    assert test_res.status_code == 200
    test_papers = test_res.json()
    assert len(test_papers) == 4
    assert all(p["split"] == "locked_test" for p in test_papers)


def test_text_examples_section(client):
    res = client.get("/api/examples/text?limit=30")
    assert res.status_code == 200
    text_exs = res.json()
    assert len(text_exs) <= 30
    assert len(text_exs) > 0

    for t in text_exs:
        assert len(t["passage_text"]) > 15
        assert len(t["gold_cause"]) > 0
        assert len(t["gold_effect"]) > 0
        assert t["match_status"] in ("TRUE_POSITIVE", "FALSE_NEGATIVE")
        assert len(t["diagnostic"]) > 0


def test_multipage_examples_section(client):
    res = client.get("/api/examples/multipage?limit=20")
    assert res.status_code == 200
    multi_exs = res.json()
    assert len(multi_exs) <= 20
    assert len(multi_exs) > 0

    for m in multi_exs:
        assert len(m["cause_concept"]) > 0
        assert len(m["effect_concept"]) > 0
        assert len(m["cause_passage"]) > 0
        assert len(m["effect_passage"]) > 0
        assert len(m["cause_location"]) > 0
        assert len(m["effect_location"]) > 0
        assert len(m["bridge_mechanism"]) > 0


def test_paper_pdf_and_detail(client):
    # PMC1804205 (Dev paper)
    res_pdf = client.get("/api/examples/paper/PMC1804205/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000

    res_detail = client.get("/api/examples/paper/PMC1804205")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["metadata"]["pmcid"] == "PMC1804205"
    assert len(detail["sections"]) >= 10
    assert len(detail["gold_relations"]) > 0
    assert len(detail["predicted_assertions"]) > 0


def test_strict_split_isolation():
    """Verify that paper splits are mutually exclusive and have zero leakage."""
    svc = RealExamplesService.get_instance()
    manifest = svc.get_manifest()
    papers = manifest["papers"]

    train_ids = {p["pmcid"] for p in papers if p["split"] == "train"}
    dev_ids = {p["pmcid"] for p in papers if p["split"] == "dev"}
    locked_ids = {p["pmcid"] for p in papers if p["split"] == "locked_test"}
    external_ids = {p["pmcid"] for p in papers if p["split"] == "external"}

    assert len(train_ids) == 4
    assert len(dev_ids) == 8
    assert len(locked_ids) == 4
    assert len(external_ids) == 4

    # Pairwise intersections must be empty
    assert len(train_ids & dev_ids) == 0
    assert len(train_ids & locked_ids) == 0
    assert len(train_ids & external_ids) == 0
    assert len(dev_ids & locked_ids) == 0
    assert len(dev_ids & external_ids) == 0
    assert len(locked_ids & external_ids) == 0


def test_load_example_to_workspace(client):
    # Load passage text into workspace
    payload = {
        "text": "Growth in mild acid (pH 5.8) promotes transcription of genes activated by the response regulator PmrA.",
        "title": "Passage Test Example"
    }
    res = client.post("/api/examples/load", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert len(data["nodes"]) >= 2
    assert any("PmrA" in n["canonical_name"] or "acid" in n["canonical_name"].lower() for n in data["nodes"])
