#!/usr/bin/env python3
"""Run controlled ablation experiments for Phase 1.10.

Ablations:
- A0: Phase 1.9 Baseline (no Phase 1.10 mechanisms)
- A1: + Strict TCSTS Syntax (eliminating comma-separated gene false positives)
- A2: + Genomic Locus Encoding (recovering PAI -> kinase/system relations)
- A3: + Mutant Resistance Defect (recovering defect-based regulator -> resistance phenotype)
- A4: Full Phase 1.10 (+ Speculation & Coordinate Sibling Filtering)
"""

import json
import os
import re
import sys
from pathlib import Path

# Ensure evryn is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor, TCSTS_AND_RE
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.real_benchmark import convert_pmc_oa_to_scientific_document, get_curated_papers


def match_edge(p_c: str, p_e: str, g_c: str, g_e: str) -> bool:
    p_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_c).strip().lower()
    p_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_e).strip().lower()
    g_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_c).strip().lower()
    g_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_e).strip().lower()
    if not p_c_n or not p_e_n or not g_c_n or not g_e_n:
        return False
    return (p_c_n in g_c_n or g_c_n in p_c_n) and (p_e_n in g_e_n or g_e_n in p_e_n)


def evaluate_extractor_on_split(extractor: PaperCausalExtractor, papers, curated_map, ingester):
    f1_scores = []
    tps, fps, fns = 0, 0, 0
    per_paper = {}
    for paper in papers:
        pmcid = paper["pmcid"]
        xml_path = f"/home/tk/projects/evryn/data/real_papers/xml/{pmcid}.xml"
        with open(xml_path, "r", encoding="utf-8") as f:
            pmc_doc = ingester.parse_xml(f.read(), pmcid)
        doc = convert_pmc_oa_to_scientific_document(pmc_doc)
        spec = curated_map[pmcid]
        gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
        canon_entities = spec.get("canonical_entities", [])

        raw = extractor.extract_assertions(doc, known_entities=canon_entities if canon_entities else None)
        clean = [a for a in raw if not a.is_negated]
        if canon_entities:
            c_set = set(canon_entities)
            filt = [a for a in clean if a.cause_canonical in c_set and a.effect_canonical in c_set]
            if len(filt) >= 2:
                clean = filt

        pred_direct = [(a.cause_canonical, a.effect_canonical) for a in clean]
        matched_gt = set()
        tp = 0
        for p_c, p_e in pred_direct:
            for idx, (g_c, g_e) in enumerate(gt_direct):
                if idx not in matched_gt and match_edge(p_c, p_e, g_c, g_e):
                    tp += 1
                    matched_gt.add(idx)
                    break
        fp = max(0, len(pred_direct) - tp)
        fn = max(0, len(gt_direct) - tp)
        p = tp / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
        r = tp / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        f1_scores.append(f1)
        tps += tp
        fps += fp
        fns += fn
        per_paper[pmcid] = {"tp": tp, "fp": fp, "fn": fn, "f1": round(f1, 4)}

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    return {
        "macro_f1": round(macro_f1, 4),
        "tp": tps,
        "fp": fps,
        "fn": fns,
        "per_paper": per_paper,
    }


