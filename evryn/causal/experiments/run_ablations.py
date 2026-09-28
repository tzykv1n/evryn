# meflux --help

"""Controlled Ablation Suite for Relational Classification and Continual Flux.

Evaluates 6 controlled conditions on Sachs (2005) signaling benchmark and Synthetic Flux stream:
A. Current classifier (unweighted, naive argmax, unweighted reference tasks)
B. Class-weighted classifier (class_weight='balanced')
C. Balanced sampling (stratified resampling of pairs across classes)
D. Class-weighted + balanced sampling
E. Matching without refinement (evidence matching memory retrieval without Bayesian adaptation)
F. Matching + refinement (full FLUX Algorithm 1 pipeline)

Uses identical random seeds, data splits, and reference task generation across all conditions.
"""

from typing import Dict, Any, List
import numpy as np

from ..datasets.sachs_loader import SachsBenchmarkLoader
from ..scm.mixed_graph import RelationType, MixedCausalGraph, evaluate_mixed_graph
from ..scm.semi_markovian_generator import SemiMarkovianTaskGenerator, MultivariateCausalTask
from ..matching.multivariate_framework import MultivariateEvidenceMatchingFramework


def run_ablation_condition(
    condition_name: str,
    class_weight: Any,
    balanced_sampling: bool,
    decision_mode: str,
    refinement_enabled: bool,
    ref_tasks: List[Any],
    sachs_tasks: List[Any],
    sachs_gt: MixedCausalGraph,
    sachs_nodes: List[str],
    flux_stream: List[Any],
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute a single ablation condition across both Sachs and synthetic benchmarks."""
    framework = MultivariateEvidenceMatchingFramework(
        memory_capacity=25,
        k_neighbors=2,
        uncertainty_threshold=0.85,
        class_weight=class_weight,
        balanced_sampling=balanced_sampling,
        edge_threshold=0.45,
        decision_mode=decision_mode,
        refinement_enabled=refinement_enabled,
        random_state=seed,
    )
    framework.fit_relational_classifier(ref_tasks)

    sachs_accs, sachs_bal, sachs_f1, sachs_shd = [], [], [], []
    sachs_evals = []
    for task in sachs_tasks:
        res = framework.process_task(
            observations=task.observations,
            var_names=task.variable_names,
            task_id=task.task_id,
            domain=task.domain,
        )
        ev = evaluate_mixed_graph(sachs_gt, res["graph"], sachs_nodes)
        sachs_accs.append(ev["accuracy"])
        sachs_bal.append(ev["balanced_accuracy"])
        sachs_f1.append(ev["macro_f1"])
        sachs_shd.append(ev["shd"])
        sachs_evals.append(ev)

    last_sachs = sachs_evals[-1]

    framework.storage.clear()
    framework.stored_graphs.clear()

    flux_accs, flux_bal, flux_f1, flux_shd = [], [], [], []
    flux_all_true, flux_all_pred = [], []
    for task in flux_stream:
        nodes = task.variable_names
        res = framework.process_task(
            observations=task.observations,
            var_names=nodes,
            task_id=task.task_id,
            domain=task.domain,
        )
        ev = evaluate_mixed_graph(task.graph, res["graph"], nodes)
        flux_accs.append(ev["accuracy"])
        flux_bal.append(ev["balanced_accuracy"])
        flux_f1.append(ev["macro_f1"])
        flux_shd.append(ev["shd"])
        flux_all_true.extend(ev["true_relations"])
        flux_all_pred.extend(ev["pred_relations"])

    y_true_s = np.array(flux_all_true)
    y_pred_s = np.array(flux_all_pred)
    rec_synth = []
    for c in range(4):
        mask = (y_true_s == c)
        rec_synth.append(np.mean(y_pred_s[mask] == c) if np.sum(mask) > 0 else 0.0)

    return {
        "condition": condition_name,
        "sachs_acc": float(np.mean(sachs_accs)),
        "sachs_bal_acc": float(np.mean(sachs_bal)),
        "sachs_macro_f1": float(np.mean(sachs_f1)),
        "sachs_shd": float(np.mean(sachs_shd)),
        "sachs_rec_none": float(last_sachs["per_class_recall"][0]),
        "sachs_rec_fwd": float(last_sachs["per_class_recall"][1]),
        "sachs_rec_bwd": float(last_sachs["per_class_recall"][2]),
        "sachs_rec_conf": float(last_sachs["per_class_recall"][3]),
        "flux_acc": float(np.mean(flux_accs)),
        "flux_bal_acc": float(np.mean(flux_bal)),
        "flux_macro_f1": float(np.mean(flux_f1)),
        "flux_shd": float(np.mean(flux_shd)),
        "flux_rec_none": float(rec_synth[0]),
        "flux_rec_fwd": float(rec_synth[1]),
        "flux_rec_bwd": float(rec_synth[2]),
        "flux_rec_conf": float(rec_synth[3]),
    }


def run_controlled_ablations(seed: int = 42) -> List[Dict[str, Any]]:
    print("\n" + "=" * 90)
    print("CONTROLLED ABLATION SUITE: 4-CLASS RELATIONAL CAUSAL DISCOVERY")
    print("=" * 90)

    gen = SemiMarkovianTaskGenerator(seed=seed)

    print("\n[Step 1] Preparing standard reference tasks and benchmark datasets...")
    ref_tasks = [
        gen.generate_task(
            f"ref_{i}",
            num_variables=6,
            num_samples=500,
            directed_prob=0.35,
            confounded_prob=0.30,
            mechanism_type=["linear", "tanh", "polynomial", "mixed"][i % 4],
            noise_type=["laplace", "gaussian", "uniform"][i % 3],
            ensure_all_classes=True,
        )
        for i in range(25)
    ]

    sachs_loader = SachsBenchmarkLoader()
    sachs_tasks = sachs_loader.load_all_condition_tasks()
    sachs_gt = sachs_loader.get_ground_truth_graph()
    sachs_nodes = sachs_loader.PROTEINS

    flux_stream = gen.generate_multivariate_flux_stream(
        num_tasks=12,
        num_variables=5,
        samples_per_task=500,
    )

    ablation_configs = [
        ("A. Current Classifier (unweighted, argmax)", None, False, "argmax", True),
        ("B. Class-Weighted Classifier", "balanced", False, "hierarchical", True),
        ("C. Balanced Sampling", None, True, "hierarchical", True),
        ("D. Class-Weighted + Balanced Sampling", "balanced", True, "hierarchical", True),
        ("E. Matching Without Refinement", "balanced", True, "hierarchical", False),
        ("F. Matching + Refinement (Full FLUX)", "balanced", True, "hierarchical", True),
    ]

    results = []
    for name, cw, bs, dm, ref in ablation_configs:
        print(f"Running Ablation Condition: {name}...")
        res = run_ablation_condition(
            condition_name=name,
            class_weight=cw,
            balanced_sampling=bs,
            decision_mode=dm,
            refinement_enabled=ref,
            ref_tasks=ref_tasks,
            sachs_tasks=sachs_tasks,
            sachs_gt=sachs_gt,
            sachs_nodes=sachs_nodes,
            flux_stream=flux_stream,
            seed=seed,
        )
        results.append(res)

    print("\n" + "=" * 90)
    print("ABLATION RESULTS TABLE 1: SACHS (2005) REAL BIOLOGICAL BENCHMARK")
    print("=" * 90)
    print(f"{'Condition':<40} | {'Macro-F1':<9} | {'Bal Acc':<8} | {'Raw Acc':<8} | {'SHD':<5} | {'Rec(None)':<10} | {'Rec(Fwd)':<9} | {'Rec(Bwd)':<9} | {'Rec(Conf)'}")
    print("-" * 115)
    for r in results:
        print(
            f"{r['condition']:<40} | {r['sachs_macro_f1']:0.4f}    | {r['sachs_bal_acc']:0.2%}  | {r['sachs_acc']:0.2%}  | {r['sachs_shd']:0.1f}   | "
            f"{r['sachs_rec_none']:0.2%}     | {r['sachs_rec_fwd']:0.2%}   | {r['sachs_rec_bwd']:0.2%}   | {r['sachs_rec_conf']:0.2%}"
        )

    print("\n" + "=" * 90)
    print("ABLATION RESULTS TABLE 2: MULTIVARIATE FLUX SYNTHETIC STREAM")
    print("=" * 90)
    print(f"{'Condition':<40} | {'Macro-F1':<9} | {'Bal Acc':<8} | {'Raw Acc':<8} | {'SHD':<5} | {'Rec(None)':<10} | {'Rec(Fwd)':<9} | {'Rec(Bwd)':<9} | {'Rec(Conf)'}")
    print("-" * 115)
    for r in results:
        print(
            f"{r['condition']:<40} | {r['flux_macro_f1']:0.4f}    | {r['flux_bal_acc']:0.2%}  | {r['flux_acc']:0.2%}  | {r['flux_shd']:0.1f}   | "
            f"{r['flux_rec_none']:0.2%}     | {r['flux_rec_fwd']:0.2%}   | {r['flux_rec_bwd']:0.2%}   | {r['flux_rec_conf']:0.2%}"
        )
    print("=" * 90)

    return results


if __name__ == "__main__":
    run_controlled_ablations()
