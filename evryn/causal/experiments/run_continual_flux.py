# meflux continual_ablation
# python -m causality_in_flux.experiments.continual_ablation

"""Continual Learning under Causality in Flux Experiment.

Evaluates Algorithm 1 (Evidence Matching Framework) in a lifelong learning setting
with non-stationary causal tasks ("Causality in Flux").

Compares:
1. Evidence Matching (Algorithm 1) with representation storage R.
2. Independent Scratch Discovery (no memory / isolated causal models).
3. Evidence Matching with Finite Memory (Reservoir Sampling capacity constraint).

Tracks:
- Continual Task Accuracy
- Backward Transfer (BWT) / Catastrophic Forgetting
- Predictive Uncertainty over time
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..scm.generator import CausalTaskGenerator, CausalTask
from ..continual.flux_stream import ContinualFluxStream
from ..continual.continual_eval import ContinualCausalEvaluator
from ..matching.framework import EvidenceMatchingFramework
from ..discovery.anm import AdditiveNoiseModel


def run_continual_experiment(
    num_tasks: int = 16,
    samples_per_task: int = 500,
    memory_capacity: int = 8,
    seed: int = 42,
    plot_output: str = "continual_flux_results.png",
) -> Dict[str, Any]:
    """Run the continual learning comparison under Causality in Flux."""
    print(f"\nInitializing Continual Flux Stream with {num_tasks} sequential tasks across domains...")

    stream = ContinualFluxStream(
        num_tasks=num_tasks,
        samples_per_task=samples_per_task,
        seed=seed,
    )

    em_full = EvidenceMatchingFramework(
        memory_capacity=None,
        random_state=seed,
    )

    em_constrained = EvidenceMatchingFramework(
        memory_capacity=memory_capacity,
        retention_policy="reservoir",
        random_state=seed,
    )

    scratch_anm = AdditiveNoiseModel(random_state=seed)

    em_full_evaluator = ContinualCausalEvaluator(num_tasks=num_tasks)
    scratch_evaluator = ContinualCausalEvaluator(num_tasks=num_tasks)

    em_predictions = []
    em_uncertainties = []
    scratch_predictions = []
    ground_truths = []
    task_domains = []

    print("Executing sequential stream processing...")
    for t_idx, task in enumerate(stream):
        y_true = task.label
        ground_truths.append(y_true)
        task_domains.append(task.domain)

        res_em = em_full.process_observations(
            task.observations,
            task_id=task.task_id,
            domain=task.domain,
            var_names=task.variable_names,
        )
        pred_em = res_em["direction"]
        unc_em = res_em["uncertainty"]
        em_predictions.append(pred_em)
        em_uncertainties.append(unc_em)

        acc_em = 1.0 if pred_em == y_true else 0.0
        em_full_evaluator.record_eval(t_idx, t_idx, acc_em)

        pred_scratch, conf_scratch = scratch_anm.predict_direction(task.observations)
        scratch_predictions.append(pred_scratch)
        acc_scratch = 1.0 if pred_scratch == y_true else 0.0
        scratch_evaluator.record_eval(t_idx, t_idx, acc_scratch)

        for past_idx in range(t_idx):
            past_task = stream.get_task(past_idx)
            past_r = em_full.encode_observations(past_task.observations)
            _, past_pred_em, _, _, _ = em_full.matcher.match_and_infer(past_r, em_full.storage)
            em_full_evaluator.record_eval(
                t_idx, past_idx, 1.0 if past_pred_em == past_task.label else 0.0
            )

            scratch_evaluator.record_eval(
                t_idx, past_idx, 1.0 if scratch_predictions[past_idx] == past_task.label else 0.0
            )

    em_metrics = em_full_evaluator.compute_metrics()
    scratch_metrics = scratch_evaluator.compute_metrics()

    cumulative_em = np.cumsum(np.array(em_predictions) == np.array(ground_truths)) / np.arange(1, num_tasks + 1)
    cumulative_scratch = np.cumsum(np.array(scratch_predictions) == np.array(ground_truths)) / np.arange(1, num_tasks + 1)

    print("\n" + "=" * 65)
    print("Continual Causality in Flux: Evaluation Summary")
    print("=" * 65)
    print(f"Total Stream Tasks:        {num_tasks}")
    print(f"Evidence Matching Acc:     {cumulative_em[-1]:0.2%}")
    print(f"Scratch Baseline Acc:      {cumulative_scratch[-1]:0.2%}")
    print(f"EM Backward Transfer:      {em_metrics['backward_transfer']:+0.3f}")
    print(f"Scratch Backward Transfer: {scratch_metrics['backward_transfer']:+0.3f}")
    print("=" * 65)

    plt.figure(figsize=(10, 5), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    tasks_x = np.arange(1, num_tasks + 1)
    plt.plot(tasks_x, cumulative_em, "o-", color="#1f77b4", linewidth=2.2, label=f"Evidence Matching (Algorithm 1) [Final: {cumulative_em[-1]:.0%}]")
    plt.plot(tasks_x, cumulative_scratch, "s--", color="#d62728", linewidth=1.8, label=f"Scratch Discovery (No Memory) [Final: {cumulative_scratch[-1]:.0%}]")
    plt.axhline(0.5, color="gray", linestyle=":", label="Random Baseline (50%)")

    domains_seen = set()
    for i, dom in enumerate(task_domains):
        if dom not in domains_seen:
            domains_seen.add(dom)
            plt.axvline(i + 1, color="#2ca02c", linestyle="--", alpha=0.3)
            plt.text(i + 1.1, 0.42, f"Flux: {dom}", rotation=90, fontsize=8, color="#2ca02c")

    plt.title("Continual Causal Discovery under Causality in Flux", fontsize=13, pad=12)
    plt.xlabel("Sequential Tasks Encountered", fontsize=11)
    plt.ylabel("Cumulative Causal Accuracy", fontsize=11)
    plt.ylim(0.35, 1.05)
    plt.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()

    out_abs = os.path.abspath(plot_output)
    plt.savefig(out_abs, dpi=300)
    plt.close()
    print(f"Plot saved to: {out_abs}\n")

    return {
        "num_tasks": num_tasks,
        "em_accuracy": float(cumulative_em[-1]),
        "scratch_accuracy": float(cumulative_scratch[-1]),
        "em_metrics": em_metrics,
        "scratch_metrics": scratch_metrics,
        "uncertainties": em_uncertainties,
        "plot_path": out_abs,
    }


if __name__ == "__main__":
    run_continual_experiment()
