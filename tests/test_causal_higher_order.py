# pytest tests/test_causal_higher_order.py
# python -m pytest tests/test_higher_order.py

"""Unit tests for higher-order causal relations, hypergraphs, features, and evaluation.

Covers:
1. Hyperedge generation (Cases A through H and negative control)
2. Hyperedge serialization and representation (HyperCausalRelation, CausalRelation)
3. Higher-order feature calculation, KSG mutual information, and synergy metrics
4. Candidate generation and screening
5. Pairwise projection
6. Hyperedge evaluation metrics and order-specific F1
"""

import numpy as np
import pytest

from evryn.causal.scm.mixed_graph import (
    RelationType,
    HyperCausalRelation,
    CausalRelation,
    MixedCausalGraph,
    evaluate_hypergraph,
)
from evryn.causal.scm.higher_order_generator import HigherOrderTaskGenerator
from evryn.causal.features.higher_order_features import (
    HigherOrderFeatureExtractor,
    ksg_mutual_information,
    compute_gaussian_entropy,
)
from evryn.causal.matching.higher_order_framework import HigherOrderEvidenceMatchingFramework


class TestHyperedgeGeneration:
    def test_canonical_benchmark_generation(self):
        gen = HigherOrderTaskGenerator(seed=42)
        tasks = gen.generate_canonical_benchmark(num_samples=300)

        assert "case_A" in tasks
        assert "case_B" in tasks
        assert "case_C" in tasks
        assert "case_D" in tasks
        assert "case_E" in tasks
        assert "case_F" in tasks
        assert "case_G" in tasks
        assert "case_H" in tasks

        b_hypers = tasks["case_B"].graph.get_hyperedges(order=2)
        assert len(b_hypers) == 1
        assert b_hypers[0].sources == frozenset(["A", "B"])
        assert b_hypers[0].target == "C"

        c_hypers = tasks["case_C"].graph.get_hyperedges(order=3)
        assert len(c_hypers) == 1
        assert c_hypers[0].sources == frozenset(["A", "B", "C"])
        assert c_hypers[0].target == "D"

    def test_negative_control_generation(self):
        gen = HigherOrderTaskGenerator(seed=42)
        t_add, t_syn = gen.generate_negative_control_pair(num_samples=300)

        assert len(t_add.graph.get_hyperedges(order=2)) == 0
        assert t_add.meta_info["is_joint"] is False

        assert len(t_syn.graph.get_hyperedges(order=2)) == 1
        assert t_syn.meta_info["is_joint"] is True


class TestHyperedgeSerialization:
    def test_hyper_causal_relation_properties(self):
        rel = HyperCausalRelation(
            sources=("A", "B"),
            targets=("C",),
            relation_type=RelationType.JOINT_CAUSAL,
        )
        assert rel.target == "C"
        assert rel.order == 2
        assert rel.is_higher_order is True
        assert "{A, B}" in str(rel)
        assert "C" in str(rel)

    def test_causal_relation_factory(self):
        r1 = CausalRelation(sources=("A",), target="B", relation_type="FORWARD")
        assert r1.order == 1
        assert r1.is_higher_order is False
        assert r1.target == "B"

        r2 = CausalRelation(sources=("X", "Y"), target="Z", relation_type="JOINT_CAUSAL")
        assert r2.order == 2
        assert r2.is_higher_order is True
        assert r2.target == "Z"


class TestHigherOrderFeatures:
    def test_ksg_mi_estimator(self):
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, 300)
        Y_dep = 2.0 * X + rng.normal(0, 0.1, 300)
        Y_indep = rng.normal(0, 1, 300)

        mi_dep = ksg_mutual_information(X, Y_dep)
        mi_indep = ksg_mutual_information(X, Y_indep)

        assert mi_dep > mi_indep
        assert mi_dep > 0.5
        assert mi_indep < 0.2

    def test_synergy_and_interaction_gain(self):
        rng = np.random.default_rng(42)
        A = rng.normal(0, 1, 400)
        B = rng.normal(0, 1, 400)
        C_joint = 2.0 * (A * B) + rng.normal(0, 0.3, 400)
        C_add = 1.0 * A + 1.0 * B + rng.normal(0, 0.3, 400)

        data_joint = np.column_stack([A, B, C_joint])
        data_add = np.column_stack([A, B, C_add])

        ext = HigherOrderFeatureExtractor(random_state=42)
        f_joint = ext.extract_triple_features(data_joint, 0, 1, 2)
        f_add = ext.extract_triple_features(data_add, 0, 1, 2)

        assert f_joint["r2_interaction_gain"] > 0.6
        assert f_add["r2_interaction_gain"] < 0.05
        assert f_joint["r2_interaction_gain"] > 10.0 * f_add["r2_interaction_gain"]

    def test_ablation_vector_dimensions(self):
        ext = HigherOrderFeatureExtractor(random_state=42)
        data = np.random.randn(200, 3)
        f_dict = ext.extract_triple_features(data, 0, 1, 2)

        v_pair = ext.vector_from_dict(f_dict, "pairwise_only")
        v_ho = ext.vector_from_dict(f_dict, "pairwise_plus_higher_order")
        v_syn = ext.vector_from_dict(f_dict, "pairwise_plus_synergy")
        v_all = ext.vector_from_dict(f_dict, "all_features")

        assert len(v_pair) == 10
        assert len(v_ho) == 14
        assert len(v_syn) == 17
        assert len(v_all) == 29
        assert not np.isnan(v_all).any()


class TestCandidateGenerationAndFramework:
    def test_candidate_screening(self):
        fw = HigherOrderEvidenceMatchingFramework(random_state=42)
        data = np.random.randn(100, 5)
        var_names = [f"X{i}" for i in range(5)]

        candidates = fw.generate_order2_candidates(data, var_names, max_sources_per_target=4)
        assert len(candidates) > 0
        for (i, j), k in candidates:
            assert i != j
            assert i != k
            assert j != k
            assert 0 <= i < 5 and 0 <= j < 5 and 0 <= k < 5

    def test_pairwise_projection(self):
        nodes = ["A", "B", "C", "D"]
        g = MixedCausalGraph(nodes)
        g.add_directed_edge("A", "B")
        g.add_bidirected_edge("C", "D")
        g.add_hyperedge(["B", "C"], "D", relation_type=RelationType.JOINT_CAUSAL)

        proj = g.pairwise_projection()
        assert ("A", "B") in proj.directed_edges
        assert frozenset(["C", "D"]) in proj.bidirected_edges
        assert ("B", "D") in proj.directed_edges
        assert ("C", "D") in proj.directed_edges


class TestHyperedgeEvaluation:
    def test_exact_hypergraph_match(self):
        nodes = ["X0", "X1", "X2"]
        gt = MixedCausalGraph(nodes)
        gt.add_hyperedge(["X0", "X1"], "X2", relation_type=RelationType.JOINT_CAUSAL)

        pred_identical = MixedCausalGraph(nodes)
        pred_identical.add_hyperedge(["X0", "X1"], "X2", relation_type=RelationType.JOINT_CAUSAL)

        eval_res = evaluate_hypergraph(gt, pred_identical, nodes)
        assert eval_res["hyperedge_f1"] == 1.0
        assert eval_res["order_2_f1"] == 1.0
        assert eval_res["exact_hypergraph_match"] == 1.0

        pred_wrong = MixedCausalGraph(nodes)
        pred_wrong.add_directed_edge("X0", "X1")

        eval_wrong = evaluate_hypergraph(gt, pred_wrong, nodes)
        assert eval_wrong["exact_hypergraph_match"] == 0.0
        assert eval_wrong["order_2_f1"] == 0.0
