# evryn higher-order
# evryn -s higher-order

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter

from .types import HigherOrderCandidate, HigherOrderCategory, HigherOrderBenchmarkResult
from .baselines import HigherOrderBaselineSuite


class HigherOrderBenchmarkRunner:

    def __init__(self):
        self.baselines = HigherOrderBaselineSuite()

    def evaluate_predictions(
        self,
        y_true: List[HigherOrderCategory],
        y_pred: List[HigherOrderCategory],
        baseline_name: str,
    ) -> HigherOrderBenchmarkResult:
        n = len(y_true)

        def _prf(target_cat: HigherOrderCategory) -> Tuple[float, float, float]:
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == target_cat and yp == target_cat)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != target_cat and yp == target_cat)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == target_cat and yp != target_cat)

            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            return p, r, f1

        p_pair, r_pair, f1_pair = _prf(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
        p_joint, r_joint, f1_joint = _prf(HigherOrderCategory.JOINT_CAUSE)
        p_int, r_int, f1_int = _prf(HigherOrderCategory.HIGHER_ORDER_INTERACTION)

        non_joint_true = sum(1 for yt in y_true if yt not in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        false_joint_pred = sum(
            1 for yt, yp in zip(y_true, y_pred)
            if yt not in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            and yp in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION)
        )
        false_joint_rate = false_joint_pred / non_joint_true if non_joint_true > 0 else 0.0

        all_cats = list(HigherOrderCategory)
        cat_f1s = [_prf(c)[2] for c in all_cats]
        macro_f1 = float(np.mean(cat_f1s))

        exact_matches = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        exact_match_rate = exact_matches / n if n > 0 else 0.0

        return HigherOrderBenchmarkResult(
            baseline_name=baseline_name,
            pairwise_decomposition_f1=float(f1_pair),
            joint_cause_precision=float(p_joint),
            joint_cause_recall=float(r_joint),
            joint_cause_f1=float(f1_joint),
            higher_order_interaction_f1=float(f1_int),
            macro_f1=float(macro_f1),
            false_joint_cause_rate=float(false_joint_rate),
            exact_structural_match=float(exact_match_rate),
        )

    def run_all_baselines(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderBenchmarkResult]:
        y_true = [c.category for c in candidates]

        preds_a = self.baselines.predict_baseline_a_pairwise(candidates)
        preds_b = self.baselines.predict_baseline_b_rule_based(candidates)
        preds_c = self.baselines.predict_baseline_c_learned_nlp(candidates)
        preds_d = self.baselines.predict_method_d_flux_evidence(candidates)
        preds_e = self.baselines.predict_method_e_full_evryn(candidates)

        return [
            self.evaluate_predictions(y_true, preds_a, "A. Pairwise-Only NLP"),
            self.evaluate_predictions(y_true, preds_b, "B. NLP + Rule Conjunction"),
            self.evaluate_predictions(y_true, preds_c, "C. Learned Higher-Order NLP"),
            self.evaluate_predictions(y_true, preds_d, "D. NLP + FLUX Evidence"),
            self.evaluate_predictions(y_true, preds_e, "E. Full EVRYN Higher-Order"),
        ]

    def plot_benchmark_figures(
        self,
        candidates: List[HigherOrderCandidate],
        results: List[HigherOrderBenchmarkResult],
        output_dir: str = "outputs",
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        paths = {}

        p_dist = os.path.join(output_dir, "ho_candidate_distribution.png")
        if os.path.exists(p_dist):
            try:
                os.remove(p_dist)
            except OSError:
                pass

        semeval_cands = [c for c in candidates if c.source_dataset == "SemEval-2010_Task8"]
        counts = Counter(c.category.value for c in semeval_cands)

        labels = [
            "PAIRWISE_DECOMP",
            "JOINT_CAUSE",
            "HO_INTERACTION",
            "LING_COORD",
            "TEMPORAL_REL",
            "CONFOUNDED",
            "INSUFFICIENT",
        ]
        vals = [
            counts.get(HigherOrderCategory.PAIRWISE_DECOMPOSABLE.value, 0),
            counts.get(HigherOrderCategory.JOINT_CAUSE.value, 0),
            counts.get(HigherOrderCategory.HIGHER_ORDER_INTERACTION.value, 0),
            counts.get(HigherOrderCategory.LINGUISTIC_COORDINATION.value, 0),
            counts.get(HigherOrderCategory.TEMPORAL_RELATION.value, 0),
            counts.get(HigherOrderCategory.CONFOUNDED.value, 0),
            counts.get(HigherOrderCategory.INSUFFICIENT_EVIDENCE.value, 0),
        ]
        import seaborn as sns
        sns.set_theme(style="whitegrid", font="sans-serif")
        palette_dist = sns.color_palette(["#0284c7", "#7c3aed", "#c026d3", "#64748b", "#d97706", "#dc2626", "#94a3b8"])

        fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=240)
        bars = ax.bar(labels, vals, color=palette_dist, width=0.55, edgecolor="#0f172a", linewidth=1.1, zorder=3)
        ax.set_ylabel("Candidate Count", fontweight="bold", fontsize=10.5)
        ax.set_title("Audited Distribution of 208 Joint-Cause Candidates", fontweight="bold", fontsize=11.5, pad=12)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=9, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        sns.despine(ax=ax, top=True, right=True)

        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                str(val),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color="#0f172a",
            )
        plt.tight_layout()
        plt.savefig(p_dist, dpi=240)
        plt.close()
        paths["distribution"] = p_dist

        p_comp = os.path.join(output_dir, "ho_nlp_benchmark_comparison.png")
        if os.path.exists(p_comp):
            try:
                os.remove(p_comp)
            except OSError:
                pass

        fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=240)

        names = [r.baseline_name.split(". ")[-1] for r in results]
        x = np.arange(len(names))
        w = 0.18

        j_f1 = [r.joint_cause_f1 for r in results]
        int_f1 = [r.higher_order_interaction_f1 for r in results]
        macro_f1 = [r.macro_f1 for r in results]
        f_rate = [r.false_joint_cause_rate for r in results]

        ax.bar(x - 1.5 * w, j_f1, width=w, label="Joint-Cause F1", color="#0284c7", edgecolor="#0f172a", linewidth=1.1, zorder=3)
        ax.bar(x - 0.5 * w, int_f1, width=w, label="Interaction F1", color="#7c3aed", edgecolor="#0f172a", linewidth=1.1, zorder=3)
        ax.bar(x + 0.5 * w, macro_f1, width=w, label="Macro-F1", color="#c026d3", edgecolor="#0f172a", linewidth=1.1, zorder=3)
        ax.bar(x + 1.5 * w, f_rate, width=w, label="False Joint Rate (Lower=Better)", color="#ef4444", edgecolor="#0f172a", linewidth=1.1, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=18, ha="right", fontsize=9, fontweight="bold")
        ax.set_ylabel("Score / Rate", fontweight="bold", fontsize=10.5)
        ax.set_title("Higher-Order Scientific NLP Benchmark: Linguistic vs FLUX Integration", fontweight="bold", fontsize=11.5, pad=12)
        ax.set_ylim(0, 1.05)
        ax.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8.5)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        sns.despine(ax=ax, top=True, right=True)

        plt.tight_layout()
        plt.savefig(p_comp, dpi=240)
        plt.close()
        paths["comparison"] = p_comp

        return paths
