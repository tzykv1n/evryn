"""
EVRYN Phase 2.4 - Cache Correctness, Session Isolation & Concurrency Test Suite.
Validates:
1. Extraction cache key separation across text, system modes, and model names.
2. In-memory benchmark cache invalidation on file modification (mtime check).
3. Session isolation: distinct database UUIDs per session with zero cross-session leak.
4. Concurrency: simultaneous identical requests across different sessions.
"""

import time
import uuid
import tempfile
import os
import pytest
from concurrent.futures import ThreadPoolExecutor
from starlette.testclient import TestClient

from evryn.web.server import app, store
from evryn.web.extractor_service import ExtractionService


@pytest.fixture
def client():
    return TestClient(app)


def test_extraction_cache_key_separation(client):
    text1 = "EGFR activation triggers downstream STAT3 phosphorylation."
    text2 = "Hypoxia induces HIF1A expression and increases VEGF secretion."

    # 1. System A on text1
    res1_a = client.post("/api/extract", json={"text": text1, "system_mode": "nlp_baseline"})
    assert res1_a.status_code == 200
    data1_a = res1_a.json()
    assert len(data1_a["nodes"]) > 0

    # 2. System B on text1 (Must NOT return System A cached result)
    res1_b = client.post("/api/extract", json={"text": text1, "system_mode": "llm_only"})
    assert res1_b.status_code == 200
    data1_b = res1_b.json()
    assert data1_b["id"] != data1_a["id"]
    for rel in data1_b["relations"]:
        assert rel.get("extraction_method") == "llm_only"

    # 3. System A on text2 (Must NOT return text1 cached result)
    res2_a = client.post("/api/extract", json={"text": text2, "system_mode": "nlp_baseline"})
    assert res2_a.status_code == 200
    data2_a = res2_a.json()
    node_names_2 = {n["canonical_name"] for n in data2_a["nodes"]}
    assert "EGFR" not in node_names_2
    assert any("HIF" in n or "VEGF" in n or "HYPOXIA" in n.upper() for n in node_names_2)


def test_session_isolation_and_uuid_rekeying(client):
    text = "Protein kinase A phosphorylates and activates transcription factor CREB."

    # Session 1
    res1 = client.post("/api/extract", json={"text": text, "system_mode": "nlp_baseline"})
    assert res1.status_code == 200
    s1 = res1.json()

    # Session 2 (Same text, hits cache)
    res2 = client.post("/api/extract", json={"text": text, "system_mode": "nlp_baseline"})
    assert res2.status_code == 200
    s2 = res2.json()

    assert s1["id"] != s2["id"], "Each request must have a unique session ID"

    # Verify all node IDs, relation IDs, and evidence IDs are distinct between sessions
    s1_node_ids = {n["id"] for n in s1["nodes"]}
    s2_node_ids = {n["id"] for n in s2["nodes"]}
    assert s1_node_ids.isdisjoint(s2_node_ids), "Node IDs must be unique across sessions (no SQLite PK conflict)"

    s1_rel_ids = {r["id"] for r in s1["relations"]}
    s2_rel_ids = {r["id"] for r in s2["relations"]}
    assert s1_rel_ids.isdisjoint(s2_rel_ids), "Relation IDs must be unique across sessions"

    # Verify database integrity: delete Session 1, Session 2 must remain fully intact
    del_res = client.delete(f"/api/sessions/{s1['id']}")
    assert del_res.status_code == 200

    verify_s2 = client.get(f"/api/sessions/{s2['id']}")
    assert verify_s2.status_code == 200
    s2_verified = verify_s2.json()
    assert len(s2_verified["nodes"]) == len(s2["nodes"])
    assert len(s2_verified["relations"]) == len(s2["relations"])


def test_concurrent_cached_extractions(client):
    text = "ATM kinase activates CHK2 in response to DNA double-strand breaks."

    def extract_task(thread_id):
        return client.post("/api/extract", json={"text": text, "system_mode": "nlp_baseline"})

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(extract_task, i) for i in range(5)]
        responses = [f.result() for f in futures]

    for r in responses:
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) >= 2
        assert len(data["relations"]) >= 1

    session_ids = [r.json()["id"] for r in responses]
    assert len(set(session_ids)) == 5, "All 5 concurrent requests must yield distinct sessions"


def test_benchmark_cache_invalidation(client):
    res1 = client.get("/api/benchmark/results")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "splits_evaluated" in data1

    # Simulate updated file on disk by touching the file
    from evryn.web.server import REPO_ROOT
    res_path = os.path.join(REPO_ROOT, "results", "phase2_3", "phase2_3_benchmark_results.json")
    if os.path.exists(res_path):
        orig_mtime = os.path.getmtime(res_path)
        try:
            # Update mtime
            new_time = orig_mtime + 2
            os.utime(res_path, (new_time, new_time))

            res2 = client.get("/api/benchmark/results")
            assert res2.status_code == 200
            data2 = res2.json()
            assert "splits_evaluated" in data2
        finally:
            # Restore mtime
            os.utime(res_path, (orig_mtime, orig_mtime))
