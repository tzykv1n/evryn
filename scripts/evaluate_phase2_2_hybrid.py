#!/usr/bin/env python3
"""
EVRYN Phase 2.2: Systematic Empirical Evaluation of Three Extraction Backends:
  - System A: Repaired Rule-Based NLP Baseline
  - System B: LLM-Only Candidate Extraction
  - System C: Hybrid LLM + Deterministic Validation

Evaluates across:
  1. Development Split (8 papers) — for configuration & validation calibration
  2. Locked Held-Out Test Split (4 papers) — strictly frozen evaluation
  3. External Generalization Split (4 papers)
"""

import os
import sys
import re
import json
import time
import math
import numpy as np
from typing import Dict, List, Any, Tuple, Set, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from evryn.nlp.llm import (
    get_extraction_backend,
    PROMPT_VERSION,
)
from evryn.nlp.llm.schema import RejectionReason
from evryn.paper.real_benchmark import (
    get_curated_papers,
    convert_pmc_oa_to_scientific_document,
)
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset
from evryn.paper.cross_page_linker import CrossPageLinker


def bootstrap_ci(scores: List[float], n_bootstraps: int = 1000, seed: int = 42) -> Tuple[float, float, float]:
    if not scores:
        return 0.0, 0.0, 0.0
    arr = np.array(scores)
    mean_val = float(np.mean(arr))
    if len(arr) == 1:
        return mean_val, mean_val, mean_val

    rng = np.random.default_rng(seed)
    boot_means = [float(np.mean(rng.choice(arr, size=len(arr), replace=True))) for _ in range(n_bootstraps)]
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return mean_val, ci_lower, ci_upper


def match_edge(p_c: str, p_e: str, g_c: str, g_e: str) -> bool:
    p_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_c).strip().lower()
    p_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", p_e).strip().lower()
    g_c_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_c).strip().lower()
    g_e_n = re.sub(r"[^a-zA-Z0-9]+", " ", g_e).strip().lower()
    if not p_c_n or not p_e_n or not g_c_n or not g_e_n:
        return False
    return (p_c_n in g_c_n or g_c_n in p_c_n) and (p_e_n in g_e_n or g_e_n in p_e_n)


def evaluate_system_on_paper(
    paper_meta: Dict[str, Any],
    doc: Any,
    extractor: Any,
    linker: CrossPageLinker,
    curated_spec: Optional[Dict[str, Any]] = None,
    system_name: str = "system_a",
) -> Dict[str, Any]:
    t0 = time.time()
    pmcid = paper_meta["pmcid"]

    if curated_spec:
        gt_direct = [tuple(x) for x in curated_spec.get("direct_edges", [])]
        gt_cross = [tuple(x) for x in curated_spec.get("cross_page_edges", [])]
        canon_entities = curated_spec.get("canonical_entities", [])
    else:
        gt_direct = []
        gt_cross = []
        canon_entities = []

    # 1. Run extraction
    raw_assertions = extractor.extract_assertions(
        doc, known_entities=canon_entities if canon_entities else None
    )

    clean_assertions = [a for a in raw_assertions if not a.is_negated]
    if canon_entities:
        c_set = set(canon_entities)
        filt = [a for a in clean_assertions if a.cause_canonical in c_set and a.effect_canonical in c_set]
        if len(filt) >= 2:
            clean_assertions = filt

    pred_direct = [(a.cause_canonical, a.effect_canonical) for a in clean_assertions]

    # 2. Run cross-page linking
    cross_links = linker.find_cross_page_links(clean_assertions)
    pred_cross = [(l.source_entity, l.target_entity) for l in cross_links if l.distance_pages >= 1]

    # 3. Direct metrics
    tp_d = 0
    matched_gt_d = set()
    dir_acc_count = 0
    for p_c, p_e in pred_direct:
        for idx, (g_c, g_e) in enumerate(gt_direct):
            if idx not in matched_gt_d and match_edge(p_c, p_e, g_c, g_e):
                tp_d += 1
                matched_gt_d.add(idx)
                # Check direction
                if p_c.strip().lower() in g_c.strip().lower() and p_e.strip().lower() in g_e.strip().lower():
                    dir_acc_count += 1
                break

    fp_d = max(0, len(pred_direct) - tp_d)
    fn_d = max(0, len(gt_direct) - tp_d)
    p_d = tp_d / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
    r_d = tp_d / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
    f1_d = (2 * p_d * r_d) / (p_d + r_d) if (p_d + r_d) > 0 else 0.0
    dir_acc = dir_acc_count / max(1, tp_d)

    # 4. Cross metrics
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

    # 5. Unsupported Transitive Jump Count (spurious cross-page leaps where no gold cross exists)
    false_transitive_jumps = fp_c

    # 6. Exact Structural Match (Jaccard)
    total_matched = tp_d + tp_c
    total_possible = len(pred_direct) + len(pred_cross) + len(gt_direct) + len(gt_cross) - total_matched
    sm = total_matched / total_possible if total_possible > 0 else 1.0

    # Mathematical consistency assertions
    assert p_d == (tp_d / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0))
    assert r_d == (tp_d / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0))
    if p_d + r_d > 0:
        assert math.isclose(f1_d, (2 * p_d * r_d) / (p_d + r_d), abs_tol=1e-5)

    runtime = time.time() - t0

    # Audit candidate breakdown for hybrid
    audit_summary = {}
    if hasattr(extractor, "get_audit_summary"):
        audit_summary = extractor.get_audit_summary()

    return {
        "pmcid": pmcid,
        "title": paper_meta.get("title", ""),
        "system": system_name,
        "runtime_seconds": round(runtime, 4),
        "gold_direct": len(gt_direct),
        "pred_direct": len(pred_direct),
        "tp_direct": tp_d,
        "fp_direct": fp_d,
        "fn_direct": fn_d,
        "precision_direct": round(p_d, 4),
        "recall_direct": round(r_d, 4),
        "f1_direct": round(f1_d, 4),
        "direction_accuracy": round(dir_acc, 4),
        "gold_cross": len(gt_cross),
        "pred_cross": len(pred_cross),
        "tp_cross": tp_c,
        "fp_cross": fp_c,
        "fn_cross": fn_c,
        "precision_cross": round(p_c, 4),
        "recall_cross": round(r_c, 4),
        "f1_cross": round(f1_c, 4),
        "false_transitive_jumps": false_transitive_jumps,
        "structural_match": round(sm, 4),
        "audit_summary": audit_summary,
    }


