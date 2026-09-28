# pytest tests/test_causal_scm.py
# python -m pytest tests/test_scm.py

"""Tests for SCMs, mechanisms, and coupled dynamical systems."""

import pytest
import numpy as np
import networkx as nx

from evryn.causal.scm.structural_causal_model import StructuralCausalModel
from evryn.causal.scm.mechanisms import (
    linear_mechanism,
    polynomial_mechanism,
    sigmoid_mechanism,
    simulate_lotka_volterra,
    simulate_financial_market_cycle,
)
from evryn.causal.scm.generator import CausalTaskGenerator


def test_scm_sampling_and_dag():
    scm = StructuralCausalModel("test_scm")
    scm.add_variable("X", parent_vars=[])
    scm.add_variable("Y", parent_vars=["X"], func=linear_mechanism(2.0))

    assert nx.is_directed_acyclic_graph(scm.graph)
    assert scm.graph.has_edge("X", "Y")

    samples = scm.sample(num_samples=200, seed=42)
    assert "X" in samples and "Y" in samples
    assert len(samples["X"]) == 200
    assert len(samples["Y"]) == 200

    corr = np.corrcoef(samples["X"], samples["Y"])[0, 1]
    assert corr > 0.7


def test_scm_intervention_do_operator():
    """Test Pearl's do-operator intervention do(X = 5.0)."""
    scm = StructuralCausalModel("interventional_scm")
    scm.add_variable("X", parent_vars=[])
    scm.add_variable("Y", parent_vars=["X"], func=linear_mechanism(3.0))

    samples = scm.sample(num_samples=100, interventions={"X": 5.0}, seed=42)
    assert np.all(samples["X"] == 5.0)
    assert np.isclose(np.mean(samples["Y"]), 15.0, atol=0.5)


def test_scm_cycle_rejection():
    """Ensure SCM rejects circular dependencies."""
    scm = StructuralCausalModel("cyclic_scm")
    scm.add_variable("X", parent_vars=[])
    scm.add_variable("Y", parent_vars=["X"])
    with pytest.raises(ValueError):
        scm.add_variable("X", parent_vars=["Y"])


def test_lotka_volterra_dynamics():
    """Test Lotka-Volterra predator-prey simulator from Paper Example 1."""
    prey, predator = simulate_lotka_volterra(num_samples=300, seed=42)
    assert len(prey) == 300
    assert len(predator) == 300
    assert np.all(prey > 0)
    assert np.all(predator > 0)
    assert np.var(prey) > 0.1
    assert np.var(predator) > 0.1


def test_financial_market_dynamics():
    """Test financial market cycle simulator from Paper Example 1."""
    price, volume = simulate_financial_market_cycle(num_samples=300, seed=42)
    assert len(price) == 300
    assert len(volume) == 300
    assert np.var(price) > 1.0
    assert np.var(volume) > 1.0


def test_generator_bivariate_pair():
    gen = CausalTaskGenerator(seed=42)
    task = gen.generate_bivariate_pair("test_pair", direction=0, mechanism_type="polynomial")
    assert task.label == 0
    assert task.observations.shape == (1000, 2)
    assert task.graph.has_edge("X0", "X1")
