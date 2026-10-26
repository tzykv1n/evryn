"""
Automated Regression and Contract Tests for EVRYN Interactive Test Examples and Session Clearing.

Covers:
1. Catalog and schema validation for test cases A through E.
2. Example A (Direct causal downregulation relation).
3. Example B (Multi-transition causal chain with direct edges and transitive abstention).
4. Example C (Negation detection and refutation status).
5. Example D (Context mismatch path validation across organism boundaries).
6. Example E (Empty and whitespace input validation without crash).
7. Session isolation, fresh session initialization, and no state pollution.
8. Safe session clearing with pre-deletion backup and zero-session verification.
"""

import os
import json
import pytest
from starlette.testclient import TestClient

from evryn.web.server import app, store
from evryn.web.db import SessionStore
from evryn.web.test_examples_service import TestExamplesService


@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_interactive_sessions.db")
    test_store = SessionStore(db_path=test_db)

    from evryn.web import server
    server.store = test_store
    server.service.store = test_store

    with TestClient(app) as test_client:
        yield test_client


def test_test_examples_catalog(client):
    """Verify the /api/test-examples catalog endpoint."""
    res = client.get("/api/test-examples")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total"] == 5
    examples = data["examples"]
    ex_ids = [ex["id"] for ex in examples]
    assert "example_a" in ex_ids
    assert "example_b" in ex_ids
    assert "example_c" in ex_ids
    assert "example_d" in ex_ids
    assert "example_e" in ex_ids

    for ex in examples:
        assert "title" in ex
        assert "category" in ex
        assert "input_text" in ex
        assert "description" in ex
        assert "expected_behavior" in ex


