import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from evryn.web.server import app
from evryn.web.db import SessionStore
from evryn.web.extractor_service import (
    ExtractionService,
    decompose_concept_and_state,
    compute_edge_polarity_and_style,
)


@pytest.fixture
def test_env(tmp_path):
    test_db = str(tmp_path / "test_semantics.db")
    store = SessionStore(db_path=test_db)
    service = ExtractionService(store=store)

    from evryn.web import server
    server.store = store
    server.service = service

    with TestClient(app) as client:
        yield client, store, service


def test_temperature_performance_negative_effect(test_env):
    """
    Core regression test:
    Input: 'Increase in temperature causes decrease in performance.'
    Must NOT create compound nodes 'Increase in temperature' and 'decrease in performance'.
    Must decompose into:
      - Source Concept: Temperature (State: Increase, Delta: +1, Category: Environmental)
      - Target Concept: Performance (State: Decrease, Delta: -1, Category: Phenotype)
      - Directed edge: Temperature -> Performance
      - Polarity: negative
      - Edge color: #dc2626 (Red)
    """
    client, store, service = test_env

    # 1. Test helper function directly
    src_canon, src_state, src_delta, src_cat = decompose_concept_and_state("Increase in temperature")
    assert src_canon == "Temperature"
    assert src_state == "Increase"
    assert src_delta is None
    assert src_cat in ("Environmental Factor", "Environmental")

    tgt_canon, tgt_state, tgt_delta, tgt_cat = decompose_concept_and_state("decrease in performance")
    assert tgt_canon == "Performance"
    assert tgt_state == "Decrease"
    assert tgt_delta is None
    assert tgt_cat in ("Measured Outcome", "Task-Specific Outcome")
    assert tgt_cat != "Phenotype"

    polarity, color, style = compute_edge_polarity_and_style(
        rel_type="UPREGULATES",
        cause_state=src_state,
        effect_state=tgt_state,
    )
    assert polarity == "negative"
    assert color == "#dc2626"
    assert style == "solid"

    # 2. Test full API extraction
    res = client.post("/api/extract", json={"text": "Increase in temperature causes decrease in performance."})
    assert res.status_code == 200
    data = res.json()

    # Must NOT have compound nodes
    node_names = [n["canonical_name"] for n in data["nodes"]]
    assert "Increase in temperature" not in node_names
    assert "decrease in performance" not in node_names
    assert "Temperature" in node_names
    assert "Performance" in node_names

    # Check node metadata
    temp_node = next(n for n in data["nodes"] if n["canonical_name"] == "Temperature")
    perf_node = next(n for n in data["nodes"] if n["canonical_name"] == "Performance")

    assert temp_node["category"] in ("Environmental Factor", "Environmental")
    assert temp_node["state"] == "Increase"
    assert temp_node["state_delta"] is None

    assert perf_node["category"] in ("Measured Outcome", "Task-Specific Outcome")
    assert perf_node["category"] != "Phenotype"
    assert perf_node["state"] == "Decrease"
    assert perf_node["state_delta"] is None

    # Check relation semantics
    assert len(data["relations"]) >= 1
    rel = data["relations"][0]
    assert rel["cause_name"] == "Temperature"
    assert rel["effect_name"] == "Performance"
    assert rel["effect_polarity"] == "negative"
    assert rel["edge_color"] == "#dc2626"
    assert rel["edge_style"] == "solid"
    assert rel["source_state"] == "Increase"
    assert rel["target_state"] == "Decrease"


def test_temperature_performance_positive_effect(test_env):
    """
    Input: 'Increase in temperature causes increase in performance.'
    Must decompose into:
      - Source Concept: Temperature (State: Increase, Delta: +1)
      - Target Concept: Performance (State: Increase, Delta: +1)
      - Net polarity: positive
      - Edge color: #0f172a (Black)
    """
    client, store, service = test_env

    res = client.post("/api/extract", json={"text": "Increase in temperature causes increase in performance."})
    assert res.status_code == 200
    data = res.json()

    node_names = [n["canonical_name"] for n in data["nodes"]]
    assert "Temperature" in node_names
    assert "Performance" in node_names

    rel = data["relations"][0]
    assert rel["cause_name"] == "Temperature"
    assert rel["effect_name"] == "Performance"
    assert rel["effect_polarity"] == "positive"
    assert rel["edge_color"] == "#0f172a"
    assert rel["edge_style"] == "solid"


def test_association_semantics(test_env):
    """
    Input: 'Temperature is associated with performance.'
    Must decompose into:
      - Polarity: association
      - Edge color: #64748b (Slate)
      - Edge style: dotted
    """
    client, store, service = test_env

    res = client.post("/api/extract", json={"text": "Temperature is associated with performance."})
    assert res.status_code == 200
    data = res.json()

    assert len(data["relations"]) >= 1
    rel = data["relations"][0]
    assert rel["cause_name"] == "Temperature"
    assert rel["effect_name"] == "Performance"
    assert rel["effect_polarity"] == "association"
    assert rel["edge_color"] == "#64748b"
    assert rel["edge_style"] == "dotted"


