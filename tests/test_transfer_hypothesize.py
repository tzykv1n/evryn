# pytest tests/test_transfer_hypothesize.py

import pytest
from evryn.core.types import ScientificDomain
from evryn.normalization.normalizer import RelationNormalizer
from evryn.transfer.cross_domain import CrossDomainTransferEngine
from evryn.hypothesize.generator import HypothesisGenerator
from evryn.temporal.evolution import TemporalEvolutionTracker
from evryn.prediction.forecasting import FutureRelationForecaster


def test_cross_domain_transfer():
    norm = RelationNormalizer()
    engine = CrossDomainTransferEngine()

    r_bio, _ = norm.normalize_higher_order(
        ["EGFR", "KRAS"], "CellProliferation", "synergistic", 0.75, 0.92,
        domain=ScientificDomain.BIOMEDICINE,
    )
    r_epi, _ = norm.normalize_higher_order(
        ["Density", "Mobility"], "TransmissionRate", "synergistic", 0.70, 0.88,
        domain=ScientificDomain.EPIDEMIOLOGY,
    )

    analogies = engine.discover_cross_domain_analogies(
        source_relations=[r_bio],
        target_relations=[r_epi],
        source_domain_name="biomedicine",
        target_domain_name="epidemiology",
    )
    assert len(analogies) >= 1
    ana = analogies[0]
    assert ana.source_domain == "biomedicine"
    assert ana.target_domain == "epidemiology"
    assert ana.structural_isomorphism_score > 0.7


def test_hypothesis_generator():
    norm = RelationNormalizer()
    generator = HypothesisGenerator()
    tracker = TemporalEvolutionTracker()
    forecaster = FutureRelationForecaster()

    r1 = norm.normalize_pairwise("GeneA", "GeneB", "FORWARD", 0.90, "GeneA activates GeneB", (0, 5), (16, 21), temporal_year=2023)
    r2 = norm.normalize_pairwise("GeneB", "GeneC", "FORWARD", 0.90, "GeneB activates GeneC", (0, 5), (16, 21), temporal_year=2024)
    r_contra1 = norm.normalize_pairwise("DrugD", "TargetE", "FORWARD", 0.85, "DrugD inhibits TargetE", (0, 5), (15, 22), temporal_year=2022)
    r_contra2 = norm.normalize_pairwise("DrugD", "TargetE", "CONFOUNDED", 0.80, "DrugD and TargetE are confounded", (0, 5), (10, 17), temporal_year=2024)

    relations = [r1, r2, r_contra1, r_contra2]
    seqs = tracker.track_evolution(relations)
    fcs = forecaster.forecast_relations(relations, seqs)

    joint_candidates = [
        {"e1": "Compound1", "e2": "Compound2", "text": "Compound1 and Compound2 jointly reduce inflammation.", "id": "test_jc"}
    ]

    hypos = generator.generate_hypotheses(
        relations=relations,
        forecasts=fcs,
        temporal_sequences=seqs,
        joint_cause_candidates=joint_candidates,
    )

    assert len(hypos) >= 2
    types = {h.hypothesis_type for h in hypos}
    assert "HIGHER_ORDER_SYNERGY" in types
    assert "CONTRADICTION_RESOLUTION" in types
    for h in hypos:
        assert h.plausibility_score > 0.0
        assert len(h.reasoning_chain) > 0
        assert h.provenance is not None
