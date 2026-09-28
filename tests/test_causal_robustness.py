# pytest tests/test_causal_robustness.py
# python -m pytest tests/test_robustness.py

"""Unit and Integration Tests for Higher-Order Robustness Benchmark.

Tests:
1. Sample-size task generation across finite N
2. Noise-level task generation and variance scaling
3. Interaction-strength task generation (Multiplicative & Continuous XOR)
4. Mechanism diversity task generation and ground-truth validation
5. Matched-marginal negative controls and statistical similarity verification
6. Non-Gaussian and heteroscedastic noise distribution tasks
7. Irrelevant variable task generation and candidate screening scaling
8. Statistical distribution metrics (mean, std, 95% CI)
9. Paired significance testing (t-test and Wilcoxon)
10. Realism failure-recovery classification
11. Probability calibration and Expected Calibration Error (ECE)
12. Deterministic reproducibility across identical seeds
"""

import os
import json
import tempfile
import numpy as np
import pytest

from evryn.causal.scm.mixed_graph import RelationType, MixedCausalGraph, evaluate_hypergraph
from evryn.causal.scm.robustness_generator import RobustnessTaskGenerator
from evryn.causal.experiments.robustness_metrics import (
    compute_distribution_statistics,
    paired_significance_test,
    evaluate_failure_recovery,
    compute_calibration_and_pr,
)
from evryn.causal.matching.higher_order_framework import HigherOrderEvidenceMatchingFramework


class TestRobustnessGenerator:
    """Tests for synthetic task generation across controlled degradation sweeps."""

    def test_sample_size_generation(self):
        gen = RobustnessTaskGenerator(seed=42)
        task_50 = gen.generate_sample_size_task(num_samples=50, seed=10)
        assert task_50.observations.shape == (50, 5)
        assert len(task_50.graph.hyper_relations) >= 1

        task_500 = gen.generate_sample_size_task(num_samples=500, seed=10)
        assert task_500.observations.shape == (500, 5)

        hypers = [r for r in task_50.graph.hyper_relations if len(r.sources) > 1]
        assert len(hypers) == 1
        assert hypers[0].sources == frozenset(["A", "B"])
        assert hypers[0].target == "C"
        assert ("C", "D") in task_50.graph.directed_edges

    def test_noise_level_sweep_scaling(self):
        gen = RobustnessTaskGenerator(seed=42)
        t_low = gen.generate_noise_sweep_task(sigma=0.05, num_samples=1000, seed=1)
        t_high = gen.generate_noise_sweep_task(sigma=2.00, num_samples=1000, seed=1)

        ab_low = t_low.observations[:, 0] * t_low.observations[:, 1]
        res_low = t_low.observations[:, 2] - 2.0 * ab_low

        ab_high = t_high.observations[:, 0] * t_high.observations[:, 1]
        res_high = t_high.observations[:, 2] - 2.0 * ab_high

        assert np.var(res_high) > 50 * np.var(res_low)

    def test_interaction_strength_generation(self):
        gen = RobustnessTaskGenerator(seed=42)
        t_mult = gen.generate_interaction_sweep_task(alpha=2.0, interaction_type="multiplicative", num_samples=200)
        assert t_mult.observations.shape == (200, 3)

        t_xor = gen.generate_interaction_sweep_task(alpha=1.5, interaction_type="xor", num_samples=200)
        assert t_xor.observations.shape == (200, 3)

    def test_mechanism_diversity(self):
        gen = RobustnessTaskGenerator(seed=42)
        mechs = ["additive", "multiplicative", "nonlinear_additive", "nonlinear_interaction", "xor", "threeway_interaction"]
        for m in mechs:
            task = gen.generate_mechanism_task(m, num_samples=200, seed=42)
            assert task.observations.shape[0] == 200
            if m in ("additive", "nonlinear_additive"):
                hypers = [r for r in task.graph.hyper_relations if len(r.sources) > 1]
                assert len(hypers) == 0
                assert ("A", "C") in task.graph.directed_edges
                assert ("B", "C") in task.graph.directed_edges
            elif m == "threeway_interaction":
                hypers = [r for r in task.graph.hyper_relations if len(r.sources) == 3]
                assert len(hypers) == 1
                assert hypers[0].sources == frozenset(["A", "B", "C"])
            else:
                hypers = [r for r in task.graph.hyper_relations if len(r.sources) == 2]
                assert len(hypers) == 1
                assert hypers[0].sources == frozenset(["A", "B"])

    def test_matched_marginal_controls(self):
        gen = RobustnessTaskGenerator(seed=42)
        t_add, t_mult, stats = gen.generate_matched_marginal_pair(num_samples=2000, seed=42)

        assert abs(stats["mean_diff_C"]) < 0.25
        assert 0.70 < stats["var_ratio_C"] < 1.35
        assert len([r for r in t_add.graph.hyper_relations if len(r.sources) > 1]) == 0
        assert len([r for r in t_mult.graph.hyper_relations if len(r.sources) > 1]) == 1

    def test_noise_distributions(self):
        gen = RobustnessTaskGenerator(seed=42)
        for nd in ["gaussian", "laplace", "student_t", "heteroscedastic"]:
            task = gen.generate_noise_distribution_task(nd, num_samples=300, seed=42)
            assert task.observations.shape == (300, 3)
            assert not np.isnan(task.observations).any()

    def test_irrelevant_vars_scaling(self):
        gen = RobustnessTaskGenerator(seed=42)
        task = gen.generate_irrelevant_vars_task(num_total_vars=15, num_samples=300, seed=42)
        assert task.observations.shape == (300, 15)

        fw = HigherOrderEvidenceMatchingFramework()
        cands = fw.generate_order2_candidates(task.observations, task.variable_names, max_sources_per_target=5)
        assert len(cands) <= 150

    def test_deterministic_reproducibility(self):
        gen1 = RobustnessTaskGenerator(seed=123)
        gen2 = RobustnessTaskGenerator(seed=123)
        t1 = gen1.generate_sample_size_task(num_samples=100, seed=999)
        t2 = gen2.generate_sample_size_task(num_samples=100, seed=999)
        np.testing.assert_array_almost_equal(t1.observations, t2.observations)


