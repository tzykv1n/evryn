# python cli.py feature_ablation --seeds 10
# meflux feature_ablation --seeds 10

import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from ..scm.mixed_graph import RelationType, evaluate_hypergraph
from ..scm.independent_hcam_generator import IndependentHCAMGenerator
from ..features.higher_order_features import HigherOrderFeatureExtractor
from ..matching.higher_order_framework import HigherOrderEvidenceMatchingFramework
from .robustness_metrics import compute_distribution_statistics, paired_significance_test


CONDITIONS = [
    ("A. Pairwise-only", "cond_A"),
    ("B. + Joint MI", "cond_B"),
    ("C. + Conditional MI", "cond_C"),
    ("D. + PID / Synergy", "cond_D"),
    ("E. + Interaction Gain", "cond_E"),
    ("F. + Invariance", "cond_F"),
    ("G. Full System", "all_features"),
]


def run_nested_feature_ablation(
    seeds: int = 5,
    samples: int = 800,
    noise: float = 0.25,
    output_dir: str = ".",
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    gen = IndependentHCAMGenerator(seed=42)
    extractor = HigherOrderFeatureExtractor(random_state=42)
    seed_list = [42 + i * 17 for i in range(seeds)]

    train_tasks = gen.generate_training_set(num_samples=samples, seed=42)
    condition_results = {}
    pairwise_o2_f1s = []

    for idx, (c_label, c_group) in enumerate(CONDITIONS):
        fw = HigherOrderEvidenceMatchingFramework(
            memory_capacity=0,
            max_order=2,
            ablation_group=c_group,
            class_weight="balanced",
            random_state=42,
        )
        fw.fit_classifiers(train_tasks)

        o2_f1s, o3_f1s, precs, recs, bal_accs, exacts, fpr_list = [], [], [], [], [], [], []

        for s in seed_list:
            test_tasks = gen.generate_test_set(num_samples=samples, noise=noise, seed=s)
            s_o2, s_o3, s_prec, s_rec, s_bal, s_exact, s_fpr = [], [], [], [], [], [], []

            for test_t in test_tasks:
                nodes = test_t.variable_names
                d = len(nodes)
                pred_g = test_t.graph.__class__(nodes)

                if c_group != "cond_A":
                    candidates = fw.generate_order2_candidates(test_t.observations, nodes)
                    for (i, j), k in candidates:
                        f_d = extractor.extract_triple_features(test_t.observations, i, j, k)
                        vec = extractor.vector_from_dict(f_d, c_group)
                        if fw.order2_clf is not None:
                            prob = fw.order2_clf.predict_proba([vec])[0][1]
                            if prob >= 0.50:
                                pred_g.add_hyperedge([nodes[i], nodes[j]], nodes[k], RelationType.JOINT_CAUSAL)

                ev = evaluate_hypergraph(test_t.graph, pred_g, nodes)
                s_o2.append(ev["order_2_f1"])
                s_o3.append(ev["order_3_f1"])
                s_prec.append(ev["hyperedge_precision"])
                s_rec.append(ev["hyperedge_recall"])
                s_bal.append(ev["pairwise_projection_balanced_acc"])
                s_exact.append(ev["exact_hypergraph_match"])

                gt_hypers = len([r for r in test_t.graph.hyper_relations if len(r.sources) > 1])
                pred_hypers = len([r for r in pred_g.hyper_relations if len(r.sources) > 1])
                if gt_hypers == 0:
                    s_fpr.append(1.0 if pred_hypers > 0 else 0.0)
                else:
                    s_fpr.append(0.0)

            o2_f1s.append(float(np.mean(s_o2)))
            o3_f1s.append(float(np.mean(s_o3)))
            precs.append(float(np.mean(s_prec)))
            recs.append(float(np.mean(s_rec)))
            bal_accs.append(float(np.mean(s_bal)))
            exacts.append(float(np.mean(s_exact)))
            fpr_list.append(float(np.mean(s_fpr)))

        if idx == 0:
            pairwise_o2_f1s = list(o2_f1s)

        paired_res = paired_significance_test(o2_f1s, pairwise_o2_f1s)

        condition_results[c_label] = {
            "order_2_f1": compute_distribution_statistics(o2_f1s),
            "order_3_f1": compute_distribution_statistics(o3_f1s),
            "precision": compute_distribution_statistics(precs),
            "recall": compute_distribution_statistics(recs),
            "balanced_accuracy": compute_distribution_statistics(bal_accs),
            "exact_match": compute_distribution_statistics(exacts),
            "false_positive_rate": compute_distribution_statistics(fpr_list),
            "paired_improvement_vs_pairwise": paired_res,
        }

    return condition_results
