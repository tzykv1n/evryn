"""
Test suite for Phase 1.7 Document-Context Relation Resolution.
Validates bounded cross-sentence extraction, demonstrative anaphora, discourse connectives,
and false-positive control invariants.
"""

import pytest
from evryn.paper.types import (
    ScientificDocument,
    SentenceSpan,
    PaperMetadata,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
)
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.document_context import DocumentContextResolver
from evryn.paper.extractor import PaperCausalExtractor


def test_demonstrative_anaphora_resolution():
    resolver = DocumentContextResolver(
        enabled=True,
        enable_sentence_stitch=False,
        enable_anaphora=True,
        enable_discourse_connectives=True,
        enable_false_positive_controls=True,
    )
    normalizer = PaperEntityNormalizer()

    s1 = SentenceSpan(
        sentence_id="s1",
        page_number=3,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=68,
        text="Inactivation of phoP resulted in defective intracellular survival.",
    )
    s2 = SentenceSpan(
        sentence_id="s2",
        page_number=3,
        section_title="Results",
        paragraph_id="p1",
        start_char=69,
        end_char=136,
        text="This phenotype accounts for the reduced virulence in systemic mice.",
    )
    doc = ScientificDocument(
        doc_id="test_pmc_001",
        file_path="dummy.xml",
        metadata=PaperMetadata(title="Test Document"),
        full_text=f"{s1.text} {s2.text}",
        sentences=[s1, s2],
    )

    prior_asrt = CausalAssertion(
        assertion_id="asrt_001",
        cause="phoP",
        cause_canonical="PhoP",
        effect="intracellular survival",
        effect_canonical="Intracellular Survival",
        direction="FORWARD",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        is_negated=False,
        uncertainty_score=0.1,
        sentence_id="s1",
        page_number=3,
        section_title="Results",
        confidence=0.9,
        evidence_quote=s1.text,
        char_span=(0, 68),
        evidence_status=EvidenceStatus.MEASURED_FACT,
    )

    known_entities = ["PhoP", "Intracellular Survival", "Virulence"]
    resolved = resolver.resolve_document_context(
        doc=doc,
        normalizer=normalizer,
        local_abbr={},
        known_entities=known_entities,
        existing_assertions=[prior_asrt],
    )

    assert len(resolved) == 1
    asrt = resolved[0]
    assert asrt.cause_canonical == "Intracellular Survival"
    assert asrt.effect_canonical == "Virulence"
    assert asrt.discourse_relation == "demonstrative_anaphora"
    assert asrt.evidence_sentence_ids == ["s1", "s2"]


def test_discourse_connective_resolution():
    resolver = DocumentContextResolver(
        enabled=True,
        enable_sentence_stitch=False,
        enable_anaphora=True,
        enable_discourse_connectives=True,
        enable_false_positive_controls=True,
    )
    normalizer = PaperEntityNormalizer()

    s1 = SentenceSpan(
        sentence_id="s1",
        page_number=4,
        section_title="Results",
        paragraph_id="p2",
        start_char=0,
        end_char=67,
        text="Phosphorylation of BvrR triggers outer membrane protein remodeling.",
    )
    s2 = SentenceSpan(
        sentence_id="s2",
        page_number=4,
        section_title="Results",
        paragraph_id="p2",
        start_char=68,
        end_char=134,
        text="Consequently, outer membrane permeability decreases significantly.",
    )
    doc = ScientificDocument(
        doc_id="test_pmc_002",
        file_path="dummy.xml",
        metadata=PaperMetadata(title="Test Document 2"),
        full_text=f"{s1.text} {s2.text}",
        sentences=[s1, s2],
    )

    prior_asrt = CausalAssertion(
        assertion_id="asrt_002",
        cause="BvrR",
        cause_canonical="BvrR",
        effect="outer membrane protein remodeling",
        effect_canonical="Outer Membrane Proteins",
        direction="FORWARD",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        is_negated=False,
        uncertainty_score=0.1,
        sentence_id="s1",
        page_number=4,
        section_title="Results",
        confidence=0.9,
        evidence_quote=s1.text,
        char_span=(0, 67),
        evidence_status=EvidenceStatus.MEASURED_FACT,
    )

    known_entities = ["BvrR", "Outer Membrane Proteins", "Membrane Permeability"]
    resolved = resolver.resolve_document_context(
        doc=doc,
        normalizer=normalizer,
        local_abbr={},
        known_entities=known_entities,
        existing_assertions=[prior_asrt],
    )

    assert len(resolved) == 1
    asrt = resolved[0]
    assert asrt.cause_canonical == "Outer Membrane Proteins"
    assert asrt.effect_canonical == "Membrane Permeability"
    assert asrt.discourse_relation == "causal_connective"


def test_false_positive_control_invariants():
    resolver = DocumentContextResolver(
        enabled=True,
        enable_false_positive_controls=True,
    )
    # Terminal phenotype cannot cause an upstream regulator
    assert not resolver._is_valid_pair("virulence", "BvrR", set())
    # Environmental input cannot be downstream outcome
    assert not resolver._is_valid_pair("BvrR", "Acid pH", set())
    # Complementation marker cannot be downstream outcome
    assert not resolver._is_valid_pair("BvrR", "complemented strain", set())
    # Duplicate pair rejected
    assert not resolver._is_valid_pair("BvrR", "Outer Membrane Proteins", {("BvrR", "Outer Membrane Proteins")})
    # Valid causal pair accepted
    assert resolver._is_valid_pair("BvrR", "Outer Membrane Proteins", set())
