#!/usr/bin/env python3
"""EVRYN Phase 1.11 Controlled Ablation Experiment Runner.

Evaluates incremental contributions of:
A0: Phase 1.10 Baseline (all Phase 1.11 mechanisms disabled)
A1: + Preceding TCSTS Slash Coupling
A2: + Expanded TCSTS Operon RK Coupling
A3: + Enzymatic Activity Coupling
A4: + Chaperone-Cargo Binding Coupling
A5: Full Phase 1.11 System (All enabled)
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evryn.paper.real_benchmark import get_curated_papers, convert_pmc_oa_to_scientific_document
from evryn.datasets.pmc_oa import PMCOAIngester
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


def evaluate_config(
    extractor: PaperCausalExtractor,
    linker: CrossPageLinker,
    papers: List[Dict[str, Any]],
    xml_dir: Path,
    ingester: PMCOAIngester,
) -> Dict[str, float]:
    f1_d_list = []
    f1_c_list = []
    em_list = []

    for spec in papers:
        pmcid = spec["pmcid"]
        xml_file = xml_dir / f"{pmcid}.xml"
        if not xml_file.exists():
            continue
        with open(xml_file, "r", encoding="utf-8") as f:
            pmc_doc = ingester.parse_xml(f.read(), pmcid)
        doc = convert_pmc_oa_to_scientific_document(pmc_doc)

        gt_direct = [tuple(x) for x in spec.get("direct_edges", [])]
        gt_cross = [tuple(x) for x in spec.get("cross_page_edges", [])]
        canon = spec.get("canonical_entities", [])

        raw = extractor.extract_assertions(doc, known_entities=canon if canon else None)
        clean = [a for a in raw if not a.is_negated]
        if canon:
            c_set = set(canon)
            filt = [a for a in clean if a.cause_canonical in c_set and a.effect_canonical in c_set]
            if len(filt) >= 2:
                clean = filt

        pred_direct = [(a.cause_canonical, a.effect_canonical) for a in clean]
        cross_links = linker.find_cross_page_links(clean)
        pred_cross = [(l.source_entity, l.target_entity) for l in cross_links if l.distance_pages >= 1]

        # Direct evaluation
        matched_d = set()
        tp_d = 0
        for p_c, p_e in pred_direct:
            for idx, (g_c, g_e) in enumerate(gt_direct):
                if idx not in matched_d and match_edge(p_c, p_e, g_c, g_e):
                    tp_d += 1
                    matched_d.add(idx)
                    break
        p_d = tp_d / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
        r_d = tp_d / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
        f1_d = (2 * p_d * r_d) / (p_d + r_d) if (p_d + r_d) > 0 else 0.0
        f1_d_list.append(f1_d)

        # Cross-page evaluation
        matched_c = set()
        tp_c = 0
        for p_c, p_e in pred_cross:
            for idx, (g_c, g_e) in enumerate(gt_cross):
                if idx not in matched_c and match_edge(p_c, p_e, g_c, g_e):
                    tp_c += 1
                    matched_c.add(idx)
                    break
        p_c = tp_c / len(pred_cross) if pred_cross else (1.0 if not gt_cross else 0.0)
        r_c = tp_c / len(gt_cross) if gt_cross else (1.0 if not pred_cross else 0.0)
        f1_c = (2 * p_c * r_c) / (p_c + r_c) if (p_c + r_c) > 0 else 0.0
        f1_c_list.append(f1_c)

        # Exact match
        tp_exact = 0
        matched_exact = set()
        for p_c, p_e in pred_direct:
            for idx, (g_c, g_e) in enumerate(gt_direct):
                if idx not in matched_exact and p_c.strip().lower() == g_c.strip().lower() and p_e.strip().lower() == g_e.strip().lower():
                    tp_exact += 1
                    matched_exact.add(idx)
                    break
        p_em = tp_exact / len(pred_direct) if pred_direct else (1.0 if not gt_direct else 0.0)
        r_em = tp_exact / len(gt_direct) if gt_direct else (1.0 if not pred_direct else 0.0)
        f1_em = (2 * p_em * r_em) / (p_em + r_em) if (p_em + r_em) > 0 else 0.0
        em_list.append(f1_em)

    return {
        "direct_f1": round(sum(f1_d_list) / len(f1_d_list), 4) if f1_d_list else 0.0,
        "cross_page_f1": round(sum(f1_c_list) / len(f1_c_list), 4) if f1_c_list else 0.0,
        "exact_match_f1": round(sum(em_list) / len(em_list), 4) if em_list else 0.0,
    }


def main():
    root = Path(__file__).resolve().parent.parent
    xml_dir = root / "data" / "real_papers" / "xml"
    manifest_path = root / "data" / "real_papers" / "split_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    split_map = {p["pmcid"]: p["split"] for p in manifest["papers"]}

    curated_v2 = get_curated_papers("v2")
    curated_v1 = get_curated_papers("v1")

    splits_v2 = {
        "train": [p for p in curated_v2 if split_map.get(p["pmcid"]) == "train"],
        "dev": [p for p in curated_v2 if split_map.get(p["pmcid"]) == "dev"],
        "locked_test": [p for p in curated_v2 if split_map.get(p["pmcid"]) == "locked_test"],
        "external_v2": [p for p in curated_v2 if split_map.get(p["pmcid"]) == "external"],
    }
    splits_v1 = {
        "external_v1": curated_v1[-4:],
    }

    ingester = PMCOAIngester()
    linker = CrossPageLinker()

    configurations = {
        "A0_Baseline_Phase1_10": {
            "enable_preceding_tcsts": False,
            "enable_operon_tcsts_rk": False,
            "enable_enzymatic_activity_coupling": False,
            "enable_chaperone_cargo_coupling": False,
        },
        "A1_Preceding_TCSTS": {
            "enable_preceding_tcsts": True,
            "enable_operon_tcsts_rk": False,
            "enable_enzymatic_activity_coupling": False,
            "enable_chaperone_cargo_coupling": False,
        },
        "A2_Operon_RK_Expansion": {
            "enable_preceding_tcsts": False,
            "enable_operon_tcsts_rk": True,
            "enable_enzymatic_activity_coupling": False,
            "enable_chaperone_cargo_coupling": False,
        },
        "A3_Enzymatic_Activity": {
            "enable_preceding_tcsts": False,
            "enable_operon_tcsts_rk": False,
            "enable_enzymatic_activity_coupling": True,
            "enable_chaperone_cargo_coupling": False,
        },
        "A4_Chaperone_Cargo": {
            "enable_preceding_tcsts": False,
            "enable_operon_tcsts_rk": False,
            "enable_enzymatic_activity_coupling": False,
            "enable_chaperone_cargo_coupling": True,
        },
        "A5_Phase1_11_Full_System": {
            "enable_preceding_tcsts": True,
            "enable_operon_tcsts_rk": True,
            "enable_enzymatic_activity_coupling": True,
            "enable_chaperone_cargo_coupling": True,
        },
    }

    out_dir = root / "results" / "phase1_11"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    print("=" * 80)
    print("EVRYN PHASE 1.11 CONTROLLED ABLATION EXPERIMENTS")
    print("=" * 80)

    for cfg_name, flags in configurations.items():
        print(f"\nRunning Ablation: {cfg_name}...")
        extractor = PaperCausalExtractor(**flags)
        cfg_res = {}

        for s_name, p_list in splits_v2.items():
            s_metrics = evaluate_config(extractor, linker, p_list, xml_dir, ingester)
            cfg_res[s_name] = s_metrics
            print(f"  {s_name.upper():<12} Direct F1: {s_metrics['direct_f1']:.4f} | Cross-Page F1: {s_metrics['cross_page_f1']:.4f}")

        for s_name, p_list in splits_v1.items():
            s_metrics = evaluate_config(extractor, linker, p_list, xml_dir, ingester)
            cfg_res[s_name] = s_metrics
            print(f"  {s_name.upper():<12} Direct F1: {s_metrics['direct_f1']:.4f} | Cross-Page F1: {s_metrics['cross_page_f1']:.4f}")

        results[cfg_name] = {
            "flags": flags,
            "metrics": cfg_res,
        }

    out_file = out_dir / "ablation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAblation results saved to: {out_file}")

    manifest_rec = {
        "experiment_id": "phase1_11_ablations",
        "description": "Controlled ablation study of Phase 1.11 mechanisms across all 5 benchmark splits.",
        "author": "EVRYN Phase 1.11 Generalization Workstream",
        "timestamp": "2026-10-25T17:10:00Z",
        "status": "COMPLETED",
        "output_file": str(out_file),
    }
    with open(out_dir / "experiment_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_rec, f, indent=2)
    print(f"Experiment manifest saved to: {out_dir / 'experiment_manifest.json'}")


if __name__ == "__main__":
    main()
