# meflux flux
# python -m causality_in_flux.experiments.run_multivariate_flux

"""Multivariate Continual Adaptation Experiment (Causality in Flux).

Evaluates Algorithm 1 on lifelong streams of multivariate semi-Markovian causal models
with directed cause-effect (->, <-), unobserved latent confounding (<->), and no-relation pairs
across non-stationary regimes (linear, nonlinear, dense, heavy-tailed).

Evaluates:
1. Continual Evidence Matching vs Scratch baseline
2. Forward Transfer (FWT) across domain shifts (with clean +/- formatting)
3. Backward Transfer (BWT) / Retention
4. Macro-F1, Balanced Accuracy, and per-class Precision, Recall, F1
5. Graph-level metrics: Structural Hamming Distance (SHD), Directed & Bidirected Edge F1
6. 4x4 Confusion Matrix
7. Supports both standard flux stream and controlled class-balanced stream variant.

Follows Seng et al. (PMLR 2024/2025): "Causality in Flux: Continual Adaptation
of Causal Knowledge via Evidence Matching".
"""

import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, balanced_accuracy_score, precision_recall_fscore_support

from ..scm.mixed_graph import RelationType, MixedCausalGraph, evaluate_mixed_graph
from ..scm.semi_markovian_generator import SemiMarkovianTaskGenerator, MultivariateCausalTask
from ..matching.multivariate_framework import MultivariateEvidenceMatchingFramework


