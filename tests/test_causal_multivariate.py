# pytest tests/test_causal_multivariate.py
# python -m pytest tests/test_multivariate.py

"""Tests for Multivariate Causality in Flux implementation.

Covers:
- MixedCausalGraph (directed, bidirected, none relations, relation matrix, hypergraph / higher-order)
- evaluate_mixed_graph (SHD, directed/bidirected edge precision & recall, macro-F1, balanced accuracy)
- SemiMarkovianTaskGenerator (explicit 4-class DAGs, negative examples, class-balanced streams)
- SachsBenchmarkLoader (observational, interventional, condition tasks, consensus GT)
- MultivariateMetaFeatureExtractor (pair features, z-scores, asymmetry, global representations)
- MultivariateEvidenceMatchingFramework (Algorithm 1, balanced sampling, hierarchical decision, ablations)
"""

import pytest
import numpy as np
from evryn.causal.scm.mixed_graph import (
    MixedCausalGraph,
    RelationType,
    HyperCausalRelation,
    evaluate_mixed_graph,
)
from evryn.causal.scm.semi_markovian_generator import (
    SemiMarkovianTaskGenerator,
    MultivariateCausalTask,
)
from evryn.causal.datasets.sachs_loader import SachsBenchmarkLoader
from evryn.causal.features.multivariate_features import MultivariateMetaFeatureExtractor
from evryn.causal.matching.multivariate_framework import MultivariateEvidenceMatchingFramework


class TestMixedCausalGraph:
    """Test MixedCausalGraph representation and higher-order hyperrelations."""

    def test_edge_relations(self):
        nodes = ["X0", "X1", "X2", "X3"]
        g = MixedCausalGraph(nodes)
        g.add_directed_edge("X0", "X1")
        g.add_bidirected_edge("X2", "X3")

        assert g.get_relation("X0", "X1") == RelationType.FORWARD
        assert g.get_relation("X1", "X0") == RelationType.BACKWARD

        assert g.get_relation("X2", "X3") == RelationType.BIDIRECTED
        assert g.get_relation("X3", "X2") == RelationType.BIDIRECTED

        assert g.get_relation("X0", "X2") == RelationType.NONE
        assert g.get_relation("X1", "X3") == RelationType.NONE

    def test_higher_order_hyper_relations(self):
        nodes = ["A", "B", "C", "D"]
        g = MixedCausalGraph(nodes)

        g.add_hyper_relation(sources=["A"], targets=["B"], relation_type=RelationType.FORWARD)
        assert g.get_relation("A", "B") == RelationType.FORWARD

        rel_abc = g.add_hyper_relation(sources=["A", "B"], targets=["C"], relation_type=RelationType.FORWARD)
        assert rel_abc.sources == frozenset(["A", "B"])
        assert rel_abc.targets == frozenset(["C"])

        g.add_hyper_relation(sources=["A", "B", "C"], targets=["D"], relation_type=RelationType.FORWARD)

        c_parents = g.get_hyper_relations(target="C")
        assert len(c_parents) == 1
        assert "A" in c_parents[0].sources and "B" in c_parents[0].sources

        s = g.summary()
        assert s["higher_order_relations"] == 2
        assert s["total_hyper_relations"] == 3

    def test_evaluate_mixed_graph_metrics(self):
        nodes = ["X0", "X1", "X2", "X3"]
        gt = MixedCausalGraph(nodes)
        gt.add_directed_edge("X0", "X1")
        gt.add_directed_edge("X1", "X2")
        gt.add_bidirected_edge("X2", "X3")

        pred = MixedCausalGraph(nodes)
        pred.add_directed_edge("X0", "X1")
        pred.add_directed_edge("X2", "X1")
        pred.add_bidirected_edge("X2", "X3")

        res = evaluate_mixed_graph(gt, pred, nodes)
        assert res["accuracy"] < 1.0
        assert res["macro_f1"] > 0.0
        assert res["balanced_accuracy"] > 0.0
        assert res["shd"] == 1
        assert res["directed_precision"] > 0.0
        assert res["bidirected_precision"] == 1.0


