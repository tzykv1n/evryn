"""
Unit and regression tests for EVRYN Phase 1.13 scientific causal extraction improvements.
Covers:
1. Genus abbreviation sentence boundary protection in both PaperSegmenter and PMCOAIngester.
2. Cross-page domain invariant gating (terminal sink phenotypes and TCSTS reverse pairs).
3. Investigative objective potential framing filtering.
4. Terminal phenotype directional invariant enforcement for secretion machinery.
"""

import pytest
from evryn.paper.segmentation import PaperSegmenter
from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.paper.cross_page_linker import CrossPageLinker, TERMINAL_PHENOTYPES, TCSTS_REVERSE_PAIRS
from evryn.paper.types import (
    CausalAssertion,
    EvidenceStatus,
    CausalRelationType,
    ScientificDocument,
    SentenceSpan,
    PaperMetadata,
)
from evryn.paper.extractor import PaperCausalExtractor


def test_genus_abbreviation_segmentation_protection():
    segmenter = PaperSegmenter()
    text = (
        "The authors have recently demonstrated that both fimbriae are required for formation of P. gingivalis biofilms. "
        "Furthermore, M. tuberculosis survives inside human macrophages for extended periods. "
        "In contrast, S. enterica invades epithelial cells through SPI1."
    )
    splits = segmenter._split_sentences_with_offsets(text, 0)
    assert len(splits) == 3, f"Expected 3 sentences, got {len(splits)}: {[s[2] for s in splits]}"
    assert "P. gingivalis biofilms" in splits[0][2]
    assert "M. tuberculosis survives" in splits[1][2]
    assert "S. enterica invades" in splits[2][2]


def test_pmc_oa_ingester_sentence_split_genus_protection():
    ingester = PMCOAIngester()
    text = "Expression of mfa1 in P. gingivalis is essential for biofilm microcolonies. Also, E. coli was tested."
    sents = ingester._split_sentences(text)
    assert len(sents) == 2, f"Expected 2 sentences, got {len(sents)}: {sents}"
    assert "P. gingivalis" in sents[0]
    assert "E. coli" in sents[1]


def test_cross_page_linker_terminal_phenotype_intermediate_rejection():
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, enable_transitive_invariants=True)
    # geneA -> biofilm (page 1), biofilm -> geneB (page 3)
    # Should NOT produce geneA -> geneB via biofilm intermediate sink
    a1 = CausalAssertion(
        assertion_id="a1",
        cause="geneA",
        cause_canonical="geneA",
        effect="biofilm",
        effect_canonical="biofilm",
        direction="FORWARD",
        relation_type=CausalRelationType.UPREGULATES,
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s1",
        page_number=1,
        section_title="Results",
        confidence=0.90,
        evidence_quote="geneA regulates biofilm.",
        char_span=(0, 20),
    )
    a2 = CausalAssertion(
        assertion_id="a2",
        cause="biofilm",
        cause_canonical="biofilm",
        effect="geneB",
        effect_canonical="geneB",
        direction="FORWARD",
        relation_type=CausalRelationType.UPREGULATES,
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s2",
        page_number=3,
        section_title="Discussion",
        confidence=0.85,
        evidence_quote="biofilm promotes geneB expression.",
        char_span=(0, 30),
    )
    links = linker.find_cross_page_links([a1, a2])
    trans_pairs = [(l.source_entity, l.target_entity) for l in links if l.linking_mechanism == "transitive_chain"]
    assert ("geneA", "geneB") not in trans_pairs, f"Spurious transitive link through biofilm sink was not filtered: {trans_pairs}"


def test_cross_page_linker_tcsts_reverse_pair_rejection():
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, enable_transitive_invariants=True)
    # SlyA -> SsrB is forward. Transitive reverse SsrB -> SlyA must be pruned.
    a1 = CausalAssertion(
        assertion_id="a1",
        cause="ssrB",
        cause_canonical="ssrb",
        effect="nodeX",
        effect_canonical="nodex",
        direction="FORWARD",
        relation_type=CausalRelationType.UPREGULATES,
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s1",
        page_number=1,
        section_title="Results",
        confidence=0.88,
        evidence_quote="ssrB activates nodeX.",
        char_span=(0, 20),
    )
    a2 = CausalAssertion(
        assertion_id="a2",
        cause="nodeX",
        cause_canonical="nodex",
        effect="slyA",
        effect_canonical="slya",
        direction="FORWARD",
        relation_type=CausalRelationType.UPREGULATES,
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s2",
        page_number=2,
        section_title="Discussion",
        confidence=0.88,
        evidence_quote="nodeX activates slyA.",
        char_span=(0, 20),
    )
    links = linker.find_cross_page_links([a1, a2])
    trans_pairs = [(l.source_entity.lower(), l.target_entity.lower()) for l in links]
    assert ("ssrb", "slya") not in trans_pairs, "TCSTS reverse pair SsrB -> SlyA was erroneously linked."


