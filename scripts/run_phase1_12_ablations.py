#!/usr/bin/env python3
"""
EVRYN Phase 1.12 Controlled Ablation Suite.
Evaluates the contributions of:
  - A0: Phase 1.11 baseline
  - A1: + Agent Nominal Activation
  - A2: + Homology & Cloning Filter
  - A3: + Relative Clause Barrier (explored)
  - A4: Phase 1.12 Production Configuration (A1 + A2)
across all splits and benchmark versions (v1 and v2).
"""

import os
import sys
import json
import time
from typing import Dict, Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evaluate_phase2_splits import evaluate_split


def run_ablations():
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    papers_by_split = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    ingester = PMCOAIngester()
    biocause = BioCauseDataset()

    ablation_definitions = [
        {
            "id": "A0_Phase1_11_Baseline",
            "description": "Phase 1.11 baseline configuration without nominal activation or homology gate",
            "params": {
                "enable_agent_nominal_activation": False,
                "enable_homology_filter": False,
                "enable_relative_clause_barrier": False,
            },
        },
        {
            "id": "A1_Nominal_Activation",
            "description": "Baseline + Agent Nominal Activation ([Agent] activation/induction of [Target])",
            "params": {
                "enable_agent_nominal_activation": True,
                "enable_homology_filter": False,
                "enable_relative_clause_barrier": False,
            },
        },
        {
            "id": "A2_Homology_Filter",
            "description": "Baseline + Homology & Gene Cloning Non-Causal Gating",
            "params": {
                "enable_agent_nominal_activation": False,
                "enable_homology_filter": True,
                "enable_relative_clause_barrier": False,
            },
        },
        {
            "id": "A3_Relative_Clause_Barrier",
            "description": "Full configuration + Relative clause antecedent barrier",
            "params": {
                "enable_agent_nominal_activation": True,
                "enable_homology_filter": True,
                "enable_relative_clause_barrier": True,
            },
        },
        {
            "id": "A4_Phase1_12_Production",
            "description": "Phase 1.12 Production Configuration (Nominal Activation + Homology Gating)",
            "params": {
                "enable_agent_nominal_activation": True,
                "enable_homology_filter": True,
                "enable_relative_clause_barrier": False,
            },
        },
    ]

    all_results = {}
    splits = ["train", "dev", "locked_test", "external"]

    for abl in ablation_definitions:
        abl_id = abl["id"]
        print(f"\n--- Running Ablation: {abl_id} ---")
        all_results[abl_id] = {
            "definition": abl,
            "v1": {},
            "v2": {},
        }

        evaluator = PaperBenchmarkEvaluator()
        for k, v in abl["params"].items():
            setattr(evaluator.extractor, k, v)

        for version in ["v1", "v2"]:
            for split_name in splits:
                papers = papers_by_split[split_name]
                res = evaluate_split(split_name, papers, evaluator, ingester, biocause, version=version)
                macro = res["macro_metrics"]
                all_results[abl_id][version][split_name] = {
                    "direct_f1_mean": macro["direct_f1_mean"],
                    "direct_f1_ci": macro["direct_f1_ci"],
                    "cross_f1_mean": macro["cross_f1_mean"],
                    "cross_f1_ci": macro["cross_f1_ci"],
                    "structural_match_mean": macro["structural_match_mean"],
                }
                print(f"[{version}] {split_name:12s} | Dir F1: {macro['direct_f1_mean']:.4f} | Cross F1: {macro['cross_f1_mean']:.4f} | SM: {macro['structural_match_mean']:.4f}")

    out_dir = os.path.join(REPO_ROOT, "results", "phase1_12")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ablation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAblation results written to {out_file}")

    manifest_out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "1.12",
        "ablations": ablation_definitions,
        "results_file": "results/phase1_12/ablation_results.json",
    }
    with open(os.path.join(out_dir, "experiment_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_out, f, indent=2)
    print("Experiment manifest saved.")


if __name__ == "__main__":
    run_ablations()
