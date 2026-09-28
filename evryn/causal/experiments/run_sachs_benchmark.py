# meflux sachs_improved
# python -m causality_in_flux.experiments.sachs_improved

"""Sachs (2005) Protein Signaling Multivariate Causal Discovery Benchmark.

Evaluates evidence matching and continual causal discovery on the 11-variable protein signaling
network from Sachs et al. (Science 2005), predicting all four relation classes:
1. NO_RELATION
2. FORWARD (->)
3. BACKWARD (<-)
4. CONFOUNDED (<->)

Evaluates:
- Macro-F1 (primary metric)
- Balanced Accuracy
- Raw Pairwise Accuracy
- Per-class Precision, Recall, and F1
- 4x4 Confusion Matrix
- Graph-level SHD (Structural Hamming Distance)
- Directed and Bidirected edge Precision & Recall

Follows Seng et al. (PMLR 2024/2025): "Causality in Flux: Continual Adaptation
of Causal Knowledge via Evidence Matching".
"""

import os
from typing import Dict, Any, List
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..datasets.sachs_loader import SachsBenchmarkLoader
from ..scm.mixed_graph import RelationType, MixedCausalGraph, evaluate_mixed_graph
from ..scm.semi_markovian_generator import SemiMarkovianTaskGenerator
from ..matching.multivariate_framework import MultivariateEvidenceMatchingFramework


