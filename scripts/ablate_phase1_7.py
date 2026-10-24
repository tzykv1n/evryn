#!/usr/bin/env python3
"""
EVRYN Phase 1.7 Controlled Ablation Script.
Evaluates Configurations A, B, C, D, and E on strictly isolated Train (4 papers) and Dev (8 papers) splits.
Saves comprehensive results to results/phase1_7/ablation_results.json.
"""

import os
import sys
import json
import time
import numpy as np
from typing import Dict, List, Any, Tuple

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import get_curated_papers, convert_pmc_oa_to_scientific_document
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.datasets.pmc_oa import PMCOAIngester
from evaluate_phase2_splits import match_edge, bootstrap_ci


def evaluate_split_with_extractor(
    extractor: PaperCausalExtractor,
    papers: List[Dict[str, Any]],
    curated_map: Dict[str, Any],
    ingester: PMCOAIngester,
    evaluator: PaperBenchmarkEvaluator,
) -> Dict[str, Any]:
    f1s_direct = []
    precisions_direct = []
    recalls_direct = []
    f1s_cross = []
    exact_matches = 0

    total_tp_d = 0
    total_fp_d = 0
    total_fn_d = 0

    for paper in papers:
        pmcid = paper["pmcid"]
        spec = curated_map[pmcid]
        xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
        with open(xml_path, "r", encoding="utf-8") as f:
            pmc_doc = ingester.parse_xml(f.read(), pmcid)
        doc = convert_pmc_oa_to_scientific_document(pmc_doc)

        gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
        gt_cross = [tuple(x) for x in spec.get("cross_page_edges", [])]
        canon_entities = spec.get("canonical_entities", [])

        raw_assertions = extractor.extract_assertions(doc, known_entities=canon_entities if canon_entities else None)
        clean_assertions = [a for a in raw_assertions if not a.is_negated]
        if canon_entities:
            c_set = set(canon_entities)
            filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
            if len(filt) >= 2:
                clean_assertions = filt

        pred_direct = [(a.cause_canonical, a.effect_canonical) for a in clean_assertions]
        cross_links = evaluator.linker.find_cross_page_links(clean_assertions)
        pred_cross = [(l.source_entity, l.target_entity) for l in cross_links if l.distance_pages >= 1]

        # Direct metrics
        tp_d = 0
        matched_gt_d = set()
        for p_c, p_e in pred_direct:
            for idx, (g_c, g_e) in enumerate(gt_direct):
                if idx not in matched_gt_d and match_edge(p_c, p_e, g_c, g_e):
                    tp_d += 1
                    matched_gt_d.add(idx)
                    break

        fp_d = max(0, len(pred_direct) - tp_d)
        fn_d = max(0, len(gt_direct) - tp_d)
        p_d = tp_d / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
        r_d = tp_d / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
        f1_d = (2 * p_d * r_d) / (p_d + r_d) if (p_d + r_d) > 0 else 0.0

        precisions_direct.append(p_d)
        recalls_direct.append(r_d)
        f1s_direct.append(f1_d)
        total_tp_d += tp_d
        total_fp_d += fp_d
        total_fn_d += fn_d

        # Cross metrics
        tp_c = 0
        matched_gt_c = set()
        for p_c, p_e in pred_cross:
            for idx, (g_c, g_e) in enumerate(gt_cross):
                if idx not in matched_gt_c and match_edge(p_c, p_e, g_c, g_e):
                    tp_c += 1
                    matched_gt_c.add(idx)
                    break
        fp_c = max(0, len(pred_cross) - tp_c)
        fn_c = max(0, len(gt_cross) - tp_c)
        p_c = tp_c / len(pred_cross) if pred_cross else (1.0 if not gt_cross else 0.0)
        r_c = tp_c / len(gt_cross) if gt_cross else (1.0 if not pred_cross else 0.0)
        f1_c = (2 * p_c * r_c) / (p_c + r_c) if (p_c + r_c) > 0 else 0.0
        f1s_cross.append(f1_c)

        if fp_d == 0 and fn_d == 0 and fp_c == 0 and fn_c == 0:
            exact_matches += 1

    d_mean, d_ci_l, d_ci_u = bootstrap_ci(f1s_direct)
    c_mean, c_ci_l, c_ci_u = bootstrap_ci(f1s_cross)

    return {
        "direct_f1": round(d_mean, 4),
        "direct_f1_ci": [round(d_ci_l, 4), round(d_ci_u, 4)],
        "direct_precision": round(float(np.mean(precisions_direct)), 4),
        "direct_recall": round(float(np.mean(recalls_direct)), 4),
        "cross_f1": round(c_mean, 4),
        "exact_match_ratio": round(exact_matches / len(papers), 4) if papers else 0.0,
        "total_tp": total_tp_d,
        "total_fp": total_fp_d,
        "total_fn": total_fn_d,
    }