def test_exploratory_potential_framing_rejection():
    extractor = PaperCausalExtractor()
    sent = SentenceSpan(
        sentence_id="s1",
        page_number=1,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=160,
        text="We analyzed the different mutant strains for their potential to induce T cell responses against ESAT-6.",
    )
    doc = ScientificDocument(
        doc_id="test_doc",
        file_path="test.xml",
        metadata=PaperMetadata(title="Test", authors=[], doi="", pmid="", pmcid="PMC001", journal="", page_count=1),
        full_text=sent.text,
        pages=[],
        sections=[],
        paragraphs=[],
        sentences=[sent],
    )
    assertions = extractor.extract_assertions(doc, known_entities=["ESAT-6", "T Cell Recognition"])
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    assert not any(p[1] == "T Cell Recognition" for p in pairs), f"Exploratory potential framing was not rejected: {pairs}"


def test_terminal_phenotype_t3ss_direction_invariant():
    extractor = PaperCausalExtractor()
    sent = SentenceSpan(
        sentence_id="s1",
        page_number=2,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=100,
        text="This process is rapid, specific and depends on the T3SS encoded within SPI1.",
    )
    doc = ScientificDocument(
        doc_id="test_doc2",
        file_path="test2.xml",
        metadata=PaperMetadata(title="Test 2", authors=[], doi="", pmid="", pmcid="PMC002", journal="", page_count=1),
        full_text=sent.text,
        pages=[],
        sections=[],
        paragraphs=[],
        sentences=[sent],
    )
    assertions = extractor.extract_assertions(doc, known_entities=["T3SS", "SPI1"])
    pairs = [(a.cause_canonical.lower(), a.effect_canonical.lower()) for a in assertions]
    assert ("t3ss", "spi1") not in pairs, f"Terminal phenotype T3SS was allowed as cause of SPI1: {pairs}"


def test_homology_and_opsonophagocytosis_invariants():
    extractor = PaperCausalExtractor()
    sent1 = SentenceSpan(
        sentence_id="s1",
        page_number=1,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=60,
        text="The S. equi genome encodes a Mac homologue SeMac.",
    )
    doc1 = ScientificDocument(
        doc_id="test_doc3",
        file_path="test3.xml",
        metadata=PaperMetadata(title="Test 3", authors=[], doi="", pmid="", pmcid="PMC003", journal="", page_count=1),
        full_text=sent1.text,
        pages=[],
        sections=[],
        paragraphs=[],
        sentences=[sent1],
    )
    assertions1 = extractor.extract_assertions(doc1, known_entities=["Mac", "SeMac"])
    assert len(assertions1) == 0, f"Homology sentence was not filtered: {assertions1}"

    sent2 = SentenceSpan(
        sentence_id="s2",
        page_number=1,
        section_title="Results",
        paragraph_id="p2",
        start_char=0,
        end_char=80,
        text="Opsonophagocytosis induces expression of SeMac.",
    )
    doc2 = ScientificDocument(
        doc_id="test_doc4",
        file_path="test4.xml",
        metadata=PaperMetadata(title="Test 4", authors=[], doi="", pmid="", pmcid="PMC004", journal="", page_count=1),
        full_text=sent2.text,
        pages=[],
        sections=[],
        paragraphs=[],
        sentences=[sent2],
    )
    assertions2 = extractor.extract_assertions(doc2, known_entities=["Opsonophagocytosis", "SeMac"])
    pairs2 = [(a.cause_canonical.lower(), a.effect_canonical.lower()) for a in assertions2]
    assert ("opsonophagocytosis", "semac") not in pairs2, "Terminal phenotype opsonophagocytosis was allowed as cause of gene."
