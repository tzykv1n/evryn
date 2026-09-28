# pytest tests/test_higher_order_nlp.py

import os
import json
import subprocess
import pytest
from collections import Counter

from evryn.nlp.higher_order.types import (
    HigherOrderCategory,
    HigherOrderCandidate,
    HigherOrderBenchmarkResult,
)
from evryn.nlp.higher_order.dataset import HigherOrderDatasetBuilder
from evryn.nlp.higher_order.auditor import CandidateAuditor
from evryn.nlp.higher_order.baselines import HigherOrderBaselineSuite
from evryn.nlp.higher_order.benchmark import HigherOrderBenchmarkRunner
from evryn.visualization.terminal_graphics import (
    detect_native_graphics_protocol,
    find_available_viewer,
    open_in_external_viewer,
)


def test_candidate_types_and_serialization():
    cand = HigherOrderCandidate(
        candidate_id="ho_001",
        sentence="Smoking and asbestos jointly trigger lung carcinoma.",
        entity1_text="Smoking",
        entity2_text="lung carcinoma",
        entity1_span=(0, 7),
        entity2_span=(37, 51),
        candidate_participants=("Smoking", "asbestos"),
        candidate_target="lung carcinoma",
        relation_trigger="jointly trigger",
        relation_direction="FORWARD",
        pairwise_pred="FORWARD",
        pairwise_conf=0.94,
        temporal_cues=[],
        coordination_cues=["and", "jointly"],
        generation_rule="conjoined_subject_joint_cause",
        category=HigherOrderCategory.HIGHER_ORDER_INTERACTION,
        validation_status="VALIDATED",
        source_dataset="SemEval-2010_Task8",
        source_split="test",
        document_id="semeval_doc_001",
        higher_order_evidence={"pid_synergy_estimate": 0.88},
    )

    d = cand.to_dict()
    assert d["candidate_id"] == "ho_001"
    assert d["category"] == "HIGHER_ORDER_INTERACTION"

    cand_back = HigherOrderCandidate.from_dict(d)
    assert cand_back.candidate_id == cand.candidate_id
    assert cand_back.category == HigherOrderCategory.HIGHER_ORDER_INTERACTION
    assert cand_back.candidate_participants == ("Smoking", "asbestos")


def test_negative_controls_generation():
    builder = HigherOrderDatasetBuilder()
    controls = builder._generate_negative_controls()
    assert len(controls) == 5
    for c in controls:
        assert c.validation_status == "NEGATIVE_CONTROL"
        assert c.category in (
            HigherOrderCategory.LINGUISTIC_COORDINATION,
            HigherOrderCategory.TEMPORAL_RELATION,
            HigherOrderCategory.PAIRWISE_DECOMPOSABLE,
        )
        assert c.higher_order_evidence["pid_synergy_estimate"] < 0.10


def test_candidate_auditor():
    cands = [
        HigherOrderCandidate(
            candidate_id="c1",
            sentence="Virus and bacteria jointly cause pneumonia.",
            entity1_text="Virus",
            entity2_text="pneumonia",
            entity1_span=(0, 5),
            entity2_span=(27, 36),
            candidate_participants=("Virus", "bacteria"),
            candidate_target="pneumonia",
            relation_trigger="jointly cause",
            relation_direction="FORWARD",
            pairwise_pred="FORWARD",
            pairwise_conf=0.91,
            temporal_cues=[],
            coordination_cues=["and"],
            generation_rule="conjoined_subject_joint_cause",
            category=HigherOrderCategory.JOINT_CAUSE,
        ),
        HigherOrderCandidate(
            candidate_id="c2",
            sentence="After the event, both teachers and students left.",
            entity1_text="teachers",
            entity2_text="students",
            entity1_span=(17, 25),
            entity2_span=(30, 38),
            candidate_participants=("teachers", "students"),
            candidate_target="students",
            relation_trigger="and",
            relation_direction="NO_RELATION",
            pairwise_pred="NO_RELATION",
            pairwise_conf=0.88,
            temporal_cues=["after"],
            coordination_cues=["and", "both"],
            generation_rule="temporal_marker",
            category=HigherOrderCategory.TEMPORAL_RELATION,
        ),
    ]

    auditor = CandidateAuditor()
    report = auditor.audit(cands)
    assert report["total_candidates"] == 2
    assert report["unique_sentences"] == 2
    assert report["has_conjunction_count"] == 2
    assert report["has_temporal_count"] == 1


def test_baseline_predictions_and_metrics():
    cands = [
        HigherOrderCandidate(
            candidate_id="t1",
            sentence="Smoking and asbestos synergistically cause cancer.",
            entity1_text="Smoking",
            entity2_text="cancer",
            entity1_span=(0, 7),
            entity2_span=(37, 43),
            candidate_participants=("Smoking", "asbestos"),
            candidate_target="cancer",
            relation_trigger="synergistically cause",
            relation_direction="FORWARD",
            pairwise_pred="FORWARD",
            pairwise_conf=0.95,
            temporal_cues=[],
            coordination_cues=["and", "synergistically"],
            generation_rule="synergy_marker",
            category=HigherOrderCategory.HIGHER_ORDER_INTERACTION,
            higher_order_evidence={"pid_synergy_estimate": 0.85, "delta_r2_gain": 0.50},
        ),
        HigherOrderCandidate(
            candidate_id="t2",
            sentence="The desk and chair were made of wood.",
            entity1_text="desk",
            entity2_text="wood",
            entity1_span=(4, 8),
            entity2_span=(27, 31),
            candidate_participants=("desk", "chair"),
            candidate_target="wood",
            relation_trigger="and",
            relation_direction="NO_RELATION",
            pairwise_pred="NO_RELATION",
            pairwise_conf=0.92,
            temporal_cues=[],
            coordination_cues=["and"],
            generation_rule="noun_conjunction",
            category=HigherOrderCategory.LINGUISTIC_COORDINATION,
            higher_order_evidence={"pid_synergy_estimate": 0.05, "delta_r2_gain": 0.01},
        ),
    ]

    suite = HigherOrderBaselineSuite()
    preds_a = suite.predict_baseline_a_pairwise(cands)
    assert preds_a[0] == HigherOrderCategory.PAIRWISE_DECOMPOSABLE
    assert preds_a[1] == HigherOrderCategory.LINGUISTIC_COORDINATION

    preds_b = suite.predict_baseline_b_rule_based(cands)
    assert preds_b[0] == HigherOrderCategory.HIGHER_ORDER_INTERACTION

    preds_d = suite.predict_method_d_flux_evidence(cands)
    assert preds_d[0] == HigherOrderCategory.HIGHER_ORDER_INTERACTION
    assert preds_d[1] == HigherOrderCategory.LINGUISTIC_COORDINATION

    runner = HigherOrderBenchmarkRunner()
    eval_res = runner.evaluate_predictions([c.category for c in cands], preds_d, "Method D")
    assert eval_res.higher_order_interaction_f1 == 1.0
    assert eval_res.false_joint_cause_rate == 0.0


def test_viewer_discovery(monkeypatch):
    viewer = find_available_viewer()
    assert viewer in ("photos", "vlc", "imv", "sxiv", "nsxiv", "feh", "xdg-open", None)

    class DummyProc:
        def __init__(self):
            self.returncode = 0

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: DummyProc())
    opened, used_viewer = open_in_external_viewer("outputs/continual_flux_results.png")
    if viewer:
        assert opened is True
        assert used_viewer == viewer
    else:
        assert opened is False
