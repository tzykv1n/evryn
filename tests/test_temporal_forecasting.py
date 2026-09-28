# pytest tests/test_temporal_forecasting.py

import pytest
from evryn.core.types import RelationType
from evryn.normalization.normalizer import RelationNormalizer
from evryn.temporal.evolution import TemporalEvolutionTracker
from evryn.prediction.forecasting import FutureRelationForecaster


def test_temporal_evolution_tracking():
    norm = RelationNormalizer()
    tracker = TemporalEvolutionTracker()

    r1 = norm.normalize_pairwise("A", "B", "FORWARD", 0.50, "A leads to B", (0, 1), (11, 12), temporal_year=2020)
    r2 = norm.normalize_pairwise("A", "B", "FORWARD", 0.70, "A causes B", (0, 1), (9, 10), temporal_year=2022)
    r3 = norm.normalize_pairwise("A", "B", "FORWARD", 0.90, "A triggers B", (0, 1), (11, 12), temporal_year=2024)

    seqs = tracker.track_evolution([r1, r2, r3])
    assert "a->b" in seqs
    seq = seqs["a->b"]
    assert seq.years == [2020, 2022, 2024]
    assert seq.confidences == [0.50, 0.70, 0.90]
    assert seq.velocity > 0.05
    assert seq.status in ("EMERGING", "CONSOLIDATED")
    assert not seq.is_contradicted


def test_temporal_contradiction_detection():
    norm = RelationNormalizer()
    tracker = TemporalEvolutionTracker()

    r1 = norm.normalize_pairwise("X", "Y", "FORWARD", 0.85, "X causes Y", (0, 1), (9, 10), temporal_year=2021)
    r2 = norm.normalize_pairwise("X", "Y", "CONFOUNDED", 0.80, "X and Y are confounded", (0, 1), (6, 7), temporal_year=2023)

    seqs = tracker.track_evolution([r1, r2])
    assert "x->y" in seqs
    seq = seqs["x->y"]
    assert seq.is_contradicted
    assert seq.status == "CONTRADICTED"


def test_future_relation_forecaster_transitive():
    norm = RelationNormalizer()
    tracker = TemporalEvolutionTracker()
    forecaster = FutureRelationForecaster()

    r_ab = norm.normalize_pairwise("NodeA", "NodeB", "FORWARD", 0.95, "NodeA causes NodeB", (0, 5), (13, 18), temporal_year=2023)
    r_bc = norm.normalize_pairwise("NodeB", "NodeC", "FORWARD", 0.90, "NodeB causes NodeC", (0, 5), (13, 18), temporal_year=2024)

    relations = [r_ab, r_bc]
    seqs = tracker.track_evolution(relations)
    forecasts = forecaster.forecast_relations(relations, seqs, current_year=2026)

    trans_forecasts = [f for f in forecasts if f.target_name == "nodec" and f.source_names == ["nodea"]]
    assert len(trans_forecasts) >= 1
    fc = trans_forecasts[0]
    assert fc.probability > 0.6
    assert "Transitive discovery" in fc.rationale


def test_future_relation_forecaster_converging_synergy():
    norm = RelationNormalizer()
    tracker = TemporalEvolutionTracker()
    forecaster = FutureRelationForecaster()

    r_p1 = norm.normalize_pairwise("Parent1", "CommonTarget", "FORWARD", 0.92, "Parent1 activates CommonTarget", (0, 7), (18, 30))
    r_p2 = norm.normalize_pairwise("Parent2", "CommonTarget", "FORWARD", 0.88, "Parent2 activates CommonTarget", (0, 7), (18, 30))

    relations = [r_p1, r_p2]
    seqs = tracker.track_evolution(relations)
    forecasts = forecaster.forecast_relations(relations, seqs, current_year=2026)

    synergy_fcs = [f for f in forecasts if f.forecasted_family == "SYNERGISTIC_CO_ACTION"]
    assert len(synergy_fcs) >= 1
    assert "Higher-Order Synergy Hypothesis" in synergy_fcs[0].rationale
