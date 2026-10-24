#!/usr/bin/env python3
"""
Phase 1.5 Controlled Ablation Experiments:
1. Baseline (Phase 1.4 Checkpoint)
2. Experiment A: Relation Trigger Coverage (requires, promoted by, abolishes, adverbial passives)
3. Experiment B: Conjoined Clause Handling (multi-cause both X and Y, conjoined relative clause protection)
4. Experiment C: Entity & Span Alignment (BioCause dereferencing, SPI1-T3SS, genitive possessives)
5. Experiment D: Confidence Calibration (calibrated thresholds 0.55 vs 0.58 vs 0.65)
6. Experiment E: Combined Phase 1.5 Configuration
"""

import os
import sys
import json
from typing import Dict, Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evaluate_phase2_splits import evaluate_split


def run_ablations():
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    train_papers = [p for p in manifest["papers"] if p["split"] == "train"]
    dev_papers = [p for p in manifest["papers"] if p["split"] == "dev"]

    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    biocause = BioCauseDataset().load()

    experiments = [
        ("Phase 1.4 Baseline", {"extended_triggers": False, "conjoined": False, "genitive": False, "min_conf": 0.58}),
        ("Exp A: Trigger Coverage", {"extended_triggers": True, "conjoined": False, "genitive": False, "min_conf": 0.58}),
        ("Exp B: Conjoined Clauses", {"extended_triggers": False, "conjoined": True, "genitive": False, "min_conf": 0.58}),
        ("Exp C: Entity & Span Alignment", {"extended_triggers": False, "conjoined": False, "genitive": True, "min_conf": 0.58}),
        ("Exp D: Confidence Calibration (0.55)", {"extended_triggers": False, "conjoined": False, "genitive": False, "min_conf": 0.55}),
        ("Exp E: Combined Phase 1.5", {"extended_triggers": True, "conjoined": True, "genitive": True, "min_conf": 0.58}),
    ]

    results = {}

    for name, cfg in experiments:
        print(f"\nRunning Experiment: {name} ...")
        norm = PaperEntityNormalizer()
        evaluator = PaperBenchmarkEvaluator(output_dir="outputs")
        evaluator.extractor = PaperCausalExtractor(
            normalizer=norm,
            enable_env_grammar=True,
            enable_extended_triggers=cfg["extended_triggers"],
            enable_conjoined_causes=cfg["conjoined"],
        )
        norm.enable_genitive_stripping = cfg["genitive"]
        evaluator.linker = CrossPageLinker(min_confidence=cfg["min_conf"])

        train_res = evaluate_split("train", train_papers, evaluator, ingester, biocause, version="v1")
        dev_res = evaluate_split("dev", dev_papers, evaluator, ingester, biocause, version="v1")

        results[name] = {
            "config": cfg,
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

    out_dir = os.path.join(REPO_ROOT, "results", "phase1_5")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAblation results saved to: {out_path}")

    print("\n" + "=" * 95)
    print("PHASE 1.5 CONTROLLED EXPERIMENTS RESULTS (TRAIN & DEV SPLITS)")
    print("=" * 95)
    print(f"{'Experiment':<35} | {'Train Dir F1':<12} | {'Dev Dir F1':<10} | {'Dev Cross F1':<12} | {'Dev Struct':<10}")
    print("-" * 95)
    for name, data in results.items():
        tr_d = data["train"]["direct_f1"]
        dev_d = data["dev"]["direct_f1"]
        dev_c = data["dev"]["cross_f1"]
        dev_s = data["dev"]["structural_match"]
        print(f"{name:<35} | {tr_d:<12.4f} | {dev_d:<10.4f} | {dev_c:<12.4f} | {dev_s:<10.4f}")
    print("=" * 95)


if __name__ == "__main__":
    run_ablations()