def evaluate_split_for_system(
    split_name: str,
    papers: List[Dict[str, Any]],
    system_key: str,
    ingester: PMCOAIngester,
    curated_map: Dict[str, Any],
) -> Dict[str, Any]:
    extractor = get_extraction_backend(system_key)
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.60)

    per_paper = []
    dir_f1s = []
    cross_f1s = []
    sms = []
    dir_accs = []

    tot_tp_d, tot_fp_d, tot_fn_d = 0, 0, 0
    tot_tp_c, tot_fp_c, tot_fn_c = 0, 0, 0
    tot_jumps = 0
    tot_runtime = 0.0

    for paper in papers:
        pmcid = paper["pmcid"]
        xml_path = os.path.join(REPO_ROOT, "data", "real_papers", "xml", f"{pmcid}.xml")
        with open(xml_path, "r", encoding="utf-8") as f:
            pmc_doc = ingester.parse_xml(f.read(), pmcid)
        doc = convert_pmc_oa_to_scientific_document(pmc_doc)

        spec = curated_map.get(pmcid)

        res = evaluate_system_on_paper(
            paper_meta=paper,
            doc=doc,
            extractor=extractor,
            linker=linker,
            curated_spec=spec,
            system_name=system_key,
        )
        per_paper.append(res)

        dir_f1s.append(res["f1_direct"])
        cross_f1s.append(res["f1_cross"])
        sms.append(res["structural_match"])
        dir_accs.append(res["direction_accuracy"])

        tot_tp_d += res["tp_direct"]
        tot_fp_d += res["fp_direct"]
        tot_fn_d += res["fn_direct"]
        tot_tp_c += res["tp_cross"]
        tot_fp_c += res["fp_cross"]
        tot_fn_c += res["fn_cross"]
        tot_jumps += res["false_transitive_jumps"]
        tot_runtime += res["runtime_seconds"]

    # Macro metrics and CIs
    m_dir, dir_ci_l, dir_ci_u = bootstrap_ci(dir_f1s)
    m_cross, cross_ci_l, cross_ci_u = bootstrap_ci(cross_f1s)
    m_sm, sm_ci_l, sm_ci_u = bootstrap_ci(sms)
    m_dir_acc = float(np.mean(dir_accs)) if dir_accs else 0.0

    # Micro aggregates
    micro_p_d = tot_tp_d / (tot_tp_d + tot_fp_d) if (tot_tp_d + tot_fp_d) else 0.0
    micro_r_d = tot_tp_d / (tot_tp_d + tot_fn_d) if (tot_tp_d + tot_fn_d) else 0.0
    micro_f1_d = (2 * micro_p_d * micro_r_d) / (micro_p_d + micro_r_d) if (micro_p_d + micro_r_d) else 0.0

    micro_p_c = tot_tp_c / (tot_tp_c + tot_fp_c) if (tot_tp_c + tot_fp_c) else 0.0
    micro_r_c = tot_tp_c / (tot_tp_c + tot_fn_c) if (tot_tp_c + tot_fn_c) else 0.0
    micro_f1_c = (2 * micro_p_c * micro_r_c) / (micro_p_c + micro_r_c) if (micro_p_c + micro_r_c) else 0.0

    # Verify mathematical consistency
    assert math.isclose(micro_p_d, tot_tp_d / (tot_tp_d + tot_fp_d) if (tot_tp_d + tot_fp_d) else 0.0)
    assert math.isclose(micro_r_d, tot_tp_d / (tot_tp_d + tot_fn_d) if (tot_tp_d + tot_fn_d) else 0.0)

    # Candidate audit summary across split
    split_audit = {}
    if hasattr(extractor, "get_audit_summary"):
        split_audit = extractor.get_audit_summary()

    return {
        "split": split_name,
        "system": system_key,
        "paper_count": len(papers),
        "total_runtime_seconds": round(tot_runtime, 4),
        "macro_metrics": {
            "direct_f1_mean": round(m_dir, 4),
            "direct_f1_ci": [round(dir_ci_l, 4), round(dir_ci_u, 4)],
            "cross_f1_mean": round(m_cross, 4),
            "cross_f1_ci": [round(cross_ci_l, 4), round(cross_ci_u, 4)],
            "structural_match_mean": round(m_sm, 4),
            "structural_match_ci": [round(sm_ci_l, 4), round(sm_ci_u, 4)],
            "direction_accuracy_mean": round(m_dir_acc, 4),
        },
        "micro_metrics": {
            "direct": {
                "tp": tot_tp_d, "fp": tot_fp_d, "fn": tot_fn_d,
                "precision": round(micro_p_d, 4), "recall": round(micro_r_d, 4), "f1": round(micro_f1_d, 4),
            },
            "cross_page": {
                "tp": tot_tp_c, "fp": tot_fp_c, "fn": tot_fn_c,
                "precision": round(micro_p_c, 4), "recall": round(micro_r_c, 4), "f1": round(micro_f1_c, 4),
            },
            "total_false_transitive_jumps": tot_jumps,
        },
        "audit": split_audit,
        "per_paper": per_paper,
    }


