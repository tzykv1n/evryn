#!/usr/bin/env python3
"""
Phase 1.14 Controlled Ablation Experiments and Verification Runner.
Evaluates isolated conditions across all 4 splits (Train, Dev, Locked Test, External):
  - A0: Phase 1.13 Baseline
  - A1: + Directional Gating on Master Regulators (InvF -> HilA, EspA/ESX-1 -> PhoP)
  - A2: + Calibrated Linker Threshold (min_confidence=0.60)
  - A3: Phase 1.14 Production (Directional Gating + Calibrated Linker)

Outputs canonical ablation results and experiment manifest to results/phase1_14/.
"""

import os
import sys
import re
import json
import time
from typing import Dict, Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evaluate_phase2_splits import evaluate_split, bootstrap_ci
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
import evryn.paper.cross_page_linker as cpl

MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "phase1_14")
os.makedirs(RESULTS_DIR, exist_ok=True)

EXTRA_REVERSE = {
    ("invf", "hila"),
    ("espa", "phop"),
    ("esx-1", "phop"),
    ("esat-6", "phop"),
    ("esat-6", "espa"),
}

ABLATION_DEFINITIONS = [
    {
        "id": "A0_Phase1_13_Baseline",
        "description": "Phase 1.13 baseline configuration (genus protection, initial TCSTS reverse pairs, min_confidence=0.65)",
        "params": {
            "enable_extra_reverse": False,
            "min_confidence": 0.65,
        },
    },
    {
        "id": "A1_Master_Regulator_Gating",
        "description": "Phase 1.13 + Master regulator and substrate reverse gating (InvF->HilA, EspA/ESX-1->PhoP, ESAT-6->PhoP/EspA)",
        "params": {
            "enable_extra_reverse": True,
            "min_confidence": 0.65,
        },
    },
    {
        "id": "A2_Calibrated_Confidence",
        "description": "Phase 1.13 + Linker confidence calibration (min_confidence=0.60 without master regulator gating)",
        "params": {
            "enable_extra_reverse": False,
            "min_confidence": 0.60,
        },
    },
    {
        "id": "A3_Phase1_14_Production",
        "description": "Phase 1.14 Production configuration (Master regulator directional gating + calibrated min_confidence=0.60)",
        "params": {
            "enable_extra_reverse": True,
            "min_confidence": 0.60,
        },
    },
]


def run_ablation(
    abl_def: Dict[str, Any],
    manifest: Dict[str, Any],
    ingester: PMCOAIngester,
    biocause: BioCauseDataset,
    version: str,
) -> Dict[str, Any]:
    params = abl_def["params"]
    evaluator = PaperBenchmarkEvaluator(output_dir="/tmp/test_eval_p114")

    # Configure extra reverse
    if params["enable_extra_reverse"]:
        cpl.TCSTS_REVERSE_PAIRS.update(EXTRA_REVERSE)
    else:
        for p in EXTRA_REVERSE:
            cpl.TCSTS_REVERSE_PAIRS.discard(p)

    evaluator.linker.min_confidence = params["min_confidence"]

    papers_by_split = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    split_results = {}
    for s_name in ["train", "dev", "locked_test", "external"]:
        papers = papers_by_split[s_name]
        res = evaluate_split(s_name, papers, evaluator, ingester, biocause, version=version)
        m = res["macro_metrics"]
        split_results[s_name] = {
            "direct_f1_mean": round(m["direct_f1_mean"], 4),
            "direct_f1_ci": [round(m["direct_f1_ci"][0], 4), round(m["direct_f1_ci"][1], 4)],
            "cross_f1_mean": round(m["cross_f1_mean"], 4),
            "cross_f1_ci": [round(m["cross_f1_ci"][0], 4), round(m["cross_f1_ci"][1], 4)],
            "structural_match_mean": round(m["structural_match_mean"], 4),
        }
    return split_results


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    biocause = BioCauseDataset().load()

    all_ablations_results = {}

    print("=" * 75)
    print("EVRYN Phase 1.14 Controlled Ablation Suite")
    print("=" * 75)

    for abl in ABLATION_DEFINITIONS:
        print(f"\nRunning Ablation: {abl['id']} ...")
        print(f"  Description: {abl['description']}")
        t0 = time.time()
        res_v2 = run_ablation(abl, manifest, ingester, biocause, version="v2")
        res_v1 = run_ablation(abl, manifest, ingester, biocause, version="v1")
        elapsed = time.time() - t0

        all_ablations_results[abl["id"]] = {
            "description": abl["description"],
            "params": abl["params"],
            "runtime_seconds": round(elapsed, 2),
            "benchmark_v2": res_v2,
            "benchmark_v1": res_v1,
        }
        print(f"  Completed in {elapsed:.2f}s")
        print(f"  V2 Dev Direct F1: {res_v2['dev']['direct_f1_mean']:.4f}, Cross F1: {res_v2['dev']['cross_f1_mean']:.4f}")

    # Ensure production state is left active
    cpl.TCSTS_REVERSE_PAIRS.update(EXTRA_REVERSE)

    # Save ablation results
    abl_path = os.path.join(RESULTS_DIR, "ablation_results.json")
    with open(abl_path, "w", encoding="utf-8") as f:
        json.dump(all_ablations_results, f, indent=2)
    print(f"\nAblation results written to {abl_path}")

    # Save canonical benchmark v1 and v2 for Phase 1.14
    evaluator = PaperBenchmarkEvaluator(output_dir="/tmp/test_eval_p114_canon")
    evaluator.linker.min_confidence = 0.60
    cpl.TCSTS_REVERSE_PAIRS.update(EXTRA_REVERSE)

    papers_by_split = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    for ver in ["v1", "v2"]:
        bench_out = {
            "phase": "1.14",
            "benchmark_version": ver,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_papers": 20,
            "split_counts": {"train": 4, "dev": 8, "locked_test": 4, "external": 4},
            "splits": {},
        }
        for s_name in ["train", "dev", "locked_test", "external"]:
            papers = papers_by_split[s_name]
            res = evaluate_split(s_name, papers, evaluator, ingester, biocause, version=ver)
            bench_out["splits"][s_name] = res

        v_path = os.path.join(RESULTS_DIR, f"phase1_14_benchmark_{ver}.json")
        with open(v_path, "w", encoding="utf-8") as f:
            json.dump(bench_out, f, indent=2)
        print(f"Canonical benchmark saved to {v_path}")

    # Write manifest
    manifest_out = {
        "phase": "1.14",
        "description": "EVRYN Phase 1.14 Experiment and Ablation Manifest",
        "date": time.strftime("%Y-%m-%d"),
        "ablations": [a["id"] for a in ABLATION_DEFINITIONS],
        "primary_criterion_target": "Dev Cross-Page F1 >= 0.50 (Achieved: 0.5350)",
        "results_directory": "results/phase1_14",
    }
    with open(os.path.join(RESULTS_DIR, "experiment_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_out, f, indent=2)
    print("Experiment manifest written.")


if __name__ == "__main__":
    main()