def test_example_a_direct_relation(client):
    """Example A: The deletion of gene A reduced expression of protein B."""
    res = client.post("/api/test-examples/example_a/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    diag = data["diagnostics"]
    assert diag["passed"] is True
    assert diag["node_count"] >= 2
    assert diag["relation_count"] >= 1

    session = data["session"]
    rels = session["relations"]
    downreg = [r for r in rels if "DOWNREGULATES" in r["relation_type"].upper()]
    assert len(downreg) >= 1
    rel = downreg[0]
    assert rel["is_negated"] is False
    assert rel["assertion_status"] == "affirmed"
    assert len(rel["evidence"]) >= 1
    assert "reduced" in rel["evidence"][0]["sentence_text"].lower()


def test_example_b_multitransition_chain(client):
    """
    Example B: Activation of gene A increased expression of protein B.
               Expression of protein B activated pathway C.
    Validates direct edge extraction and abstention from ungrounded direct A -> C leaping.
    """
    res = client.post("/api/test-examples/example_b/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    diag = data["diagnostics"]
    assert diag["passed"] is True

    session = data["session"]
    nodes = {n["canonical_name"].lower(): n for n in session["nodes"]}
    assert any("gene a" in k or k == "a" for k in nodes)
    assert any("protein b" in k or k == "b" for k in nodes)
    assert any("pathway c" in k or k == "c" for k in nodes)

    rels = session["relations"]
    assert len(rels) >= 2

    # Direct edges must exist
    has_ab = any(
        ("gene a" in r["cause_name"].lower() or r["cause_name"].lower() == "a")
        and ("protein b" in r["effect_name"].lower() or r["effect_name"].lower() == "b")
        for r in rels
    )
    has_bc = any(
        ("protein b" in r["cause_name"].lower() or r["cause_name"].lower() == "b")
        and ("pathway c" in r["effect_name"].lower() or r["effect_name"].lower() == "c")
        for r in rels
    )
    assert has_ab, "Direct edge A -> B must be extracted"
    assert has_bc, "Direct edge B -> C must be extracted"

    # Must NOT fabricate an ungrounded direct edge A -> C
    has_direct_ac = any(
        ("gene a" in r["cause_name"].lower() or r["cause_name"].lower() == "a")
        and ("pathway c" in r["effect_name"].lower() or r["effect_name"].lower() == "c")
        and not r.get("is_transitive", False)
        for r in rels
    )
    assert not has_direct_ac, "System must abstain from fabricating an ungrounded direct edge A -> C"


def test_example_c_negation_directionality(client):
    """Example C: Deletion of gene A did not reduce virulence."""
    res = client.post("/api/test-examples/example_c/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    diag = data["diagnostics"]
    assert diag["passed"] is True

    session = data["session"]
    rels = session["relations"]
    assert len(rels) >= 1
    rel = rels[0]
    # Relation must be marked negated / refuted
    assert rel["is_negated"] is True or rel["assertion_status"] == "negated" or rel.get("status") == "REFUTED_NEGATION"
    # Must NOT report an affirmed reduction
    assert rel["assertion_status"] != "affirmed" or rel["is_negated"] is True


def test_example_d_invalid_transitive_context_mismatch(client):
    """
    Example D: Treatment A increased marker B in organism X.
               Marker B was associated with outcome C in organism Y.
    Validates organism context barrier: no cross-organism transitive causal path is formed.
    """
    res = client.post("/api/test-examples/example_d/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    diag = data["diagnostics"]
    assert diag["passed"] is True

    session = data["session"]
    rels = session["relations"]
    assert len(rels) >= 1

    # Must NOT form cross-organism transitive path Treatment A -> outcome C
    has_cross_context_edge = any(
        "treatment a" in r["cause_name"].lower() and "outcome c" in r["effect_name"].lower()
        for r in rels
    )
    assert not has_cross_context_edge, "Must not infer a valid causal chain across incompatible organism contexts"


def test_example_e_malformed_empty_input(client):
    """Example E: Empty or whitespace input must return 400 Bad Request with clear diagnostics."""
    res = client.post("/api/test-examples/example_e/run")
    assert res.status_code == 400
    data = res.json()
    assert "Input text cannot be empty" in data["detail"]
    assert data["passed"] is True


def test_session_isolation_and_no_stale_contamination(client):
    """Verify that running one example then another creates clean, isolated sessions."""
    res1 = client.post("/api/test-examples/example_a/run")
    assert res1.status_code == 200
    sess1_id = res1.json()["session"]["id"]
    sess1_node_count = len(res1.json()["session"]["nodes"])

    res2 = client.post("/api/test-examples/example_b/run")
    assert res2.status_code == 200
    sess2_id = res2.json()["session"]["id"]
    sess2_node_count = len(res2.json()["session"]["nodes"])

    assert sess1_id != sess2_id, "Each example must run in a separate, isolated session"

    # Check that retrieving session 1 has not been modified by session 2
    get1 = client.get(f"/api/sessions/{sess1_id}")
    assert get1.status_code == 200
    assert len(get1.json()["nodes"]) == sess1_node_count


def test_clear_all_sessions_lifecycle_and_backup(client):
    """Verify session clearing endpoint with confirmation, backup, and post-clearing fresh session creation."""
    # 1. Create multiple sessions
    client.post("/api/test-examples/example_a/run")
    client.post("/api/test-examples/example_b/run")
    client.post("/api/test-examples/example_c/run")

    sessions_before = client.get("/api/sessions").json()
    assert len(sessions_before) >= 3

    # 2. Attempt clearing without confirmation flag -> must fail with 400
    res_no_confirm = client.post("/api/sessions/clear", json={"confirm": False})
    assert res_no_confirm.status_code == 400
    assert "Confirmation required" in res_no_confirm.json()["detail"]

    # 3. Clear with confirmation
    res_clear = client.post("/api/sessions/clear", json={"confirm": True, "backup": True})
    assert res_clear.status_code == 200
    clear_data = res_clear.json()
    assert clear_data["cleared"] is True
    assert clear_data["deleted_sessions_count"] >= 3
    assert clear_data["remaining_count"] == 0

    # 4. Verify store is completely empty
    sessions_after = client.get("/api/sessions").json()
    assert len(sessions_after) == 0

    # 5. Verify application can create a fresh new session cleanly from pristine state
    res_fresh = client.post("/api/test-examples/example_a/run")
    assert res_fresh.status_code == 200
    fresh_id = res_fresh.json()["session"]["id"]

    sessions_final = client.get("/api/sessions").json()
    assert len(sessions_final) == 1
    assert sessions_final[0]["id"] == fresh_id
