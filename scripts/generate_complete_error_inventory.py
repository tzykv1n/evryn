#!/usr/bin/env python3
"""
Generate complete post-fix error inventory for EVRYN Phase 1.6.
Analyzes all false negatives and false positives across Train, Dev, Locked Test, and External splits.
"""
import os
import sys
import json
import re
from typing import Dict, List, Any, Tuple, Set

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import get_curated_papers, convert_pmc_oa_to_scientific_document
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.datasets.pmc_oa import PMCOAIngester
from evaluate_phase2_splits import match_edge

def main():
    with open(os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")) as f:
        manifest = json.load(f)

    evaluator = PaperBenchmarkEvaluator()
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    
    # We audit both V1 and V2, prioritizing V2 authenticated
    for version in ["v2", "v1"]:
        curated_map = {p["pmcid"]: p for p in get_curated_papers(version)}
        all_errors = {
            "version": version,
            "false_negatives": [],
            "false_positives": []
        }

        for p_meta in manifest["papers"]:
            pmcid = p_meta["pmcid"]
            split = p_meta["split"]
            spec = curated_map[pmcid]
            xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
            with open(xml_path, "r", encoding="utf-8") as f:
                pmc_doc = ingester.parse_xml(f.read(), pmcid)
            doc = convert_pmc_oa_to_scientific_document(pmc_doc)

            gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
            gt_cross = [tuple(x) for x in spec.get("cross_page_edges", [])]
            canon_entities = spec.get("canonical_entities", [])

            raw_assertions = evaluator.extractor.extract_assertions(doc, known_entities=canon_entities if canon_entities else None)
            clean_assertions = [a for a in raw_assertions if not a.is_negated]
            if canon_entities:
                c_set = set(canon_entities)
                filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
                if len(filt) >= 2:
                    clean_assertions = filt

            seen_pred = set()
            pred_edges = []
            for a in clean_assertions:
                edge = (a.cause_canonical, a.effect_canonical)
                if edge not in seen_pred:
                    seen_pred.add(edge)
                    pred_edges.append(a)

            matched_pred_indices = set()
            for gc, ge in gt_direct:
                matched = False
                matched_pred = None
                for idx, a in enumerate(pred_edges):
                    if match_edge(a.cause_canonical, a.effect_canonical, gc, ge):
                        matched = True
                        matched_pred_indices.add(idx)
                        matched_pred = a
                        break
                
                if not matched:
                    cand_sents = []
                    for s in doc.sentences:
                        s_low = s.text.lower()
                        if gc.lower() in s_low and ge.lower() in s_low:
                            cand_sents.append(s.text.strip())
                    
                    root_cause = "relation_triggering"
                    is_direct = bool(cand_sents)
                    evidence_type = "direct" if cand_sents else "indirect"
                    
                    if not cand_sents:
                        root_cause = "cross_sentence_discourse"
                    elif any("not" in s.lower() or "did not" in s.lower() for s in cand_sents):
                        evidence_type = "negated"
                    elif any(w in s_low for w in ["suggest", "indicate", "hypothesize", "speculate"] for s_low in [s.lower() for s in cand_sents]):
                        evidence_type = "speculative"

                    all_errors["false_negatives"].append({
                        "pmcid": pmcid,
                        "split": split,
                        "version": version,
                        "gold_source": gc,
                        "gold_target": ge,
                        "relation_label": "DIRECT_CAUSE",
                        "evidence_sentences": cand_sents[:2],
                        "evidence_type": evidence_type,
                        "failure_category": root_cause,
                        "error_origin": "extraction_failure" if cand_sents else "annotation_granularity"
                    })

            for idx, a in enumerate(pred_edges):
                if idx not in matched_pred_indices:
                    pc = a.cause_canonical
                    pe = a.effect_canonical
                    
                    in_cross = any(match_edge(pc, pe, gc, ge) for gc, ge in gt_cross)
                    is_rev_direct = any(match_edge(pe, pc, gc, ge) for gc, ge in gt_direct)
                    is_rev_cross = any(match_edge(pe, pc, gc, ge) for gc, ge in gt_cross)

                    if in_cross:
                        fp_cat = "cross_page_gold_predicted_direct"
                        err_orig = "annotation_granularity_direct_vs_cross"
                    elif is_rev_direct or is_rev_cross:
                        fp_cat = "direction_reversal"
                        err_orig = "extraction_failure"
                    else:
                        fp_cat = "spurious_or_unsupported"
                        err_orig = "extraction_failure"

                    all_errors["false_positives"].append({
                        "pmcid": pmcid,
                        "split": split,
                        "version": version,
                        "predicted_source": pc,
                        "predicted_target": pe,
                        "relation_label": a.relation_type.value,
                        "confidence": a.confidence,
                        "evidence_quote": a.evidence_quote,
                        "evidence_type": "direct",
                        "failure_category": fp_cat,
                        "error_origin": err_orig
                    })

        os.makedirs(os.path.join(REPO_ROOT, "results", "phase1_6"), exist_ok=True)
        out_path = os.path.join(REPO_ROOT, "results", "phase1_6", f"error_inventory_{version}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_errors, f, indent=2)
        print(f"Saved {len(all_errors['false_negatives'])} FNs and {len(all_errors['false_positives'])} FPs to {out_path}")

if __name__ == "__main__":
    main()
