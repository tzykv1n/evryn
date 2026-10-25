#!/usr/bin/env python3
"""
Phase 1.8 Controlled Experiment Evaluator.
Evaluates extraction improvements on strictly isolated Train (4 papers) and Dev (8 papers) splits.
"""

import os
import sys
import json
import copy
from typing import Dict, Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import importlib.util
spec = importlib.util.spec_from_file_location("eval_splits", os.path.join(REPO_ROOT, "scripts", "evaluate_phase2_splits.py"))
eval_splits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_splits)

def evaluate_extractor(extractor=None, version="v2", splits=None):
    if splits is None:
        splits = ["train", "dev"]
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ingester = eval_splits.PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    evaluator = eval_splits.PaperBenchmarkEvaluator()
    if extractor is not None:
        evaluator.extractor = extractor
    biocause = eval_splits.BioCauseDataset(os.path.join(REPO_ROOT, "data", "biocause"))

    papers_by_split: Dict[str, List[Dict[str, Any]]] = {}
    for p in manifest["papers"]:
        s = p["split"]
        papers_by_split.setdefault(s, []).append(p)

    results = {}
    for s_name in splits:
        papers = papers_by_split.get(s_name, [])
        split_res = eval_splits.evaluate_split(s_name, papers, evaluator, ingester, biocause, version=version)
        results[s_name] = split_res
        m = split_res["macro_metrics"]
        print(f"[{s_name.upper()}] Direct F1: {m['direct_f1_mean']:.4f} [CI: {m['direct_f1_ci'][0]:.4f}, {m['direct_f1_ci'][1]:.4f}] | Cross F1: {m['cross_f1_mean']:.4f} | Struct: {m['structural_match_mean']:.4f}")
        for p in split_res["per_paper"]:
            print(f"    {p['pmcid']}: TP={p['tp_direct']} FP={p['fp_direct']} FN={p['fn_direct']} P={p['direct_precision']:.3f} R={p['direct_recall']:.3f} F1={p['direct_f1']:.3f}")
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=["v1", "v2"], default="v2")
    parser.add_argument("--splits", nargs="+", default=["train", "dev"])
    args = parser.parse_args()
    evaluate_extractor(version=args.version, splits=args.splits)
