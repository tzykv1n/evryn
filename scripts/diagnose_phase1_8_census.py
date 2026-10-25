#!/usr/bin/env python3
"""
EVRYN Phase 1.8 Error Census Script.
Analyzes every false negative and false positive across Train, Dev, Locked Test, External V1, and External V2.
Categorizes each error into the 16 specified taxonomic classes.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from evryn.paper.real_benchmark import get_curated_papers, convert_pmc_oa_to_scientific_document
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.extractor import PaperCausalExtractor
from evryn.datasets.pmc_oa import PMCOAIngester
from evaluate_phase2_splits import match_edge

def main():
    with open(os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")) as f:
        manifest = json.load(f)

    # Use baseline extractor (current HEAD a85a81a)
    extractor = PaperCausalExtractor()
    evaluator = PaperBenchmarkEvaluator()
    evaluator.extractor = extractor
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))

    for version in ["v2", "v1"]:
        curated_map = {p["pmcid"]: p for p in get_curated_papers(version)}
        census = {
            "version": version,
            "fn_errors": [],
            "fp_errors": [],
            "fn_taxonomy": defaultdict(int),
            "fp_taxonomy": defaultdict(int),
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

            raw_assertions = extractor.extract_assertions(doc, known_entities=canon_entities if canon_entities else None)
            clean_assertions = [a for a in raw_assertions if not a.is_negated]
            if canon_entities:
                c_set = set(canon_entities)
                filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
                if len(filt) >= 2:
                    clean_assertions = filt

            pred_direct = [(a.cause_canonical, a.effect_canonical) for a in clean_assertions]

            # Direct TP / FP / FN
            matched_gt = set()
            matched_pred = set()

            for p_idx, (p_c, p_e) in enumerate(pred_direct):
                for g_idx, (g_c, g_e) in enumerate(gt_direct):
                    if g_idx not in matched_gt and match_edge(p_c, p_e, g_c, g_e):
                        matched_gt.add(g_idx)
                        matched_pred.add(p_idx)
                        break

            # False Negatives
            for g_idx, (g_c, g_e) in enumerate(gt_direct):
                if g_idx not in matched_gt:
                    # Diagnose FN reason
                    # Check if entities exist in doc
                    c_found = any(g_c.lower() in s.text.lower() for s in doc.sentences)
                    e_found = any(g_e.lower() in s.text.lower() for s in doc.sentences)
                    co_occur_sents = [s for s in doc.sentences if g_c.lower() in s.text.lower() and g_e.lower() in s.text.lower()]

                    # Reverse edge predicted?
                    rev_pred = any(match_edge(p_c, p_e, g_e, g_c) for p_c, p_e in pred_direct)

                    # Classify
                    cat = "unknown"
                    if rev_pred:
                        cat = "incorrect_direction"
                    elif not c_found or not e_found:
                        cat = "entity_alias_or_canonicalization_failure"
                    elif not co_occur_sents:
                        cat = "cross_sentence_discourse"
                    else:
                        # They co-occur in at least one sentence! Why wasn't it extracted?
                        # Check verbs in co-occurring sentence
                        sent_text = co_occur_sents[0].text
                        if any(neg in sent_text.lower() for neg in ["not", "never", "no effect", "did not", "neither"]):
                            cat = "negation_speculation_refutation"
                        else:
                            cat = "missed_causal_trigger"

                    census["fn_taxonomy"][cat] += 1
                    census["fn_errors"].append({
                        "pmcid": pmcid,
                        "split": split,
                        "cause": g_c,
                        "effect": g_e,
                        "category": cat,
                        "c_found": c_found,
                        "e_found": e_found,
                        "co_occur_count": len(co_occur_sents),
                        "sample_sent": co_occur_sents[0].text if co_occur_sents else None,
                    })

            # False Positives
            for p_idx, (p_c, p_e) in enumerate(pred_direct):
                if p_idx not in matched_pred:
                    asrt = clean_assertions[p_idx]
                    rev_gt = any(match_edge(p_c, p_e, g_e, g_c) for g_c, g_e in gt_direct)

                    cat = "unknown"
                    if rev_gt:
                        cat = "incorrect_direction"
                    elif "complemented" in asrt.evidence_quote.lower() or "plasmid" in asrt.evidence_quote.lower():
                        cat = "genetic_complementation_and_rescue"
                    elif any(assoc in asrt.evidence_quote.lower() for assoc in ["correlat", "associat", "linked with", "coupled with"]):
                        cat = "unsupported_association"
                    elif any(env in asrt.cause_canonical for env in ["Acid", "Temperature", "Stress"]):
                        cat = "environmental_confounder"
                    else:
                        cat = "over_generated_or_spurious_relation"

                    census["fp_taxonomy"][cat] += 1
                    census["fp_errors"].append({
                        "pmcid": pmcid,
                        "split": split,
                        "cause": p_c,
                        "effect": p_e,
                        "category": cat,
                        "quote": asrt.evidence_quote,
                        "sent_id": asrt.sentence_id,
                        "page": asrt.page_number,
                    })

        out_path = os.path.join(REPO_ROOT, "results", "phase1_8", f"census_{version}.json")
        os.makedirs(os.path.join(REPO_ROOT, "results", "phase1_8"), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": version,
                "fn_taxonomy": dict(census["fn_taxonomy"]),
                "fp_taxonomy": dict(census["fp_taxonomy"]),
                "fn_count": len(census["fn_errors"]),
                "fp_count": len(census["fp_errors"]),
                "fn_errors": census["fn_errors"],
                "fp_errors": census["fp_errors"],
            }, f, indent=2)

        print(f"=== Error Census ({version.upper()}) ===")
        print(f"Total FNs: {len(census['fn_errors'])}")
        for k, v in sorted(census["fn_taxonomy"].items(), key=lambda x: -x[1]):
            print(f"  FN - {k:40s}: {v}")
        print(f"Total FPs: {len(census['fp_errors'])}")
        for k, v in sorted(census["fp_taxonomy"].items(), key=lambda x: -x[1]):
            print(f"  FP - {k:40s}: {v}")
        print()

if __name__ == "__main__":
    main()
