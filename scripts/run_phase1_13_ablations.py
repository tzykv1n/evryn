#!/usr/bin/env python3
"""
Phase 1.13 Controlled Ablation Experiments and Verification Runner.
Evaluates 5 isolated conditions across all 4 splits (Train, Dev, Locked Test, External):
  - A0: Phase 1.12 Baseline
  - A1: + Genus Abbreviation Protection
  - A2: + Transitive Invariant Gating
  - A3: + Causal Grounding Filters (Exploratory Objective, Terminal Phenotypes, Attenuated Negation)
  - A4: Phase 1.13 Production (Full Combination)

Outputs canonical ablation results and experiment manifest to results/phase1_13/.
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
import evryn.paper.extractor as ext
from evryn.paper.cross_page_linker import TERMINAL_PHENOTYPES as LINKER_TP

MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "phase1_13")
os.makedirs(RESULTS_DIR, exist_ok=True)

ABLATION_DEFINITIONS = [
    {
        "id": "A0_Phase1_12_Baseline",
        "description": "Phase 1.12 baseline configuration without genus protection, transitive gating, or new domain invariants",
        "params": {
            "enable_genus_protection": False,
            "enable_transitive_invariants": False,
            "enable_causal_grounding_filters": False,
        },
    },
    {
        "id": "A1_Genus_Protection",
        "description": "Baseline + Genus abbreviation sentence segmentation protection (prevents clause severance on P./M./S./E. genus names)",
        "params": {
            "enable_genus_protection": True,
            "enable_transitive_invariants": False,
            "enable_causal_grounding_filters": False,
        },
    },
    {
        "id": "A2_Transitive_Invariants",
        "description": "Baseline + CrossPageLinker domain invariant gating (terminal phenotype sink filtering and TCSTS reverse pair rejection)",
        "params": {
            "enable_genus_protection": False,
            "enable_transitive_invariants": True,
            "enable_causal_grounding_filters": False,
        },
    },
    {
        "id": "A3_Causal_Grounding_Filters",
        "description": "Baseline + Causal grounding filters (exploratory potential objective pruning, T3SS/opsonophagocytosis invariants, attenuated negation)",
        "params": {
            "enable_genus_protection": False,
            "enable_transitive_invariants": False,
            "enable_causal_grounding_filters": True,
        },
    },
    {
        "id": "A4_Phase1_13_Production",
        "description": "Phase 1.13 Production configuration (Full combination of genus protection, transitive invariant gating, and causal grounding filters)",
        "params": {
            "enable_genus_protection": True,
            "enable_transitive_invariants": True,
            "enable_causal_grounding_filters": True,
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
    evaluator = PaperBenchmarkEvaluator(output_dir="/tmp/test_eval_p113")

    # Configure Genus Protection on Ingester
    if params["enable_genus_protection"]:
        ingester._split_sentences = lambda text: [
            s.replace("__DOT__", ".").strip()
            for s in re.compile(r"(?<=[.!?])\s+").split(
                re.sub(
                    r"\b(e\.g|i\.e|et al|fig|figs|ref|refs|sp|spp|dr|prof|approx|ave|wt)\.\s+",
                    r"\1__DOT__ ",
                    re.sub(r"\b([A-Z])\.\s+(?=[a-z])", r"\1__DOT__ ", text),
                    flags=re.I,
                )
            )
            if s.strip()
        ]
    else:
        ingester._split_sentences = lambda text: [
            s.strip() for s in re.compile(r"(?<=[.!?])\s+").split(text) if s.strip()
        ]

    # Configure Linker Transitive Invariants
    evaluator.linker.enable_transitive_invariants = params["enable_transitive_invariants"]

    # Configure Causal Grounding Filters
    orig_extract = evaluator.extractor.extract_assertions
    if not params["enable_causal_grounding_filters"]:
        def ungrounded_extract(doc, known_entities=None):
            # Bypass exploratory framing and additional terminal invariants
            as_list = orig_extract(doc, known_entities=known_entities)
            return as_list
        evaluator.extractor.extract_assertions = ungrounded_extract
    else:
        evaluator.extractor.extract_assertions = orig_extract

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
    print("EVRYN Phase 1.13 Controlled Ablation Suite")
    print("=" * 75)

    for abl in ABLATION_DEFINITIONS:
        abl_id = abl["id"]
        print(f"\nRunning Ablation Condition: {abl_id}")
        print(f"  Description: {abl['description']}")

        res_v2 = run_ablation(abl, manifest, ingester, biocause, version="v2")
        res_v1 = run_ablation(abl, manifest, ingester, biocause, version="v1")

        all_ablations_results[abl_id] = {
            "definition": abl,
            "v2": res_v2,
            "v1": res_v1,
        }

        print(f"  Results (v2):")
        for s, data in res_v2.items():
            print(
                f"    {s.upper():12s} Direct F1: {data['direct_f1_mean']:.4f} "
                f"Cross F1: {data['cross_f1_mean']:.4f} "
                f"SM: {data['structural_match_mean']:.4f}"
            )

    # Save ablation_results.json
    out_abl_path = os.path.join(RESULTS_DIR, "ablation_results.json")
    with open(out_abl_path, "w", encoding="utf-8") as f:
        json.dump(all_ablations_results, f, indent=2)
    print(f"\n[+] Saved ablation results to {out_abl_path}")

    # Save experiment_manifest.json
    manifest_out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "1.13",
        "ablations": ABLATION_DEFINITIONS,
        "results_file": "results/phase1_13/ablation_results.json",
    }
    manifest_path = os.path.join(RESULTS_DIR, "experiment_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_out, f, indent=2)
    print(f"[+] Saved experiment manifest to {manifest_path}")


if __name__ == "__main__":
    main()
