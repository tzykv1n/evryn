"""
Unit and integration tests for EVRYN Phase 2.6:
1. Split-Graph UI data provenance (gold graphs built strictly and exclusively from ground truth).
2. Endpoint verification (/api/examples/gold/{pmcid}).
3. Targeted extraction repair for PMC1804205:
   - "responding to" passive direction inversion recovery (Acid pH -> PmrB).
   - "Because ... (Author et al., 1993)" cited literature preamble false positive suppression.
4. Cross-page linker invariant:
   - Accessory adapter proteins (PmrD) cannot initiate transitive chains into terminal resistance phenotypes.
5. Invariance & non-mutation:
   - Frozen ground truth remains immutable.
   - Phase 1 artifacts remain unaltered.
"""

import os
import json
import hashlib
import pytest
from fastapi.testclient import TestClient

from evryn.web.server import app
from evryn.paper.extractor import PaperCausalExtractor, CausalRelationType
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.types import ScientificDocument, SentenceSpan, PaperMetadata, ScientificSectionType
from evryn.paper.real_benchmark import convert_pmc_oa_to_scientific_document
from evryn.datasets.pmc_oa import PMCOAIngester

client = TestClient(app)

PHASE1_MAIN_HASH = "4e7eb0ffb6390260b4d0e8bea70abc420237d7a952ebd7fa977ad2db8b8fce5d"
PHASE1_PRESENTATION_HASH = "dfeafd264a583442d9cf8a647db5f0465d5cbeaf3f488135eb10138ebefc822b"


def test_phase1_artifacts_strictly_frozen():
    """Verify Phase 1 research artifacts remain untouched with identical cryptographic hashes."""
    main_path = "docs/phase1/main.pdf"
    pres_path = "docs/phase1/Temporal_Causal_Knowledge_Phase1_Presentation.pdf"

    assert os.path.exists(main_path), f"Missing {main_path}"
    assert os.path.exists(pres_path), f"Missing {pres_path}"

    with open(main_path, "rb") as f:
        h_main = hashlib.sha256(f.read()).hexdigest()
    assert h_main == PHASE1_MAIN_HASH, f"Phase 1 main.pdf modified! Hash: {h_main}"

    with open(pres_path, "rb") as f:
        h_pres = hashlib.sha256(f.read()).hexdigest()
    assert h_pres == PHASE1_PRESENTATION_HASH, f"Phase 1 presentation modified! Hash: {h_pres}"


def test_gold_standard_endpoint_provenance():
    """Verify /api/examples/gold/{pmcid} serves unmodified frozen ground truth without predictions."""
    res = client.get("/api/examples/gold/PMC1804205")
    assert res.status_code == 200
    gt = res.json()
    assert gt["pmcid"] == "PMC1804205"

    assert "canonical_entities" in gt
    assert "direct_edges" in gt
    assert "cross_page_edges" in gt

    # Ensure ground truth matches disk artifact exactly
    with open("data/real_papers/PMC1804205_ground_truth.json", "r") as f:
        disk_gt = json.load(f)

    assert gt["canonical_entities"] == disk_gt["canonical_entities"]
    assert gt["direct_edges"] == disk_gt["direct_edges"]
    assert gt["cross_page_edges"] == disk_gt["cross_page_edges"]


def test_gold_standard_endpoint_404_for_unknown():
    """Verify /api/examples/gold/{pmcid} cleanly returns 404 for unknown or synthetic papers."""
    res = client.get("/api/examples/gold/PMC9999999")
    assert res.status_code == 404
    assert "not found for PMC9999999" in res.json()["detail"]


def test_extraction_repair_passive_responding_to():
    """Verify 'is required for responding to' extracts backward stimulus -> responder direction."""
    extractor = PaperCausalExtractor()
    doc = ScientificDocument(
        doc_id="test_doc",
        file_path="",
        metadata=PaperMetadata(title="Test", pmcid="PMC1804205"),
        full_text="PmrA's cognate sensor kinase PmrB is required for responding to external changes in pH.",
        sentences=[
            SentenceSpan(
                sentence_id="s1", paragraph_id="p1", page_number=1,
                section_title="Abstract",
                text="PmrA's cognate sensor kinase PmrB is required for responding to external changes in pH.",
                start_char=0, end_char=88
            )
        ]
    )

    assertions = extractor.extract_assertions(doc, known_entities=["PmrA", "PmrB", "Acid pH"])
    # Must extract Acid pH -> PmrB (stimulus is cause, sensor is effect)
    stimulus_edges = [a for a in assertions if a.cause_canonical == "Acid pH" and a.effect_canonical == "PmrB"]
    assert len(stimulus_edges) >= 1, "Failed to extract Acid pH -> PmrB from 'is required for responding to'"
    # Inverted edge PmrB -> Acid pH must NOT be extracted
    inverted_edges = [a for a in assertions if a.cause_canonical == "PmrB" and a.effect_canonical == "Acid pH"]
    assert len(inverted_edges) == 0, f"Spurious inverted direction extracted: {inverted_edges}"