def run_sachs_experiment() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("Sachs (2005) Multivariate Signaling Network: Continual Evidence Matching")
    print("=" * 80)

    loader = SachsBenchmarkLoader()
    tasks = loader.load_all_condition_tasks()
    gt_graph = loader.get_ground_truth_graph()
    nodes = loader.PROTEINS

    print(f"Loaded {len(tasks)} biological experimental conditions:")
    for t in tasks:
        print(f"  - {t.task_id:<32} | {t.num_samples:5d} cells | {t.domain}")

    print("\nGround Truth Consensus Mixed Graph Structure (11 variables, 55 possible pairs):")
    for k, v in gt_graph.summary().items():
        print(f"  - {k}: {v}")

    print("\n[Step 1] Pre-training Relational Prior on Reference Semi-Markovian Tasks...")
    gen = SemiMarkovianTaskGenerator(seed=42)
    ref_tasks = [
        gen.generate_task(
            f"ref_{i}",
            num_variables=6,
            num_samples=600,
            directed_prob=0.35,
            confounded_prob=0.30,
            mechanism_type=["linear", "tanh", "polynomial", "mixed"][i % 4],
            noise_type=["laplace", "gaussian", "uniform"][i % 3],
            ensure_all_classes=True,
        )
        for i in range(30)
    ]

    framework = MultivariateEvidenceMatchingFramework(
        memory_capacity=20,
        k_neighbors=2,
        uncertainty_threshold=0.85,
        class_weight="balanced",
        balanced_sampling=True,
        edge_threshold=0.45,
        decision_mode="hierarchical",
        refinement_enabled=True,
        random_state=42,
    )
    framework.fit_relational_classifier(ref_tasks)
    print("Relational classifier pre-trained successfully (class_weight='balanced', balanced_sampling=True).")

    print("\n[Step 2] Executing Continual Evidence Matching (Algorithm 1)...")
    task_names = []
    accuracies = []
    bal_accuracies = []
    macro_f1s = []
    shd_list = []
    uncertainties = []
    sources = []
    all_evals = []

    print(f"{'Condition':<26} | {'Acc':<7} | {'BalAcc':<7} | {'MacF1':<7} | {'SHD':<4} | {'Uncert':<7} | {'Source'}")
    print("-" * 88)

    for idx, task in enumerate(tasks):
        res = framework.process_task(
            observations=task.observations,
            var_names=task.variable_names,
            task_id=task.task_id,
            domain=task.domain,
        )
        eval_res = evaluate_mixed_graph(gt_graph, res["graph"], nodes)

        clean_name = task.task_id.replace("sachs_", "").replace("int_", "")
        task_names.append(clean_name)
        accuracies.append(eval_res["accuracy"])
        bal_accuracies.append(eval_res["balanced_accuracy"])
        macro_f1s.append(eval_res["macro_f1"])
        shd_list.append(eval_res["shd"])
        uncertainties.append(res["uncertainty"])
        sources.append(res["source"])
        all_evals.append(eval_res)

        print(f"{clean_name:<26} | {eval_res['accuracy']:0.2%} | {eval_res['balanced_accuracy']:0.2%} | {eval_res['macro_f1']:0.4f} | {eval_res['shd']:3d} | {res['uncertainty']:0.3f}   | {res['source']}")

    mean_acc = float(np.mean(accuracies))
    mean_bal_acc = float(np.mean(bal_accuracies))
    mean_macro_f1 = float(np.mean(macro_f1s))
    mean_shd = float(np.mean(shd_list))

    print("\n" + "=" * 80)
    print("Sachs (2005) Continual Evidence Matching: Summary Across Conditions")
    print("=" * 80)
    print(f"Mean Pairwise Accuracy:       {mean_acc:0.2%}")
    print(f"Mean Balanced Accuracy:       {mean_bal_acc:0.2%}")
    print(f"Mean Macro-F1:                {mean_macro_f1:0.4f}")
    print(f"Mean Structural Hamming (SHD):{mean_shd:0.2f}")
    print("=" * 80)

    last_eval = all_evals[-1]
    target_names = ["No Relation", "Forward (->)", "Backward (<-)", "Confounded (<->)"]
    print("\nFinal Mixed Graph Relation Classification Breakdown:")
    print(f"{'Class':<20} | {'True':<5} | {'Pred':<5} | {'Match':<5} | {'Recall':<8} | {'Precision':<10} | {'F1-Score'}")
    print("-" * 80)

    for code, name in enumerate(target_names):
        count_true = int(last_eval["per_class_support"][code])
        count_pred = int(np.sum(last_eval["pred_relations"] == code))
        correct = int(last_eval["confusion_matrix"][code, code])
        rec = float(last_eval["per_class_recall"][code])
        prec = float(last_eval["per_class_precision"][code])
        f1 = float(last_eval["per_class_f1"][code])
        print(f"[{code}] {name:<16} | {count_true:4d}  | {count_pred:4d}  | {correct:4d}  | {rec:0.2%}   | {prec:0.2%}     | {f1:0.4f}")

    print("\nConfusion Matrix (Rows: True, Columns: Predicted):")
    print("                None  Forward Backward Confounded")
    for r_idx, r_name in enumerate(["None      ", "Forward   ", "Backward  ", "Confounded"]):
        row_str = "  ".join(f"{last_eval['confusion_matrix'][r_idx, c_idx]:4d}" for c_idx in range(4))
        print(f"  {r_name}: {row_str}")

    print("\nGraph-Level Topology Metrics:")
    print(f"  Directed Edges   : Precision = {last_eval['directed_precision']:0.2%}, Recall = {last_eval['directed_recall']:0.2%}, F1 = {last_eval['directed_f1']:0.4f}")
    print(f"  Bidirected Edges : Precision = {last_eval['bidirected_precision']:0.2%}, Recall = {last_eval['bidirected_recall']:0.2%}, F1 = {last_eval['bidirected_f1']:0.4f}")
    print(f"  SHD              : {last_eval['shd']} (out of 55 pairs)")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    x_idx = range(1, len(tasks) + 1)
    axes[0].plot(x_idx, [f * 100 for f in macro_f1s], marker="o", color="#2ca02c", linewidth=2.5, markersize=8, label="Macro-F1 (%)")
    axes[0].plot(x_idx, [b * 100 for b in bal_accuracies], marker="s", color="#1f77b4", linewidth=2.0, linestyle="--", markersize=7, label="Balanced Acc (%)")
    axes[0].plot(x_idx, [a * 100 for a in accuracies], color="gray", linewidth=1.5, linestyle=":", alpha=0.7, label="Raw Acc (%)")
    axes[0].axhline(y=mean_macro_f1 * 100, color="#2ca02c", linestyle=":", alpha=0.6)
    axes[0].set_title("Continual Adaptation on Sachs (2005)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Experimental Condition", fontsize=11)
    axes[0].set_ylabel("Metric (%)", fontsize=11)
    axes[0].set_xticks(x_idx)
    axes[0].set_xticklabels([f"C{i}" for i in x_idx])
    axes[0].set_ylim(0, 100)
    axes[0].grid(True, linestyle=":", alpha=0.6)
    axes[0].legend()

    cm = last_eval["confusion_matrix"]
    im = axes[1].imshow(cm, cmap="Blues", interpolation="nearest")
    axes[1].set_title("Final Confusion Matrix (Sachs)", fontsize=13, fontweight="bold")
    tick_marks = range(4)
    axes[1].set_xticks(tick_marks)
    axes[1].set_yticks(tick_marks)
    axes[1].set_xticklabels(["None", "Fwd", "Bwd", "Conf"], fontsize=10)
    axes[1].set_yticklabels(["None", "Fwd", "Bwd", "Conf"], fontsize=10)
    axes[1].set_xlabel("Predicted Label", fontsize=11)
    axes[1].set_ylabel("True Label", fontsize=11)
    for i in range(4):
        for j in range(4):
            val = cm[i, j]
            color = "white" if val > cm.max() / 2.0 else "black"
            axes[1].text(j, i, str(val), ha="center", va="center", color=color, fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)

    colors = ["#2ca02c" if s == "matched_and_refined" else "#d62728" for s in sources]
    axes[2].bar(x_idx, uncertainties, color=colors, alpha=0.8)
    axes[2].set_title("Evidence Uncertainty & Matching Hits", fontsize=13, fontweight="bold")
    axes[2].set_xlabel("Experimental Condition", fontsize=11)
    axes[2].set_ylabel("Normalized Uncertainty u_t", fontsize=11)
    axes[2].set_xticks(x_idx)
    axes[2].set_xticklabels([f"C{i}" for i in x_idx])
    axes[2].grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sachs_continual_results.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"\nPublication plot saved successfully to: {out_path}")

    return {
        "mean_accuracy": mean_acc,
        "mean_balanced_accuracy": mean_bal_acc,
        "mean_macro_f1": mean_macro_f1,
        "mean_shd": mean_shd,
        "final_evaluation": last_eval,
    }


if __name__ == "__main__":
    run_sachs_experiment()
