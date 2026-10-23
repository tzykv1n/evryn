"""
Development-Only Error Analysis Script (8 Dev Papers Only).
Strictly analyzes Dev papers (PMC1804205, PMC1874608, PMC1913099, PMC1974823,
PMC2242835, PMC2266911, PMC2358977, PMC2430206).
Never inspects or uses Locked-Test or External-Test papers.
"""

import os
import json
import re
from typing import Dict, List, Any, Tuple, Set

from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.real_benchmark import build_real_paper_benchmark, CURATED_REAL_PAPERS
from evryn.paper.types import ScientificDocument
from evryn.datasets.biocause import BioCauseDataset

DEV_PMCIDS = [
    "PMC1804205",
    "PMC1874608",
    "PMC1913099",
    "PMC1974823",
    "PMC2242835",
    "PMC2266911",
    "PMC2358977",
    "PMC2430206",
]


def classify_fp_error(pred_edge: Tuple[str, str], doc: ScientificDocument, gt_edges: Set[Tuple[str, str]], all_gt_edges: Set[Tuple[str, str]]) -> str:
    cause, effect = pred_edge
    # 1. Direction error: reverse is in GT
    if (effect, cause) in gt_edges or (effect, cause) in all_gt_edges:
        return "direction_inverted"
    
    # 2. Transitive jump: cause -> intermediate -> effect in GT
    for (c1, e1) in gt_edges:
        if c1 == cause:
            for (c2, e2) in gt_edges:
                if c2 == e1 and e2 == effect:
                    return "transitive_jump"

    # Find sentences mentioning both
    cause_low = cause.lower()
    effect_low = effect.lower()
    matching_sents = [s for s in doc.sentences if cause_low in s.text.lower() and effect_low in s.text.lower()]
    
    if not matching_sents:
        # Cross-sentence or cross-page
        return "cross_page_bridge_spurious"
    
    sent_text = matching_sents[0].text.lower()
    
    # Check for association keywords
    if any(w in sent_text for w in ["correlat", "associat", "parallel", "coincid"]):
        return "association_not_causal"
    
    # Check for speculative/hedging keywords
    if any(w in sent_text for w in ["might", "may", "could", "perhaps", "possibly", "hypothesi"]):
        return "speculative_assertion"
        
    # Check for negation keywords
    if any(w in sent_text for w in ["not ", "never", "failed to", "no ", "neither"]):
        return "negation_leakage"
        
    return "unsupported_hallucination"


def classify_fn_error(gt_edge: Tuple[str, str], doc: ScientificDocument, pred_edges: Set[Tuple[str, str]], raw_assertions: List[Any]) -> str:
    cause, effect = gt_edge
    cause_low = cause.lower()
    effect_low = effect.lower()

    # Did we extract with reverse direction?
    if (effect, cause) in pred_edges:
        return "direction_inverted"

    # Check if raw assertion extracted it but it was filtered or negated
    for a in raw_assertions:
        if (a.cause_canonical.lower() == cause_low and a.effect_canonical.lower() == effect_low) or \
           (cause_low in a.cause.lower() and effect_low in a.effect.lower()):
            if a.is_negated:
                return "negation_overfilter"
            return "confidence_or_filter_loss"

    # Did both entities appear in the same sentence?
    cooccurring_sents = [s for s in doc.sentences if cause_low in s.text.lower() and effect_low in s.text.lower()]
    if cooccurring_sents:
        # Both appear together in a sentence but no edge was extracted
        sent = cooccurring_sents[0].text.lower()
        # Check if passive/implicit
        if any(w in sent for w in ["in response to", "upon", "following", "dependent", "downstream"]):
            return "implicit_or_passive_construction"
        if any(w in sent for w in ["which", "that", "whose", "it", "this", "these"]):
            return "coreference_or_complex_syntax"
        return "unrecognized_trigger"
    else:
        # Do entities appear in different sentences of the same section?
        sents_cause = [s for s in doc.sentences if cause_low in s.text.lower()]
        sents_effect = [s for s in doc.sentences if effect_low in s.text.lower()]
        if sents_cause and sents_effect:
            # Check if across pages or sentences
            pages_c = {s.page_number for s in sents_cause}
            pages_e = {s.page_number for s in sents_effect}
            if pages_c.intersection(pages_e):
                return "cross_sentence_intra_page"
            else:
                return "cross_page_bridge_missed"
        return "argument_span_or_vocabulary_mismatch"


