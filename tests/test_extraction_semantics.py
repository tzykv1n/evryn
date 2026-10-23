"""
Comprehensive table-driven regression tests for EVRYN causal extraction semantics,
entity boundary cleaning, relative clause resolution, negation handling,
ontology classification, and quantitative delta rules.
"""

import pytest
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import (
    ScientificDocument,
    PageBoundary,
    PaperMetadata,
    ParagraphSpan,
    SentenceSpan,
    CausalRelationType,
    EvidenceStatus,
)
from evryn.web.extractor_service import (
    ExtractionService,
    infer_entity_category_and_confidence,
    decompose_concept_and_state,
    compute_edge_polarity_and_style,
)


def _make_doc(text: str) -> ScientificDocument:
    return ScientificDocument(
        doc_id="doc_semantics_test",
        file_path="test_semantics.pdf",
        metadata=PaperMetadata(title="Semantics Test"),
        full_text=text,
        pages=[PageBoundary(page_number=1, start_char=0, end_char=len(text), char_count=len(text))],
        sections=[],
        paragraphs=[ParagraphSpan(paragraph_id="p1", section_title="Results", page_number=1, start_char=0, end_char=len(text), text=text)],
        sentences=[SentenceSpan(sentence_id="s1", paragraph_id="p1", section_title="Results", page_number=1, start_char=0, end_char=len(text), text=text)],
    )


class TestCausalExtractionSemantics:
    """Verifies all mandatory test cases A through F in isolation and end-to-end."""

    def test_case_a_temperature_and_performance(self):
        """Case A: Increase in temperature causes decrease in performance."""
        svc = ExtractionService()
        text = "Increase in temperature causes decrease in performance."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "Temperature" in nodes
        assert "Performance" in nodes

        temp_node = nodes["Temperature"]
        perf_node = nodes["Performance"]

        assert temp_node["category"] == "Environmental Factor"
        assert temp_node["state"] == "Increase"
        assert temp_node["state_delta"] is None  # Never fabricate numeric delta without measurement!

        assert perf_node["category"] == "Measured Outcome"
        assert perf_node["state"] == "Decrease"
        assert perf_node["state_delta"] is None

        rels = res["relations"]
        assert len(rels) >= 1
        r = next(r for r in rels if r["cause_name"] == "Temperature" and r["effect_name"] == "Performance")
        assert r["relation_type"] == "DIRECT_CAUSE"
        assert r["effect_polarity"] == "negative"
        assert r["assertion_status"] == "affirmed"
        assert r["is_negated"] is False

    def test_case_b_hsp90_and_apoptosis_relative_clause(self):
        """Case B: Heat activates HSP90, which suppresses cellular apoptosis."""
        svc = ExtractionService()
        text = "Heat activates HSP90, which suppresses cellular apoptosis."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "Heat" in nodes
        assert "HSP90" in nodes
        assert "Apoptosis" in nodes

        assert nodes["Heat"]["category"] == "Environmental Factor"
        assert nodes["HSP90"]["category"] == "Gene/Protein"
        assert nodes["Apoptosis"]["category"] == "Biological Process"

        rels = res["relations"]
        edge_pairs = {(r["cause_name"], r["effect_name"]): r for r in rels}

        # Must extract Heat -> HSP90 (+)
        assert ("Heat", "HSP90") in edge_pairs
        r1 = edge_pairs[("Heat", "HSP90")]
        assert r1["relation_type"] == "UPREGULATES"
        assert r1["effect_polarity"] == "positive"

        # Must extract HSP90 -> Apoptosis (-)
        assert ("HSP90", "Apoptosis") in edge_pairs
        r2 = edge_pairs[("HSP90", "Apoptosis")]
        assert r2["relation_type"] == "DOWNREGULATES"
        assert r2["effect_polarity"] == "negative"

        # Must NOT form direct Heat -> Apoptosis shortcut
        assert ("Heat", "Apoptosis") not in edge_pairs

    def test_case_c_tp53_strip_section_heading(self):
        """Case C: Introduction\\nTP53 regulates cell cycle progression."""
        svc = ExtractionService()
        text = "Introduction\nTP53 regulates cell cycle progression."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "TP53" in nodes
        assert "Cell Cycle Progression" in nodes

        # Section header 'Introduction' must not be in any node
        for n_name in nodes.keys():
            assert "introduction" not in n_name.lower()

        assert nodes["TP53"]["category"] == "Gene/Protein"
        assert nodes["Cell Cycle Progression"]["category"] == "Biological Process"

        rels = res["relations"]
        assert any(r["cause_name"] == "TP53" and r["effect_name"] == "Cell Cycle Progression" for r in rels)

    def test_case_d_atm_chk2_cdk2_chain(self):
        """Case D: Activation of ATM phosphorylates CHK2, which downregulates CDK2 activity."""
        svc = ExtractionService()
        text = "Activation of ATM phosphorylates CHK2, which downregulates CDK2 activity."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "ATM" in nodes
        assert "CHK2" in nodes
        assert "CDK2" in nodes

        for name in ("ATM", "CHK2", "CDK2"):
            assert nodes[name]["category"] == "Gene/Protein"

        rels = res["relations"]
        edge_pairs = {(r["cause_name"], r["effect_name"]): r for r in rels}

        # Must have ATM -> CHK2 (+)
        assert ("ATM", "CHK2") in edge_pairs
        assert edge_pairs[("ATM", "CHK2")]["relation_type"] == "UPREGULATES"
        assert edge_pairs[("ATM", "CHK2")]["effect_polarity"] == "positive"

        # Must have CHK2 -> CDK2 (-)
        assert ("CHK2", "CDK2") in edge_pairs
        assert edge_pairs[("CHK2", "CDK2")]["relation_type"] == "DOWNREGULATES"
        assert edge_pairs[("CHK2", "CDK2")]["effect_polarity"] == "negative"

        # Must NOT collapse into direct ATM -> CDK2
        assert ("ATM", "CDK2") not in edge_pairs

    def test_case_e_cdk2_inhibition_prevents_dna_synthesis(self):
        """Case E: Results\\nCDK2 inhibition prevents DNA synthesis."""
        svc = ExtractionService()
        text = "Results\nCDK2 inhibition prevents DNA synthesis."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "CDK2" in nodes
        assert "DNA synthesis" in nodes

        # Section header 'Results' must NOT be in any node
        for n_name in nodes.keys():
            assert "results" not in n_name.lower()

        assert nodes["CDK2"]["category"] == "Gene/Protein"
        assert nodes["CDK2"]["state"] in ("Decrease", "Inhibited")
        assert nodes["CDK2"]["state_delta"] is None  # '2' in CDK2 must not be treated as delta!

        assert nodes["DNA synthesis"]["category"] == "Biological Process"

        rels = res["relations"]
        r = next(r for r in rels if r["cause_name"] == "CDK2" and r["effect_name"] == "DNA synthesis")
        assert r["relation_type"] == "PREVENTS"
        assert r["effect_polarity"] == "negative"  # PREVENTS is inherently negative, never positive!

    def test_case_f_passive_construction(self):
        """Case F: Consequently, cellular apoptosis is induced by prolonged arrest."""
        svc = ExtractionService()
        text = "Consequently, cellular apoptosis is induced by prolonged arrest."
        res = svc.process_text_input(text)

        nodes = {n["canonical_name"]: n for n in res["nodes"]}
        assert "Prolonged Arrest" in nodes
        assert "Apoptosis" in nodes

        # Neither node may have 'cellular' or 'by' as noise
        assert "by" not in nodes["Prolonged Arrest"]["canonical_name"].lower().split()
        assert "cellular" not in nodes["Apoptosis"]["canonical_name"].lower().split()

        rels = res["relations"]
        # Must have Prolonged Arrest -> Apoptosis (+)
        assert any(r["cause_name"] == "Prolonged Arrest" and r["effect_name"] == "Apoptosis" for r in rels)

        # Must NOT generate reversed Apoptosis -> Prolonged Arrest
        assert not any(r["cause_name"] == "Apoptosis" and r["effect_name"] == "Prolonged Arrest" for r in rels)


