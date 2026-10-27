#!/usr/bin/env python3
import os
import sys
import re
import json

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)

from evryn.paper.real_benchmark import get_curated_papers, convert_pmc_oa_to_scientific_document
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker

def match_edge(p_c: str, p_e: str, g_c: str, g_e: str) -> bool:
    p_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_c).strip().lower()
    p_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_e).strip().lower()
    g_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_c).strip().lower()
    g_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_e).strip().lower()
    if not p_c_n or not p_e_n or not g_c_n or not g_e_n:
        return False
    return (p_c_n in g_c_n or g_c_n in p_c_n) and (p_e_n in g_e_n or g_e_n in p_e_n)

def audit_paper(pmcid: str):
    ingester = PMCOAIngester()
    curated = get_curated_papers()
    curated_map = {p["pmcid"]: p for p in curated}

    xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
    if not os.path.exists(xml_path):
        print(f"Paper XML for {pmcid} not found at {xml_path}")
        return

    with open(xml_path, "r", encoding="utf-8") as f:
        pmc_doc = ingester.parse_xml(f.read(), pmcid)
    doc = convert_pmc_oa_to_scientific_document(pmc_doc)
    c_spec = curated_map.get(pmcid, {})

    from evryn.nlp.llm import get_extraction_backend
    extractor = get_extraction_backend("nlp_baseline")
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.60)

    gt_direct = [tuple(x) for x in c_spec.get("direct_edges", [])]
    gt_cross = [tuple(x) for x in c_spec.get("cross_page_edges", [])]
    canon_entities = c_spec.get("canonical_entities", [])

    raw_assertions = extractor.extract_assertions(doc, known_entities=canon_entities)
    clean_assertions = [a for a in raw_assertions if not a.is_negated]
    if canon_entities:
        c_set = set(canon_entities)
        filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
        if len(filt) >= 2:
            clean_assertions = filt

    print(f"==================================================================")
    print(f"AUDIT FOR PAPER: {pmcid} - {doc.metadata.title}")
    print(f"Gold Direct: {len(gt_direct)} | Gold Cross: {len(gt_cross)}")
    print(f"Predicted Direct: {len(clean_assertions)}")
    print(f"==================================================================")

    matched_gt = set()
    adjudications = []

    for idx, a in enumerate(clean_assertions):
        is_match = False
        matched_gold_edge = None
        for g_idx, (g_c, g_e) in enumerate(gt_direct):
            if g_idx not in matched_gt and match_edge(a.cause_canonical, a.effect_canonical, g_c, g_e):
                is_match = True
                matched_gold_edge = (g_c, g_e)
                matched_gt.add(g_idx)
                break

        print(f"\n[Pred #{idx+1}] {a.cause_canonical} -> {a.effect_canonical}")
        print(f"  Type: {a.relation_type.value} | Negated: {a.is_negated} | Page: {a.page_number} | Conf: {a.confidence:.2f}")
        print(f"  Quote: \"{a.evidence_quote.strip()}\"")
        print(f"  Gold Match: {is_match} {matched_gold_edge if is_match else ''}")

    print("\n--- Missed Gold Direct Edges ---")
    for g_idx, g_edge in enumerate(gt_direct):
        if g_idx not in matched_gt:
            print(f"  Missed: {g_edge}")

    cross_links = linker.find_cross_page_links(clean_assertions)
    pred_cross = [(l.source_entity, l.target_entity, l) for l in cross_links if l.distance_pages >= 1]
    print(f"\n==================================================================")
    print(f"CROSS-PAGE INFERRED RELATIONS ({len(pred_cross)} total)")
    print(f"==================================================================")
    matched_cross = set()
    for idx, (p_c, p_e, l) in enumerate(pred_cross):
        is_match = False
        matched_gold_edge = None
        for g_idx, (g_c, g_e) in enumerate(gt_cross):
            if g_idx not in matched_cross and match_edge(p_c, p_e, g_c, g_e):
                is_match = True
                matched_gold_edge = (g_c, g_e)
                matched_cross.add(g_idx)
                break
        hop_str = f"{p_c} -> {l.intermediate_entity} -> {p_e}"
        print(f"\n[Cross #{idx+1}] {p_c} -> {p_e} (Gold Match: {is_match} {matched_gold_edge if is_match else ''})")
        print(f"  Pages: {l.cause_page} -> {l.effect_page} (dist={l.distance_pages}) | Confidence: {l.confidence:.2f}")
        print(f"  Chain: {hop_str}")
        print(f"  Mechanism: \"{l.linking_mechanism}\"")

if __name__ == "__main__":
    pmcid = sys.argv[1] if len(sys.argv) > 1 else "PMC1804205"
    audit_paper(pmcid)
