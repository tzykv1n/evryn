# evryn hypothesize

import os
import json
import time
from typing import Dict, Any, List

from ..core.config import EvrynConfig
from ..core.cache import EvrynCache
from ..core.types import ScientificDomain, RelationType
from ..normalization.normalizer import RelationNormalizer
from ..families.discovery import RelationFamilyDiscoverer
from ..temporal.evolution import TemporalEvolutionTracker
from ..prediction.forecasting import FutureRelationForecaster
from ..transfer.cross_domain import CrossDomainTransferEngine
from ..hypothesize.generator import HypothesisGenerator, ScientificHypothesis
from ..ui.console import print_box, print_table, get_progress_bar


def run_evryn_pipeline(config: EvrynConfig, cache: EvrynCache) -> Dict[str, Any]:
    print_box(
        "EVRYN : End-to-End Scientific Knowledge Discovery",
        "Evidence -> Normalization -> Families -> Temporal -> Forecasting -> Transfer -> Hypotheses",
    )

    normalizer = RelationNormalizer(config.normalization)
    family_discoverer = RelationFamilyDiscoverer(config.families)
    temporal_tracker = TemporalEvolutionTracker(config.temporal)
    forecaster = FutureRelationForecaster(config.prediction)
    transfer_engine = CrossDomainTransferEngine(config.transfer)
    hypo_generator = HypothesisGenerator(config.hypotheses)

    with get_progress_bar("Executing EVRYN Discovery Pipeline") as prog:
        t_id = prog.add_task("Step 1: Normalizing Literature & Causal Evidence...", total=6)

        sample_corpus = [
            ("smoking", "lung cancer", "FORWARD", 0.94, "Cigarette smoking causes lung cancer through DNA adduct formation.", (0, 7), (25, 36), 2018, ScientificDomain.EPIDEMIOLOGY),
            ("nicotine", "dopamine release", "FORWARD", 0.91, "Nicotine administration produces rapid dopamine release in nucleus accumbens.", (0, 8), (32, 48), 2019, ScientificDomain.NEUROSCIENCE),
            ("dopamine release", "addiction reinforcement", "FORWARD", 0.88, "Elevated dopamine release results in strong addiction reinforcement.", (9, 25), (37, 61), 2021, ScientificDomain.NEUROSCIENCE),
            ("p53 mutation", "cellular proliferation", "FORWARD", 0.92, "Loss-of-function p53 mutation induces uncontrolled cellular proliferation.", (18, 30), (39, 64), 2020, ScientificDomain.BIOMEDICINE),
            ("p53 mutation", "cellular proliferation", "CONFOUNDED", 0.79, "Co-occurring genomic instability confounds p53 mutation and cellular proliferation.", (24, 36), (41, 66), 2023, ScientificDomain.BIOMEDICINE),
            ("VEGF upregulation", "angiogenesis", "FORWARD", 0.95, "Hypoxia-induced VEGF upregulation promotes tumor angiogenesis.", (16, 33), (43, 55), 2022, ScientificDomain.BIOMEDICINE),
            ("angiogenesis", "tumor metastasis", "FORWARD", 0.89, "Extensive angiogenesis accelerates subsequent tumor metastasis.", (10, 22), (34, 50), 2024, ScientificDomain.BIOMEDICINE),
        ]

        normalized_relations = []
        for e1, e2, rel_t, conf, sent, sp1, sp2, yr, dom in sample_corpus:
            norm_r = normalizer.normalize_pairwise(
                e1_text=e1,
                e2_text=e2,
                pred_type=rel_t,
                confidence=conf,
                sentence=sent,
                e1_span=sp1,
                e2_span=sp2,
                source_doc=f"lit_{yr}_{dom.value}",
                domain=dom,
                temporal_year=yr,
            )
            normalized_relations.append(norm_r)

        ho_norm, _ = normalizer.normalize_higher_order(
            source_names=["p53 mutation", "KRAS activation"],
            target_name="metastatic invasiveness",
            interaction_type="synergistic_co_action",
            synergy_score=0.88,
            confidence=0.89,
            evidence_text="Concurrent p53 mutation and KRAS activation synergistically trigger metastatic invasiveness.",
            domain=ScientificDomain.BIOMEDICINE,
            temporal_year=2024,
        )
        normalized_relations.append(ho_norm)
        prog.advance(t_id)

        prog.update(t_id, description="Step 2: Grouping into Relation Families...")
        family_results = family_discoverer.discover_families(normalized_relations)
        prog.advance(t_id)

        prog.update(t_id, description="Step 3: Tracking Temporal Knowledge Evolution...")
        temporal_seqs = temporal_tracker.track_evolution(normalized_relations)
        prog.advance(t_id)

        prog.update(t_id, description="Step 4: Forecasting Future Relations...")
        forecasts = forecaster.forecast_relations(normalized_relations, temporal_seqs)
        prog.advance(t_id)

        prog.update(t_id, description="Step 5: Evaluating Cross-Domain Knowledge Transfer...")
        bio_rels = [r for r in normalized_relations if r.domain == ScientificDomain.BIOMEDICINE]
        neuro_rels = [r for r in normalized_relations if r.domain == ScientificDomain.NEUROSCIENCE]
        analogies = transfer_engine.discover_cross_domain_analogies(
            bio_rels, neuro_rels, "biomedicine", "neuroscience"
        )
        prog.advance(t_id)

        prog.update(t_id, description="Step 6: Generating Scientific Hypotheses...")
        joint_candidates = [
            {"id": "jc_001", "e1": "avian influenza A", "e2": "secondary bacterial infection", "text": "Co-infection of avian influenza A and secondary bacterial infection triggers severe pneumonia."},
            {"id": "jc_002", "e1": "chronic inflammation", "e2": "epigenetic silencing", "text": "Combined chronic inflammation and epigenetic silencing jointly accelerate oncogenesis."},
        ]
        hypotheses = hypo_generator.generate_hypotheses(
            relations=normalized_relations,
            forecasts=forecasts,
            analogies=analogies,
            temporal_sequences=temporal_seqs,
            joint_cause_candidates=joint_candidates,
        )
        prog.advance(t_id)

    fam_headers = ["Relation Family", "Polarity", "Active Members", "Canonical Description"]
    fam_rows = []
    for f_name, f_data in family_results.items():
        if f_data["count"] > 0:
            fam_rows.append([
                f_data["canonical_name"],
                f"{'+' if f_data['polarity']>0 else ('-' if f_data['polarity']<0 else '0')}",
                str(f_data["count"]),
                f_data["description"][:50] + "...",
            ])
    print_table(fam_headers, fam_rows, title="Discovered Relation Families")

    fc_headers = ["Forecast Candidate", "Family", "Target Year", "Prob (95% CI)", "Discovery Rationale"]
    fc_rows = []
    for fc in forecasts[:4]:
        src = " + ".join(fc.source_names)
        ci_str = f"[{fc.confidence_interval[0]:.2f}, {fc.confidence_interval[1]:.2f}]"
        fc_rows.append([
            f"{src} -> {fc.target_name}",
            fc.forecasted_family,
            str(fc.horizon_year),
            f"{fc.probability:.3f} {ci_str}",
            fc.rationale[:55] + "...",
        ])
    print_table(fc_headers, fc_rows, title="Future Relation Forecasts")

    hypo_headers = ["Hypothesis ID", "Type", "Plausibility", "Candidate Scientific Statement"]
    hypo_rows = []
    for h in hypotheses[:5]:
        hypo_rows.append([
            h.hypothesis_id,
            h.hypothesis_type,
            f"{h.plausibility_score:.3f}",
            h.statement[:65] + "...",
        ])
    print_table(hypo_headers, hypo_rows, title="Synthesized Scientific Hypotheses")

    os.makedirs(config.output_dir, exist_ok=True)
    out_json = os.path.join(config.output_dir, "evryn_discovery_state.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "normalized_relations": [r.to_dict() for r in normalized_relations],
                "family_results": family_results,
                "temporal_sequences": {k: s.to_dict() for k, s in temporal_seqs.items()},
                "forecasts": [fc.to_dict() for fc in forecasts],
                "analogies": [a.to_dict() for a in analogies],
                "hypotheses": [h.to_dict() for h in hypotheses],
            },
            f,
            indent=2,
        )

    out_md = os.path.join(config.output_dir, "evryn_discovery_report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# EVRYN Scientific Discovery Master Report\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 1. Discovered Relation Families\n\n")
        f.write("| Family | Polarity | Count | Description |\n| :--- | :---: | :---: | :--- |\n")
        for f_name, f_data in family_results.items():
            if f_data["count"] > 0:
                f.write(f"| **{f_data['canonical_name']}** | {f_data['polarity']} | {f_data['count']} | {f_data['description']} |\n")
        f.write("\n## 2. Future Relation Forecasts\n\n")
        for fc in forecasts:
            src = " + ".join(fc.source_names)
            f.write(f"* **{src} -> {fc.target_name}** ({fc.forecasted_family}, year {fc.horizon_year})\n")
            f.write(f"  * Probability: {fc.probability:.3f} (95% CI {fc.confidence_interval})\n")
            f.write(f"  * Rationale: {fc.rationale}\n\n")
        f.write("## 3. Generated Scientific Hypotheses\n\n")
        for h in hypotheses:
            f.write(f"### {h.title} (`{h.hypothesis_id}`)\n")
            f.write(f"**Plausibility**: {h.plausibility_score:.3f} | **Type**: `{h.hypothesis_type}`\n\n")
            f.write(f"> {h.statement}\n\n")
            f.write("**Reasoning Chain**:\n")
            for step in h.reasoning_chain:
                f.write(f"1. {step}\n")
            f.write("\n")

    return {
        "num_relations": len(normalized_relations),
        "num_families": len([f for f in family_results.values() if f["count"] > 0]),
        "num_forecasts": len(forecasts),
        "num_analogies": len(analogies),
        "num_hypotheses": len(hypotheses),
        "report_path": out_md,
    }
