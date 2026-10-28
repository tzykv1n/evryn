import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from evryn.web.server import app, store
from evryn.web.db import SessionStore


@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_sessions.db")
    test_store = SessionStore(db_path=test_db)
    
    # Patch store in app
    from evryn.web import server
    server.store = test_store
    server.service.store = test_store

    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "EVRYN" in data["service"]


def test_extract_simple_causality(client):
    payload = {
        "text": "Epidermal growth factor receptor (EGFR) activation directly stimulates the downstream MAPK pathway."
    }
    res = client.post("/api/extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert len(data["nodes"]) >= 2
    assert len(data["relations"]) >= 1

    rel = data["relations"][0]
    assert rel["relation_type"] == "UPREGULATES"
    assert len(rel["evidence"]) >= 1
    assert "stimulates" in rel["evidence"][0]["sentence_text"]


def test_session_lifecycle_and_persistence(client):
    # 1. Create via extract
    payload = {"text": "Interleukin-6 activates STAT3 phosphorylation."}
    res1 = client.post("/api/extract", json=payload)
    assert res1.status_code == 200
    sess_id = res1.json()["id"]

    # 2. List sessions
    res2 = client.get("/api/sessions")
    assert res2.status_code == 200
    sessions = res2.json()
    assert any(s["id"] == sess_id for s in sessions)

    # 3. Retrieve session
    res3 = client.get(f"/api/sessions/{sess_id}")
    assert res3.status_code == 200
    sess_data = res3.json()
    assert sess_data["id"] == sess_id
    assert len(sess_data["nodes"]) >= 2

    # 4. Continuation in same session
    cont_payload = {
        "text": "Activated STAT3 stimulates the transcription of SOCS3, which downregulates JAK kinase activity."
    }
    res4 = client.post(f"/api/sessions/{sess_id}/continue", json=cont_payload)
    assert res4.status_code == 200
    cont_data = res4.json()
    assert cont_data["id"] == sess_id
    # Nodes count should have grown incrementally
    assert len(cont_data["nodes"]) > len(sess_data["nodes"])

    # 5. Delete session
    res5 = client.delete(f"/api/sessions/{sess_id}")
    assert res5.status_code == 200
    assert res5.json()["deleted"] is True

    # 6. Verify 404 after deletion
    res6 = client.get(f"/api/sessions/{sess_id}")
    assert res6.status_code == 404


def test_layout_position_persistence(client):
    payload = {"text": "A activates B."}
    res = client.post("/api/extract", json=payload)
    sess_id = res.json()["id"]

    layout_payload = {
        "positions": {
            "A": {"x": 120.5, "y": 240.0},
            "B": {"x": 350.0, "y": 420.5},
        }
    }
    res_layout = client.post(f"/api/sessions/{sess_id}/layout", json=layout_payload)
    assert res_layout.status_code == 200

    # Retrieve and verify coordinates
    res_get = client.get(f"/api/sessions/{sess_id}")
    nodes = {n["canonical_name"]: n for n in res_get.json()["nodes"]}
    if "A" in nodes:
        assert nodes["A"]["x"] == 120.5
        assert nodes["A"]["y"] == 240.0


def test_contradiction_preservation(client):
    # Statement 1: Positive regulation
    payload1 = {"text": "Compound X activates p53 signaling."}
    res1 = client.post("/api/extract", json=payload1)
    sess_id = res1.json()["id"]

    # Statement 2: Negation / contradiction
    payload2 = {"text": "Compound X does not activate p53 signaling."}
    res2 = client.post(f"/api/sessions/{sess_id}/continue", json=payload2)
    assert res2.status_code == 200
    data = res2.json()

    # Verify contradiction was recorded and multiple evidence pieces exist
    rel = [r for r in data["relations"] if "Compound X" in r["cause_name"] or "p53" in r["effect_name"]][0]
    assert rel["has_contradiction"] is True
    assert len(rel["evidence"]) >= 2


def test_synthetic_demo_examples_removed(client):
    """Verify that synthetic demo examples endpoint and files are completely removed."""
    import os
    res = client.get("/api/demo-examples")
    # Endpoint should not exist
    assert res.status_code == 404
    # Demo examples text files must not exist in web directory or repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(repo_root, "evryn", "web", "EVRYN_Demo_Examples.txt"))
    assert not os.path.exists(os.path.expanduser("~/Downloads/EVRYN_Demo_Examples.txt"))


def test_real_examples_endpoints(client):
    """Verify the Phase 2 real-paper evaluation examples endpoints."""
    # Summary
    res = client.get("/api/examples/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["synthetic_examples_active"] is False
    assert summary["total_papers"] == 20
    assert summary["split_counts"]["train"] == 4
    assert summary["split_counts"]["dev"] == 8
    assert summary["split_counts"]["locked_test"] == 4
    assert summary["split_counts"]["external"] == 4
    assert summary["sections"]["pdf_examples_count"] == 20

    # Catalog contract
    res = client.get("/api/examples/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert catalog["status"] == "success"
    assert catalog["version"] == "2.1.0"
    assert catalog["total"] == 20
    assert len(catalog["papers"]) == 20
    assert catalog["split_counts"]["dev"] == 8

    # Cache-control headers on root index and static assets
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "no-cache" in res_index.headers.get("cache-control", "").lower()
    html_text = res_index.text
    assert "style.css?v=2.1.0" in html_text
    assert "background.js?v=2.1.0" in html_text
    assert "graph.js?v=2.1.0" in html_text
    assert "app.js?v=2.1.0" in html_text

    res_css = client.get("/static/css/style.css?v=2.1.0")
    assert res_css.status_code == 200
    assert "no-cache" in res_css.headers.get("cache-control", "").lower()

    res_js = client.get("/static/js/app.js?v=2.1.0")
    assert res_js.status_code == 200
    assert "no-cache" in res_js.headers.get("cache-control", "").lower()

    # PDF examples
    res = client.get("/api/examples/pdf?split=dev")
    assert res.status_code == 200
    pdf_list = res.json()
    assert len(pdf_list) == 8
    assert all(p["split"] == "dev" for p in pdf_list)
    assert "direct_metrics" in pdf_list[0]
    assert "cross_page_metrics" in pdf_list[0]

    # Text examples
    res = client.get("/api/examples/text?limit=10")
    assert res.status_code == 200
    text_list = res.json()
    assert len(text_list) <= 10
    assert "passage_text" in text_list[0]
    assert "gold_cause" in text_list[0]

    # Multipage examples
    res = client.get("/api/examples/multipage?limit=5")
    assert res.status_code == 200
    multi_list = res.json()
    assert len(multi_list) <= 5
    assert "cause_concept" in multi_list[0]
    assert "effect_concept" in multi_list[0]

    # PDF serve endpoint
    res = client.get("/api/examples/paper/PMC1804205/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000


def test_file_upload_batch(client, tmp_path):
    f1 = tmp_path / "paper_alpha.txt"
    f1.write_text("Extracellular Wnt3a recruits Dishevelled to activate beta-catenin.", encoding="utf-8")

    f2 = tmp_path / "paper_beta.txt"
    f2.write_text("Beta-catenin translocates to activate Cyclin D1 expression.", encoding="utf-8")

    with open(f1, "rb") as b1, open(f2, "rb") as b2:
        res = client.post(
            "/api/upload",
            files=[
                ("files", ("paper_alpha.txt", b1, "text/plain")),
                ("files", ("paper_beta.txt", b2, "text/plain")),
            ],
        )

    assert res.status_code == 200
    data = res.json()
    assert len(data["documents"]) == 2
    assert data["documents"][0]["filename"] == "paper_alpha.txt"
    assert data["documents"][1]["filename"] == "paper_beta.txt"
    assert len(data["combined_graph"]["nodes"]) >= 3


def test_bulk_delete_sessions(client):
    res1 = client.post("/api/extract", json={"text": "Gene Alpha induces Factor Beta."})
    res2 = client.post("/api/extract", json={"text": "Factor Gamma inhibits Protein Delta."})
    assert res1.status_code == 200
    assert res2.status_code == 200
    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    del_res = client.post("/api/sessions/bulk-delete", json={"session_ids": [id1, id2]})
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["deleted_count"] == 2
    assert id1 not in [s["id"] for s in client.get("/api/sessions").json()]
    assert id2 not in [s["id"] for s in client.get("/api/sessions").json()]


def test_deduplicate_sessions(client):
    # Create duplicate sessions with identical text/title
    for _ in range(3):
        client.post("/api/extract", json={"text": "Heat activates HSP90, which suppresses cellular stress."})
    
    sessions_before = client.get("/api/sessions").json()
    titles = [s["title"] for s in sessions_before if "Heat activates HSP90" in s["title"]]
    assert len(titles) >= 3

    dedup_res = client.post("/api/sessions/deduplicate")
    assert dedup_res.status_code == 200
    dedup_data = dedup_res.json()
    assert dedup_data["removed_count"] >= 2

    sessions_after = client.get("/api/sessions").json()
    titles_after = [s["title"] for s in sessions_after if "Heat activates HSP90" in s["title"]]
    assert len(titles_after) == 1


def test_extract_with_system_modes(client):
    """Verify Phase 2.2 selectable extraction backends via API."""
    text = "Activation of PmrB directly upregulates PmrA transcription."

    # 1. System A (NLP baseline)
    res_a = client.post("/api/extract", json={"text": text, "system_mode": "nlp_baseline"})
    assert res_a.status_code == 200
    assert len(res_a.json()["relations"]) >= 1

    # 2. System B (LLM-only)
    res_b = client.post("/api/extract", json={"text": text, "system_mode": "llm_only"})
    assert res_b.status_code == 200
    assert len(res_b.json()["relations"]) >= 1

    # 3. System C (Hybrid LLM + Validation)
    res_c = client.post("/api/extract", json={"text": text, "system_mode": "hybrid"})
    assert res_c.status_code == 200
    assert len(res_c.json()["relations"]) >= 1
    rel = res_c.json()["relations"][0]
    assert rel["validation_status"] == "ACCEPTED"


def test_phase2_3_benchmark_endpoints(client):
    """Verify Phase 2.3 benchmark evaluation endpoints."""
    # 1. /api/benchmark/results
    b_res = client.get("/api/benchmark/results")
    assert b_res.status_code == 200
    data = b_res.json()
    assert "splits_evaluated" in data
    assert "dev" in data["splits_evaluated"]
    assert "locked_test" in data["splits_evaluated"]
    assert "external" in data["splits_evaluated"]
    assert "results" in data
    assert "nlp_baseline" in data["results"]["dev"]

    # 2. /api/evaluate
    ev_res = client.post("/api/evaluate")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["status"] == "completed"
    assert ev_data["phase"] == "Phase 2.3"
    assert "direct_precision" in ev_data["metrics"]
    assert ev_data["metrics"]["direct_precision"] >= 0.50
    assert ev_data["metrics"]["direct_f1"] >= 0.65


def test_phase3_api_endpoints(client):
    """Verify Phase 3 causal chains and cross-paper API endpoints."""
    # 1. /api/phase3/results
    res = client.get("/api/phase3/results")
    assert res.status_code == 200
    data = res.json()
    assert "ablation_matrix" in data
    assert len(data["ablation_matrix"]) == 8
    assert "full_evaluation" in data
    assert "splits" in data["full_evaluation"]
    assert "dev" in data["full_evaluation"]["splits"]
    assert "train" in data["full_evaluation"]["splits"]
    assert "locked_test" in data["full_evaluation"]["splits"]
    assert "external" in data["full_evaluation"]["splits"]

    # 2. /api/phase3/chains/PMC1804205
    chains_res = client.get("/api/phase3/chains/PMC1804205")
    assert chains_res.status_code == 200
    p_data = chains_res.json()
    assert p_data["pmcid"] == "PMC1804205"
    assert "chain_length_recovery" in p_data
    assert "composition_class_distribution" in p_data

    # 3. /api/phase3/cross-paper-links
    links_res = client.get("/api/phase3/cross-paper-links")
    assert links_res.status_code == 200
    bridges = links_res.json()
    assert isinstance(bridges, list)
    assert len(bridges) >= 1
    pair1 = bridges[0]
    assert "paper_pair" in pair1
    assert "bridges_discovered_count" in pair1


def test_phase3_2_api_endpoint(client):
    """Verify Phase 3.2 independent validation results API endpoint."""
    res = client.get("/api/phase3_2/results")
    assert res.status_code == 200
    data = res.json()
    assert data["phase"] == "3.2"
    assert "track1_and_2_composition_validation" in data
    assert "track3_semeval_task8_framing" in data
    assert "track4_and_5_biocause_and_scierc" in data
    assert "track6_cross_paper_adjudication" in data
    assert "track7_external_direct_extraction" in data