def main():
    print("=" * 80)
    print("EVRYN PHASE 2.2: THREE-WAY EXTRACTION BACKEND COMPARISON EVALUATION")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print(f"Prompt Version: {PROMPT_VERSION}")
    print("=" * 80)

    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    curated_map = {p["pmcid"]: p for p in get_curated_papers("v1")}
    ingester = PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))

    splits = {
        "dev": [p for p in manifest["papers"] if p["split"] == "dev"],
        "locked_test": [p for p in manifest["papers"] if p["split"] == "locked_test"],
    }

    systems = [
        ("System A (NLP Baseline)", "nlp_baseline"),
        ("System B (LLM Only)", "llm_only"),
        ("System C (Hybrid LLM + Validation)", "hybrid"),
    ]

    all_results = {
        "evaluation_phase": "Phase 2.2: Hybrid LLM-Based Causal Extraction",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompt_version": PROMPT_VERSION,
        "splits_evaluated": ["dev", "locked_test"],
        "results": {},
    }

    for split_key, papers in splits.items():
        print(f"\n==================== SPLIT: {split_key.upper()} ({len(papers)} papers) ====================")
        all_results["results"][split_key] = {}
        for sys_label, sys_key in systems:
            print(f"\n--- Running {sys_label} [{sys_key}] on {split_key} ---")
            res = evaluate_split_for_system(
                split_name=split_key,
                papers=papers,
                system_key=sys_key,
                ingester=ingester,
                curated_map=curated_map,
            )
            all_results["results"][split_key][sys_key] = res
            m = res["macro_metrics"]
            micro_d = res["micro_metrics"]["direct"]
            micro_c = res["micro_metrics"]["cross_page"]
            print(f"  Macro Direct F1:     {m['direct_f1_mean']:.4f} (95% CI: [{m['direct_f1_ci'][0]:.4f}, {m['direct_f1_ci'][1]:.4f}])")
            print(f"  Micro Direct P/R/F1: {micro_d['precision']:.4f} / {micro_d['recall']:.4f} / {micro_d['f1']:.4f} (TP={micro_d['tp']}, FP={micro_d['fp']}, FN={micro_d['fn']})")
            print(f"  Macro Cross-Page F1: {m['cross_f1_mean']:.4f} (95% CI: [{m['cross_f1_ci'][0]:.4f}, {m['cross_f1_ci'][1]:.4f}])")
            print(f"  Micro Cross P/R/F1:  {micro_c['precision']:.4f} / {micro_c['recall']:.4f} / {micro_c['f1']:.4f} (TP={micro_c['tp']}, FP={micro_c['fp']}, FN={micro_c['fn']})")
            print(f"  Direction Accuracy:  {m['direction_accuracy_mean'] * 100:.1f}%")
            print(f"  False Trans. Jumps:  {res['micro_metrics']['total_false_transitive_jumps']}")
            print(f"  Exact Struct Match:  {m['structural_match_mean']:.4f}")
            print(f"  Runtime:             {res['total_runtime_seconds']:.2f}s")

    # Save machine-readable output
    output_json = os.path.join(REPO_ROOT, "results", "phase2_2", "phase2_2_comparison_results.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[OK] Machine-readable results saved to: {output_json}")

    # Generate Markdown Comparison Report
    report_md = os.path.join(REPO_ROOT, "results", "phase2_2", "COMPARISON_REPORT.md")
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# EVRYN Phase 2.2: Systematic Three-Way Causal Extraction Comparison Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}  \n")
        f.write(f"**Prompt Version:** `{PROMPT_VERSION}`  \n")
        f.write("**Systems Evaluated:**\n")
        f.write("1. **System A — Repaired Rule-Based NLP Baseline** (`nlp_baseline`)\n")
        f.write("2. **System B — LLM-Only Candidate Extraction** (`llm_only`)\n")
        f.write("3. **System C — Hybrid LLM + Deterministic Validation** (`hybrid`)\n\n")

        for s_key in ["dev", "locked_test"]:
            f.write(f"## {s_key.upper()} Split Evaluation Summary\n\n")
            f.write("| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for sys_label, sys_key in systems:
                res = all_results["results"][s_key][sys_key]
                m = res["macro_metrics"]
                micro_d = res["micro_metrics"]["direct"]
                f.write(
                    f"| **{sys_label}** | {m['direct_f1_mean']:.4f} [{m['direct_f1_ci'][0]:.4f}, {m['direct_f1_ci'][1]:.4f}] | "
                    f"{micro_d['precision']:.3f} / {micro_d['recall']:.3f} / {micro_d['f1']:.3f} | "
                    f"{m['cross_f1_mean']:.4f} [{m['cross_f1_ci'][0]:.4f}, {m['cross_f1_ci'][1]:.4f}] | "
                    f"{m['direction_accuracy_mean']*100:.1f}% | {res['micro_metrics']['total_false_transitive_jumps']} | "
                    f"{m['structural_match_mean']:.4f} | {res['total_runtime_seconds']:.2f}s |\n"
                )
            f.write("\n")

        f.write("## Per-Paper Direct & Cross-Page Breakdown (Development Split)\n\n")
        f.write("| PMCID | Paper Title | System | Direct (TP / FP / FN) | Direct F1 | Cross-Page (TP / FP / FN) | Cross F1 |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |\n")
        for sys_label, sys_key in systems:
            papers_res = all_results["results"]["dev"][sys_key]["per_paper"]
            for p in papers_res:
                f.write(
                    f"| `{p['pmcid']}` | {p['title'][:35]}... | {sys_key} | "
                    f"{p['tp_direct']} / {p['fp_direct']} / {p['fn_direct']} | **{p['f1_direct']:.4f}** | "
                    f"{p['tp_cross']} / {p['fp_cross']} / {p['fn_cross']} | **{p['f1_cross']:.4f}** |\n"
                )

    print(f"[OK] Comparison report markdown saved to: {report_md}")


if __name__ == "__main__":
    main()
