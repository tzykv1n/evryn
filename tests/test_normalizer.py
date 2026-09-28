# pytest tests/test_normalizer.py

import pytest
from evryn.core.types import RelationType, ScientificDomain
from evryn.core.config import NormalizationConfig
from evryn.normalization.normalizer import RelationNormalizer


def test_canonicalize_entity_name():
    norm = RelationNormalizer()
    assert norm.canonicalize_entity_name("the covid-19") == "SARS-CoV-2"
    assert norm.canonicalize_entity_name("a hypertension") == "high blood pressure"
    assert norm.canonicalize_entity_name("  myocardial infarction  ") == "heart attack"
    assert norm.canonicalize_entity_name("novel protein x") == "novel protein x"


def test_create_entity():
    norm = RelationNormalizer()
    ent = norm.create_entity("Coronavirus", entity_type="virus", domain=ScientificDomain.BIOMEDICINE)
    assert ent.canonical_name == "SARS-CoV-2"
    assert ent.entity_type == "virus"
    assert ent.domain == ScientificDomain.BIOMEDICINE
    assert ent.entity_id.startswith("ent_")


def test_normalize_pairwise_forward():
    norm = RelationNormalizer()
    rel = norm.normalize_pairwise(
        e1_text="Drug A",
        e2_text="Receptor B",
        pred_type="FORWARD",
        confidence=0.85,
        sentence="Drug A activates Receptor B in vitro.",
        e1_span=(0, 6),
        e2_span=(17, 27),
        source_doc="doc_01",
        temporal_year=2023,
    )
    assert rel.relation_type == RelationType.FORWARD
    assert rel.source_entities[0].canonical_name == "drug a"
    assert rel.target_entities[0].canonical_name == "receptor b"
    assert rel.temporal_year == 2023
    assert len(rel.evidence_spans) == 2


def test_normalize_pairwise_backward():
    norm = RelationNormalizer()
    rel = norm.normalize_pairwise(
        e1_text="Outcome Y",
        e2_text="Cause X",
        pred_type="BACKWARD",
        confidence=0.90,
        sentence="Outcome Y is caused by Cause X.",
        e1_span=(0, 9),
        e2_span=(23, 30),
        source_doc="doc_02",
    )
    assert rel.relation_type == RelationType.FORWARD
    assert rel.source_entities[0].canonical_name == "cause x"
    assert rel.target_entities[0].canonical_name == "outcome y"


def test_normalize_pairwise_confounded():
    norm = RelationNormalizer()
    rel = norm.normalize_pairwise(
        e1_text="Gene A",
        e2_text="Gene B",
        pred_type="CONFOUNDED",
        confidence=0.77,
        sentence="Gene A correlates with Gene B due to latent confounder.",
        e1_span=(0, 6),
        e2_span=(23, 29),
    )
    assert rel.relation_type == RelationType.CONFOUNDED


def test_normalize_higher_order():
    norm = RelationNormalizer()
    norm_rel, ho_rel = norm.normalize_higher_order(
        source_names=["Gene 1", "Gene 2"],
        target_name="Phenotype 3",
        interaction_type="epistatic_synergy",
        synergy_score=0.62,
        confidence=0.91,
        evidence_text="Gene 1 and Gene 2 jointly induce Phenotype 3.",
        temporal_year=2025,
    )
    assert norm_rel.relation_type == RelationType.HIGHER_ORDER_JOINT
    assert norm_rel.relation_family == "SYNERGISTIC_CO_ACTION"
    assert len(norm_rel.source_entities) == 2
    assert norm_rel.higher_order_order == 2
    assert ho_rel.order == 2
    assert ho_rel.synergy_score == 0.62
    assert ho_rel.interaction_type == "epistatic_synergy"
