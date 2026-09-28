# python cli.py sachs_improved
# meflux sachs_improved

import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression, RidgeClassifier

from ..datasets.sachs_loader import SachsBenchmarkLoader
from ..scm.mixed_graph import MixedCausalGraph, RelationType, evaluate_mixed_graph
from ..scm.semi_markovian_generator import SemiMarkovianTaskGenerator
from ..matching.multivariate_framework import MultivariateEvidenceMatchingFramework
from ..features.multivariate_features import MultivariateMetaFeatureExtractor
from ..discovery.anm import compute_distance_correlation
from .robustness_metrics import compute_distribution_statistics, compute_calibration_and_pr


class SachsEvidenceEnsemble:

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.extractor = MultivariateMetaFeatureExtractor(random_state=random_state)
        self.rf_framework: Optional[MultivariateEvidenceMatchingFramework] = None
        self.ensemble_weights: Optional[np.ndarray] = None
        self.threshold: float = 0.50

    def fit_on_reference_tasks(self, ref_tasks: List[Any]) -> None:
        self.rf_framework = MultivariateEvidenceMatchingFramework(
            memory_capacity=20,
            class_weight="balanced",
            balanced_sampling=True,
            edge_threshold=0.45,
            decision_mode="hierarchical",
            random_state=self.random_state,
        )
        self.rf_framework.fit_relational_classifier(ref_tasks)

        X_ens, y_ens = [], []
        for task in ref_tasks[:15]:
            d = len(task.variable_names)
            nodes = task.variable_names
            data = task.observations
            n_samples = len(data)
            split_size = n_samples // 3
            if split_size < 30:
                continue
            envs = [data[:split_size], data[split_size:2*split_size], data[2*split_size:]]

            for i in range(d):
                for j in range(d):
                    if i != j:
                        rel = task.graph.get_relation(nodes[i], nodes[j])
                        is_forward = 1 if rel == RelationType.FORWARD else 0

                        f_pair = self.extractor.extract_pair_features(data, i, j)
                        probs = self.rf_framework.classifier.predict_proba([f_pair])[0]
                        clf_p = float(probs[1]) if len(probs) > 1 else 0.0

                        corr_val = abs(float(f_pair[0]))
                        part_corr = abs(float(f_pair[2]))

                        slopes = []
                        for ed in envs:
                            sl, _, _, _, _ = stats.linregress(ed[:, i], ed[:, j])
                            slopes.append(float(sl))
                        var_slopes = float(np.var(slopes))
                        inv_score = float(1.0 / (1.0 + var_slopes))

                        shifts = [abs(float(np.mean(ed[:, j]) - np.mean(data[:, j]))) for ed in envs]
                        shift_score = float(np.mean(shifts))

                        asym = float(f_pair[9])

                        conf_p = float(probs[3]) if len(probs) > 3 else 0.0

                        feat_vec = np.array([clf_p, part_corr, inv_score, shift_score, asym, conf_p], dtype=np.float32)
                        X_ens.append(feat_vec)
                        y_ens.append(is_forward)

        if X_ens and len(np.unique(y_ens)) > 1:
            X_arr = np.array(X_ens)
            y_arr = np.array(y_ens)
            model = LogisticRegression(class_weight="balanced", random_state=self.random_state)
            model.fit(X_arr, y_arr)
            self.ensemble_weights = model.coef_[0]
            self.intercept = float(model.intercept_[0])
            val_probs = model.predict_proba(X_arr)[:, 1]
            best_t, best_bal = 0.50, 0.0
            for t_cand in np.linspace(0.40, 0.70, 15):
                pred_binary = (val_probs >= t_cand).astype(int)
                tp = np.sum((pred_binary == 1) & (y_arr == 1))
                fn = np.sum((pred_binary == 0) & (y_arr == 1))
                tn = np.sum((pred_binary == 0) & (y_arr == 0))
                fp = np.sum((pred_binary == 1) & (y_arr == 0))
                bal = 0.5 * (tp / max(1, tp + fn) + tn / max(1, tn + fp))
                if bal > best_bal:
                    best_bal = bal
                    best_t = float(t_cand)
            self.threshold = best_t
        else:
            self.ensemble_weights = np.array([1.0, 0.5, 0.5, 0.5, 0.5, -0.5], dtype=np.float32)
            self.intercept = 0.0
            self.threshold = 0.50

    def compute_pair_evidence(self, env_data: List[np.ndarray], i: int, j: int, combined_data: np.ndarray) -> Dict[str, float]:
        f_pair = self.extractor.extract_pair_features(combined_data, i, j)
        probs = self.rf_framework.classifier.predict_proba([f_pair])[0] if self.rf_framework is not None else np.zeros(4)
        clf_p = float(probs[1]) if len(probs) > 1 else 0.0
        conf_p = float(probs[3]) if len(probs) > 3 else 0.0

        part_corr = abs(float(f_pair[2]))

        slopes = []
        for ed in env_data:
            s_i = np.std(ed[:, i])
            s_j = np.std(ed[:, j])
            if s_i > 1e-9 and s_j > 1e-9:
                sl, _, _, _, _ = stats.linregress(ed[:, i], ed[:, j])
                slopes.append(float(sl))
            else:
                slopes.append(0.0)

        var_slopes = float(np.var(slopes))
        inv_score = float(1.0 / (1.0 + var_slopes))

        control_mean = float(np.mean(env_data[0][:, j])) if len(env_data) > 0 else 0.0
        shifts = [abs(float(np.mean(ed[:, j])) - control_mean) for ed in env_data[1:]] if len(env_data) > 1 else [0.0]
        shift_score = float(np.mean(shifts))

        asym = float(f_pair[9])

        vec = np.array([clf_p, part_corr, inv_score, shift_score, asym, conf_p], dtype=np.float32)
        raw_score = float(np.dot(self.ensemble_weights, vec) + getattr(self, "intercept", 0.0)) if self.ensemble_weights is not None else float(clf_p)
        score_norm = float(1.0 / (1.0 + np.exp(-raw_score)))

        return {
            "score": score_norm,
            "clf_prob": clf_p,
            "conf_prob": conf_p,
            "part_corr": part_corr,
            "invariance": inv_score,
            "shift": shift_score,
            "asym": asym,
        }

    def predict_sachs_graph(self, condition_tasks: List[Any], use_ensemble: bool = True) -> Tuple[MixedCausalGraph, Dict[str, Any]]:
        nodes = condition_tasks[0].variable_names
        d = len(nodes)
        env_data = [t.observations for t in condition_tasks]
        combined = np.vstack(env_data)

        graph = MixedCausalGraph(nodes)
        edge_evidence = {}

        for i in range(d):
            for j in range(i + 1, d):
                ev_ij = self.compute_pair_evidence(env_data, i, j, combined)
                ev_ji = self.compute_pair_evidence(env_data, j, i, combined)
                edge_evidence[f"{nodes[i]}->{nodes[j]}"] = ev_ij
                edge_evidence[f"{nodes[j]}->{nodes[i]}"] = ev_ji

                s_ij = ev_ij["score"] if use_ensemble else ev_ij["clf_prob"]
                s_ji = ev_ji["score"] if use_ensemble else ev_ji["clf_prob"]
                c_p = (ev_ij["conf_prob"] + ev_ji["conf_prob"]) / 2.0
                thresh = self.threshold if use_ensemble else 0.45

                if c_p >= 0.50 and c_p > s_ij and c_p > s_ji:
                    graph.add_bidirected_edge(nodes[i], nodes[j])
                elif s_ij >= thresh or s_ji >= thresh:
                    if s_ij >= s_ji:
                        graph.add_directed_edge(nodes[i], nodes[j])
                    else:
                        graph.add_directed_edge(nodes[j], nodes[i])

        return graph, edge_evidence