def test_extraction_repair_cited_preamble_suppression():
    """Verify introductory literature citation preamble 'Because ... (Author et al., Year)' is not extracted."""
    extractor = PaperCausalExtractor()
    doc = ScientificDocument(
        doc_id="test_doc",
        file_path="",
        metadata=PaperMetadata(title="Test", pmcid="PMC1804205"),
        full_text="Because the PmrA/PmrB system is required for resistance to the antimicrobial peptide polymyxin B (Roland et al., 1993), we hypothesized that mild acid pH could induce this resistance.",
        sentences=[
            SentenceSpan(
                sentence_id="s1", paragraph_id="p1", page_number=6,
                section_title="Mild acid pH induces resistance to the antimicrobial peptide polymyxin B",
                text="Because the PmrA/PmrB system is required for resistance to the antimicrobial peptide polymyxin B (Roland et al., 1993), we hypothesized that mild acid pH could induce this resistance.",
                start_char=0, end_char=186
            )
        ]
    )

    assertions = extractor.extract_assertions(doc, known_entities=["PmrA", "PmrB", "Polymyxin B", "Acid pH"])
    # PmrA -> Polymyxin B must NOT be extracted from the cited rationale clause
    pmra_poly = [a for a in assertions if a.cause_canonical == "PmrA" and a.effect_canonical == "Polymyxin B"]
    assert len(pmra_poly) == 0, f"False positive extracted from cited preamble: {pmra_poly}"


def test_cross_page_adapter_protein_invariant():
    """Verify adapter proteins (e.g. PmrD) cannot initiate transitive jumps into terminal resistance phenotypes."""
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, enable_transitive_invariants=True)

    from evryn.paper.types import CausalAssertion, EvidenceStatus, CausalRelationType

    # Create a chain: PmrD -> PmrA on page 2, PmrA -> LPS on page 3, LPS -> Polymyxin B on page 3
    assertions = [
        CausalAssertion(
            assertion_id="a1",
            cause="PmrD",
            cause_canonical="PmrD",
            effect="PmrA",
            effect_canonical="PmrA",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.1,
            sentence_id="s1",
            page_number=2,
            section_title="Intro",
            confidence=0.9,
            evidence_quote="PmrD favours phosphorylated PmrA",
            char_span=(0, 30),
        ),
        CausalAssertion(
            assertion_id="a2",
            cause="PmrA",
            cause_canonical="PmrA",
            effect="Lipopolysaccharide",
            effect_canonical="Lipopolysaccharide",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.1,
            sentence_id="s2",
            page_number=3,
            section_title="Results",
            confidence=0.9,
            evidence_quote="PmrA regulates LPS",
            char_span=(0, 20),
        ),
        CausalAssertion(
            assertion_id="a3",
            cause="Lipopolysaccharide",
            cause_canonical="Lipopolysaccharide",
            effect="Polymyxin B",
            effect_canonical="Polymyxin B",
            direction="FORWARD",
            relation_type=CausalRelationType.MEDIATES,
            is_negated=False,
            uncertainty_score=0.1,
            sentence_id="s3",
            page_number=3,
            section_title="Results",
            confidence=0.9,
            evidence_quote="LPS mediates Polymyxin B resistance",
            char_span=(0, 30),
        ),
    ]

    links = linker.find_cross_page_links(assertions)
    # PmrD -> Polymyxin B must NOT be formed
    pmrd_links = [l for l in links if l.source_entity == "PmrD" and l.target_entity == "Polymyxin B"]
    assert len(pmrd_links) == 0, f"Adapter protein PmrD generated transitive link to Polymyxin B: {pmrd_links}"
