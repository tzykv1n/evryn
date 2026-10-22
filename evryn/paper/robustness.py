# evryn benchmark --suite multi-page
# pytest tests/test_paper_pipeline.py

import os
import copy
import json
import random
from typing import List, Dict, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

from .types import ScientificDocument
from .evaluator import PaperBenchmarkEvaluator


class PaperRobustnessExperiments:

    def __init__(self, evaluator: PaperBenchmarkEvaluator, output_dir: str = "outputs", seed: int = 42):
        self.evaluator = evaluator
        self.output_dir = output_dir
        self.seed = seed
        os.makedirs(output_dir, exist_ok=True)

    def run_dropout_ablation(
        self,
        docs: List[ScientificDocument],
        ground_truths: List[Dict[str, Any]],
        dropout_rates: List[float] = [0.0, 0.1, 0.2, 0.3],
    ) -> Dict[str, Any]:
        random.seed(self.seed)
        results: Dict[str, Any] = {}

        for rate in dropout_rates:
            ablated_docs: List[ScientificDocument] = []
            for doc in docs:
                new_doc = copy.deepcopy(doc)
                if rate > 0.0 and len(new_doc.sentences) > 2:
                    keep_count = max(2, int(len(new_doc.sentences) * (1.0 - rate)))
                    indices = sorted(random.sample(range(len(new_doc.sentences)), keep_count))
                    new_doc.sentences = [new_doc.sentences[i] for i in indices]
                ablated_docs.append(new_doc)

            summary = self.evaluator.run_suite(ablated_docs, ground_truths)
            results[f"{int(rate * 100)}%"] = {
                "rate": rate,
                "direct_f1": summary["system_c_evryn"]["direct_f1"],
                "cross_page_f1": summary["system_c_evryn"]["cross_page_f1"],
                "structural_match": summary["system_c_evryn"]["structural_match"],
            }

        return results

    def run_noise_experiment(
        self,
        docs: List[ScientificDocument],
        ground_truths: List[Dict[str, Any]],
        noise_rates: List[float] = [0.0, 0.15, 0.30],
    ) -> Dict[str, Any]:
        random.seed(self.seed)
        results: Dict[str, Any] = {}
        distractors = ["Albumin", "Glucose", "Hemoglobin", "Saline", "Creatinine", "Collagen-IV"]

        for rate in noise_rates:
            noisy_docs: List[ScientificDocument] = []
            for doc in docs:
                new_doc = copy.deepcopy(doc)
                if rate > 0.0:
                    for sent in new_doc.sentences:
                        if random.random() < rate:
                            d1, d2 = random.sample(distractors, 2)
                            sent.text += f" Treatment with {d1} had no observable effect on {d2} levels."
                noisy_docs.append(new_doc)

            summary = self.evaluator.run_suite(noisy_docs, ground_truths)
            results[f"{int(rate * 100)}%"] = {
                "rate": rate,
                "direct_f1": summary["system_c_evryn"]["direct_f1"],
                "cross_page_f1": summary["system_c_evryn"]["cross_page_f1"],
                "structural_match": summary["system_c_evryn"]["structural_match"],
            }

        return results

    def run_all_robustness(
        self,
        docs: List[ScientificDocument],
        ground_truths: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        dropout_res = self.run_dropout_ablation(docs, ground_truths)
        noise_res = self.run_noise_experiment(docs, ground_truths)

        all_robustness = {
            "sentence_dropout_ablation": dropout_res,
            "distractor_noise_experiment": noise_res,
        }

        json_path = os.path.join(self.output_dir, "multipage_robustness_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_robustness, f, indent=2)

        fig_path = os.path.join(self.output_dir, "multipage_robustness_curves.png")
        self._plot_robustness_curves(dropout_res, noise_res, fig_path)

        all_robustness["artifacts"] = {
            "json_path": json_path,
            "figure_path": fig_path,
        }
        return all_robustness

    def _plot_robustness_curves(
        self,
        dropout_res: Dict[str, Any],
        noise_res: Dict[str, Any],
        output_png: str,
    ):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), dpi=300, layout="constrained")

        d_rates = [v["rate"] * 100 for v in dropout_res.values()]
        d_direct = [v["direct_f1"] for v in dropout_res.values()]
        d_cross = [v["cross_page_f1"] for v in dropout_res.values()]
        d_sm = [v["structural_match"] for v in dropout_res.values()]

        axes[0].plot(d_rates, d_direct, marker="o", color="#059669", lw=2, label="Direct F1")
        axes[0].plot(d_rates, d_cross, marker="s", color="#8b5cf6", lw=2, label="Cross-Page F1")
        axes[0].plot(d_rates, d_sm, marker="^", color="#0284c7", lw=2, linestyle="--", label="Structural Match")
        axes[0].set_title("Missing Sentence Dropout Ablation", fontsize=11, fontweight="bold", pad=10)
        axes[0].set_xlabel("Sentence Dropout Rate (%)", fontsize=10, fontweight="bold")
        axes[0].set_ylabel("Metric Score", fontsize=10, fontweight="bold")
        axes[0].set_ylim(0, 1.05)
        axes[0].grid(True, linestyle="--", alpha=0.5)
        axes[0].legend(loc="lower left", fontsize=9)

        n_rates = [v["rate"] * 100 for v in noise_res.values()]
        n_direct = [v["direct_f1"] for v in noise_res.values()]
        n_cross = [v["cross_page_f1"] for v in noise_res.values()]
        n_sm = [v["structural_match"] for v in noise_res.values()]

        axes[1].plot(n_rates, n_direct, marker="o", color="#059669", lw=2, label="Direct F1")
        axes[1].plot(n_rates, n_cross, marker="s", color="#8b5cf6", lw=2, label="Cross-Page F1")
        axes[1].plot(n_rates, n_sm, marker="^", color="#0284c7", lw=2, linestyle="--", label="Structural Match")
        axes[1].set_title("Distractor & Negation Noise Injection", fontsize=11, fontweight="bold", pad=10)
        axes[1].set_xlabel("Distractor Injection Rate (%)", fontsize=10, fontweight="bold")
        axes[1].set_ylabel("Metric Score", fontsize=10, fontweight="bold")
        axes[1].set_ylim(0, 1.05)
        axes[1].grid(True, linestyle="--", alpha=0.5)
        axes[1].legend(loc="lower left", fontsize=9)

        fig.suptitle("EVRYN Multi-Page Causal Discovery Robustness Profiles", fontsize=13, fontweight="bold", color="#0f172a")
        plt.savefig(output_png, dpi=300)
        plt.close(fig)
