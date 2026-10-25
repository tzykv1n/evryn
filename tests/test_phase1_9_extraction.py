import pytest
from evryn.paper.extractor import PaperCausalExtractor, CausalRelationType
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import ScientificDocument, SentenceSpan, PaperMetadata, PageBoundary


def _make_doc(text: str, sentence_id: str = "s1") -> ScientificDocument:
    return ScientificDocument(
        doc_id="test_doc",
        file_path="test.pdf",
        metadata=PaperMetadata(title="Test Paper"),
        full_text=text,
        pages=[PageBoundary(page_number=1, start_char=0, end_char=len(text), char_count=len(text))],
        paragraphs=[],
        sentences=[
            SentenceSpan(
                sentence_id=sentence_id,
                page_number=1,
                section_title="RESULTS",
                paragraph_id="p1",
                start_char=0,
                end_char=len(text),
                text=text,
            )
        ],
    )


def test_ligand_sensing_forward_syntax():
    """Verify that ligand sensing ('X is sensed by Y') extracts forward causal activation X -> Y."""
    extractor = PaperCausalExtractor()
    text = "They produce membrane diffusible signalling molecules, acyl homoserine lactones (AHLs), which are sensed by the receptor/regulator LuxR when exceeding a threshold concentration."
    s1 = text.index("AHLs")
    e1 = s1 + len("AHLs")
    s2 = text.index("LuxR")
    e2 = s2 + len("LuxR")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "FORWARD"
    assert rel_type == CausalRelationType.UPREGULATES
    assert conf >= 0.90


def test_appositive_role_prefix_canonicalization():
    """Verify that appositive role prefixes ('receptor/regulator', 'sensor kinase', 'response regulator') are cleanly stripped."""
    normalizer = PaperEntityNormalizer()
    known = ["LuxR", "PmrB", "FimR", "SlyA", "SrcA"]

    assert normalizer.canonicalize("the receptor/regulator LuxR", known_entities=known) == "LuxR"
    assert normalizer.canonicalize("sensor kinase PmrB", known_entities=known) == "PmrB"
    assert normalizer.canonicalize("response regulator FimR", known_entities=known) == "FimR"
    assert normalizer.canonicalize("transcriptional regulator SlyA", known_entities=known) == "SlyA"
    assert normalizer.canonicalize("chaperone protein SrcA", known_entities=known) == "SrcA"


def test_tcsts_directional_invariant():
    """Verify that response regulators cannot act as upstream regulators of their cognate sensor kinases."""
    extractor = PaperCausalExtractor(enable_tcsts_directional_invariant=True)
    text = "FimR, a response regulator of the fimS/fimR two-component system was identified."
    doc = _make_doc(text)
    assertions = extractor.extract_assertions(doc, known_entities=["FimS", "FimR"])
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    assert ("FimR", "FimS") not in pairs


def test_irrespective_control_clause_cutting():
    """Verify that 'irrespective of' cuts effect spans and prevents spurious regulation of control conditions."""
    extractor = PaperCausalExtractor()
    text = "Over-expression of HilD caused the induction of hilA by 2-fold irrespective of mlc mutation when tested."
    doc = _make_doc(text)
    assertions = extractor.extract_assertions(doc, known_entities=["HilD", "hilA", "Mlc"])
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    assert ("HilD", "Mlc") not in pairs


def test_binding_domain_false_positive_filter():
    """Verify that non-relational binding domain attributes are filtered from causal assertions."""
    extractor = PaperCausalExtractor()
    text = "35 of these potential LuxR-like receptors exhibit PAS_4 signal binding domains instead of an AHL-binding domain."
    doc = _make_doc(text)
    assertions = extractor.extract_assertions(doc, known_entities=["LuxR", "AHL"])
    pairs = [(a.cause_canonical, a.effect_canonical) for a in assertions]
    assert ("LuxR", "AHL") not in pairs
