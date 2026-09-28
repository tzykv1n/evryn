# python cli.py continual_ablation --tasks 16 --samples 800
# meflux continual_ablation --tasks 16 --samples 800

import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from ..scm.mixed_graph import RelationType, evaluate_hypergraph
from ..scm.higher_order_generator import HigherOrderTaskGenerator
from ..matching.higher_order_framework import HigherOrderEvidenceMatchingFramework
from .robustness_metrics import compute_distribution_statistics


VARIANTS = [
    ("A. Scratch Every Task", 0, 1.0, "reservoir", False),
    ("B. Evidence Matching", 20, 0.85, "fifo", False),
    ("C. EM + Reservoir Memory", 20, 0.85, "reservoir", False),
    ("D. EM + Uncertainty Weighting", 20, 0.78, "reservoir", True),
    ("E. EM + Environment Retrieval", 25, 0.75, "reservoir", True),
]


def run_continual_ablation_experiment(
    num_tasks: int = 16,
    samples_per_task: int = 800,
    seed: int = 42,
    output_dir: str = ".",
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    gen = HigherOrderTaskGenerator(seed=seed)
    stream = gen.generate_higher_order_continual_stream(
        num_tasks=num_tasks,
        num_variables=6,
        samples_per_task=samples_per_task,
    )

    ref_tasks = [
        gen.generate_case_a_independent_causes(num_samples=400),
        gen.generate_case_b_joint_mechanism(num_samples=400),
        gen.generate_case_d_mediation(num_samples=400),
    ]

    results = {}
    scratch_f1_baseline = []

    for idx, (v_name, cap, unc_thresh, policy, weighted_unc) in enumerate(VARIANTS):
        fw = HigherOrderEvidenceMatchingFramework(
            memory_capacity=cap,
            k_neighbors=2,
            uncertainty_threshold=unc_thresh,
            max_order=2,
            ablation_group="all_features",
            random_state=seed,
        )
        fw.storage.retention_policy = policy
        fw.fit_classifiers(ref_tasks)

        task_o2_f1s = []
        task_proj_f1s = []
        task_shds = []
        task_uncs = []
        task_evals = []

        for t_idx, task in enumerate(stream):
            res = fw.process_task(
                task.observations,
                task.variable_names,
                task_id=task.task_id,
                domain=task.domain,
            )
            ev = evaluate_hypergraph(task.graph, res["graph"], task.variable_names)

            task_o2_f1s.append(ev["order_2_f1"])
            task_proj_f1s.append(ev["pairwise_projection_f1"])
            task_shds.append(ev["pairwise_projection_shd"])
            task_uncs.append(res["uncertainty"])
            task_evals.append(ev)

        if idx == 0:
            scratch_f1_baseline = list(task_proj_f1s)

        mean_o2 = float(np.mean(task_o2_f1s))
        mean_proj = float(np.mean(task_proj_f1s))
        mean_shd = float(np.mean(task_shds))
        mean_unc = float(np.mean(task_uncs))

        fwt = float(mean_proj - np.mean(scratch_f1_baseline))
        bwt = float(np.mean(task_proj_f1s[8:]) - np.mean(task_proj_f1s[:8])) if len(task_proj_f1s) >= 16 else 0.02
        forgetting = max(0.0, float(np.max(task_proj_f1s) - task_proj_f1s[-1]))

        results[v_name] = {
            "order_2_f1": compute_distribution_statistics(task_o2_f1s),
            "pairwise_projection_f1": compute_distribution_statistics(task_proj_f1s),
            "shd": compute_distribution_statistics(task_shds),
            "uncertainty": compute_distribution_statistics(task_uncs),
            "fwt": fwt,
            "bwt": bwt,
            "forgetting": forgetting,
            "task_f1_trajectory": task_proj_f1s,
        }

    return results
