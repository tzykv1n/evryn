# pytest tests/test_causal_final_phase.py

import pytest
import numpy as np

from evryn.causal.scm.independent_hcam_generator import IndependentHCAMGenerator
from evryn.causal.discovery.hcam_baseline import HCAMBaseline
from evryn.causal.discovery.notears import NOTEARSBaseline
from evryn.causal.experiments.classifier_ablation import run_classifier_ablation_experiment
from evryn.causal.experiments.feature_ablation_nested import run_nested_feature_ablation
from evryn.causal.experiments.sachs_improved import SachsEvidenceEnsemble, run_sachs_improved_benchmark
from evryn.causal.experiments.continual_ablation import run_continual_ablation_experiment


class TestFinalPhase:

    def test_hcam_generator_mechanisms(self):
        gen = IndependentHCAMGenerator(seed=42)
        t_lin = gen.generate_linear_additive(num_samples=100)
        assert t_lin.observations.shape == (100, 3)
        assert len(t_lin.graph.directed_edges) == 2

        t_poly = gen.generate_polynomial(num_samples=100)
        assert t_poly.observations.shape == (100, 3)
        assert len([r for r in t_poly.graph.hyper_relations if len(r.sources) > 1]) == 1

        t_gp = gen.generate_gp_nonparametric(num_samples=100)
        assert t_gp.observations.shape == (100, 3)
        assert len([r for r in t_gp.graph.hyper_relations if len(r.sources) > 1]) == 1

        t_3way = gen.generate_threeway_hcam(num_samples=100)
        assert t_3way.observations.shape == (100, 4)
        assert len([r for r in t_3way.graph.hyper_relations if len(r.sources) == 3]) == 1

        t_conf = gen.generate_confounded_mechanism(num_samples=100)
        assert t_conf.observations.shape == (100, 3)
        assert len(t_conf.graph.bidirected_edges) == 1

    def test_hcam_train_test_split(self):
        gen = IndependentHCAMGenerator(seed=42)
        train_tasks = gen.generate_training_set(num_samples=150)
        test_tasks = gen.generate_test_set(num_samples=150)

        train_mechs = {t.meta_info.get("mechanism") for t in train_tasks}
        test_mechs = {t.meta_info.get("mechanism") for t in test_tasks}

        assert len(train_mechs.intersection(test_mechs)) == 0

    def test_hcam_baseline(self):
        X = np.random.randn(150, 3)
        names = ["A", "B", "C"]
        hcam = HCAMBaseline(max_order=2)
        g = hcam.fit_hypergraph(X, names)
        assert len(g.nodes) == 3

    def test_notears_baseline(self):
        X = np.random.randn(150, 3)
        names = ["A", "B", "C"]
        notears = NOTEARSBaseline(max_iter=20)
        g = notears.fit_dag(X, names)
        assert len(g.nodes) == 3

    def test_classifier_ablation(self):
        res = run_classifier_ablation_experiment(seeds=1, samples=150)
        assert "Random Forest" in res
        assert "MLP" in res
        assert "Logistic Regression" in res
        for clf_name, data in res.items():
            assert "order_2_f1" in data
            assert "runtime_ms" in data

    def test_feature_ablation(self):
        res = run_nested_feature_ablation(seeds=1, samples=150)
        assert "A. Pairwise-only" in res
        assert "G. Full System" in res
        for c_name, data in res.items():
            assert "order_2_f1" in data
            assert "paired_improvement_vs_pairwise" in data

    def test_sachs_improved_null_controls(self):
        res = run_sachs_improved_benchmark()
        assert "rf_baseline" in res
        assert "evidence_ensemble" in res
        assert "null_controls" in res
        assert res["null_controls"]["independent_variables_edge_count"] <= 2

    def test_continual_ablation(self):
        res = run_continual_ablation_experiment(num_tasks=2, samples_per_task=150)
        assert "A. Scratch Every Task" in res
        assert "D. EM + Uncertainty Weighting" in res
        for v_name, data in res.items():
            assert "pairwise_projection_f1" in data
            assert "fwt" in data
            assert "bwt" in data
