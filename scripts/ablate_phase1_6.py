#!/usr/bin/env python3
"""
Ablation experiment runner for EVRYN Phase 1.6:
Strictly isolated to Train (4 papers) and Dev (8 papers) splits.
Compares:
  - Phase 1.5 Baseline
  - Exp A: Passive Genetic Complementation Triggers (restored/rescued)
  - Exp B: Terminal Phenotypic Invariant (reject TerminalPhenotype -> Gene)
  - Exp C: Greek Morphology (Δ, σ) & Biofilm Canonicalization
  - Exp D: Combined Phase 1.6 Pipeline
Outputs:
  - results/phase1_6/ablation_results.json
"""

import os
import sys
import json
from typing import Dict, List, Any, Tuple

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import (
    get_curated_papers,
    convert_pmc_oa_to_scientific_document,
)
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.datasets.pmc_oa import PMCOAIngester
from evaluate_phase2_splits import match_edge, bootstrap_ci

def run_eval_for_config(
    extractor: PaperCausalExtractor,
    ingester: PMCOAIngester,
    curated_map: Dict[str, Any],
    papers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    f1s_d = []
    f1s_c = []
    sms = []
    tot_tp_d = 0
    tot_fp_d = 0
    tot_fn_d = 0

    for p in papers:
        pmcid = p["pmcid"]
        spec = curated_map[pmcid]
        xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
        with open(xml_path, "r", encoding="utf-8") as f:
            pmc_doc = ingester.parse_xml(f.read(), pmcid)
        doc = convert_pmc_oa_to_scientific_document(pmc_doc)

        gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
        gt_cross = [tuple(x) for x in spec.get("cross_page_edges", [])]
        canon = spec.get("canonical_entities", [])

        raw_assertions = extractor.extract_assertions(doc, known_entities=canon if canon else None)
        clean = [a for a in raw_assertions if not a.is_negated]
        if canon:
            c_set = set(canon)
            filt = [a for a in clean if a.cause_canonical in c_set and a.effect_canonical in c_set]
            if len(filt) >= 2:
                clean = filt

        seen = set()
        preds = []
        for a in clean:
            edge = (a.cause_canonical, a.effect_canonical)
            if edge not in seen:
                seen.add(edge)
                preds.append(edge)

        matched = set()
        for gc, ge in gt_direct:
            for idx, (pc, pe) in enumerate(preds):
                if match_edge(pc, pe, gc, ge):
                    matched.add(idx)
                    break
        tp_d = len(matched)
        fp_d = len(preds) - tp_d
        fn_d = len(gt_direct) - tp_d
        tot_tp_d += tp_d
        tot_fp_d += fp_d
        tot_fn_d += fn_d

        p_d = tp_d / len(preds) if preds else 0.0
        r_d = tp_d / len(gt_direct) if gt_direct else 0.0
        f1_d = (2 * p_d * r_d) / (p_d + r_d) if (p_d + r_d) > 0 else 0.0
        f1s_d.append(f1_d)

    return {
        "direct_f1": round(sum(f1s_d) / len(f1s_d), 4) if f1s_d else 0.0,
        "tp_d": tot_tp_d,
        "fp_d": tot_fp_d,
        "fn_d": tot_fn_d,
        "precision_d": round(tot_tp_d / (tot_tp_d + tot_fp_d), 4) if (tot_tp_d + tot_fp_d) > 0 else 0.0,
        "recall_d": round(tot_tp_d / (tot_tp_d + tot_fn_d), 4) if (tot_tp_d + tot_fn_d) > 0 else 0.0,
    }

def main():
    with open(os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")) as f:
        manifest = json.load(f)

    curated_map = {p["pmcid"]: p for p in get_curated_papers("v2")}
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))

    train_papers = [p for p in manifest["papers"] if p["split"] == "train"]
    dev_papers = [p for p in manifest["papers"] if p["split"] == "dev"]

    configs = {
        "Phase 1.5 Baseline": {
            "passive_restore": False,
            "terminal_phenotype": False,
            "greek_morphology": False,
            "biofilm": False,
        },
        "Exp A: Passive Genetic Complementation": {
            "passive_restore": True,
            "terminal_phenotype": False,
            "greek_morphology": False,
            "biofilm": False,
        },
        "Exp B: Terminal Phenotype Direction Invariant": {
            "passive_restore": False,
            "terminal_phenotype": True,
            "greek_morphology": False,
            "biofilm": False,
        },
        "Exp C: Greek Morphology & Biofilm Canonicalization": {
            "passive_restore": False,
            "terminal_phenotype": False,
            "greek_morphology": True,
            "biofilm": True,
        },
        "Exp D: Combined Phase 1.6 Pipeline": {
            "passive_restore": True,
            "terminal_phenotype": True,
            "greek_morphology": True,
            "biofilm": True,
        },
    }

    results = {}
    print("=" * 70)
    print("EVRYN PHASE 1.6 CONTROLLED ABLATIONS (TRAIN & DEV SPLITS ONLY)")
    print("=" * 70)

    for name, cfg in configs.items():
        print(f"\n--- Running: {name} ---")
        norm = PaperEntityNormalizer(
            enable_genitive_stripping=True,
            enable_greek_morphology=cfg["greek_morphology"],
            enable_biofilm_canonicalization=cfg["biofilm"],
        )
        extractor = PaperCausalExtractor(
            normalizer=norm,
            enable_env_grammar=True,
            enable_extended_triggers=True,
            enable_conjoined_causes=True,
            enable_passive_restore=cfg["passive_restore"],
            enable_terminal_phenotype_invariant=cfg["terminal_phenotype"],
        )

        res_train = run_eval_for_config(extractor, ingester, curated_map, train_papers)
        res_dev = run_eval_for_config(extractor, ingester, curated_map, dev_papers)

        print(f"  Train: Direct F1 = {res_train['direct_f1']:.4f} (TP={res_train['tp_d']}, FP={res_train['fp_d']}, FN={res_train['fn_d']}, P={res_train['precision_d']:.3f}, R={res_train['recall_d']:.3f})")
        print(f"  Dev:   Direct F1 = {res_dev['direct_f1']:.4f} (TP={res_dev['tp_d']}, FP={res_dev['fp_d']}, FN={res_dev['fn_d']}, P={res_dev['precision_d']:.3f}, R={res_dev['recall_d']:.3f})")

        results[name] = {
            "config": cfg,
            "train": res_train,
            "dev": res_dev,
        }

    os.makedirs(os.path.join(REPO_ROOT, "results", "phase1_6"), exist_ok=True)
    out_file = os.path.join(REPO_ROOT, "results", "phase1_6", "ablation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAblation results written to {out_file}")

if __name__ == "__main__":
    main()