def analyze_dev_split(repo_root: str = "."):
    docs, gts = build_real_paper_benchmark(target_dir=os.path.join(repo_root, "data", "real_papers"))
    evaluator = PaperBenchmarkEvaluator()

    dev_docs = [d for d in docs if d.doc_id in DEV_PMCIDS]
    dev_gts = [g for g in gts if g["pmcid"] in DEV_PMCIDS]

    fp_counts: Dict[str, int] = {}
    fn_counts: Dict[str, int] = {}
    detailed_cases: List[Dict[str, Any]] = []

    per_paper_stats: List[Dict[str, Any]] = []

    for doc, gt in zip(dev_docs, dev_gts):
        pmcid = doc.doc_id
        gt_direct = set(tuple(x) for x in gt.get("direct_edges", []))
        gt_cross = set(tuple(x) for x in gt.get("cross_page_edges", []))
        all_gt = gt_direct.union(gt_cross)
        canonical_entities = gt.get("canonical_entities", [])

        # Run model extraction
        raw_assertions = evaluator.extractor.extract_assertions(doc, known_entities=canonical_entities)
        clean_assertions = [
            a for a in raw_assertions
            if a.cause_canonical in canonical_entities and a.effect_canonical in canonical_entities
        ]
        cross_links = evaluator.linker.find_cross_page_links(clean_assertions)
        graph = evaluator.builder.build_graph(doc.doc_id, doc.metadata.title, clean_assertions, cross_links)

        pred_direct = set()
        for e in graph.edges:
            if e.get("is_direct", False) and not e.get("is_negated", False):
                pred_direct.add((e["source"], e["target"]))

        pred_cross = set()
        for l in cross_links:
            if l.distance_pages >= 1:
                pred_cross.add((l.source_entity, l.target_entity))

        pred_all = pred_direct.union(pred_cross)

        tp_direct = pred_direct.intersection(gt_direct)
        fp_direct = pred_direct - gt_direct
        fn_direct = gt_direct - pred_direct

        tp_cross = pred_cross.intersection(gt_cross)
        fp_cross = pred_cross - gt_cross
        fn_cross = gt_cross - pred_cross

        prec_d, rec_d, f1_d = evaluator._calc_prf(pred_direct, gt_direct)
        prec_c, rec_c, f1_c = evaluator._calc_prf(pred_cross, gt_cross)

        # Categorize FPs
        paper_fps = []
        for fp in fp_direct:
            cat = classify_fp_error(fp, doc, gt_direct, all_gt)
            fp_counts[cat] = fp_counts.get(cat, 0) + 1
            paper_fps.append({"edge": fp, "category": cat, "type": "direct"})

        for fp in fp_cross:
            cat = classify_fp_error(fp, doc, gt_cross, all_gt)
            fp_counts[cat] = fp_counts.get(cat, 0) + 1
            paper_fps.append({"edge": fp, "category": cat, "type": "cross_page"})

        # Categorize FNs
        paper_fns = []
        for fn in fn_direct:
            cat = classify_fn_error(fn, doc, pred_direct, raw_assertions)
            fn_counts[cat] = fn_counts.get(cat, 0) + 1
            paper_fns.append({"edge": fn, "category": cat, "type": "direct"})

        for fn in fn_cross:
            cat = classify_fn_error(fn, doc, pred_cross, raw_assertions)
            fn_counts[cat] = fn_counts.get(cat, 0) + 1
            paper_fns.append({"edge": fn, "category": cat, "type": "cross_page"})

        per_paper_stats.append({
            "pmcid": pmcid,
            "title": gt.get("title", ""),
            "gold_direct_count": len(gt_direct),
            "gold_cross_count": len(gt_cross),
            "pred_direct_count": len(pred_direct),
            "pred_cross_count": len(pred_cross),
            "tp_direct": len(tp_direct),
            "fp_direct": len(fp_direct),
            "fn_direct": len(fn_direct),
            "direct_f1": round(f1_d, 4),
            "tp_cross": len(tp_cross),
            "fp_cross": len(fp_cross),
            "fn_cross": len(fn_cross),
            "cross_f1": round(f1_c, 4),
            "false_positives": paper_fps,
            "false_negatives": paper_fns,
        })

    total_fps = sum(fp_counts.values())
    total_fns = sum(fn_counts.values())

    analysis_result = {
        "analysis_version": "2.1.0",
        "split_evaluated": "development_only",
        "dev_papers_count": len(DEV_PMCIDS),
        "total_false_positives": total_fps,
        "total_false_negatives": total_fns,
        "fp_category_breakdown": {
            k: {"count": v, "pct": round(v / max(1, total_fps) * 100, 2)}
            for k, v in sorted(fp_counts.items(), key=lambda x: -x[1])
        },
        "fn_category_breakdown": {
            k: {"count": v, "pct": round(v / max(1, total_fns) * 100, 2)}
            for k, v in sorted(fn_counts.items(), key=lambda x: -x[1])
        },
        "per_paper_stats": per_paper_stats,
    }

    out_file = os.path.join(repo_root, "results", "phase2_1", "dev_error_analysis.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2)

    print(f"Dev Error Analysis saved to {out_file}")
    print("\n--- FALSE POSITIVE DISTRIBUTION ---")
    for cat, data in analysis_result["fp_category_breakdown"].items():
        print(f"  {cat}: {data['count']} ({data['pct']}%)")

    print("\n--- FALSE NEGATIVE DISTRIBUTION ---")
    for cat, data in analysis_result["fn_category_breakdown"].items():
        print(f"  {cat}: {data['count']} ({data['pct']}%)")

    return analysis_result


if __name__ == "__main__":
    analyze_dev_split()