def main():
    ingester = PMCOAIngester()
    manifest_path = "/home/tk/projects/evryn/data/real_papers/split_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    curated_map = {p["pmcid"]: p for p in get_curated_papers("v2")}
    dev_papers = [p for p in manifest["papers"] if p["split"] == "dev"]
    train_papers = [p for p in manifest["papers"] if p["split"] == "train"]
    test_papers = [p for p in manifest["papers"] if p["split"] == "locked_test"]
    ext_papers = [p for p in manifest["papers"] if p["split"] == "external"]

    configurations = [
        {
            "id": "A0_Phase1_9_Baseline",
            "name": "Phase 1.9 Production Baseline",
            "locus": False,
            "phenotype": False,
            "speculation": False,
        },
        {
            "id": "A1_Strict_TCSTS_Syntax",
            "name": "Phase 1.9 + Strict TCSTS Syntax",
            "locus": False,
            "phenotype": False,
            "speculation": False,
        },
        {
            "id": "A2_Locus_Encoding",
            "name": "Phase 1.9 + Strict TCSTS + Locus Encoding",
            "locus": True,
            "phenotype": False,
            "speculation": False,
        },
        {
            "id": "A3_Resistance_Defect",
            "name": "Phase 1.9 + Strict TCSTS + Locus + Resistance Defect",
            "locus": True,
            "phenotype": True,
            "speculation": False,
        },
        {
            "id": "A4_Full_Phase1_10",
            "name": "Full Phase 1.10 (+ Speculation & Coordinate Filtering)",
            "locus": True,
            "phenotype": True,
            "speculation": True,
        },
    ]

    normalizer = PaperEntityNormalizer()
    ablation_results = {}

    import evryn.paper.extractor as ext_mod
    original_strict_tcsts = ext_mod.TCSTS_AND_RE
    loose_phase1_9_tcsts = re.compile(
        r"\b([A-Za-z0-9_-]{2,15})(?:\s+protein)?\s+and\s+(?:the\s+|its\s+(?:cognate\s+)?(?:sensor\s+)?kinase\s+)?([A-Za-z0-9_-]{2,15})\b(?:\s+proteins?)?\s*(?:,|forming|constitute|form|belonging)",
        re.IGNORECASE,
    )

    for cfg in configurations:
        print(f"\nEvaluating Configuration: {cfg['name']} ({cfg['id']})")
        if cfg["id"] == "A0_Phase1_9_Baseline":
            ext_mod.TCSTS_AND_RE = loose_phase1_9_tcsts
        else:
            ext_mod.TCSTS_AND_RE = original_strict_tcsts
        # Instantiate extractor with configuration
        extractor = PaperCausalExtractor(
            normalizer=normalizer,
            enable_locus_encoding_inference=cfg["locus"],
            enable_phenotype_defect_inference=cfg["phenotype"],
            enable_speculation_and_sibling_validation=cfg["speculation"],
        )

        dev_res = evaluate_extractor_on_split(extractor, dev_papers, curated_map, ingester)
        test_res = evaluate_extractor_on_split(extractor, test_papers, curated_map, ingester)
        train_res = evaluate_extractor_on_split(extractor, train_papers, curated_map, ingester)
        ext_res = evaluate_extractor_on_split(extractor, ext_papers, curated_map, ingester)

        print(f"  Dev F1: {dev_res['macro_f1']} (TP={dev_res['tp']}, FP={dev_res['fp']}, FN={dev_res['fn']})")
        print(f"  Locked Test F1: {test_res['macro_f1']} (TP={test_res['tp']}, FP={test_res['fp']}, FN={test_res['fn']})")

        ablation_results[cfg["id"]] = {
            "name": cfg["name"],
            "settings": {
                "enable_locus_encoding_inference": cfg["locus"],
                "enable_phenotype_defect_inference": cfg["phenotype"],
                "enable_speculation_and_sibling_validation": cfg["speculation"],
            },
            "dev": dev_res,
            "locked_test": test_res,
            "train": train_res,
            "external": ext_res,
        }

    os.makedirs("/home/tk/projects/evryn/results/phase1_10", exist_ok=True)
    out_file = "/home/tk/projects/evryn/results/phase1_10/ablation_results.json"
    with open(out_file, "w") as f:
        json.dump(ablation_results, f, indent=2)
    print(f"\nAblation results successfully saved to {out_file}")

    manifest_out = "/home/tk/projects/evryn/results/phase1_10/experiment_manifest.json"
    manifest_data = {
        "phase": "1.10",
        "description": "EVRYN Phase 1.10 Advanced Extraction Improvements, Evidence Validation, and Synchronized Deliverables",
        "timestamp": "2026-10-25T16:00:00Z",
        "branch": "phase2.1-benchmark-audit-and-ui-fix",
        "baseline_dev_macro_f1": 0.6137,
        "final_dev_macro_f1": ablation_results["A4_Full_Phase1_10"]["dev"]["macro_f1"],
        "baseline_locked_test_f1": 0.4658,
        "final_locked_test_f1": ablation_results["A4_Full_Phase1_10"]["locked_test"]["macro_f1"],
        "train_macro_f1": ablation_results["A4_Full_Phase1_10"]["train"]["macro_f1"],
        "external_macro_f1_v2": ablation_results["A4_Full_Phase1_10"]["external"]["macro_f1"],
        "configurations": configurations,
    }
    with open(manifest_out, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Experiment manifest successfully saved to {manifest_out}")


if __name__ == "__main__":
    main()