class TestRobustnessMetrics:
    """Tests for statistical aggregators, significance testing, and calibration metrics."""

    def test_distribution_statistics(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = compute_distribution_statistics(vals)
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["ci_95_lower"] < 3.0 < stats["ci_95_upper"]
        assert stats["count"] == 5

    def test_distribution_statistics_single_element(self):
        stats = compute_distribution_statistics([4.2])
        assert stats["mean"] == 4.2
        assert stats["std"] == 0.0
        assert stats["ci_95_lower"] == 4.2
        assert stats["ci_95_upper"] == 4.2

    def test_paired_significance_test(self):
        ho = [0.95, 0.90, 0.92, 0.94, 0.91, 0.89, 0.93, 0.96]
        pw = [0.50, 0.52, 0.48, 0.51, 0.49, 0.53, 0.50, 0.47]
        test = paired_significance_test(ho, pw)

        assert test["mean_difference"] > 0.35
        assert test["is_significant"] is True
        assert test["t_pvalue"] < 0.001

    def test_realism_failure_recovery(self):
        pw = [False, False, True, True]
        ho = [True, False, True, False]
        res = evaluate_failure_recovery(pw, ho)

        assert res["total_cases"] == 4
        assert res["both_correct_count"] == 1
        assert res["pw_fails_ho_recovers_count"] == 1
        assert res["both_fail_count"] == 1
        assert res["ho_fails_pw_correct_count"] == 1

    def test_calibration_and_pr(self):
        y_true = [0, 0, 1, 1, 0, 1]
        y_prob = [0.1, 0.2, 0.8, 0.9, 0.3, 0.7]
        metrics = compute_calibration_and_pr(y_true, y_prob, n_bins=5)

        assert "brier_score" in metrics
        assert metrics["brier_score"] < 0.15
        assert "ece" in metrics
        assert metrics["average_precision"] > 0.80
        assert metrics["roc_auc"] == 1.0
        assert len(metrics["bin_confidences"]) == 5
