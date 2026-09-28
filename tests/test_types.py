# pytest tests/test_types.py

import pytest
from evryn.core.types import (
    ScientificDomain,
    RelationType,
    EvidenceModality,
    Provenance,
    NormalizedEntity,
    EvidenceSpan,
    NormalizedRelation,
    HigherOrderRelation,
)


def test_enums():
    assert ScientificDomain.BIOMEDICINE.value == "biomedicine"
    assert RelationType.FORWARD.value == "FORWARD"
    assert RelationType.HIGHER_ORDER_JOINT.value == "HIGHER_ORDER_JOINT"
    assert EvidenceModality.TEXTUAL_LITERATURE.value == "textual_literature"


def test_provenance_roundtrip():
    prov = Provenance(
        source_id="doc_123",
        citation="Smith et al., 2024",
        timestamp="2024-01-01",
        confidence=0.95,
    )
    d = prov.to_dict()
    assert d["source_id"] == "doc_123"
    assert d["confidence"] == 0.95
    restored = Provenance.from_dict(d)
    assert restored.source_id == prov.source_id
    assert restored.citation == prov.citation
    assert restored.confidence == prov.confidence


def test_normalized_entity_roundtrip():
    ent = NormalizedEntity(
        entity_id="ent_001",
        canonical_name="tp53",
        surface_forms=["p53", "tumor protein p53"],
        entity_type="gene",
        domain=ScientificDomain.BIOMEDICINE,
    )
    d = ent.to_dict()
    assert d["canonical_name"] == "tp53"
    assert d["domain"] == "biomedicine"
    restored = NormalizedEntity.from_dict(d)
    assert restored.entity_id == ent.entity_id
    assert restored.domain == ScientificDomain.BIOMEDICINE


def test_evidence_span_roundtrip():
    span = EvidenceSpan(
        text="A inhibits B",
        start_char=0,
        end_char=12,
        sentence="A inhibits B in human lung cells.",
        document_id="pmc_456",
    )
    d = span.to_dict()
    assert d["text"] == "A inhibits B"
    restored = EvidenceSpan.from_dict(d)
    assert restored.start_char == 0
    assert restored.document_id == "pmc_456"


def test_normalized_relation_roundtrip():
    e1 = NormalizedEntity(entity_id="e1", canonical_name="A")
    e2 = NormalizedEntity(entity_id="e2", canonical_name="B")
    span = EvidenceSpan(text="A -> B", start_char=0, end_char=6, sentence="A causes B")
    prov = Provenance(source_id="test_doc", confidence=0.88)
    rel = NormalizedRelation(
        relation_id="rel_001",
        source_entities=[e1],
        target_entities=[e2],
        relation_type=RelationType.FORWARD,
        relation_family="CAUSAL_PRODUCTION",
        evidence_spans=[span],
        confidence=0.88,
        provenance=prov,
        temporal_year=2024,
        domain=ScientificDomain.BIOMEDICINE,
    )
    d = rel.to_dict()
    assert d["relation_id"] == "rel_001"
    assert d["relation_type"] == "FORWARD"
    restored = NormalizedRelation.from_dict(d)
    assert restored.relation_id == rel.relation_id
    assert restored.source_entities[0].canonical_name == "A"
    assert restored.target_entities[0].canonical_name == "B"
    assert restored.relation_type == RelationType.FORWARD
    assert restored.temporal_year == 2024


def test_higher_order_relation_roundtrip():
    s1 = NormalizedEntity(entity_id="e1", canonical_name="GeneA")
    s2 = NormalizedEntity(entity_id="e2", canonical_name="GeneB")
    tgt = NormalizedEntity(entity_id="e3", canonical_name="PhenotypeC")
    ho = HigherOrderRelation(
        relation_id="ho_001",
        sources=[s1, s2],
        targets=[tgt],
        interaction_type="synergistic_epistasis",
        synergy_score=0.45,
        confidence=0.92,
        order=2,
    )
    d = ho.to_dict()
    assert d["interaction_type"] == "synergistic_epistasis"
    assert d["synergy_score"] == 0.45
    restored = HigherOrderRelation.from_dict(d)
    assert len(restored.sources) == 2
    assert restored.order == 2
    assert restored.targets[0].canonical_name == "PhenotypeC"
