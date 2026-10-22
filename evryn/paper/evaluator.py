# evryn paper evaluate
# pytest tests/test_paper_pipeline.py

import os
import time
import json
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
import matplotlib.pyplot as plt
import numpy as np

from .types import (
    ScientificDocument,
    CausalAssertion,
    CrossPageLink,
    PaperCausalGraph,
)
from .ingestion import PaperIngestion
from .segmentation import PaperSegmenter
from .normalizer import PaperEntityNormalizer
from .extractor import PaperCausalExtractor
from .cross_page_linker import CrossPageLinker
from .graph_builder import PaperGraphBuilder


@dataclass
class PaperEvaluationResult:
    doc_id: str
    baseline_a_f1: float
    baseline_b_f1: float
    system_c_f1: float
    baseline_a_cross_f1: float
    baseline_b_cross_f1: float
    system_c_cross_f1: float
    baseline_a_structural_match: float
    baseline_b_structural_match: float
    system_c_structural_match: float
    provenance_completeness: float
    runtime_seconds: float


class PaperBenchmarkEvaluator:

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.normalizer = PaperEntityNormalizer()
        self.extractor = PaperCausalExtractor(self.normalizer)
        self.linker = CrossPageLinker(min_page_distance=0)
        self.builder = PaperGraphBuilder(include_inferred_cross_page_edges=True)

    def evaluate_paper(
        self,
        doc: ScientificDocument,
        ground_truth: Dict[str, Any],
    ) -> PaperEvaluationResult:
        t0 = time.time()
        gt_direct = set(tuple(x) for x in ground_truth.get("direct_edges", []))
        gt_cross = set(tuple(x) for x in ground_truth.get("cross_page_edges", []))
        gt_all = gt_direct.union(gt_cross)

        raw_assertions = self.extractor.extract_assertions(doc)

        b_a_edges = set()
        for a in raw_assertions:
            if not a.is_negated:
                b_a_edges.add((a.cause, a.effect))

        b_b_edges = set()
        for a in raw_assertions:
            if not a.is_negated:
                b_b_edges.add((a.cause_canonical, a.effect_canonical))

        cross_links = self.linker.find_cross_page_links(raw_assertions)
        graph = self.builder.build_graph(doc.doc_id, doc.metadata.title, raw_assertions, cross_links)

        sys_c_direct = set()
        for e in graph.edges:
            if e["is_direct"]:
                sys_c_direct.add((e["source"], e["target"]))

        sys_c_cross = set((l.source_entity, l.target_entity) for l in cross_links if l.linking_mechanism == "transitive_chain")
        sys_c_all = sys_c_direct.union(sys_c_cross)

        def _calc_prf(pred_set: Set[Tuple[str, str]], gt_set: Set[Tuple[str, str]]) -> Tuple[float, float, float]:
            if not gt_set:
                return (1.0, 1.0, 1.0) if not pred_set else (0.0, 1.0, 0.0)
            if not pred_set:
                return (0.0, 0.0, 0.0)
            tp = len(pred_set.intersection(gt_set))
            prec = tp / len(pred_set)
            rec = tp / len(gt_set)
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            return prec, rec, f1

        def _calc_structural_match(pred_set: Set[Tuple[str, str]], gt_set: Set[Tuple[str, str]]) -> float:
            if not gt_set and not pred_set:
                return 1.0
            union_len = len(pred_set.union(gt_set))
            if union_len == 0:
                return 1.0
            return len(pred_set.intersection(gt_set)) / union_len

        b_a_cross: Set[Tuple[str, str]] = set()
        b_b_cross: Set[Tuple[str, str]] = set()

        _, _, ba_f1 = _calc_prf(b_a_edges, gt_direct)
        _, _, bb_f1 = _calc_prf(b_b_edges, gt_direct)
        _, _, sc_f1 = _calc_prf(sys_c_direct, gt_direct)

        _, _, ba_cross_f1 = _calc_prf(b_a_cross, gt_cross)
        _, _, bb_cross_f1 = _calc_prf(b_b_cross, gt_cross)
        _, _, sc_cross_f1 = _calc_prf(sys_c_cross, gt_cross)

        ba_sm = _calc_structural_match(b_a_edges, gt_all)
        bb_sm = _calc_structural_match(b_b_edges, gt_all)
        sc_sm = _calc_structural_match(sys_c_all, gt_all)

        grounded_edges = [e for e in graph.edges if len(e["pages"]) > 0]
        prov_comp = len(grounded_edges) / len(graph.edges) if graph.edges else 1.0
        elapsed = time.time() - t0

        return PaperEvaluationResult(
            doc_id=doc.doc_id,
            baseline_a_f1=round(ba_f1, 4),
            baseline_b_f1=round(bb_f1, 4),
            system_c_f1=round(sc_f1, 4),
            baseline_a_cross_f1=round(ba_cross_f1, 4),
            baseline_b_cross_f1=round(bb_cross_f1, 4),
            system_c_cross_f1=round(sc_cross_f1, 4),
            baseline_a_structural_match=round(ba_sm, 4),
            baseline_b_structural_match=round(bb_sm, 4),
            system_c_structural_match=round(sc_sm, 4),
            provenance_completeness=round(prov_comp, 4),
            runtime_seconds=round(elapsed, 4),
        )

    def run_suite(
        self,
        docs: List[ScientificDocument],
        ground_truths: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        results: List[PaperEvaluationResult] = []
        for doc, gt in zip(docs, ground_truths):
            res = self.evaluate_paper(doc, gt)
            results.append(res)

        ba_f1_avg = float(np.mean([r.baseline_a_f1 for r in results]))
        bb_f1_avg = float(np.mean([r.baseline_b_f1 for r in results]))
        sc_f1_avg = float(np.mean([r.system_c_f1 for r in results]))

        ba_cross_avg = float(np.mean([r.baseline_a_cross_f1 for r in results]))
        bb_cross_avg = float(np.mean([r.baseline_b_cross_f1 for r in results]))
        sc_cross_avg = float(np.mean([r.system_c_cross_f1 for r in results]))

        ba_sm_avg = float(np.mean([r.baseline_a_structural_match for r in results]))
        bb_sm_avg = float(np.mean([r.baseline_b_structural_match for r in results]))
        sc_sm_avg = float(np.mean([r.system_c_structural_match for r in results]))

        prov_avg = float(np.mean([r.provenance_completeness for r in results]))
        total_time = float(np.sum([r.runtime_seconds for r in results]))

        summary = {
            "total_papers": len(docs),
            "baseline_a": {
                "direct_f1": round(ba_f1_avg, 4),
                "cross_page_f1": round(ba_cross_avg, 4),
                "structural_match": round(ba_sm_avg, 4),
            },
            "baseline_b": {
                "direct_f1": round(bb_f1_avg, 4),
                "cross_page_f1": round(bb_cross_avg, 4),
                "structural_match": round(bb_sm_avg, 4),
            },
            "system_c_evryn": {
                "direct_f1": round(sc_f1_avg, 4),
                "cross_page_f1": round(sc_cross_avg, 4),
                "structural_match": round(sc_sm_avg, 4),
                "provenance_completeness": round(prov_avg, 4),
            },
            "total_runtime_seconds": round(total_time, 4),
            "per_paper_results": [r.__dict__ for r in results],
        }

        json_out = os.path.join(self.output_dir, "multipage_benchmark_results.json")
        csv_out = os.path.join(self.output_dir, "multipage_benchmark_results.csv")
        fig_out = os.path.join(self.output_dir, "multipage_benchmark_comparison.png")

        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(csv_out, "w", encoding="utf-8") as f:
            f.write("doc_id,baseline_a_f1,baseline_b_f1,system_c_f1,baseline_a_cross_f1,baseline_b_cross_f1,system_c_cross_f1,baseline_a_structural_match,baseline_b_structural_match,system_c_structural_match,provenance_completeness,runtime_seconds\n")
            for r in results:
                f.write(f"{r.doc_id},{r.baseline_a_f1},{r.baseline_b_f1},{r.system_c_f1},{r.baseline_a_cross_f1},{r.baseline_b_cross_f1},{r.system_c_cross_f1},{r.baseline_a_structural_match},{r.baseline_b_structural_match},{r.system_c_structural_match},{r.provenance_completeness},{r.runtime_seconds}\n")

        self._plot_suite_comparison(summary, fig_out)

        return summary

    def _plot_suite_comparison(self, summary: Dict[str, Any], output_path: str):
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), dpi=300, layout="constrained")

        categories = ["Baseline A\n(Sentence Only)", "Baseline B\n(+ Normalizer)", "System C\n(EVRYN Multi-Page)"]
        colors = ["#94a3b8", "#38bdf8", "#059669"]

        direct_vals = [
            summary["baseline_a"]["direct_f1"],
            summary["baseline_b"]["direct_f1"],
            summary["system_c_evryn"]["direct_f1"],
        ]
        bars1 = axes[0].bar(categories, direct_vals, color=colors, width=0.55, edgecolor="#0f172a", linewidth=1.2)
        axes[0].set_title("Direct Sentence Causal F1", fontsize=11, fontweight="bold", pad=10)
        axes[0].set_ylim(0, 1.15)
        axes[0].grid(axis="y", linestyle="--", alpha=0.5)
        for b in bars1:
            h = b.get_height()
            axes[0].annotate(f"{h:.3f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        cross_vals = [
            summary["baseline_a"]["cross_page_f1"],
            summary["baseline_b"]["cross_page_f1"],
            summary["system_c_evryn"]["cross_page_f1"],
        ]
        bars2 = axes[1].bar(categories, cross_vals, color=colors, width=0.55, edgecolor="#0f172a", linewidth=1.2)
        axes[1].set_title("Cross-Page Transitive F1", fontsize=11, fontweight="bold", pad=10)
        axes[1].set_ylim(0, 1.15)
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)
        for b in bars2:
            h = b.get_height()
            axes[1].annotate(f"{h:.3f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        sm_vals = [
            summary["baseline_a"]["structural_match"],
            summary["baseline_b"]["structural_match"],
            summary["system_c_evryn"]["structural_match"],
        ]
        bars3 = axes[2].bar(categories, sm_vals, color=colors, width=0.55, edgecolor="#0f172a", linewidth=1.2)
        axes[2].set_title("Complete Graph Structural Match", fontsize=11, fontweight="bold", pad=10)
        axes[2].set_ylim(0, 1.15)
        axes[2].grid(axis="y", linestyle="--", alpha=0.5)
        for b in bars3:
            h = b.get_height()
            axes[2].annotate(f"{h:.3f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        fig.suptitle(f"EVRYN Multi-Page Causal Discovery Evaluation (N={summary['total_papers']} Real Scientific Papers)", fontsize=13, fontweight="bold", color="#0f172a")
        plt.savefig(output_path, dpi=300)
        plt.close(fig)
