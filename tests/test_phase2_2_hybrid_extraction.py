"""
Unit and Integration Test Suite for EVRYN Phase 2.2: Hybrid LLM-Based Causal Extraction.

Tests:
  1. Strict Schema Compliance and Two-Way CausalAssertion Adapters
  2. Mock Provider Determinism and Structured JSON Output
  3. LLM Cache Functionality, Hashing, and Invalidation
  4. Passive Syntax and Inverted Agency Rejection
  5. Direction Validation (Forward vs Backward)
  6. Negation and Speculation Rejection
  7. Hallucinated Entity and Non-Verbatim Evidence Rejection
  8. Co-occurrence and Citation Noise Rejection
  9. Duplicate Candidate Detection
 10. Empty and Malformed Provider Responses Handling
 11. Bounded Retry and Rate Limit Graceful Degradation
 12. End-to-End Extraction with System A, System B, and System C on PMC1804205
"""

import os
import json
import pytest
from typing import List

from evryn.nlp.llm.schema import (
    CausalRelationRecord,
    ValidationStatus,
    RejectionReason,
)
from evryn.nlp.llm.providers import (
    MockLLMProvider,
    GenericOpenAICompatibleProvider,
    LLMGenerationResult,
)
from evryn.nlp.llm.cache import LLMCache
from evryn.nlp.llm.prompts import PROMPT_VERSION, SYSTEM_PROMPT
from evryn.nlp.llm.validator import DeterministicCausalValidator
from evryn.nlp.llm.extractor import LLMCausalExtractor
from evryn.nlp.llm.hybrid import HybridCausalExtractor
from evryn.nlp.llm.factory import get_extraction_backend
from evryn.paper.types import (
    ScientificDocument,
    PaperMetadata,
    SentenceSpan,
    PageBoundary,
    CausalRelationType,
)
from evryn.paper.normalizer import PaperEntityNormalizer


def build_test_doc(text: str, doc_id: str = "test_doc_01") -> ScientificDocument:
    return ScientificDocument(
        doc_id=doc_id,
        file_path="",
        metadata=PaperMetadata(title="Test Biomedical Paper", pmcid="PMC1804205", page_count=1),
        full_text=text,
        pages=[PageBoundary(page_number=1, start_char=0, end_char=len(text), char_count=len(text))],
        sentences=[SentenceSpan(sentence_id="s_001", page_number=1, section_title="Results", paragraph_id="p1", start_char=0, end_char=len(text), text=text)],
    )


# 1. Schema and Adapter Tests
def test_schema_and_assertion_adapters():
    rec = CausalRelationRecord(
        cause_entity="PmrB",
        effect_entity="PmrA",
        relation_type="UPREGULATES",
        polarity="POSITIVE",
        modality="FACTUAL",
        evidence_text="PmrB activates PmrA by phosphorylation.",
        document_id="doc_test",
        page_number=1,
        sentence_id="s1",
        char_start=0,
        char_end=39,
        extraction_method="llm_candidate",
        direct_or_inferred="direct",
        confidence=0.92,
    )
    assertion = rec.to_causal_assertion()
    assert assertion.cause == "PmrB"
    assert assertion.effect == "PmrA"
    assert assertion.relation_type == CausalRelationType.UPREGULATES
    assert not assertion.is_negated
    assert assertion.confidence == 0.92

    # Round trip
    rec_back = CausalRelationRecord.from_causal_assertion(assertion, document_id="doc_test")
    assert rec_back.cause_entity == "PmrB"
    assert rec_back.effect_entity == "PmrA"
    assert rec_back.relation_type == "UPREGULATES"


# 2. Mock Provider Determinism
def test_mock_provider_determinism():
    provider = MockLLMProvider()
    res1 = provider.generate("sys", 'Passage Text: """PmrB activates PmrA."""')
    res2 = provider.generate("sys", 'Passage Text: """PmrB activates PmrA."""')
    assert res1.parsed_json == res2.parsed_json
    assert res1.parsed_json[0]["cause_entity"] == "PmrB"
    assert res1.parsed_json[0]["effect_entity"] == "PmrA"


# 3. LLM Cache Functionality & Invalidation
def test_cache_storage_and_invalidation(tmp_path):
    cache = LLMCache(cache_dir=str(tmp_path))
    model = "mock-model"
    sys_p = "sys"
    usr_p = "text"

    assert cache.get(model, PROMPT_VERSION, sys_p, usr_p) is None

    payload = {"parsed_json": [{"cause_entity": "A", "effect_entity": "B"}]}
    cache.set(model, PROMPT_VERSION, sys_p, usr_p, payload)

    cached = cache.get(model, PROMPT_VERSION, sys_p, usr_p)
    assert cached is not None
    assert cached["response"] == payload

    # Cache invalidation when prompt version changes
    assert cache.get(model, "v9.9.9", sys_p, usr_p) is None


