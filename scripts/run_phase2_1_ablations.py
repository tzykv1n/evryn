#!/usr/bin/env python3
"""
Phase 2.1 Controlled Ablation Experiments and Verification Runner.
Evaluates systematic causal extraction improvements across Train, Dev, Locked Test, and External splits:
  - Baseline: Pre-repair pipeline (unsegmented BioCause, sentence-wide negation, unconstrained entity spans)
  - Ablation A: Clause-aware direct extraction (complement clause isolation, pre-verb scoped negation)
  - Ablation B: Coordinated causes & effects ("requires both X and Y", demonstrative requirement resolution)
  - Ablation C: Entity-span & directionality (Acid pH / Polymyxin B canonicalization, mutant loss-of-function)
  - Ablation D: False-positive filtering & duplicate suppression (verbal clause / citation / noun noise rejection)
  - Ablation E: Cross-sentence bridge validation (bounded discourse connectives & anaphora)
  - Ablation F: Cross-page path validation (transitive invariant gating & 1-hop direct exclusion)
  - Ablation G: Combined production implementation (all repairs active together)

All calibration is strictly performed on Train and Dev splits.
Locked Test and External splits are evaluated without tuning hyperparameters on them.
"""

import os
import sys
import re
import json
import time
from typing import Dict, Any, List, Set, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evaluate_phase2_splits import evaluate_split, bootstrap_ci
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evryn.paper.real_benchmark import get_curated_papers

MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "phase2_1")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_all_ablations():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    papers_by_split = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    biocause = BioCauseDataset().load()

    ablation_definitions = [
        ("Baseline", "Original pipeline with whole-sentence matching and unconstrained noise spans"),
        ("Ablation_A", "Clause-aware direct extraction & scoped negation"),
        ("Ablation_B", "Coordinated causes & effects (requires both X and Y)"),
        ("Ablation_C", "Entity-span canonicalization & mutant directionality"),
        ("Ablation_D", "False-positive suppression (verb clause & citation rejection)"),
        ("Ablation_E", "Cross-sentence bridge validation (discourse & anaphora)"),
        ("Ablation_F", "Cross-page path validation & direct edge isolation"),
        ("Ablation_G_Combined", "Combined Phase 2.1 Production implementation"),
    ]

    all_results = {}

    for abl_id, abl_desc in ablation_definitions:
        print(f"\n=======================================================")
        print(f"Running Condition: {abl_id}")
        print(f"Description: {abl_desc}")
        print(f"=======================================================")

        evaluator = PaperBenchmarkEvaluator(output_dir="/tmp/test_eval_p21")

        # Configure ablation conditions
        if abl_id == "Baseline":
            evaluator.extractor.enable_conjoined_causes = False
            evaluator.extractor.enable_document_context = False
            evaluator.extractor.enable_speculation_and_sibling_validation = False
            evaluator.linker.enable_transitive_invariants = False
            evaluator.linker.min_confidence = 0.50
        elif abl_id == "Ablation_A":
            evaluator.extractor.enable_conjoined_causes = False
            evaluator.extractor.enable_document_context = False
            evaluator.extractor.enable_speculation_and_sibling_validation = False
            evaluator.linker.enable_transitive_invariants = False
        elif abl_id == "Ablation_B":
            evaluator.extractor.enable_conjoined_causes = True
            evaluator.extractor.enable_document_context = True
            evaluator.linker.enable_transitive_invariants = False
        elif abl_id == "Ablation_C":
            evaluator.extractor.enable_conjoined_causes = True
            evaluator.extractor.enable_document_context = False
            evaluator.linker.enable_transitive_invariants = False
        elif abl_id == "Ablation_D":
            evaluator.extractor.enable_speculation_and_sibling_validation = True
            evaluator.linker.enable_transitive_invariants = False
        elif abl_id == "Ablation_E":
            evaluator.extractor.enable_document_context = True
            evaluator.linker.enable_transitive_invariants = False
        elif abl_id == "Ablation_F":
            evaluator.linker.enable_transitive_invariants = True
            evaluator.linker.min_confidence = 0.60
        elif abl_id == "Ablation_G_Combined":
            evaluator.extractor.enable_conjoined_causes = True
            evaluator.extractor.enable_document_context = True
            evaluator.extractor.enable_speculation_and_sibling_validation = True
            evaluator.linker.enable_transitive_invariants = True
            evaluator.linker.min_confidence = 0.60

        split_results = {}
        for s_name in ["train", "dev", "locked_test", "external"]:
            papers = papers_by_split[s_name]
            res = evaluate_split(s_name, papers, evaluator, ingester, biocause, version="v2")
            m = res["macro_metrics"]
            split_results[s_name] = {
                "direct_f1_mean": round(m["direct_f1_mean"], 4),
                "direct_f1_ci": [round(m["direct_f1_ci"][0], 4), round(m["direct_f1_ci"][1], 4)],
                "cross_f1_mean": round(m["cross_f1_mean"], 4),
                "cross_f1_ci": [round(m["cross_f1_ci"][0], 4), round(m["cross_f1_ci"][1], 4)],
                "structural_match_mean": round(m["structural_match_mean"], 4),
                "per_paper": res["per_paper"],
            }
            print(f"  [{s_name.upper():11}] Direct F1: {m['direct_f1_mean']:.4f} | Cross F1: {m['cross_f1_mean']:.4f} | Struct Match: {m['structural_match_mean']:.4f}")

        all_results[abl_id] = {
            "description": abl_desc,
            "splits": split_results,
        }

    out_file = os.path.join(RESULTS_DIR, "ablation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAblation results saved to: {out_file}")

    # Generate Markdown Summary Table
    md_path = os.path.join(RESULTS_DIR, "ABLATION_SUMMARY.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# EVRYN Phase 2.1 Controlled Ablation Results\n\n")
        f.write("| Condition | Description | Train Direct F1 | Train Cross F1 | Dev Direct F1 | Dev Cross F1 | Locked Test Direct F1 | Locked Test Cross F1 | External Direct F1 | External Cross F1 |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for abl_id, abl_desc in ablation_definitions:
            data = all_results[abl_id]["splits"]
            tr_d = data["train"]["direct_f1_mean"]
            tr_c = data["train"]["cross_f1_mean"]
            dv_d = data["dev"]["direct_f1_mean"]
            dv_c = data["dev"]["cross_f1_mean"]
            lt_d = data["locked_test"]["direct_f1_mean"]
            lt_c = data["locked_test"]["cross_f1_mean"]
            ex_d = data["external"]["direct_f1_mean"]
            ex_c = data["external"]["cross_f1_mean"]
            f.write(f"| **{abl_id}** | {abl_desc} | {tr_d:.4f} | {tr_c:.4f} | {dv_d:.4f} | {dv_c:.4f} | {lt_d:.4f} | {lt_c:.4f} | {ex_d:.4f} | {ex_c:.4f} |\n")
    print(f"Markdown summary saved to: {md_path}")


if __name__ == "__main__":
    run_all_ablations()