def run_multivariate_flux_experiment(
    num_tasks: int = 16,
    num_variables: int = 5,
    samples_per_task: int = 600,
    seed: int = 42,
    variant: str = "standard",
) -> Dict[str, Any]:
    print("\n" + "=" * 85)
    print(f"Multivariate Causality in Flux: Continual Evidence Matching Stream ({variant.upper()})")
    print("=" * 85)

    gen = SemiMarkovianTaskGenerator(seed=seed)

    print("\n[Step 1] Pre-training Relational Prior on Reference Semi-Markovian Tasks...")
    ref_tasks = [
        gen.generate_task(
            f"ref_{i}",
            num_variables=num_variables,
            num_samples=500,
            directed_prob=0.35,
            confounded_prob=0.30,
            mechanism_type=["linear", "tanh", "polynomial", "mixed"][i % 4],
            noise_type=["laplace", "gaussian", "uniform"][i % 3],
            ensure_all_classes=True,
        )
        for i in range(30)
    ]

    matching_framework = MultivariateEvidenceMatchingFramework(
        memory_capacity=25,
        k_neighbors=2,
        uncertainty_threshold=0.80,
        class_weight="balanced",
        balanced_sampling=True,
        edge_threshold=0.45,
        decision_mode="hierarchical",
        refinement_enabled=True,
        random_state=seed,
    )
    matching_framework.fit_relational_classifier(ref_tasks)

    scratch_framework = MultivariateEvidenceMatchingFramework(
        memory_capacity=0,
        uncertainty_threshold=1.0,
        class_weight="balanced",
        balanced_sampling=True,
        edge_threshold=0.45,
        decision_mode="hierarchical",
        refinement_enabled=False,
        random_state=seed,
    )
    scratch_framework.fit_relational_classifier(ref_tasks)

    if variant == "balanced":
        print(f"\n[Step 2] Generating Controlled Class-Balanced Stream of {num_tasks} Tasks...")
        stream = gen.generate_class_balanced_stream(
            num_tasks=num_tasks,
            num_variables=max(5, num_variables),
            samples_per_task=samples_per_task,
        )
    else:
        print(f"\n[Step 2] Generating Non-Stationary Flux Stream of {num_tasks} Tasks across 4 Regimes...")
        stream = gen.generate_multivariate_flux_stream(
            num_tasks=num_tasks,
            num_variables=num_variables,
            samples_per_task=samples_per_task,
            regimes=["linear_sparse", "nonlinear_confounded", "dense_mixed", "heavy_tail_flux"],
        )

    matching_accuracies = []
    matching_bal_accs = []
    matching_macro_f1s = []
    matching_shds = []

    scratch_accuracies = []
    scratch_bal_accs = []
    scratch_macro_f1s = []
    scratch_shds = []

    uncertainties = []
    sources = []
    task_labels = []
    regimes = []
    all_true_rels = []
    all_pred_matching = []
    all_pred_scratch = []

    print("\n[Step 3] Processing Stream under Domain Flux...")
    print(f"{'Task':<6} | {'Regime':<21} | {'EM Acc':<7} | {'Scr Acc':<7} | {'EM MacF1':<8} | {'EM BalAcc':<9} | {'EM SHD':<6} | {'Uncert':<7} | {'Source'}")
    print("-" * 105)

    for idx, task in enumerate(stream):
        nodes = task.variable_names
        regime = task.domain
        regimes.append(regime)
        label = f"T{idx+1:02d}"
        task_labels.append(label)

        res_matching = matching_framework.process_task(
            observations=task.observations,
            var_names=nodes,
            task_id=task.task_id,
            domain=regime,
        )
        em_eval = evaluate_mixed_graph(task.graph, res_matching["graph"], nodes)

        g_scratch = scratch_framework.identify_from_scratch(task.observations, nodes)
        sc_eval = evaluate_mixed_graph(task.graph, g_scratch, nodes)

        matching_accuracies.append(em_eval["accuracy"])
        matching_bal_accs.append(em_eval["balanced_accuracy"])
        matching_macro_f1s.append(em_eval["macro_f1"])
        matching_shds.append(em_eval["shd"])

        scratch_accuracies.append(sc_eval["accuracy"])
        scratch_bal_accs.append(sc_eval["balanced_accuracy"])
        scratch_macro_f1s.append(sc_eval["macro_f1"])
        scratch_shds.append(sc_eval["shd"])

        uncertainties.append(res_matching["uncertainty"])
        sources.append(res_matching["source"])

        all_true_rels.extend(em_eval["true_relations"])
        all_pred_matching.extend(em_eval["pred_relations"])
        all_pred_scratch.extend(sc_eval["pred_relations"])

        print(f"{label:<6} | {regime:<21} | {em_eval['accuracy']:0.2%} | {sc_eval['accuracy']:0.2%} | {em_eval['macro_f1']:0.4f}   | {em_eval['balanced_accuracy']:0.2%}   | {em_eval['shd']:3d}    | {res_matching['uncertainty']:0.3f}   | {res_matching['source']}")

    print("\n[Step 4] Evaluating Backward Transfer (Retention on Past Tasks)...")
    bwt_diffs = []
    for idx, task in enumerate(stream[:-1]):
        nodes = task.variable_names
        g_final = matching_framework.stored_graphs[idx]
        eval_retained = evaluate_mixed_graph(task.graph, g_final, nodes)
        bwt_diffs.append(eval_retained["accuracy"] - matching_accuracies[idx])

    mean_bwt = float(np.mean(bwt_diffs)) if bwt_diffs else 0.0
    mean_matching_acc = float(np.mean(matching_accuracies))
    mean_scratch_acc = float(np.mean(scratch_accuracies))
    mean_matching_bal = float(np.mean(matching_bal_accs))
    mean_scratch_bal = float(np.mean(scratch_bal_accs))
    mean_matching_f1 = float(np.mean(matching_macro_f1s))
    mean_scratch_f1 = float(np.mean(scratch_macro_f1s))
    mean_matching_shd = float(np.mean(matching_shds))
    mean_scratch_shd = float(np.mean(scratch_shds))

    forward_transfer = [m - s for m, s in zip(matching_accuracies, scratch_accuracies)]
    mean_fwt = float(np.mean(forward_transfer))

    print("\n" + "=" * 85)
    print("Multivariate Causality in Flux: Evaluation Summary")
    print("=" * 85)
    print(f"Mean Evidence Matching Accuracy: {mean_matching_acc:0.2%} (Scratch: {mean_scratch_acc:0.2%})")
    print(f"Mean Balanced Accuracy:          {mean_matching_bal:0.2%} (Scratch: {mean_scratch_bal:0.2%})")
    print(f"Mean Macro-F1 Score:             {mean_matching_f1:0.4f} (Scratch: {mean_scratch_f1:0.4f})")
    print(f"Mean Structural Hamming (SHD):   {mean_matching_shd:0.2f} (Scratch: {mean_scratch_shd:0.2f})")
    print(f"Mean Forward Transfer (FWT):      {mean_fwt * 100:+0.2f}%")
    print(f"Mean Backward Transfer (BWT):     {mean_bwt * 100:+0.2f}% (Retention)")
    print("=" * 85)

    y_true_all = np.array(all_true_rels)
    y_em_all = np.array(all_pred_matching)
    cm_global = confusion_matrix(y_true_all, y_em_all, labels=[0, 1, 2, 3])
    prec, rec, f1, sup = precision_recall_fscore_support(y_true_all, y_em_all, labels=[0, 1, 2, 3], zero_division=0)

    target_names = ["No Relation", "Forward (->)", "Backward (<-)", "Confounded (<->)"]
    print("\nGlobal Relation Classification Breakdown across Lifelong Stream:")
    print(f"{'Class':<20} | {'True':<6} | {'Pred':<6} | {'Match':<6} | {'Recall':<8} | {'Precision':<10} | {'F1-Score'}")
    print("-" * 85)
    for code, name in enumerate(target_names):
        count_true = int(sup[code])
        count_pred = int(np.sum(y_em_all == code))
        correct = int(cm_global[code, code])
        print(f"[{code}] {name:<16} | {count_true:5d}  | {count_pred:5d}  | {correct:5d}  | {rec[code]:0.2%}   | {prec[code]:0.2%}     | {f1[code]:0.4f}")

    print("\nGlobal Confusion Matrix across Stream (Rows: True, Columns: Predicted):")
    print("                None  Forward Backward Confounded")
    for r_idx, r_name in enumerate(["None      ", "Forward   ", "Backward  ", "Confounded"]):
        row_str = "  ".join(f"{cm_global[r_idx, c_idx]:5d}" for c_idx in range(4))
        print(f"  {r_name}: {row_str}")

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    x = np.arange(1, num_tasks + 1)

    axes[0, 0].plot(x, [f * 100 for f in matching_macro_f1s], marker="o", color="#2ca02c", linewidth=2.5, label=f"Evidence Matching Macro-F1 ({mean_matching_f1:0.3f})")
    axes[0, 0].plot(x, [f * 100 for f in scratch_macro_f1s], marker="s", linestyle="--", color="#ff7f0e", linewidth=2.0, label=f"Scratch Macro-F1 ({mean_scratch_f1:0.3f})")
    axes[0, 0].plot(x, [b * 100 for b in matching_bal_accs], color="#1f77b4", linestyle=":", linewidth=1.8, label=f"EM Balanced Acc ({mean_matching_bal:0.1%})")
    axes[0, 0].set_title("A: Continual Relational Macro-F1 under Flux", fontsize=13, fontweight="bold")
    axes[0, 0].set_xlabel("Task Index in Lifelong Stream", fontsize=11)
    axes[0, 0].set_ylabel("Metric (%)", fontsize=11)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(task_labels, rotation=45)
    axes[0, 0].set_ylim(0, 105)
    axes[0, 0].grid(True, linestyle=":", alpha=0.6)
    axes[0, 0].legend(loc="lower right", framealpha=0.9)

    fwt_pct = [f * 100 for f in forward_transfer]
    bar_colors = ["#2ca02c" if v >= 0 else "#d62728" for v in fwt_pct]
    axes[0, 1].bar(x, fwt_pct, color=bar_colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    axes[0, 1].axhline(y=0, color="black", linestyle="-", linewidth=1.0)
    axes[0, 1].axhline(y=mean_fwt * 100, color="#1f77b4", linestyle="--", label=f"Mean FWT ({mean_fwt*100:+0.1f}%)")
    axes[0, 1].set_title("B: Forward Transfer (Accuracy Advantage vs Scratch)", fontsize=13, fontweight="bold")
    axes[0, 1].set_xlabel("Task Index", fontsize=11)
    axes[0, 1].set_ylabel("Accuracy Advantage (%)", fontsize=11)
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(task_labels, rotation=45)
    axes[0, 1].grid(True, linestyle=":", alpha=0.6)
    axes[0, 1].legend()

    uncert_colors = ["#2ca02c" if s == "matched_and_refined" else "#d62728" for s in sources]
    axes[1, 0].scatter(x, uncertainties, c=uncert_colors, s=120, edgecolors="black", zorder=3)
    axes[1, 0].plot(x, uncertainties, color="gray", linestyle=":", alpha=0.7, zorder=2)
    axes[1, 0].axhline(y=matching_framework.uncertainty_threshold, color="red", linestyle="--", label=f"tau = {matching_framework.uncertainty_threshold}")
    axes[1, 0].set_title("C: Evidence Uncertainty u_t Across Domain Shifts", fontsize=13, fontweight="bold")
    axes[1, 0].set_xlabel("Task Index", fontsize=11)
    axes[1, 0].set_ylabel("Representation Uncertainty u_t", fontsize=11)
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(task_labels, rotation=45)
    axes[1, 0].set_ylim(-0.05, 1.05)
    axes[1, 0].grid(True, linestyle=":", alpha=0.6)
    axes[1, 0].legend()

    im = axes[1, 1].imshow(cm_global, cmap="Blues", interpolation="nearest")
    axes[1, 1].set_title("D: Global Confusion Matrix across Lifelong Stream", fontsize=13, fontweight="bold")
    tick_marks = range(4)
    axes[1, 1].set_xticks(tick_marks)
    axes[1, 1].set_yticks(tick_marks)
    axes[1, 1].set_xticklabels(["None", "Fwd", "Bwd", "Conf"], fontsize=10)
    axes[1, 1].set_yticklabels(["None", "Fwd", "Bwd", "Conf"], fontsize=10)
    axes[1, 1].set_xlabel("Predicted Label", fontsize=11)
    axes[1, 1].set_ylabel("True Label", fontsize=11)
    for i in range(4):
        for j in range(4):
            val = cm_global[i, j]
            color = "white" if val > cm_global.max() / 2.0 else "black"
            axes[1, 1].text(j, i, str(val), ha="center", va="center", color=color, fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=axes[1, 1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "multivariate_flux_results.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"\nPublication plot saved successfully to: {out_path}")

    return {
        "mean_matching_acc": mean_matching_acc,
        "mean_scratch_acc": mean_scratch_acc,
        "mean_matching_bal": mean_matching_bal,
        "mean_matching_macro_f1": mean_matching_f1,
        "mean_fwt": mean_fwt,
        "mean_bwt": mean_bwt,
        "mean_matching_shd": mean_matching_shd,
        "global_confusion_matrix": cm_global,
    }


if __name__ == "__main__":
    run_multivariate_flux_experiment()