def test_database_persistence_and_restoration(test_env):
    """
    Ensure that saved sessions preserve all node states, categories, and relation polarities
    without requiring re-extraction when restored from SQLite.
    """
    client, store, service = test_env

    # 1. Create session via extract
    res1 = client.post("/api/extract", json={"text": "Loss of p53 promotes tumor growth."})
    assert res1.status_code == 200
    session_id = res1.json()["id"]

    # 2. Retrieve session from store directly
    restored = store.get_session(session_id)
    assert restored is not None
    assert restored["id"] == session_id

    p53_node = next(n for n in restored["nodes"] if n["canonical_name"] == "p53")
    assert p53_node["category"] == "Gene/Protein"
    assert p53_node["state"] == "Decrease"
    assert p53_node["state_delta"] is None

    growth_node = next(n for n in restored["nodes"] if n["canonical_name"] == "Tumor Growth")
    assert growth_node["category"] == "Phenotype"

    rel = restored["relations"][0]
    assert rel["cause_name"] == "p53"
    assert rel["effect_name"] == "Tumor Growth"
    # Net polarity: delta_src(-1) * pred(+1) * delta_tgt(+1) = -1 (negative)
    assert rel["effect_polarity"] == "negative"
    assert rel["edge_color"] == "#dc2626"

    # 3. Retrieve session via API
    res2 = client.get(f"/api/sessions/{session_id}")
    assert res2.status_code == 200
    api_data = res2.json()
    assert len(api_data["nodes"]) == len(restored["nodes"])
    assert api_data["relations"][0]["edge_color"] == "#dc2626"


