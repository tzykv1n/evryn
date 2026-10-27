#!/usr/bin/env python3
"""
Detailed Relation-by-Relation Audit for PMC1804205 (Perez & Groisman, 2007).
Audits all 12 relations specified in EVRYN Phase 2.6 Objective B:
  Matched:
    1. Acid pH -> PmrA
    2. PmrB -> PmrA
  Unmatched (candidate omissions / FPs):
    3. PmrA -> Polymyxin B
    4. PmrD -> PmrA
  Missed direct gold:
    5. Acid pH -> PmrB
    6. PmrA -> PmrD
    7. PmrA -> Lipopolysaccharide
    8. Lipopolysaccharide -> Polymyxin B
  Missed cross-page gold:
    9. Acid pH -> PmrD
    10. PmrB -> Lipopolysaccharide
    11. PmrB -> Polymyxin B
    12. Acid pH -> Polymyxin B
"""

import sys
import os
import re
import json

REPO_ROOT = "/home/tk/projects/evryn"
sys.path.insert(0, REPO_ROOT)

from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.paper.real_benchmark import convert_pmc_oa_to_scientific_document
from evryn.paper.extractor import PaperCausalExtractor, CausalRelationType
from evryn.paper.cross_page_linker import CrossPageLinker


def run_relation_audit():
    ingester = PMCOAIngester()
    with open("data/real_papers/xml/PMC1804205.xml", "r", encoding="utf-8") as f:
        doc = convert_pmc_oa_to_scientific_document(ingester.parse_xml(f.read(), "PMC1804205"))

    with open("data/real_papers/PMC1804205_ground_truth.json", "r") as f:
        gt = json.load(f)

    gt_direct = [tuple(x) for x in gt["direct_edges"]]
    gt_cross = [tuple(x) for x in gt["cross_page_edges"]]

    extractor = PaperCausalExtractor()
    raw_assertions = extractor.extract_assertions(doc, known_entities=gt["canonical_entities"])
    clean_assertions = [a for a in raw_assertions if not a.is_negated]
    c_set = set(gt["canonical_entities"])
    filt_assertions = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]

    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.60)
    cross_links = linker.find_cross_page_links(filt_assertions)
    cross_links = [l for l in cross_links if l.distance_pages >= 1]

    print("=" * 80)
    print("RELATION AUDIT TABLE FOR PMC1804205")
    print("=" * 80)

    # Search for all relevant text spans in document sentences
    target_relations = [
        ("Acid pH", "PmrA"),
        ("PmrB", "PmrA"),
        ("PmrA", "Polymyxin B"),
        ("PmrD", "PmrA"),
        ("Acid pH", "PmrB"),
        ("PmrA", "PmrD"),
        ("PmrA", "Lipopolysaccharide"),
        ("Lipopolysaccharide", "Polymyxin B"),
        ("Acid pH", "PmrD"),
        ("PmrB", "Lipopolysaccharide"),
        ("PmrB", "Polymyxin B"),
        ("Acid pH", "Polymyxin B"),
    ]

    for c, e in target_relations:
        is_direct_gold = (c, e) in gt_direct
        is_cross_gold = (c, e) in gt_cross

        pred_direct = [a for a in filt_assertions if a.cause_canonical == c and a.effect_canonical == e]
        pred_cross = [l for l in cross_links if l.source_entity == c and l.target_entity == e]

        print(f"\n>>> RELATION: {c} -> {e}")
        print(f"    Gold Status: {'DIRECT GOLD' if is_direct_gold else ('CROSS-PAGE GOLD' if is_cross_gold else 'NOT IN GOLD')}")
        print(f"    Extracted Direct: {len(pred_direct)} instances | Extracted Cross: {len(pred_cross)} instances")

        if pred_direct:
            for d in pred_direct:
                print(f"    - Extracted Direct (P{d.page_number}, {d.section_title}): \"{d.evidence_quote[:120]}...\" [Conf: {d.confidence}, Type: {d.relation_type}]")

        if pred_cross:
            for l in pred_cross:
                print(f"    - Extracted Cross (P{l.cause_page} -> P{l.effect_page}): via [{l.intermediate_entity}] [Conf: {l.confidence}]")

        # Find supporting sentences in document
        supporting_sentences = []
        c_pat = re.escape(c)
        e_pat = re.escape(e)
        if c == "Acid pH":
            c_pat = r"acid|pH|5\.8"
        if e == "Acid pH":
            e_pat = r"acid|pH|5\.8"
        if c == "Lipopolysaccharide":
            c_pat = r"lipopolysaccharide|LPS"
        if e == "Lipopolysaccharide":
            e_pat = r"lipopolysaccharide|LPS"
        if c == "Polymyxin B":
            c_pat = r"polymyxin|antimicrobial peptide"
        if e == "Polymyxin B":
            e_pat = r"polymyxin|antimicrobial peptide"

        for sent in doc.sentences:
            if re.search(c_pat, sent.text, re.IGNORECASE) and re.search(e_pat, sent.text, re.IGNORECASE):
                supporting_sentences.append((sent.page_number, sent.section_title, sent.text.strip()))

        print(f"    Text Co-occurrences in Full Paper: {len(supporting_sentences)}")
        for p, sec, txt in supporting_sentences[:2]:
            print(f"      [P{p} - {sec}]: \"{txt[:140]}...\"")


if __name__ == "__main__":
    run_relation_audit()
