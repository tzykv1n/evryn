# pytest tests/test_causal_continual_stream.py
# python -m pytest tests/test_continual_stream.py

"""Tests for Continual Flux Stream and Evaluator."""

import pytest
import numpy as np

from evryn.causal.continual.flux_stream import ContinualFluxStream
from evryn.causal.continual.continual_eval import ContinualCausalEvaluator
from evryn.causal.continual.abstractions import CausalAbstraction
import networkx as nx


def test_flux_stream_generation():
    stream = ContinualFluxStream(num_tasks=8, samples_per_task=100, seed=42)
    assert len(stream) == 8

    domains = []
    for task in stream:
        assert task.observations.shape == (100, 2)
        assert task.label in (0, 1)
        domains.append(task.domain)

    assert len(set(domains)) >= 3


def test_continual_evaluator_metrics():
    evaluator = ContinualCausalEvaluator(num_tasks=3)
    evaluator.record_eval(0, 0, 1.0)
    evaluator.record_eval(1, 1, 1.0)
    evaluator.record_eval(2, 2, 1.0)

    evaluator.record_eval(2, 0, 1.0)
    evaluator.record_eval(2, 1, 1.0)

    metrics = evaluator.compute_metrics()
    assert metrics["average_accuracy"] == 1.0
    assert metrics["backward_transfer"] == 0.0
    assert metrics["catastrophic_forgetting"] == 0.0


def test_causal_abstraction():
    abs_module = CausalAbstraction()
    g = nx.DiGraph()
    g.add_edge("X1", "Y1")
    g.add_edge("X2", "Y2")

    mapping = {"X1": "X", "X2": "X", "Y1": "Y", "Y2": "Y"}
    abstracted = abs_module.abstract_graph(g, mapping)

    assert set(abstracted.nodes()) == {"X", "Y"}
    assert abstracted.has_edge("X", "Y")
    assert abstracted.number_of_edges() == 1