class TestEntityTaxonomyAndDeltaContract:
    """Verifies ontology classification, state separation, and numeric delta rules."""

    def test_ontology_category_classification(self):
        cases = [
            ("TP53", "Gene/Protein"),
            ("ATM", "Gene/Protein"),
            ("HSP90", "Gene/Protein"),
            ("CDK2", "Gene/Protein"),
            ("Cell Cycle Progression", "Biological Process"),
            ("DNA synthesis", "Biological Process"),
            ("Apoptosis", "Biological Process"),
            ("Temperature", "Environmental Factor"),
            ("Humidity", "Environmental Factor"),
            ("Performance", "Measured Outcome"),
            ("Accuracy", "Measured Outcome"),
            ("Latency", "Measured Outcome"),
            ("LPS", "Chemical"),
            ("Glucose", "Chemical"),
            ("Tumorigenesis", "Phenotype"),
        ]
        for term, expected_cat in cases:
            cat, conf, rationale = infer_entity_category_and_confidence(term)
            assert cat == expected_cat, f"Expected {term} -> {expected_cat}, got {cat} ({rationale})"
            assert 0.0 <= conf <= 1.0

    def test_state_and_delta_decomposition(self):
        # Without numeric measurement: delta must be None
        c1, s1, d1, cat1 = decompose_concept_and_state("Increase in temperature")
        assert c1 == "Temperature"
        assert s1 == "Increase"
        assert d1 is None

        c2, s2, d2, cat2 = decompose_concept_and_state("decrease in performance")
        assert c2 == "Performance"
        assert s2 == "Decrease"
        assert d2 is None

        # With explicit numeric measurement: delta must be numeric
        c3, s3, d3, cat3 = decompose_concept_and_state("15% decrease in performance")
        assert c3 == "Performance"
        assert s3 == "Decrease"
        assert d3 == -15.0

        c4, s4, d4, cat4 = decompose_concept_and_state("2.5-fold increase in temperature")
        assert c4 == "Temperature"
        assert s4 == "Increase"
        assert d4 == 2.5

    def test_compute_edge_polarity(self):
        # Negated relation -> unknown / neutral
        p1, col1, sty1 = compute_edge_polarity_and_style("DIRECT_CAUSE", is_negated=True)
        assert p1 == "unknown"
        assert sty1 == "dashed"

        # Downregulates / Inhibits / Prevents -> always negative
        for rel in ["DOWNREGULATES", "INHIBITS", "PREVENTS", "SUPPRESSES", "BLOCKS"]:
            p, col, sty = compute_edge_polarity_and_style(rel, cause_state="Increase", effect_state="Decrease")
            assert p == "negative"
            assert col == "#dc2626"

        # Direct cause with opposing states -> negative
        p_opp, _, _ = compute_edge_polarity_and_style("DIRECT_CAUSE", cause_state="Increase", effect_state="Decrease")
        assert p_opp == "negative"

        # Direct cause with reinforcing states -> positive
        p_reinf, _, _ = compute_edge_polarity_and_style("DIRECT_CAUSE", cause_state="Increase", effect_state="Increase")
        assert p_reinf == "positive"