class TestSemiMarkovianTaskGenerator:
    """Test semi-Markovian task generation with latent confounders."""

    def test_generate_task_properties(self):
        gen = SemiMarkovianTaskGenerator(seed=42)
        task = gen.generate_task(
            task_id="test_task",
            num_variables=5,
            num_samples=400,
            directed_prob=0.35,
            confounded_prob=0.25,
            mechanism_type="linear",
            noise_type="laplace",
        )
        assert isinstance(task, MultivariateCausalTask)
        assert task.observations.shape == (400, 5)
        assert len(task.variable_names) == 5
        assert np.all(np.isfinite(task.observations))

    def test_flux_stream_generation(self):
        gen = SemiMarkovianTaskGenerator(seed=42)
        stream = gen.generate_multivariate_flux_stream(
            num_tasks=8,
            num_variables=4,
            samples_per_task=300,
        )
        assert len(stream) == 8
        domains = set(t.domain for t in stream)
        assert len(domains) >= 3

    def test_class_balanced_stream_generation(self):
        gen = SemiMarkovianTaskGenerator(seed=42)
        stream = gen.generate_class_balanced_stream(
            num_tasks=4,
            num_variables=6,
            samples_per_task=300,
        )
        assert len(stream) == 4
        for t in stream:
            nodes = t.variable_names
            rels = [t.graph.get_relation(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i + 1, len(nodes))]
            for c in range(4):
                assert c in rels, f"Class {c} missing in balanced stream task {t.task_id}"


class TestSachsBenchmarkLoader:
    """Test loading Sachs (2005) single-cell protein signaling dataset."""

    def test_load_observational_task(self):
        loader = SachsBenchmarkLoader()
        task = loader.load_observational_task()
        assert task.num_variables == 11
        assert task.num_samples == 853
        assert np.all(np.isfinite(task.observations))

    def test_load_all_conditions(self):
        loader = SachsBenchmarkLoader()
        tasks = loader.load_all_condition_tasks()
        assert len(tasks) == 7
        for t in tasks:
            assert t.num_variables == 11
            assert t.num_samples >= 500

    def test_ground_truth_graph(self):
        loader = SachsBenchmarkLoader()
        gt = loader.get_ground_truth_graph()
        s = gt.summary()
        assert s["num_variables"] == 11
        assert s["total_pairs"] == 55
        assert s["directed_edges (->)"] == 14
        assert s["bidirected_edges (<->)"] == 4
        assert s["no_relations (none)"] == 37


class TestMultivariateMetaFeatureExtractor:
    """Test feature extraction for multivariate pairs and datasets."""

    def test_extract_pair_features(self):
        extractor = MultivariateMetaFeatureExtractor(random_state=42)
        rng = np.random.default_rng(42)
        X = rng.normal(size=(200, 4))
        X[:, 1] = 0.8 * X[:, 0] + rng.normal(scale=0.5, size=200)

        feats = extractor.extract_pair_features(X, 0, 1)
        assert feats.shape == (16,)
        assert np.all(np.isfinite(feats))
        assert feats[0] > 0.4

    def test_constant_input_robustness(self):
        extractor = MultivariateMetaFeatureExtractor(random_state=42)
        X = np.zeros((100, 3))
        feats = extractor.extract_pair_features(X, 0, 1)
        assert feats.shape == (16,)
        assert np.all(np.isfinite(feats))

    def test_dataset_representation(self):
        extractor = MultivariateMetaFeatureExtractor(random_state=42)
        rng = np.random.default_rng(42)
        X = rng.normal(size=(150, 4))
        rep = extractor.extract_dataset_representation(X)
        assert len(rep) == 48
        assert np.all(np.isfinite(rep))


class TestMultivariateEvidenceMatchingFramework:
    """Test Algorithm 1 execution with continual evidence matching."""

    def test_framework_continual_adaptation(self):
        gen = SemiMarkovianTaskGenerator(seed=42)
        t1 = gen.generate_task("task_1", num_variables=4, num_samples=300)
        t2 = gen.generate_task("task_2", num_variables=4, num_samples=300)

        framework = MultivariateEvidenceMatchingFramework(
            memory_capacity=10,
            uncertainty_threshold=0.85,
            class_weight="balanced",
            balanced_sampling=True,
            decision_mode="hierarchical",
            random_state=42,
        )

        res1 = framework.process_task(t1.observations, t1.variable_names, task_id="t1", domain="regime_A")
        assert res1["source"] == "scratch_discovery"
        assert len(framework.stored_graphs) == 1

        res2 = framework.process_task(t2.observations, t2.variable_names, task_id="t2", domain="regime_A")
        assert res2["source"] in ("matched_and_refined", "scratch_discovery")
        assert len(framework.stored_graphs) == 2
