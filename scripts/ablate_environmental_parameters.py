#!/usr/bin/env python3
"""
Phase 1.4 Ablation Study: Environmental Parameter-Change Extraction
Compares four configurations across Train and Dev splits:
1. Baseline Phase 1.3 (environmental grammar disabled: enable_env_grammar=False)
2. Temperature-only (enable_env_grammar=True, env_variables={"temperature"})
3. pH-only (enable_env_grammar=True, env_variables={"ph"})
4. Combined Phase 1.4 (enable_env_grammar=True, env_variables=None)
"""

import os
import sys
import json
from typing import Dict, Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import CURATED_REAL_PAPERS
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evaluate_phase2_splits import evaluate_split


def run_ablation():
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    train_papers = [p for p in manifest["papers"] if p["split"] == "train"]
    dev_papers = [p for p in manifest["papers"] if p["split"] == "dev"]

    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    biocause = BioCauseDataset().load()

    configs = [
        ("Phase 1.3 Baseline (No Env Grammar)", False, None, 0.65),
        ("Temperature-Only Grammar", True, {"temperature"}, 0.58),
        ("pH-Only Grammar", True, {"ph"}, 0.58),
        ("Phase 1.4 Combined (Temp + pH + Linker)", True, None, 0.58),
    ]

    results = {}

    for name, enable_env, env_vars, min_conf in configs:
        print(f"\nEvaluating Configuration: {name} ...")
        evaluator = PaperBenchmarkEvaluator(output_dir=os.path.join(REPO_ROOT, "outputs"))
        evaluator.extractor = PaperCausalExtractor(
            evaluator.normalizer,
            enable_env_grammar=enable_env,
            env_variables=env_vars,
        )
        evaluator.linker = CrossPageLinker(
            min_page_distance=1,
            max_transitive_hops=2,
            min_confidence=min_conf,
        )

        train_res = evaluate_split("train", train_papers, evaluator, ingester, biocause, version="v1")
        dev_res = evaluate_split("dev", dev_papers, evaluator, ingester, biocause, version="v1")

        results[name] = {
            "config": {
                "enable_env_grammar": enable_env,
                "env_variables": list(env_vars) if env_vars else None,
                "min_confidence": min_conf,
            },
            "train": {
                "direct_f1": train_res["macro_metrics"]["direct_f1_mean"],
                "cross_f1": train_res["macro_metrics"]["cross_f1_mean"],
                "structural_match": train_res["macro_metrics"]["structural_match_mean"],
                "tp_d": train_res["micro_metrics"]["direct"]["tp"],
                "fp_d": train_res["micro_metrics"]["direct"]["fp"],
                "fn_d": train_res["micro_metrics"]["direct"]["fn"],
            },
            "dev": {
                "direct_f1": dev_res["macro_metrics"]["direct_f1_mean"],
                "cross_f1": dev_res["macro_metrics"]["cross_f1_mean"],
                "structural_match": dev_res["macro_metrics"]["structural_match_mean"],
                "tp_d": dev_res["micro_metrics"]["direct"]["tp"],
                "fp_d": dev_res["micro_metrics"]["direct"]["fp"],
                "fn_d": dev_res["micro_metrics"]["direct"]["fn"],
            },
        }

    out_dir = os.path.join(REPO_ROOT, "results", "phase1_4")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAblation results saved to: {out_path}")

    print("\n" + "=" * 95)
    print("PHASE 1.4 ABLATION STUDY RESULTS (DEVELOPMENT SPLITS)")
    print("=" * 95)
    print(f"{'Configuration':<40} | {'Train Dir F1':<12} | {'Dev Dir F1':<10} | {'Dev Cross F1':<12} | {'Dev Struct':<10}")
    print("-" * 95)
    for name, data in results.items():
        tr_d = data["train"]["direct_f1"]
        dev_d = data["dev"]["direct_f1"]
        dev_c = data["dev"]["cross_f1"]
        dev_s = data["dev"]["structural_match"]
        print(f"{name:<40} | {tr_d:<12.4f} | {dev_d:<10.4f} | {dev_c:<12.4f} | {dev_s:<10.4f}")
    print("=" * 95)


if __name__ == "__main__":
    run_ablation()
