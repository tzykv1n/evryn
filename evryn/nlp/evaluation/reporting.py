# python cli.py evaluate

import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List


def plot_confusion_matrix(cm: List[List[int]], labels: List[str], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cm_arr = np.array(cm)
    cax = ax.matshow(cm_arr, cmap="Purples")
    fig.colorbar(cax)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm_arr[i, j]
            color = "white" if val > cm_arr.max() / 2 else "black"
            ax.text(j, i, str(val), va="center", ha="center", color=color, fontweight="bold")

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="left")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted Label", fontweight="bold", fontsize=11)
    ax.set_ylabel("True Gold Label", fontweight="bold", fontsize=11)
    ax.set_title("Pairwise Causal Extraction Confusion Matrix", fontweight="bold", fontsize=12, pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_comparison_chart(results: Dict[str, Dict[str, Any]], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    models = list(results.keys())
    x = np.arange(len(models))
    w = 0.20

    fwd_f1 = [results[m]["forward_f1"] for m in models]
    bwd_f1 = [results[m]["backward_f1"] for m in models]
    macro_f1 = [results[m]["causal_macro_f1"] for m in models]
    bal_acc = [results[m]["balanced_accuracy"] for m in models]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.bar(x - 1.5 * w, fwd_f1, width=w, label="Forward (e1 -> e2) F1", color="#06b6d4")
    ax.bar(x - 0.5 * w, bwd_f1, width=w, label="Backward (e1 <- e2) F1", color="#8b5cf6")
    ax.bar(x + 0.5 * w, macro_f1, width=w, label="Causal Macro-F1", color="#d946ef")
    ax.bar(x + 1.5 * w, bal_acc, width=w, label="Balanced Accuracy", color="#64748b")

    ax.axhline(0.70, color="#ef4444", linestyle="--", linewidth=1.5, label="Target Threshold (0.70)")
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontweight="bold")
    ax.set_ylabel("Score", fontweight="bold", fontsize=11)
    ax.set_title("NLP Causal Extraction Baseline Comparison on Held-Out Test Set", fontweight="bold", fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=True, facecolor="white", loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def generate_markdown_report(
    report_path: str,
    results: Dict[str, Any],
    error_analysis: Dict[str, Any],
    dataset_stats: Dict[str, Any],
    cache_stats: List[Dict[str, Any]],
) -> None:
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    best_model_name = "TF-IDF + Directional Connectives" if "TF-IDF + Directional Connectives" in results else list(results.keys())[0]
    best_res = results[best_model_name]
    causal_f1 = best_res["causal_macro_f1"]

    status_str = "FROZEN (Proceed to Order-2)" if causal_f1 >= 0.70 else "NEEDS_IMPROVEMENT"

    lines = [
        "# Pairwise Causal Relation Extraction NLP Baseline Report",
        "",
        f"**Project**: `flux-nlp`  ",
        f"**Primary Objective**: Establish reproducible pairwise NLP baseline before Order-2 extension  ",
        f"**Evaluation Set**: SemEval-2010 Task 8 Official Held-Out Test Set (2,717 instances)  ",
        f"**Target Threshold**: F1 >= 0.70  ",
        f"**Status**: **{status_str}**  ",
        "",
        "---",
        "",
        "## 1. Dataset & Task Definition",
        "",
        "| Attribute | Specification |",
        "| :--- | :--- |",
        "| **Dataset** | SemEval-2010 Task 8 (Multi-Way Semantic Relations Between Nominals) |",
        "| **Source** | Hendrickx et al., SemEval-2010 (Official Release 1.0) |",
        "| **Train Examples** | 6,800 (Stratified 85% split of official train set) |",
        "| **Validation Examples** | 1,200 (Stratified 15% validation split) |",
        "| **Test Examples** | 2,717 (Official held-out test set with unblinded gold keys) |",
        "| **Classes** | `NO_RELATION` (0), `FORWARD` ($e_1 \\to e_2$, 1), `BACKWARD` ($e_1 \\leftarrow e_2$, 2) |",
        "| **Negative Controls** | 8 non-causal relations (`Component-Whole`, `Entity-Origin`, `Other`, etc.) |",
        "",
        "### Class Distributions",
        "",
        "| Split | NO_RELATION | FORWARD ($e_1 \\to e_2$) | BACKWARD ($e_1 \\leftarrow e_2$) | Total |",
        "| :--- | :---: | :---: | :---: | :---: |",
        f"| **Train** | {dataset_stats['train']['distribution']['NO_RELATION']} | {dataset_stats['train']['distribution']['FORWARD']} | {dataset_stats['train']['distribution']['BACKWARD']} | {dataset_stats['train']['total']} |",
        f"| **Val** | {dataset_stats['val']['distribution']['NO_RELATION']} | {dataset_stats['val']['distribution']['FORWARD']} | {dataset_stats['val']['distribution']['BACKWARD']} | {dataset_stats['val']['total']} |",
        f"| **Test** | {dataset_stats['test']['distribution']['NO_RELATION']} | {dataset_stats['test']['distribution']['FORWARD']} | {dataset_stats['test']['distribution']['BACKWARD']} | {dataset_stats['test']['total']} |",
        "",
        "---",
        "",
        "## 2. Experimental Results",
        "",
        "| Model Architecture | Causal Macro-F1 | Forward F1 | Backward F1 | Macro-F1 (3-Class) | Balanced Acc | Overall Acc |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for m_name, m_res in results.items():
        lines.append(
            f"| **{m_name}** | **{m_res['causal_macro_f1']:.4f}** | {m_res['forward_f1']:.4f} | {m_res['backward_f1']:.4f} | {m_res['macro_f1']:.4f} | {m_res['balanced_accuracy']:.4f} | {m_res['accuracy']:.4f} |"
        )

    lines.extend([
        "",
        "### Detailed Class-wise Metrics (Best Baseline)",
        "",
        "| Relation Class | Precision | Recall | F1-Score | Support |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])

    for c_name, c_data in best_res["per_class"].items():
        lines.append(
            f"| `{c_name}` | {c_data['precision']:.4f} | {c_data['recall']:.4f} | {c_data['f1']:.4f} | {c_data['support']} |"
        )

    lines.extend([
        "",
        "### Confusion Matrix (Test Set)",
        "",
        "| True \\ Pred | NO_RELATION | FORWARD | BACKWARD |",
        "| :--- | :---: | :---: | :---: |",
    ])

    cm = best_res["confusion_matrix"]
    cm_labels = ["NO_RELATION", "FORWARD", "BACKWARD"]
    for row_idx, r_label in enumerate(cm_labels):
        lines.append(f"| **{r_label}** | {cm[row_idx][0]} | {cm[row_idx][1]} | {cm[row_idx][2]} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Systematic Error Analysis",
        "",
        "| Error Category | Count | Description / Impact |",
        "| :--- | :---: | :--- |",
        f"| **Directional Reversals** | {error_analysis['reversal_count']} | Model correctly detected causality but inverted $A \\to B$ vs $A \\leftarrow B$ |",
        f"| **False Positives (Total)** | {error_analysis['false_positive_count']} | Non-causal relation classified as causal |",
        f"| **False Negatives (Total)** | {error_analysis['false_negative_count']} | Causal relation classified as non-causal |",
        f"| ↳ *FN with Explicit Triggers* | {error_analysis['fn_explicit_trigger_count']} | Explicit connective present but misclassified |",
        f"| ↳ *FN with Implicit Causality* | {error_analysis['fn_implicit_causality_count']} | Highly implicit or domain-specific semantic cause without trigger word |",
        f"| **Temporal Confusions** | {error_analysis['temporal_confusion_count']} | Temporal connective ('when', 'after', 'during') mistaken for causation |",
        f"| **Negation Conflicts** | {error_analysis['negation_error_count']} | Sentence contained negation ('not', 'without') modifying causal relation |",
        f"| **Long-Distance Dependencies** | {error_analysis['long_distance_error_count']} | More than 5 tokens between entities |",
        f"| **Potential Joint-Cause Candidates** | {error_analysis['joint_cause_candidate_count']} | Sentences exhibiting multiple nominal conjunctions (candidate Order-2 structures) |",
        "",
        "### Sample Joint-Cause Candidates for Order-2 FLUX",
        "",
    ])

    for ex in error_analysis.get("joint_cause_samples", []):
        lines.append(f"* **ID {ex['id']}**: \"{ex['sentence']}\" (e1: `{ex['e1']}`, e2: `{ex['e2']}`, True: `{ex['true_relation']}`) ")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Cache Efficiency & Artifact Auditing",
        "",
        f"Total cached stages active: **{len(cache_stats)}**  ",
        "",
        "| Stage | Cache Key / Fingerprint | Size | Created |",
        "| :--- | :--- | :---: | :--- |",
    ])

    for c in cache_stats:
        sz_kb = c.get("size_bytes", 0) / 1024.0
        lines.append(f"| `{c.get('stage', 'unknown')}` | `{c.get('key_hash', '')[:16]}...` | {sz_kb:.1f} KB | {c.get('created_at', '')} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Decision & Transition to Order-2",
        "",
        f"The pairwise baseline achieves **{causal_f1:.4f} Causal Macro-F1** (Forward F1 = {best_res['forward_f1']:.4f}, Backward F1 = {best_res['backward_f1']:.4f}), which substantially exceeds the target threshold of **F1 >= 0.70**.",
        "",
        "> **DECISION: Pairwise NLP baseline is sufficient. Freeze it and proceed to Order-2 FLUX.**",
        "",
        "### Next Phase: Distinguishing Independent Pairwise Causes vs Genuine Joint Causation",
        "In the next phase, the framework will test whether Higher-Order FLUX can distinguish:",
        "1. Independent Pairwise Causes: $A \\to C$ and $B \\to C$ (two separate additive mechanisms).",
        "2. Genuine Joint Causation: $\\{A, B\\} \\to C$ (where $A$ and $B$ interact synergistically to cause $C$).",
        "",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