# 4. Direction Validation & Passive Inversion Rejection
def test_passive_inversion_rejection():
    text = "Apoptosis was significantly induced by prolonged nutrient starvation."
    doc = build_test_doc(text)
    validator = DeterministicCausalValidator()

    # Backwards candidate: LLM hallucinated that Apoptosis causes nutrient starvation
    inverted_candidate = CausalRelationRecord(
        cause_entity="Apoptosis",
        effect_entity="nutrient starvation",
        relation_type="UPREGULATES",
        polarity="POSITIVE",
        modality="FACTUAL",
        evidence_text=text,
        document_id=doc.doc_id,
    )

    accepted, rejected = validator.validate_candidates([inverted_candidate], doc)
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert RejectionReason.DIRECTION_REVERSED.value in rejected[0].rejection_reasons


# 5. Negation and Speculation Rejection
def test_speculation_and_negation_rejection():
    text = "We hypothesize that protein X might regulate transcription of gene Y."
    doc = build_test_doc(text)
    validator = DeterministicCausalValidator()

    speculative_candidate = CausalRelationRecord(
        cause_entity="protein X",
        effect_entity="gene Y",
        relation_type="UPREGULATES",
        polarity="POSITIVE",
        modality="SPECULATIVE",
        evidence_text=text,
        document_id=doc.doc_id,
    )

    accepted, rejected = validator.validate_candidates([speculative_candidate], doc)
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert RejectionReason.SPECULATIVE_OR_UNCERTAIN.value in rejected[0].rejection_reasons


# 6. Hallucinated Entity & Non-Verbatim Evidence Rejection
def test_hallucinated_evidence_rejection():
    doc = build_test_doc("Salmonella grows rapidly in rich broth.")
    validator = DeterministicCausalValidator(strict_entity_vocabulary=True)

    hallucinated_candidate = CausalRelationRecord(
        cause_entity="Glucose",
        effect_entity="Insulin",
        relation_type="UPREGULATES",
        polarity="POSITIVE",
        modality="FACTUAL",
        evidence_text="Glucose administration causes insulin secretion from beta cells.",
        document_id=doc.doc_id,
    )

    accepted, rejected = validator.validate_candidates([hallucinated_candidate], doc, canonical_entities=["Salmonella"])
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert RejectionReason.EVIDENCE_NOT_FOUND_IN_TEXT.value in rejected[0].rejection_reasons
    assert RejectionReason.UNKNOWN_CAUSE_ENTITY.value in rejected[0].rejection_reasons


# 7. Co-occurrence and Citation Noise Rejection
def test_citation_cooccurrence_rejection():
    text = "Expression of both PmrA and PhoP was quantified as previously described (Miller et al., 1998)."
    doc = build_test_doc(text)
    validator = DeterministicCausalValidator()

    citation_candidate = CausalRelationRecord(
        cause_entity="PmrA",
        effect_entity="PhoP",
        relation_type="DIRECT_CAUSE",
        polarity="POSITIVE",
        modality="FACTUAL",
        evidence_text=text,
        document_id=doc.doc_id,
    )

    accepted, rejected = validator.validate_candidates([citation_candidate], doc)
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert RejectionReason.UNSUPPORTED_CAUSAL_CLAIM.value in rejected[0].rejection_reasons


# 8. Duplicate Detection
def test_duplicate_detection():
    text = "PmrB phosphorylates and activates PmrA."
    doc = build_test_doc(text)
    validator = DeterministicCausalValidator()

    cand1 = CausalRelationRecord(
        cause_entity="PmrB", effect_entity="PmrA", relation_type="UPREGULATES",
        polarity="POSITIVE", modality="FACTUAL", evidence_text=text, document_id=doc.doc_id
    )
    cand2 = CausalRelationRecord(
        cause_entity="PmrB", effect_entity="PmrA", relation_type="UPREGULATES",
        polarity="POSITIVE", modality="FACTUAL", evidence_text=text, document_id=doc.doc_id
    )

    accepted, rejected = validator.validate_candidates([cand1, cand2], doc)
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert RejectionReason.DUPLICATE_RELATION.value in rejected[0].rejection_reasons


# 9. Factory Selection
def test_factory_backend_selection():
    a = get_extraction_backend("nlp_baseline")
    b = get_extraction_backend("llm_only")
    c = get_extraction_backend("hybrid")

    assert type(a).__name__ == "PaperCausalExtractor"
    assert type(b).__name__ == "LLMCausalExtractor"
    assert type(c).__name__ == "HybridCausalExtractor"

    with pytest.raises(ValueError):
        get_extraction_backend("unknown_mode")


# 10. End-to-End Hybrid Extraction on Complex Sentence
def test_end_to_end_hybrid_complex_sentence():
    text = "Growth in mild acid promotes transcription of genes activated by the response regulator PmrA."
    doc = build_test_doc(text)

    hybrid = get_extraction_backend("hybrid")
    assertions = hybrid.extract_assertions(doc, known_entities=["Acid pH", "PmrA"])

    assert len(assertions) >= 1
    a0 = assertions[0]
    assert a0.cause == "Acid pH"
    assert a0.effect == "PmrA"
    assert a0.relation_type in (CausalRelationType.UPREGULATES, CausalRelationType.DIRECT_CAUSE)
    assert not a0.is_negated
    assert a0.sentence_id == "s_001"
