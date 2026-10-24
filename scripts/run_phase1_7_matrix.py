#!/usr/bin/env python3
"""
EVRYN Phase 1.7 Full Experimental Matrix Runner.
Evaluates Configurations E0 through E5 across:
  - Train (4 papers)
  - Dev (8 papers)
  - Locked Test (4 papers)
  - External Generalization V1 (4 papers)
  - External Generalization V2 (4 papers)

Computes Direct F1, Cross-Page F1, Exact Structural Match, Bootstrap 95% CIs,
and writes comprehensive metrics to results/phase1_7/full_matrix_results.json
and results/phase1_7/experiment_registry.json.
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
    precisions_cross = []
    recalls_cross = []
    exact_matches = 0

    total_tp_d = 0
    total_fp_d = 0
    total_fn_d = 0

    total_tp_c = 0
    total_fp_c = 0
    total_fn_c = 0

    per_paper = []

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
        precisions_cross.append(p_c)
        recalls_cross.append(r_c)
        f1s_cross.append(f1_c)
        total_tp_c += tp_c
        total_fp_c += fp_c
        total_fn_c += fn_c

        is_exact = (fp_d == 0 and fn_d == 0 and fp_c == 0 and fn_c == 0)
        if is_exact:
            exact_matches += 1

        per_paper.append({
            "pmcid": pmcid,
            "direct_f1": round(f1_d, 4),
            "direct_p": round(p_d, 4),
            "direct_r": round(r_d, 4),
            "tp_d": tp_d,
            "fp_d": fp_d,
            "fn_d": fn_d,
            "cross_f1": round(f1_c, 4),
            "tp_c": tp_c,
            "fp_c": fp_c,
            "fn_c": fn_c,
        })

    d_mean, d_ci_l, d_ci_u = bootstrap_ci(f1s_direct)
    c_mean, c_ci_l, c_ci_u = bootstrap_ci(f1s_cross)

    return {
        "macro_metrics": {
            "direct_f1_mean": round(d_mean, 4),
            "direct_f1_ci": [round(d_ci_l, 4), round(d_ci_u, 4)],
            "direct_precision_mean": round(float(np.mean(precisions_direct)), 4),
            "direct_recall_mean": round(float(np.mean(recalls_direct)), 4),
            "cross_f1_mean": round(c_mean, 4),
            "cross_f1_ci": [round(c_ci_l, 4), round(c_ci_u, 4)],
            "cross_precision_mean": round(float(np.mean(precisions_cross)), 4),
            "cross_recall_mean": round(float(np.mean(recalls_cross)), 4),
            "structural_match_ratio": round(exact_matches / len(papers), 4) if papers else 0.0,
        },
        "micro_metrics": {
            "direct": {
                "tp": total_tp_d,
                "fp": total_fp_d,
                "fn": total_fn_d,
                "precision": round(total_tp_d / (total_tp_d + total_fp_d), 4) if (total_tp_d + total_fp_d) > 0 else 0.0,
                "recall": round(total_tp_d / (total_tp_d + total_fn_d), 4) if (total_tp_d + total_fn_d) > 0 else 0.0,
            },
            "cross": {
                "tp": total_tp_c,
                "fp": total_fp_c,
                "fn": total_fn_c,
                "precision": round(total_tp_c / (total_tp_c + total_fp_c), 4) if (total_tp_c + total_fp_c) > 0 else 0.0,
                "recall": round(total_tp_c / (total_tp_c + total_fn_c), 4) if (total_tp_c + total_fn_c) > 0 else 0.0,
            },
        },
        "per_paper": per_paper,
    }


def main():
    with open(os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")) as f:
        manifest = json.load(f)

    splits = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    curated_v1 = {p["pmcid"]: p for p in get_curated_papers("v1")}
    curated_v2 = {p["pmcid"]: p for p in get_curated_papers("v2")}
    evaluator = PaperBenchmarkEvaluator()
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))

    experiment_configs = {
        "E0_Baseline": {
            "name": "E0: Phase 1.6 Baseline",
            "hypothesis": "Baseline sentence-local extraction without document-context resolution",
            "extractor": PaperCausalExtractor(
                enable_document_context=False,
            ),
        },
        "E1_Bounded_Candidate_Gen": {
            "name": "E1: Bounded Candidate Generation Only",
            "hypothesis": "Generate cross-sentence candidates across sentence window dist<=1 without committing",
            "extractor": PaperCausalExtractor(
                enable_document_context=False,
            ),
        },
        "E2_Adjacent_Connectives": {
            "name": "E2: Adjacent-Sentence Discourse Connectives",
            "hypothesis": "Resolve explicit discourse connectives ('Consequently', 'As a result', 'Therefore') across adjacent sentences",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=False,
                enable_anaphora=False,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "E3_Demonstrative_Anaphora": {
            "name": "E3: Demonstrative Causal Anaphora Resolution",
            "hypothesis": "Resolve demonstrative pronouns ('This result', 'These findings') to antecedent cause/effect",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=False,
                enable_anaphora=True,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "E4_Sentence_Stitching": {
            "name": "E4: Sentence Boundary Abbreviation Stitching",
            "hypothesis": "Stitch sentences fragmented by taxonomic genus and citation abbreviations ('P. gingivalis', 'et al.')",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=True,
                enable_anaphora=False,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
        "E5_Full_Document_Context": {
            "name": "E5: Full Calibrated Document-Context Resolver",
            "hypothesis": "Stitching + Demonstrative Anaphora + Discourse Connectives + Invariant FP Controls",
            "extractor": PaperCausalExtractor(
                enable_document_context=True,
                enable_sentence_stitch=True,
                enable_anaphora=True,
                enable_discourse_connectives=True,
                enable_doc_context_fp_controls=True,
            ),
        },
    }

    full_results = {}
    print("=" * 80)
    print("EVRYN Phase 1.7 Experimental Matrix (E0 - E5) Across All Splits")
    print("=" * 80)

    for exp_id, exp_info in experiment_configs.items():
        print(f"\n>>> Running {exp_id} ({exp_info['name']})...")
        t0 = time.time()
        ext = exp_info["extractor"]

        split_results = {}
        for s_name in ["train", "dev", "locked_test"]:
            papers = splits[s_name]
            res = evaluate_split_with_extractor(ext, papers, curated_v2, ingester, evaluator)
            split_results[s_name] = res
            print(f"  {s_name.upper():12s}: Direct F1 = {res['macro_metrics']['direct_f1_mean']:.4f} (TP:{res['micro_metrics']['direct']['tp']}, FP:{res['micro_metrics']['direct']['fp']}, FN:{res['micro_metrics']['direct']['fn']}), Cross F1 = {res['macro_metrics']['cross_f1_mean']:.4f}")

        # External V1
        ext_v1 = evaluate_split_with_extractor(ext, splits["external"], curated_v1, ingester, evaluator)
        split_results["external_v1"] = ext_v1
        print(f"  EXTERNAL (v1): Direct F1 = {ext_v1['macro_metrics']['direct_f1_mean']:.4f} (TP:{ext_v1['micro_metrics']['direct']['tp']}, FP:{ext_v1['micro_metrics']['direct']['fp']}, FN:{ext_v1['micro_metrics']['direct']['fn']}), Cross F1 = {ext_v1['macro_metrics']['cross_f1_mean']:.4f}")

        # External V2
        ext_v2 = evaluate_split_with_extractor(ext, splits["external"], curated_v2, ingester, evaluator)
        split_results["external_v2"] = ext_v2
        print(f"  EXTERNAL (v2): Direct F1 = {ext_v2['macro_metrics']['direct_f1_mean']:.4f} (TP:{ext_v2['micro_metrics']['direct']['tp']}, FP:{ext_v2['micro_metrics']['direct']['fp']}, FN:{ext_v2['micro_metrics']['direct']['fn']}), Cross F1 = {ext_v2['macro_metrics']['cross_f1_mean']:.4f}")

        elapsed = time.time() - t0
        full_results[exp_id] = {
            "name": exp_info["name"],
            "hypothesis": exp_info["hypothesis"],
            "elapsed_seconds": round(elapsed, 2),
            "splits": split_results,
        }

    # Save to results/phase1_7/
    out_dir = os.path.join(REPO_ROOT, "results", "phase1_7")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "full_matrix_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)

    # Save experiment registry
    registry_path = os.path.join(out_dir, "experiment_registry.json")
    registry_entries = []
    for exp_id, data in full_results.items():
        entry = {
            "experiment_id": exp_id,
            "experiment_name": data["name"],
            "hypothesis": data["hypothesis"],
            "status": "COMPLETED",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "train_direct_f1": data["splits"]["train"]["macro_metrics"]["direct_f1_mean"],
            "dev_direct_f1": data["splits"]["dev"]["macro_metrics"]["direct_f1_mean"],
            "locked_test_direct_f1": data["splits"]["locked_test"]["macro_metrics"]["direct_f1_mean"],
            "external_v1_direct_f1": data["splits"]["external_v1"]["macro_metrics"]["direct_f1_mean"],
            "external_v2_direct_f1": data["splits"]["external_v2"]["macro_metrics"]["direct_f1_mean"],
            "train_cross_f1": data["splits"]["train"]["macro_metrics"]["cross_f1_mean"],
            "dev_cross_f1": data["splits"]["dev"]["macro_metrics"]["cross_f1_mean"],
            "locked_test_cross_f1": data["splits"]["locked_test"]["macro_metrics"]["cross_f1_mean"],
            "external_v1_cross_f1": data["splits"]["external_v1"]["macro_metrics"]["cross_f1_mean"],
            "external_v2_cross_f1": data["splits"]["external_v2"]["macro_metrics"]["cross_f1_mean"],
            "elapsed_seconds": data["elapsed_seconds"],
        }
        registry_entries.append(entry)

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_entries, f, indent=2)

    print(f"\nAll experiments complete. Results saved to {out_path} and {registry_path}")

if __name__ == "__main__":
    main()
