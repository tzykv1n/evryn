# python cli.py classifier_ablation --seeds 10
# meflux classifier_ablation --seeds 10

import os
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from ..scm.mixed_graph import RelationType, evaluate_hypergraph
from ..scm.independent_hcam_generator import IndependentHCAMGenerator
from ..features.higher_order_features import HigherOrderFeatureExtractor
from ..matching.higher_order_framework import HigherOrderEvidenceMatchingFramework
from .robustness_metrics import compute_distribution_statistics


from sklearn.calibration import CalibratedClassifierCV


def get_classifier(name: str, seed: int = 42):
    if name == "Random Forest":
        return RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=seed, n_jobs=-1)
    elif name == "SVM-RBF":
        return CalibratedClassifierCV(SVC(kernel="rbf", C=1.0, class_weight="balanced", random_state=seed), cv=2, ensemble=False)
    elif name == "Logistic Regression":
        return LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
    elif name == "MLP":
        return MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=400, random_state=seed)
    elif name == "HistGradientBoosting":
        return HistGradientBoostingClassifier(max_iter=100, class_weight="balanced", random_state=seed)
    elif name == "ExtraTrees":
        return ExtraTreesClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=seed, n_jobs=-1)
    else:
        raise ValueError(f"Unknown classifier: {name}")


def run_classifier_ablation_experiment(
    seeds: int = 5,
    samples: int = 800,
    output_dir: str = ".",
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    classifier_names = [
        "Random Forest",
        "SVM-RBF",
        "Logistic Regression",
        "MLP",
        "HistGradientBoosting",
        "ExtraTrees",
    ]
    results = {}
    seed_list = [42 + i * 13 for i in range(seeds)]

    gen = IndependentHCAMGenerator(seed=42)
    extractor = HigherOrderFeatureExtractor(random_state=42)

    train_tasks = gen.generate_training_set(num_samples=samples, seed=42)
    X_train_o2, y_train_o2 = [], []

    for task in train_tasks:
        nodes = task.variable_names
        d = len(nodes)
        if d < 3:
            continue
        gt_hyper = set()
        for r in task.graph.hyper_relations:
            if len(r.sources) == 2 and r.relation_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
                gt_hyper.add((frozenset(r.sources), r.target))

        fw_dummy = HigherOrderEvidenceMatchingFramework()
        candidates = fw_dummy.generate_order2_candidates(task.observations, nodes)
        for (i, j), k in candidates:
            src = frozenset([nodes[i], nodes[j]])
            tgt = nodes[k]
            is_joint = 1 if (src, tgt) in gt_hyper else 0
            f_dict = extractor.extract_triple_features(task.observations, i, j, k)
            vec = extractor.vector_from_dict(f_dict, "all_features")
            X_train_o2.append(vec)
            y_train_o2.append(is_joint)

    X_train_arr = np.array(X_train_o2, dtype=np.float32)
    y_train_arr = np.array(y_train_o2, dtype=int)

    for clf_name in classifier_names:
        o2_f1s, o3_f1s, bal_accs, runtimes = [], [], [], []

        for s in seed_list:
            t0 = time.time()
            clf = get_classifier(clf_name, seed=s)
            clf.fit(X_train_arr, y_train_arr)
            t_fit = time.time() - t0

            test_tasks = gen.generate_test_set(num_samples=samples, seed=s)
            seed_o2, seed_o3, seed_bal = [], [], []

            for test_t in test_tasks:
                nodes = test_t.variable_names
                d = len(nodes)
                fw = HigherOrderEvidenceMatchingFramework(max_order=2, random_state=s)
                candidates = fw.generate_order2_candidates(test_t.observations, nodes)

                pred_g = test_t.graph.__class__(nodes)
                for (i, j), k in candidates:
                    f_d = extractor.extract_triple_features(test_t.observations, i, j, k)
                    v = extractor.vector_from_dict(f_d, "all_features")
                    prob = clf.predict_proba([v])[0][1] if hasattr(clf, "predict_proba") else 0.5
                    if prob >= 0.50:
                        pred_g.add_hyperedge([nodes[i], nodes[j]], nodes[k], RelationType.JOINT_CAUSAL)

                ev = evaluate_hypergraph(test_t.graph, pred_g, nodes)
                seed_o2.append(ev["order_2_f1"])
                seed_o3.append(ev["order_3_f1"])
                seed_bal.append(ev["pairwise_projection_balanced_acc"])

            t_total = (time.time() - t0) * 1000.0
            o2_f1s.append(float(np.mean(seed_o2)))
            o3_f1s.append(float(np.mean(seed_o3)))
            bal_accs.append(float(np.mean(seed_bal)))
            runtimes.append(t_total)

        results[clf_name] = {
            "order_2_f1": compute_distribution_statistics(o2_f1s),
            "order_3_f1": compute_distribution_statistics(o3_f1s),
            "balanced_accuracy": compute_distribution_statistics(bal_accs),
            "runtime_ms": compute_distribution_statistics(runtimes),
        }

    return results
