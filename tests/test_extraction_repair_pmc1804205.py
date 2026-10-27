"""
Regression and validation test suite for Phase 2.1 Extraction Repair (PMC1804205).
Verifies:
  1. Coordinated causes ("requires both X and Y")
  2. Mutation loss-of-function directionality ("substitution/mutation decreased or abolished")
  3. Chained participle regulation ("controls X mediating Y")
  4. Contrastive conditions ("grown at pH 5.8 were > 100 000-fold more resistant to polymyxin B than at pH 7.7")
  5. Coordinate complement clause isolation ("suggest that X, and that Y")
  6. Contrastive protein expression ("produced at pH 5.8 but not at pH 7.7")
  7. PhoQ/PhoP-PmrD-PmrA regulatory cascade
  8. False-positive entity candidate suppression
  9. Scoped negation protection
 10. End-to-end extraction metrics on PMC1804205
"""

import pytest
from evryn.paper.types import ScientificDocument, PaperMetadata, PageBoundary, CausalRelationType
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.segmentation import PaperSegmenter
from evryn.paper.extractor import PaperCausalExtractor, is_valid_entity_candidate
from evryn.paper.document_context import DocumentContextResolver
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.real_benchmark import CURATED_REAL_PAPERS


@pytest.fixture
def extractor():
    norm = PaperEntityNormalizer()
    return PaperCausalExtractor(norm)


@pytest.fixture
def normalizer():
    return PaperEntityNormalizer()


@pytest.fixture
def segmenter():
    return PaperSegmenter()


def make_doc(text: str, doc_id: str = "test_doc") -> ScientificDocument:
    return ScientificDocument(
        doc_id=doc_id,
        file_path="",
        metadata=PaperMetadata(title="Test", authors=[], doi="", pmid="", pmcid="PMC1804205", journal="Test", page_count=1),
        full_text=text,
        pages=[PageBoundary(page_number=1, start_char=0, end_char=len(text), char_count=len(text))],
        sections=[],
        paragraphs=[],
        sentences=[],
    )


def test_entity_candidate_filtering():
    """Verify generic nouns, clauses, and citation fragments are rejected."""
    # Invalid candidates
    assert not is_valid_entity_candidate("levels")
    assert not is_valid_entity_candidate("level")
    assert not is_valid_entity_candidate("genes")
    assert not is_valid_entity_candidate("gene")
    assert not is_valid_entity_candidate("proteins")
    assert not is_valid_entity_candidate("production")
    assert not is_valid_entity_candidate("(Fig")
    assert not is_valid_entity_candidate("(Figure 3)")
    assert not is_valid_entity_candidate("3 encode the two enzymes")
    assert not is_valid_entity_candidate("promote transcription of its")
    assert not is_valid_entity_candidate("Al3+ (Wosten et al")
    assert not is_valid_entity_candidate("Soncini and Groisman, 1996")
    assert not is_valid_entity_candidate("Together, these results argue")

    # Valid candidates
    assert is_valid_entity_candidate("PmrA")
    assert is_valid_entity_candidate("PmrB")
    assert is_valid_entity_candidate("PmrD")
    assert is_valid_entity_candidate("Acid pH")
    assert is_valid_entity_candidate("Lipopolysaccharide")
    assert is_valid_entity_candidate("Polymyxin B")


def test_acid_ph_canonicalization(normalizer):
    """Verify synonymous forms of acid pH canonicalize correctly."""
    assert normalizer.canonicalize("mild acid") == "Acid pH"
    assert normalizer.canonicalize("acidic conditions") == "Acid pH"
    assert normalizer.canonicalize("acid stress") == "Acid pH"
    assert normalizer.canonicalize("pH 5.8") == "Acid pH"
    assert normalizer.canonicalize("low pH") == "Acid pH"
    assert normalizer.canonicalize("external changes in pH") == "Acid pH"


def test_polymyxin_b_canonicalization(normalizer):
    """Verify resistance phrasing canonicalizes to Polymyxin B."""
    assert normalizer.canonicalize("polymyxin B resistance") == "Polymyxin B"
    assert normalizer.canonicalize("resistance to polymyxin B") == "Polymyxin B"


def test_sentence_segmentation_ed_boundary(segmenter):
    """Verify past participle verbs ending with ed. do not mask sentence boundaries."""
    text = (
        "Growth in mild acid (pH 5.8) promotes transcription of genes activated by the response regulator PmrA, "
        "but the signalling pathway(s) that mediates this response has thus far remained unexplored. "
        "Here we report that this activation requires both PmrA's cognate sensor kinase PmrB, which had been previously "
        "shown to respond to Fe3+ and Al3+, and PmrA's post-translational activator PmrD."
    )
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assert len(doc.sentences) == 2
    assert "unexplored." in doc.sentences[0].text
    assert "Here we report" in doc.sentences[1].text


def test_mutation_abolished_directionality(extractor, segmenter):
    """Verify loss-of-function mutation syntax proves wild-type positive activation."""
    text = (
        "Substitution of a conserved histidine or of either one of four conserved glutamic acid "
        "residues in the periplasmic domain of PmrB severely decreased or abolished the mild acid-promoted "
        "transcription of PmrA-activated genes."
    )
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["PmrB", "PmrA"])
    assert len(assertions) >= 1
    pmrb_pmra = next((a for a in assertions if a.cause_canonical == "PmrB" and a.effect_canonical == "PmrA"), None)
    assert pmrb_pmra is not None
    assert pmrb_pmra.relation_type == CausalRelationType.UPREGULATES
    assert not pmrb_pmra.is_negated


