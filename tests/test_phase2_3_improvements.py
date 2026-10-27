import pytest
from evryn.paper.types import (
    ScientificDocument,
    SentenceSpan,
    PaperMetadata,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
    CrossPageLink,
)
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker


def make_doc(sentences_text: list) -> ScientificDocument:
    spans = []
    char_offset = 0
    for idx, (p_num, sec, text) in enumerate(sentences_text):
        s_id = f"sent_{idx+1}"
        spans.append(
            SentenceSpan(
                sentence_id=s_id,
                paragraph_id=f"p_{idx+1}",
                text=text,
                page_number=p_num,
                start_char=char_offset,
                end_char=char_offset + len(text),
                section_title=sec,
            )
        )
        char_offset += len(text) + 1
    return ScientificDocument(
        doc_id="test_doc_p23",
        file_path="dummy.pdf",
        metadata=PaperMetadata(title="Test Paper"),
        full_text="\n".join([s[2] for s in sentences_text]),
        sentences=spans,
    )


class TestPhase23Improvements:

    def test_intent_preamble_suppression(self):
        """Pre-clauses stating experimental intent ('To identify...') must not emit causal relations."""
        extractor = PaperCausalExtractor()
        doc = make_doc([
            (
                7,
                "Results",
                "To identify the target gene in SPI1 that is regulated by Mlc, the expression patterns of the SPI1-regulatory genes were examined.",
            )
        ])
        known = ["Mlc", "SPI1", "HilA", "InvF"]
        asrt = extractor.extract_assertions(doc, known_entities=known)
        # Should not extract Mlc -> SPI1 from within the introductory infinitive intent clause
        pairs = [(a.cause_canonical, a.effect_canonical) for a in asrt if not a.is_negated]
        assert ("Mlc", "SPI1") not in pairs

    def test_evidential_reporting_boundary_rejection(self):
        """Entities before and after evidential complement clauses (', which suggests that') must not cross-pair."""
        extractor = PaperCausalExtractor()
        doc = make_doc([
            (
                12,
                "Results",
                "The over-expression of hilC suppressed the hilD mutation, thereby promoting high levels of hilA and invF expression, which suggests that HilC can partially compensate for the loss of function of HilD.",
            )
        ])
        known = ["HilC", "HilD", "HilA", "InvF"]
        asrt = extractor.extract_assertions(doc, known_entities=known)
        pairs = [(a.cause_canonical, a.effect_canonical) for a in asrt if not a.is_negated]
        assert ("HilA", "HilD") not in pairs
        assert ("InvF", "HilD") not in pairs

    def test_strain_construct_modifier_exclusion(self):
        """Strain identifiers with double-colon construct notation (H37Ra::phoP) must not be parsed as molecular entities."""
        norm = PaperEntityNormalizer()
        text = "In contrast, splenocytes from H37Ra::phoP inoculated mice showed very strong IFN-gamma production in response to incubation with ESAT-6."
        known = ["PhoP", "ESAT-6"]
        detected = norm.detect_entities_in_sentence(text, known_entities=known)
        detected_canon = [d[1] for d in detected]
        assert "ESAT-6" in detected_canon
        assert "PhoP" not in detected_canon

    def test_cross_page_link_rich_evidence_retention(self):
        """Inferred cross-page paths must retain constituent edges, intermediate hops, inference rules, and provenance."""
        linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.50)
        a1 = CausalAssertion(
            assertion_id="asrt_001",
            cause="KinaseA",
            cause_canonical="KinaseA",
            effect="RegulatorB",
            effect_canonical="RegulatorB",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.05,
            sentence_id="s1",
            page_number=1,
            section_title="Introduction",
            confidence=0.95,
            evidence_quote="KinaseA activates RegulatorB upon environmental stimulus.",
            char_span=(0, 50),
            evidence_status=EvidenceStatus.MEASURED_FACT,
        )
        a2 = CausalAssertion(
            assertion_id="asrt_002",
            cause="RegulatorB",
            cause_canonical="RegulatorB",
            effect="TargetC",
            effect_canonical="TargetC",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.05,
            sentence_id="s2",
            page_number=3,
            section_title="Results",
            confidence=0.92,
            evidence_quote="Phosphorylated RegulatorB induces transcription of TargetC.",
            char_span=(0, 55),
            evidence_status=EvidenceStatus.MEASURED_FACT,
        )

        links = linker.find_cross_page_links([a1, a2])
        assert len(links) >= 1
        trans_link = [l for l in links if l.source_entity == "KinaseA" and l.target_entity == "TargetC"][0]
        assert trans_link.intermediate_entity == "RegulatorB"
        assert trans_link.distance_pages == 2
        assert trans_link.linking_mechanism == "transitive_chain"
        assert trans_link.inference_rule == "transitive_path_composition"
        assert trans_link.validation_status == "validated"
        assert len(trans_link.constituent_edges) == 2
        assert trans_link.constituent_edges[0]["source"] == "KinaseA"
        assert trans_link.constituent_edges[0]["target"] == "RegulatorB"
        assert trans_link.constituent_edges[1]["source"] == "RegulatorB"
        assert trans_link.constituent_edges[1]["target"] == "TargetC"
        assert trans_link.constituent_edges[0]["assertion_id"] == "asrt_001"
        assert trans_link.constituent_edges[1]["assertion_id"] == "asrt_002"

    def test_claim_grounding_rich_evidence(self):
        """Claim-to-evidence cross-page links must store constituent quotes from both pages."""
        linker = CrossPageLinker(min_page_distance=1)
        a1 = CausalAssertion(
            assertion_id="asrt_res",
            cause="LigandX",
            cause_canonical="LigandX",
            effect="PathwayY",
            effect_canonical="PathwayY",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.05,
            sentence_id="s1",
            page_number=2,
            section_title="Results",
            confidence=0.95,
            evidence_quote="LigandX directly stimulates PathwayY.",
            char_span=(0, 40),
            evidence_status=EvidenceStatus.MEASURED_FACT,
        )
        a2 = CausalAssertion(
            assertion_id="asrt_disc",
            cause="LigandX",
            cause_canonical="LigandX",
            effect="PathwayY",
            effect_canonical="PathwayY",
            direction="FORWARD",
            relation_type=CausalRelationType.UPREGULATES,
            is_negated=False,
            uncertainty_score=0.10,
            sentence_id="s2",
            page_number=6,
            section_title="Discussion",
            confidence=0.90,
            evidence_quote="Our findings establish that LigandX stimulates PathwayY.",
            char_span=(0, 50),
            evidence_status=EvidenceStatus.MEASURED_FACT,
        )

        links = linker.find_cross_page_links([a1, a2])
        assert len(links) == 1
        ground_link = links[0]
        assert ground_link.linking_mechanism == "claim_to_evidence_grounding"
        assert ground_link.inference_rule == "cross_section_grounding"
        assert len(ground_link.constituent_edges) == 2
        assert ground_link.constituent_edges[0]["page_number"] == 2
        assert ground_link.constituent_edges[1]["page_number"] == 6

    def test_repressed_in_mutant_directional_accuracy(self):
        """'expression of mfa1 was repressed threefold in the fimR mutant' -> FimR activates mfa1."""
        extractor = PaperCausalExtractor()
        doc = make_doc([
            (
                5,
                "Results",
                "The striking finding is that expression of the mfa1 gene was also repressed threefold in the fimR mutant.",
            )
        ])
        asrt = extractor.extract_assertions(doc, known_entities=["FimR", "mfa1"])
        assert len(asrt) >= 1
        a = asrt[0]
        assert a.cause_canonical == "FimR"
        assert a.effect_canonical == "mfa1"
        assert a.relation_type == CausalRelationType.UPREGULATES

    def test_phase1_baseline_independent_execution(self):
        """Phase 1 baseline extractor must remain independently runnable and produce deterministic output."""
        extractor = PaperCausalExtractor()
        doc = make_doc([
            (
                1,
                "Abstract",
                "KinA promotes phosphorylation of RegB.",
            ),
            (
                3,
                "Results",
                "RegB triggers expression of EffectorC.",
            ),
        ])
        assertions = extractor.extract_assertions(doc)
        assert len(assertions) >= 2
        linker = CrossPageLinker(min_page_distance=1)
        links = linker.find_cross_page_links(assertions)
        assert any(l.source_entity == "KinA" and l.target_entity == "EffectorC" for l in links)
