#!/usr/bin/env python3
"""Comprehensive live verification of EVRYN web server endpoints, engines, and persistence."""
import sys
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_live_server():
    print(f"Testing live server at {BASE_URL}...")
    
    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health = r.json()
    assert health["status"] == "healthy"
    print(" [PASS] Health check OK:", health)
    
    # 2. Benchmark results API
    r = requests.get(f"{BASE_URL}/api/benchmark/results")
    assert r.status_code == 200, f"Benchmark results failed: {r.status_code}"
    bench = r.json()
    assert "results" in bench
    assert "dev" in bench["results"]
    assert "locked_test" in bench["results"]
    assert "external" in bench["results"]
    print(" [PASS] Benchmark results API OK: splits =", list(bench["results"].keys()))
    
    # 3. Extraction with System A (Repaired NLP)
    payload_a = {
        "text": "Low magnesium concentrations activate PhoQ kinase activity, which phosphorylates PhoP. Phosphorylated PhoP directly activates pmrD transcription, promoting polymyxin resistance.",
        "engine": "nlp_baseline"
    }
    r = requests.post(f"{BASE_URL}/api/extract", json=payload_a)
    assert r.status_code == 200, f"System A extract failed: {r.status_code}"
    data_a = r.json()
    session_id = data_a["id"]
    nodes_a = data_a["nodes"]
    relations_a = data_a["relations"]
    assert len(nodes_a) >= 2, f"Expected >= 2 nodes, got {len(nodes_a)}"
    assert len(relations_a) >= 1, f"Expected >= 1 relation, got {len(relations_a)}"
    print(f" [PASS] System A (NLP Baseline): Extracted {len(nodes_a)} nodes, {len(relations_a)} relations. Session ID: {session_id}")
    
    # Check evidence distinctions
    for rel in relations_a:
        assert "relation_type" in rel
        assert "evidence" in rel
        assert "edge_color" in rel
        assert "edge_style" in rel
        assert "extraction_method" in rel
    print(" [PASS] System A relations contain rich evidence, edge_color, edge_style, and extraction_method.")

    # 4. Extraction with System B (LLM-Only)
    payload_b = {
        "text": "Acid pH activates the PmrA/PmrB system, leading to polymyxin B resistance in Salmonella enterica.",
        "engine": "llm_only"
    }
    r = requests.post(f"{BASE_URL}/api/extract", json=payload_b)
    assert r.status_code == 200, f"System B extract failed: {r.status_code}"
    data_b = r.json()
    print(f" [PASS] System B (LLM-Only): Extracted {len(data_b['nodes'])} nodes, {len(data_b['relations'])} relations.")

    # 5. Extraction with System C (Hybrid LLM + Validation)
    payload_c = {
        "text": "Acid pH activates the PmrA/PmrB system, leading to polymyxin B resistance in Salmonella enterica.",
        "engine": "hybrid"
    }
    r = requests.post(f"{BASE_URL}/api/extract", json=payload_c)
    assert r.status_code == 200, f"System C extract failed: {r.status_code}"
    data_c = r.json()
    print(f" [PASS] System C (Hybrid): Extracted {len(data_c['nodes'])} nodes, {len(data_c['relations'])} relations.")

    # 6. Session Persistence & Retrieval
    r = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    assert r.status_code == 200, f"Session retrieval failed: {r.status_code}"
    sess = r.json()
    assert sess["id"] == session_id
    assert len(sess["nodes"]) == len(nodes_a)
    print(f" [PASS] Session retrieval verified for {session_id}")

    # 7. Evaluate endpoint
    r = requests.post(f"{BASE_URL}/api/evaluate")
    assert r.status_code == 200, f"Evaluate endpoint failed: {r.status_code}"
    eval_res = r.json()
    assert "metrics" in eval_res
    print(f" [PASS] Evaluate endpoint returned metrics: F1={eval_res['metrics'].get('f1')}")

    # 7b. File upload batch
    files_payload = [
        ("files", ("paper_alpha.txt", "Extracellular Wnt3a recruits Dishevelled to activate beta-catenin.", "text/plain")),
        ("files", ("paper_beta.txt", "Beta-catenin translocates to activate Cyclin D1 expression.", "text/plain"))
    ]
    r = requests.post(f"{BASE_URL}/api/upload", files=files_payload)
    assert r.status_code == 200, f"Upload endpoint failed: {r.status_code}"
    upload_data = r.json()
    assert len(upload_data["documents"]) == 2
    assert len(upload_data["combined_graph"]["nodes"]) >= 3
    print(f" [PASS] File upload batch: uploaded 2 documents, combined graph has {len(upload_data['combined_graph']['nodes'])} nodes.")

    # 8. Edge cases: Empty input
    r = requests.post(f"{BASE_URL}/api/extract", json={"text": ""})
    assert r.status_code in [200, 400, 422], f"Unexpected status on empty: {r.status_code}"
    print(f" [PASS] Empty text handled gracefully with status {r.status_code}")

    # 9. Edge cases: Malformed json
    r = requests.post(f"{BASE_URL}/api/extract", data="invalid json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422, f"Expected 422 for malformed json, got {r.status_code}"
    print(f" [PASS] Malformed JSON handled gracefully with status 422")

    print("\nALL LIVE SERVER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_live_server()