def main():
    with open(os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")) as f:
        manifest = json.load(f)

    train_papers = [p for p in manifest["papers"] if p["split"] == "train"]
    dev_papers = [p for p in manifest["papers"] if p["split"] == "dev"]

    curated_map = {p["pmcid"]: p for p in get_curated_papers("v2")}
    evaluator = PaperBenchmarkEvaluator()
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))

    configs = {
        "config_a_baseline": {
            "description": "Phase 1.6 baseline (no document-context resolution)",
            "extractor": PaperCausalExtractor(
                enable_document_context=False,
            ),
        },
        "config_b_candidate_gen_only": {
            "description": "Candidate generation only (candidates identified, not committed)",
            "extractor": PaperCausalExtractor(
                enable_document_context=False,
            ),
        },
        "config_c_connectives_only": {
            "description": "Discourse connectives only (no sentence stitching, no anaphora)",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=False,
                enable_anaphora=False,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "config_d_full_document_context": {
            "description": "Full document-context resolution (stitching + demonstrative anaphora + connectives + FP controls)",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=True,
                enable_anaphora=True,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "config_e1_no_sentence_stitch": {
            "description": "Ablation: Full system without sentence boundary stitching",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=False,
                enable_anaphora=True,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "config_e2_no_anaphora": {
            "description": "Ablation: Full system without demonstrative anaphora",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=True,
                enable_anaphora=False,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "config_e3_no_fp_controls": {
            "description": "Ablation: Full system without false-positive controls",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=True,
                enable_anaphora=True,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=False,
            ),
        },
    }

    results = {}
    print("=" * 80)
    print("EVRYN Phase 1.7 Controlled Ablation Evaluation (Train & Dev Splits Strictly)")
    print("=" * 80)

    for cfg_id, cfg_info in configs.items():
        print(f"\nRunning {cfg_id}: {cfg_info['description']}...")
        ext = cfg_info["extractor"]
        t0 = time.time()
        train_res = evaluate_split_with_extractor(ext, train_papers, curated_map, ingester, evaluator)
        dev_res = evaluate_split_with_extractor(ext, dev_papers, curated_map, ingester, evaluator)
        elapsed = time.time() - t0

        results[cfg_id] = {
            "description": cfg_info["description"],
            "train": train_res,
            "dev": dev_res,
            "elapsed_seconds": round(elapsed, 2),
        }

        print(f"  Train: Direct F1 = {train_res['direct_f1']:.4f} (P={train_res['direct_precision']:.4f}, R={train_res['direct_recall']:.4f}), Cross F1 = {train_res['cross_f1']:.4f}")
        print(f"  Dev:   Direct F1 = {dev_res['direct_f1']:.4f} (P={dev_res['direct_precision']:.4f}, R={dev_res['direct_recall']:.4f}), Cross F1 = {dev_res['cross_f1']:.4f}")

    os.makedirs(os.path.join(REPO_ROOT, "results", "phase1_7"), exist_ok=True)
    out_path = os.path.join(REPO_ROOT, "results", "phase1_7", "ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAblation evaluation complete. Saved to {out_path}")

if __name__ == "__main__":
    main()
