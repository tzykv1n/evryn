# pytest tests/test_causal_evidence_matching.py
# python -m pytest tests/test_evidence_matching.py

"""Tests for Evidence Matching Framework (Algorithm 1) and Storage."""

import pytest
import numpy as np
import networkx as nx

from evryn.causal.matching.storage import RepresentationStorage
from evryn.causal.matching.distance import compute_distances
from evryn.causal.matching.matcher import EvidenceMatcher
from evryn.causal.matching.framework import EvidenceMatchingFramework


def test_storage_capacity_and_reservoir():
    storage = RepresentationStorage(capacity=3, retention_policy="reservoir", seed=42)
    assert storage.is_empty()

    g = nx.DiGraph()
    g.add_edge("X0", "X1")

    for i in range(10):
        storage.add(
            representation=np.array([i, i], dtype=float),
            graph=g,
            label=0,
            task_id=f"task_{i}",
        )

    assert len(storage) == 3
    assert storage.total_seen == 10
    matrix, items = storage.get_representations_matrix()
    assert matrix.shape == (3, 2)


def test_matcher_inference_and_uncertainty():
    storage = RepresentationStorage()
    g0 = nx.DiGraph()
    g0.add_edge("X0", "X1")
    g1 = nx.DiGraph()
    g1.add_edge("X1", "X0")

    for _ in range(5):
        storage.add(np.array([1.0, 1.0]), g0, label=0, domain="A")
        storage.add(np.array([-1.0, -1.0]), g1, label=1, domain="B")

    matcher = EvidenceMatcher(k_neighbors=3, metric="euclidean")

    query0 = np.array([0.9, 0.9])
    _, pred0, conf0, unc0, matches0 = matcher.match_and_infer(query0, storage)
    assert pred0 == 0
    assert conf0 > 0.8
    assert unc0 < 0.5

    query1 = np.array([-0.9, -0.9])
    _, pred1, conf1, unc1, matches1 = matcher.match_and_infer(query1, storage)
    assert pred1 == 1
    assert conf1 > 0.8


def test_algorithm1_framework_end_to_end():
    framework = EvidenceMatchingFramework()
    rng = np.random.default_rng(42)

    data1 = rng.normal(0, 1, (200, 2))
    res1 = framework.process_observations(data1, task_id="t1", domain="test")
    assert res1["source"] == "scratch_discovery"
    assert len(framework.storage) == 1

    data2 = rng.normal(0, 1, (200, 2))
    res2 = framework.process_observations(data2, task_id="t2", domain="test")
    assert res2["source"] == "matched_and_refined"
    assert len(framework.storage) == 2