def run_sachs_improved_benchmark(output_dir: str = ".", quick: bool = False) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    loader = SachsBenchmarkLoader()
    tasks = loader.load_all_condition_tasks()
    gt = loader.get_ground_truth_graph()
    nodes = loader.PROTEINS

    num_ref = 8 if quick else 25
    gen = SemiMarkovianTaskGenerator(seed=42)
    ref_tasks = [
        gen.generate_task(
            f"ref_{i}",
            num_variables=6,
            num_samples=400 if quick else 600,
            directed_prob=0.35,
            confounded_prob=0.30,
            mechanism_type=["linear", "tanh", "polynomial", "mixed"][i % 4],
            noise_type=["laplace", "gaussian", "uniform"][i % 3],
            ensure_all_classes=True,
        )
        for i in range(num_ref)
    ]

    ensemble = SachsEvidenceEnsemble(random_state=42)
    ensemble.fit_on_reference_tasks(ref_tasks)

    g_rf, ev_rf = ensemble.predict_sachs_graph(tasks, use_ensemble=False)
    metrics_rf = evaluate_mixed_graph(gt, g_rf, nodes)

    g_ens, ev_ens = ensemble.predict_sachs_graph(tasks, use_ensemble=True)
    metrics_ens = evaluate_mixed_graph(gt, g_ens, nodes)

    null_results = {}
    env_data = [t.observations for t in tasks]
    combined = np.vstack(env_data)

    shuffled_data = combined.copy()
    rng_null = np.random.default_rng(42)
    for col in range(shuffled_data.shape[1]):
        shuffled_data[:, col] = rng_null.permutation(shuffled_data[:, col])
    d_len = len(nodes)
    fake_tasks = [tasks[0].__class__(f"null_{idx}", shuffled_data[idx*500:(idx+1)*500], gt, nodes, "null") for idx in range(3)]
    g_null_shuf, _ = ensemble.predict_sachs_graph(fake_tasks, use_ensemble=True)
    null_results["shuffled_variables_edge_count"] = len(g_null_shuf.directed_edges) + len(g_null_shuf.bidirected_edges)

    rng = np.random.default_rng(42)
    indep_data = rng.normal(0, 1.0, size=combined.shape)
    indep_tasks = [tasks[0].__class__(f"indep_{idx}", indep_data[idx*500:(idx+1)*500], gt, nodes, "indep") for idx in range(3)]
    g_null_indep, _ = ensemble.predict_sachs_graph(indep_tasks, use_ensemble=True)
    null_results["independent_variables_edge_count"] = len(g_null_indep.directed_edges) + len(g_null_indep.bidirected_edges)

    y_true_pairs = []
    y_prob_rf = []
    y_prob_ens = []
    for i in range(d_len):
        for j in range(i + 1, d_len):
            u, v = nodes[i], nodes[j]
            is_edge = 1 if (u, v) in gt.directed_edges or (v, u) in gt.directed_edges or frozenset([u, v]) in gt.bidirected_edges else 0
            y_true_pairs.append(is_edge)
            y_prob_rf.append(max(ev_rf[f"{u}->{v}"]["clf_prob"], ev_rf[f"{v}->{u}"]["clf_prob"]))
            y_prob_ens.append(max(ev_ens[f"{u}->{v}"]["score"], ev_ens[f"{v}->{u}"]["score"]))

    cal_rf = compute_calibration_and_pr(y_true_pairs, y_prob_rf)
    cal_ens = compute_calibration_and_pr(y_true_pairs, y_prob_ens)

    out = {
        "rf_baseline": {
            "macro_f1": metrics_rf["macro_f1"],
            "balanced_accuracy": metrics_rf["balanced_accuracy"],
            "accuracy": metrics_rf["accuracy"],
            "shd": metrics_rf["shd"],
            "directed_precision": metrics_rf["directed_precision"],
            "directed_recall": metrics_rf["directed_recall"],
            "calibration": cal_rf,
        },
        "evidence_ensemble": {
            "macro_f1": metrics_ens["macro_f1"],
            "balanced_accuracy": metrics_ens["balanced_accuracy"],
            "accuracy": metrics_ens["accuracy"],
            "shd": metrics_ens["shd"],
            "directed_precision": metrics_ens["directed_precision"],
            "directed_recall": metrics_ens["directed_recall"],
            "calibration": cal_ens,
        },
        "improved": {
            "macro_f1": metrics_ens["macro_f1"],
            "balanced_acc": metrics_ens["balanced_accuracy"],
            "balanced_accuracy": metrics_ens["balanced_accuracy"],
            "precision": metrics_ens["directed_precision"],
            "directed_precision": metrics_ens["directed_precision"],
            "recall": metrics_ens["directed_recall"],
            "directed_recall": metrics_ens["directed_recall"],
            "shd": metrics_ens["shd"],
            "accuracy": metrics_ens["accuracy"],
            "calibration": cal_ens,
        },
        "calibration": cal_ens,
        "null_controls": null_results,
        "predicted_edges_rf": list(g_rf.directed_edges),
        "predicted_edges_ens": list(g_ens.directed_edges),
        "ground_truth_directed": list(gt.directed_edges),
    }

    return out
