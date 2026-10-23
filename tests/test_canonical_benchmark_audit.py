# tests/test_canonical_benchmark_audit.py
# Verify canonical evaluation artifacts, zero leakage, and metric validity

import os
import json
import pytest
import pandas as pd


def test_canonical_benchmark_results_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "outputs", "multipage_benchmark_results.json")
    csv_path = os.path.join(base_dir, "outputs", "multipage_benchmark_results.csv")
    ci_path = os.path.join(base_dir, "outputs", "confidence_intervals.json")
    per_paper_path = os.path.join(base_dir, "outputs", "per_paper_results.csv")

    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(csv_path), f"Missing {csv_path}"
    assert os.path.exists(ci_path), f"Missing {ci_path}"
    assert os.path.exists(per_paper_path), f"Missing {per_paper_path}"


def test_benchmark_metrics_validity():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "outputs", "multipage_benchmark_results.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_papers"] == 12
    evryn = data["system_c_evryn"]

    # Mean within bootstrap CI
    assert evryn["direct_f1_ci"][0] <= evryn["direct_f1"] <= evryn["direct_f1_ci"][1]
    assert evryn["cross_page_f1_ci"][0] <= evryn["cross_page_f1"] <= evryn["cross_page_f1_ci"][1]
    assert evryn["structural_match_ci"][0] <= evryn["structural_match"] <= evryn["structural_match_ci"][1]

    # Provenance completeness must be 100%
    assert evryn["provenance_completeness"] == 1.0

    # Measured performance verification
    assert evryn["direct_f1"] >= 0.40
    assert evryn["cross_page_f1"] >= 0.20


def test_dev_test_split_partitioning_and_no_leakage():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    per_paper_path = os.path.join(base_dir, "outputs", "per_paper_results.csv")
    df = pd.read_csv(per_paper_path)

    assert len(df) == 12
    dev_split = df[df["split"] == "DEV"]
    test_split = df[df["split"] == "TEST"]

    assert len(dev_split) == 8
    assert len(test_split) == 4

    # Ensure no overlap in doc_ids
    dev_ids = set(dev_split["doc_id"])
    test_ids = set(test_split["doc_id"])
    assert len(dev_ids.intersection(test_ids)) == 0

    # Test split must have positive performance on unseen papers
    assert test_split["system_c_f1"].mean() >= 0.35