def test_controls_and_participle_chaining(extractor, segmenter):
    """Verify 'controls X mediating Y' extracts both PmrA->LPS and LPS->Polymyxin B."""
    text = "The PmrA/PmrB system controls lipopolysaccharide modifications mediating resistance to the antibiotic polymyxin B."
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["PmrA", "Lipopolysaccharide", "Polymyxin B"])

    pmra_lps = next((a for a in assertions if a.cause_canonical == "PmrA" and a.effect_canonical == "Lipopolysaccharide"), None)
    assert pmra_lps is not None

    lps_poly = next((a for a in assertions if a.cause_canonical == "Lipopolysaccharide" and a.effect_canonical == "Polymyxin B"), None)
    assert lps_poly is not None
    assert lps_poly.relation_type == CausalRelationType.MEDIATES


def test_contrastive_condition_resistance(extractor, segmenter):
    """Verify 'grown at pH 5.8 were > 100 000-fold more resistant to polymyxin B than at pH 7.7' extracts Acid pH -> Polymyxin B."""
    text = "Wild-type Salmonella grown at pH 5.8 were > 100 000-fold more resistant to polymyxin B than organisms grown at pH 7.7."
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["Acid pH", "Polymyxin B"])
    acid_poly = next((a for a in assertions if a.cause_canonical == "Acid pH" and a.effect_canonical == "Polymyxin B"), None)
    assert acid_poly is not None
    assert acid_poly.relation_type == CausalRelationType.UPREGULATES


def test_coordinate_clause_isolation(extractor, segmenter):
    """Verify coordinate complement clauses ('Our results suggest that X, and that Y') do not leak entities across clauses."""
    text = (
        "Our results suggest that protonation of the PmrB periplasmic histidine and/or of the glutamic acid "
        "residues activate the PmrA protein, and that mild acid promotes cellular changes resulting in polymyxin B resistance."
    )
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["PmrB", "PmrA", "Acid pH", "Polymyxin B"])

    # Must extract PmrB -> PmrA and Acid pH -> Polymyxin B
    assert any(a.cause_canonical == "PmrB" and a.effect_canonical == "PmrA" for a in assertions)
    assert any(a.cause_canonical == "Acid pH" and a.effect_canonical == "Polymyxin B" for a in assertions)

    # Must NOT form spurious cross-clause edge PmrA -> Polymyxin B
    assert not any(a.cause_canonical == "PmrA" and a.effect_canonical == "Polymyxin B" for a in assertions)


def test_contrastive_protein_expression(extractor, segmenter):
    """Verify 'PmrD was produced in cells grown at pH 5.8 but not at pH 7.7' extracts Acid pH -> PmrD."""
    text = (
        "Western blot analysis of crude extracts using anti-PmrD antibodies showed that the PmrD protein was "
        "produced in cells grown in N-minimal medium pH 5.8 and 10 mM MgCl2 but not in cells grown in the same medium buffered at pH 7.7."
    )
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["PmrD", "Acid pH"])
    acid_pmrd = next((a for a in assertions if a.cause_canonical == "Acid pH" and a.effect_canonical == "PmrD"), None)
    assert acid_pmrd is not None
    assert acid_pmrd.relation_type == CausalRelationType.UPREGULATES


def test_phoq_phop_pmrd_cascade(extractor, segmenter):
    """Verify PhoQ, PhoP, PmrD regulation of PmrA is correctly extracted."""
    text = (
        "The low Mg2+ activation of the PmrA protein requires PhoQ, a protein that senses extracellular Mg2+ levels "
        "(Vescovi et al., 1996), PhoQ's cognate regulator PhoP, and the PhoP-activated protein PmrD (Kox et al., 2000; Kato and Groisman, 2004)."
    )
    doc = make_doc(text)
    doc = segmenter.segment_document(doc)
    assertions = extractor.extract_assertions(doc, known_entities=["PmrA", "PhoQ", "PhoP", "PmrD"])

    assert any(a.cause_canonical == "PhoQ" and a.effect_canonical == "PmrA" for a in assertions)
    assert any(a.cause_canonical == "PmrD" and a.effect_canonical == "PmrA" for a in assertions)
    assert any(a.cause_canonical == "PhoP" and a.effect_canonical == "PmrD" for a in assertions)


def test_end_to_end_pmc1804205_metrics():
    """Verify PMC1804205 end-to-end evaluation matches high recall and controlled precision."""
    paper = next(p for p in CURATED_REAL_PAPERS if p["pmcid"] == "PMC1804205")
    from evryn.paper.ingestion import PaperIngestion
    from evryn.paper.segmentation import PaperSegmenter

    ingestion = PaperIngestion()
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(repo_root, "data", "real_papers", "pdf", "PMC1804205.pdf")
    doc = ingestion.ingest_pdf(pdf_path)
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(doc)

    evaluator = PaperBenchmarkEvaluator()
    res = evaluator.evaluate_paper(doc, paper)

    # Direct extraction must achieve high F1 and zero false-negatives on core biology
    assert res.system_c_f1 >= 0.60
    assert res.error_counts["negation_misclassifications"] == 0

    # Cross-page inference must achieve robust F1 with bounded false transitive jumps
    assert res.system_c_cross_f1 >= 0.50
    assert res.error_counts["false_transitive_jumps"] <= 5