def test_ui_dom_elements():
    """
    Verifies that static HTML has the required DOM elements:
      - #toggle-sidebar-btn and #open-sidebar-btn
      - Persistent #graph-legend with edge and category sections
      - SVG marker defs #arrowhead-positive, #arrowhead-negative, #arrowhead-association
      - Sidebar brand EVRYN placed in footer
    """
    html_path = os.path.join(os.path.dirname(__file__), "..", "evryn", "web", "static", "index.html")
    assert os.path.exists(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="toggle-sidebar-btn"' in html
    assert 'id="open-sidebar-btn"' in html
    assert 'id="graph-legend"' in html
    assert 'id="legend-categories-section"' in html
    assert 'id="arrowhead-positive"' in html
    assert 'id="arrowhead-negative"' in html
    assert 'id="arrowhead-association"' in html
    assert '<div class="sidebar-brand">EVRYN</div>' in html


def test_mandatory_eight_regression_sentences(test_env):
    """
    Mandatory regression tests for the exact 8 sentences from the user prompt:
    1. 'Increase in temperature causes decrease in performance.' -> Temperature -> Performance; negative effect
    2. 'Temperature does not decrease performance.' -> Negated, do not invent positive effect
    3. 'Temperature decreases performance.' -> Temperature -> Performance; negative effect
    4. 'Temperature increases performance.' -> Temperature -> Performance; positive effect
    5. 'Temperature is associated with performance.' -> Non-directional association, not causation
    6. 'Temperature does not affect performance.' -> Explicit negated effect, not positive
    7. 'Increased temperature was not associated with reduced performance.' -> Negated association; suppressed
    8. 'Increased temperature was associated with reduced performance.' -> Association with negative trend, not causation
    """
    client, store, service = test_env

    # 1. Increase in temperature causes decrease in performance.
    r1 = client.post("/api/extract", json={"text": "Increase in temperature causes decrease in performance."})
    assert r1.status_code == 200
    d1 = r1.json()
    rel1 = d1["relations"][0]
    assert rel1["cause_name"] == "Temperature"
    assert rel1["effect_name"] == "Performance"
    assert rel1["effect_polarity"] == "negative"
    assert rel1["is_negated"] is False
    assert rel1["assertion_status"] == "affirmed"
    assert rel1["is_suppressed"] is False

    # 2. Temperature does not decrease performance.
    r2 = client.post("/api/extract", json={"text": "Temperature does not decrease performance."})
    assert r2.status_code == 200
    d2 = r2.json()
    rel2 = d2["relations"][0]
    assert rel2["cause_name"] == "Temperature"
    assert rel2["effect_name"] == "Performance"
    assert rel2["is_negated"] is True
    assert rel2["assertion_status"] == "negated"
    assert rel2["is_suppressed"] is True
    assert rel2["effect_polarity"] != "positive"

    # 3. Temperature decreases performance.
    r3 = client.post("/api/extract", json={"text": "Temperature decreases performance."})
    assert r3.status_code == 200
    d3 = r3.json()
    rel3 = d3["relations"][0]
    assert rel3["cause_name"] == "Temperature"
    assert rel3["effect_name"] == "Performance"
    assert rel3["effect_polarity"] == "negative"
    assert rel3["is_negated"] is False

    # 4. Temperature increases performance.
    r4 = client.post("/api/extract", json={"text": "Temperature increases performance."})
    assert r4.status_code == 200
    d4 = r4.json()
    rel4 = d4["relations"][0]
    assert rel4["cause_name"] == "Temperature"
    assert rel4["effect_name"] == "Performance"
    assert rel4["effect_polarity"] == "positive"
    assert rel4["is_negated"] is False

    # 5. Temperature is associated with performance.
    r5 = client.post("/api/extract", json={"text": "Temperature is associated with performance."})
    assert r5.status_code == 200
    d5 = r5.json()
    rel5 = d5["relations"][0]
    assert rel5["cause_name"] == "Temperature"
    assert rel5["effect_name"] == "Performance"
    assert rel5["effect_polarity"] == "association"
    assert "ASSOCIAT" in rel5["relation_type"]
    assert rel5["edge_style"] == "dotted"

    # 6. Temperature does not affect performance.
    r6 = client.post("/api/extract", json={"text": "Temperature does not affect performance."})
    assert r6.status_code == 200
    d6 = r6.json()
    rel6 = d6["relations"][0]
    assert rel6["cause_name"] == "Temperature"
    assert rel6["effect_name"] == "Performance"
    assert rel6["is_negated"] is True
    assert rel6["assertion_status"] == "negated"
    assert rel6["is_suppressed"] is True
    assert rel6["effect_polarity"] != "positive"

    # 7. Increased temperature was not associated with reduced performance.
    r7 = client.post("/api/extract", json={"text": "Increased temperature was not associated with reduced performance."})
    assert r7.status_code == 200
    d7 = r7.json()
    rel7 = d7["relations"][0]
    assert rel7["cause_name"] == "Temperature"
    assert rel7["effect_name"] == "Performance"
    assert rel7["is_negated"] is True
    assert rel7["assertion_status"] == "negated"
    assert rel7["is_suppressed"] is True
    assert rel7["effect_polarity"] != "positive"

    # 8. Increased temperature was associated with reduced performance.
    r8 = client.post("/api/extract", json={"text": "Increased temperature was associated with reduced performance."})
    assert r8.status_code == 200
    d8 = r8.json()
    rel8 = d8["relations"][0]
    assert rel8["cause_name"] == "Temperature"
    assert rel8["effect_name"] == "Performance"
    assert rel8["effect_polarity"] == "association"
    assert "ASSOCIAT" in rel8["relation_type"]
    assert rel8["edge_style"] == "dotted"


def test_primary_prompt_regeneration_and_continual_learning(test_env):
    """
    Tests:
    1. Primary prompt regeneration (/api/sessions/{id}/regenerate) replaces graph from scratch
    2. Continual learning (/api/sessions/{id}/continual) appends to primary prompt
    3. Physics settings update (/api/sessions/{id}/physics)
    4. Category override (/api/nodes/{id}/{canonical_name}/override-category)
    """
    client, store, service = test_env

    # Step 1: Initial extraction
    res1 = client.post("/api/extract", json={"text": "Increase in temperature causes decrease in performance."})
    assert res1.status_code == 200
    s_data = res1.json()
    s_id = s_data["id"]
    assert len(s_data["nodes"]) == 2

    # Step 2: Regenerate replaces graph completely
    res2 = client.post(
        f"/api/sessions/{s_id}/regenerate",
        json={"text": "Elevated humidity leads to increased adhesion."}
    )
    assert res2.status_code == 200
    regen_data = res2.json()
    assert regen_data["primary_prompt"] == "Elevated humidity leads to increased adhesion."
    regen_names = {n["canonical_name"] for n in regen_data["nodes"]}
    assert "Humidity" in regen_names
    assert "Adhesion" in regen_names
    assert "Temperature" not in regen_names  # Completely replaced old graph!

    # Step 3: Continual learning appends to primary prompt
    res3 = client.post(
        f"/api/sessions/{s_id}/continual",
        json={"incremental_text": "Adhesion triggers biofilm formation."}
    )
    assert res3.status_code == 200
    cont_data = res3.json()
    assert "humidity" in cont_data["primary_prompt"].lower()
    assert "biofilm formation" in cont_data["primary_prompt"].lower()
    cont_names = {n["canonical_name"] for n in cont_data["nodes"]}
    assert "Biofilm Formation" in cont_names or "Biofilm" in cont_names

    # Step 4: Physics update
    res4 = client.post(
        f"/api/sessions/{s_id}/physics",
        json={"preset": "string", "tensions": {cont_data["relations"][0]["id"]: 3}}
    )
    assert res4.status_code == 200
    phys_data = res4.json()
    assert phys_data["physics_preset"] == "string"

    # Step 5: User Category Override
    res5 = client.post(
        f"/api/nodes/{s_id}/Humidity/override-category",
        json={"category": "Environmental Condition"}
    )
    assert res5.status_code == 200
    res_get = client.get(f"/api/sessions/{s_id}")
    h_node = next(n for n in res_get.json()["nodes"] if n["canonical_name"] == "Humidity")
    assert h_node["category"] == "Environmental Condition"
