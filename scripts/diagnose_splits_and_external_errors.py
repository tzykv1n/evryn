#!/usr/bin/env python3
"""
Phase 1.1 Split Diagnostics and External Generalization Failure Audit Harness.
Analyzes the 20 benchmark papers across Train, Dev, Locked Test, and External Generalization.
Generates structured diagnostic metrics, error taxonomy distributions, and writes:
  - results/phase1_1/split_diagnostics.json
  - results/phase1_1/error_breakdown.json
"""

import os
import sys
import re
import json
import numpy as np
from typing import Dict, List, Any, Tuple, Set

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import CURATED_REAL_PAPERS, convert_pmc_oa_to_scientific_document
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evaluate_phase2_splits import match_edge, bootstrap_ci


def run_diagnostics():
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    evaluator = PaperBenchmarkEvaluator()
    ingester = PMCOAIngester()
    biocause = BioCauseDataset()
    curated_map = {p["pmcid"]: p for p in CURATED_REAL_PAPERS}

    split_groups = {
        "train": [p for p in manifest["papers"] if p["split"] == "train"],
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
        "external": [p for p in manifest["papers"] if p["split"] == "external"],
    }

    results = {
        "timestamp": "2026-10-24T02:00:00Z",
        "description": "EVRYN Phase 1.1 Diagnostic Audit across 20 authentic PMC papers",
        "splits": {},
        "taxonomy_summary": {},
    }

    taxonomy_counts = {
        "gt_xml_mismatch": 0,
        "entity_normalization_gap": 0,
        "direction_reversal": 0,
        "duplicate_assertion_inflation": 0,
        "missing_transitive_bridge": 0,
        "filter_fallback_explosion": 0,
        "spurious_cooccurrence": 0,
    }

    for split_name, papers in split_groups.items():
        direct_f1s = []
        cross_f1s = []
        sms = []
        per_paper_data = []

        total_tp_d, total_fp_d, total_fn_d = 0, 0, 0
        total_tp_c, total_fp_c, total_fn_c = 0, 0, 0

        for paper in papers:
            pmcid = paper["pmcid"]
            xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
            with open(xml_path, "r", encoding="utf-8") as f:
                pmc_doc = ingester.parse_xml(f.read(), pmcid)
            doc = convert_pmc_oa_to_scientific_document(pmc_doc)

            spec = curated_map.get(pmcid, {})
            gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
            gt_cross = [tuple(x) for x in spec.get("cross_page_edges", [])]
            canon_entities = spec.get("canonical_entities", [])

            # Check if canonical entities actually exist in doc full text
            full_text_lower = doc.full_text.lower()
            present_entities = [e for e in canon_entities if e.lower() in full_text_lower]
            entity_coverage = len(present_entities) / len(canon_entities) if canon_entities else 0.0

            is_gt_mismatch = entity_coverage < 0.2
            if is_gt_mismatch:
                taxonomy_counts["gt_xml_mismatch"] += 1

            raw_assertions = evaluator.extractor.extract_assertions(
                doc, known_entities=canon_entities if canon_entities else None
            )
            clean_assertions = [a for a in raw_assertions if not a.is_negated]
            
            c_set = set(canon_entities) if canon_entities else set()
            filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
            
            fell_back_unfiltered = False
            if len(filt) >= 2:
                eval_assertions = filt
            else:
                eval_assertions = clean_assertions
                if canon_entities and len(clean_assertions) > len(filt):
                    fell_back_unfiltered = True
                    taxonomy_counts["filter_fallback_explosion"] += 1

            pred_direct = [(a.cause_canonical, a.effect_canonical) for a in eval_assertions]
            cross_links = evaluator.linker.find_cross_page_links(eval_assertions)
            pred_cross = [(l.source_entity, l.target_entity) for l in cross_links if l.distance_pages >= 1]

            # Check duplicate inflation
            unique_direct = list(set(pred_direct))
            dup_direct_count = len(pred_direct) - len(unique_direct)
            if dup_direct_count > 3:
                taxonomy_counts["duplicate_assertion_inflation"] += 1

            # Direct evaluation
            tp_d = 0
            matched_gt_d = set()
            direction_reversals = 0
            for p_c, p_e in pred_direct:
                for idx, (g_c, g_e) in enumerate(gt_direct):
                    if idx not in matched_gt_d and match_edge(p_c, p_e, g_c, g_e):
                        tp_d += 1
                        matched_gt_d.add(idx)
                        break
                    elif match_edge(p_e, p_c, g_c, g_e):
                        direction_reversals += 1

            if direction_reversals > 0:
                taxonomy_counts["direction_reversal"] += 1

            fp_d = max(0, len(pred_direct) - tp_d)
            fn_d = max(0, len(gt_direct) - tp_d)
            p_d = tp_d / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
            r_d = tp_d / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
            f1_d = (2 * p_d * r_d) / (p_d + r_d) if (p_d + r_d) > 0 else 0.0

            # Cross evaluation
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

            if len(gt_cross) > 0 and len(pred_cross) == 0:
                taxonomy_counts["missing_transitive_bridge"] += 1

            total_matched = tp_d + tp_c
            total_possible = len(pred_direct) + len(pred_cross) + len(gt_direct) + len(gt_cross) - total_matched
            sm = total_matched / total_possible if total_possible > 0 else 1.0

            total_tp_d += tp_d
            total_fp_d += fp_d
            total_fn_d += fn_d
            total_tp_c += tp_c
            total_fp_c += fp_c
            total_fn_c += fn_c

            direct_f1s.append(f1_d)
            cross_f1s.append(f1_c)
            sms.append(sm)

            per_paper_data.append({
                "pmcid": pmcid,
                "title": paper["title"],
                "entity_coverage": round(entity_coverage, 4),
                "is_gt_mismatch": is_gt_mismatch,
                "fell_back_unfiltered": fell_back_unfiltered,
                "gold_direct": len(gt_direct),
                "gold_cross": len(gt_cross),
                "pred_direct": len(pred_direct),
                "pred_direct_unique": len(unique_direct),
                "pred_cross": len(pred_cross),
                "tp_direct": tp_d,
                "fp_direct": fp_d,
                "fn_direct": fn_d,
                "direct_f1": round(f1_d, 4),
                "direct_p": round(p_d, 4),
                "direct_r": round(r_d, 4),
                "tp_cross": tp_c,
                "fp_cross": fp_c,
                "fn_cross": fn_c,
                "cross_f1": round(f1_c, 4),
                "structural_match": round(sm, 4),
                "direction_reversals": direction_reversals,
                "sample_direct_preds": pred_direct[:5],
                "sample_cross_preds": pred_cross[:5],
            })

        m_d, d_ci_l, d_ci_u = bootstrap_ci(direct_f1s)
        m_c, c_ci_l, c_ci_u = bootstrap_ci(cross_f1s)
        m_sm, sm_ci_l, sm_ci_u = bootstrap_ci(sms)

        results["splits"][split_name] = {
            "paper_count": len(papers),
            "macro_metrics": {
                "direct_f1_mean": round(m_d, 4),
                "direct_f1_ci": [round(d_ci_l, 4), round(d_ci_u, 4)],
                "cross_f1_mean": round(m_c, 4),
                "cross_f1_ci": [round(c_ci_l, 4), round(c_ci_u, 4)],
                "structural_match_mean": round(m_sm, 4),
                "structural_match_ci": [round(sm_ci_l, 4), round(sm_ci_u, 4)],
            },
            "micro_metrics": {
                "direct": {
                    "tp": total_tp_d,
                    "fp": total_fp_d,
                    "fn": total_fn_d,
                    "precision": round(total_tp_d / (total_tp_d + total_fp_d), 4) if (total_tp_d + total_fp_d) > 0 else 0.0,
                    "recall": round(total_tp_d / (total_tp_d + total_fn_d), 4) if (total_tp_d + total_fn_d) > 0 else 0.0,
                    "f1": round((2 * total_tp_d) / (2 * total_tp_d + total_fp_d + total_fn_d), 4) if (2 * total_tp_d + total_fp_d + total_fn_d) > 0 else 0.0,
                },
                "cross": {
                    "tp": total_tp_c,
                    "fp": total_fp_c,
                    "fn": total_fn_c,
                    "precision": round(total_tp_c / (total_tp_c + total_fp_c), 4) if (total_tp_c + total_fp_c) > 0 else 0.0,
                    "recall": round(total_tp_c / (total_tp_c + total_fn_c), 4) if (total_tp_c + total_fn_c) > 0 else 0.0,
                    "f1": round((2 * total_tp_c) / (2 * total_tp_c + total_fp_c + total_fn_c), 4) if (2 * total_tp_c + total_fp_c + total_fn_c) > 0 else 0.0,
                },
            },
            "papers": per_paper_data,
        }

    results["taxonomy_summary"] = taxonomy_counts

    out_dir = os.path.join(REPO_ROOT, "results", "phase1_1")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "split_diagnostics.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Diagnostics written to {out_file}")
    return results


if __name__ == "__main__":
    run_diagnostics()
