"""Tests for EVRYN Phase 1.10 advanced causal relation extraction improvements.

Covers:
1. TCSTS_AND_RE strict syntax (rejecting comma gene lists, accepting genuine TCSTS pairs).
2. Genomic locus encoding inference (e.g. 89K -> SalK).
3. Mutant resistance defect inference (e.g. SalR -> PMN Resistance).
4. Speculative framing validation (filtering out hypothetical edges).
5. Coordinate sibling validation (filtering out intra-operon/intra-list co-member edges).
6. Configurable ablation flags.
"""

import pytest
from evryn.paper.types import ScientificDocument, SentenceSpan, PaperMetadata, CausalRelationType
from evryn.paper.extractor import PaperCausalExtractor, TCSTS_AND_RE
from evryn.paper.normalizer import PaperEntityNormalizer


def test_tcsts_and_re_strict_syntax():
    """Verify that TCSTS_AND_RE matches authentic two-component systems and rejects comma-separated gene lists."""
    # Authentic TCSTS mentions
    pos1 = "SalK and the cognate sensor kinase SalR, forming a two-component regulatory system"
    pos2 = "FimS and FimR which constitute a two-component system"
    pos3 = "PmrA and PmrB forming a regulatory system"
    
    assert TCSTS_AND_RE.search(pos1) is not None
    assert TCSTS_AND_RE.search(pos2) is not None
    assert TCSTS_AND_RE.search(pos3) is not None

    # False positive mentions (e.g., coordinate lists or gene lists with commas)
    neg1 = "hilA and invF, which are transcriptional activators"
    neg2 = "invF and hilA, as previously described"
    neg3 = "Smith and Jones, 2004"
    
    assert TCSTS_AND_RE.search(neg1) is None
    assert TCSTS_AND_RE.search(neg2) is None
    assert TCSTS_AND_RE.search(neg3) is None


def test_locus_encoding_inference():
    """Verify genomic locus encoding extraction (e.g. 89K -> SalK)."""
    normalizer = PaperEntityNormalizer()
    extractor = PaperCausalExtractor(normalizer=normalizer, enable_locus_encoding_inference=True)
    
    sent_text = (
        "The salK and salR genes were located in the candidate 89K pathogenicity island (PAI) of S. suis."
    )
    doc = ScientificDocument(
        doc_id="PMC2358977",
        file_path="/tmp/PMC2358977.xml",
        metadata=PaperMetadata(title="Test PAI Locus Encoding", authors=["Test Author"]),
        sentences=[
            SentenceSpan(
                sentence_id="PMC2358977_s001",
                page_number=1,
                section_title="Results",
                paragraph_id="p1",
                start_char=0,
                end_char=len(sent_text),
                text=sent_text,
            )
        ],
        full_text=sent_text,
    )
    
    known = ["89K", "SalK", "SalR", "Virulence"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    
    assert ("89K", "SalK") in pairs
    
    # Test ablation flag disable
    extractor_off = PaperCausalExtractor(normalizer=normalizer, enable_locus_encoding_inference=False)
    assertions_off = extractor_off.extract_assertions(doc, known_entities=known)
    pairs_off = [(a.cause_canonical, a.effect_canonical) for a in assertions_off]
    assert ("89K", "SalK") not in pairs_off


def test_phenotype_defect_inference():
    """Verify mutant phenotype resistance defect inference (e.g. SalR -> PMN Resistance)."""
    normalizer = PaperEntityNormalizer()
    extractor = PaperCausalExtractor(normalizer=normalizer, enable_phenotype_defect_inference=True)
    
    sent_text = (
        "In vitro killing assays showed that the ΔsalKR mutant was less able to resist killing by PMNs "
        "compared to wild-type strains."
    )
    doc = ScientificDocument(
        doc_id="PMC2358977",
        file_path="/tmp/PMC2358977.xml",
        metadata=PaperMetadata(title="Test Resistance Phenotype", authors=["Test Author"]),
        sentences=[
            SentenceSpan(
                sentence_id="PMC2358977_s002",
                page_number=3,
                section_title="Results",
                paragraph_id="p1",
                start_char=0,
                end_char=len(sent_text),
                text=sent_text,
            )
        ],
        full_text=sent_text,
    )
    
    known = ["SalK", "SalR", "PMN Resistance", "Virulence"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    
    assert ("SalR", "PMN Resistance") in pairs
    
    # Test ablation flag disable
    extractor_off = PaperCausalExtractor(normalizer=normalizer, enable_phenotype_defect_inference=False)
    assertions_off = extractor_off.extract_assertions(doc, known_entities=known)
    pairs_off = [(a.cause_canonical, a.effect_canonical) for a in assertions_off]
    assert ("SalR", "PMN Resistance") not in pairs_off


def test_speculation_and_coordinate_filtering():
    """Verify that speculative framing and coordinate list members do not form spurious causal edges."""
    normalizer = PaperEntityNormalizer()
    extractor = PaperCausalExtractor(normalizer=normalizer, enable_speculation_and_sibling_validation=True)
    
    sent1 = (
        "From these results, we speculated that Mlc was regulating hilA and invF transcription through HilD."
    )
    sent2 = (
        "SPI1 encodes numerous virulence factors, which include hilA, invF, hilC and hilD."
    )
    full_text = f"{sent1} {sent2}"
    
    doc = ScientificDocument(
        doc_id="PMC1874608",
        file_path="/tmp/PMC1874608.xml",
        metadata=PaperMetadata(title="Test Speculation Filter", authors=["Test Author"]),
        sentences=[
            SentenceSpan(
                sentence_id="PMC1874608_s001",
                page_number=2,
                section_title="Discussion",
                paragraph_id="p1",
                start_char=0,
                end_char=len(sent1),
                text=sent1,
            ),
            SentenceSpan(
                sentence_id="PMC1874608_s002",
                page_number=2,
                section_title="Introduction",
                paragraph_id="p2",
                start_char=len(sent1) + 1,
                end_char=len(full_text),
                text=sent2,
            ),
        ],
        full_text=full_text,
    )
    
    known = ["Mlc", "HilA", "InvF", "HilD", "HilC", "SPI1"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    
    # Speculative edges should be rejected
    assert ("Mlc", "HilA") not in pairs
    assert ("Mlc", "InvF") not in pairs
    assert ("HilA", "HilD") not in pairs
    
    # Coordinate list members should not form direct regulation of the locus
    assert ("HilD", "SPI1") not in pairs
    assert ("HilA", "SPI1") not in pairs
