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


def test_demo_examples_endpoint(client):
    res = client.get("/api/demo-examples")
    assert res.status_code == 200
    examples = res.json()
    assert len(examples) >= 5
    assert any("Direct" in ex["title"] for ex in examples)
    assert "text" in examples[0]
    assert "test_purpose" in examples[0]


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
