import pytest
from evryn.paper.extractor import PaperCausalExtractor, CausalRelationType
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import ScientificDocument, SentenceSpan, PaperMetadata

def test_exact_entity_canonicalization_priority():
    normalizer = PaperEntityNormalizer()
    known = ["GraRS", "GraR", "dltA", "LL-37", "Virulence"]
    assert normalizer.canonicalize("graRS", known_entities=known) == "GraRS"
    assert normalizer.canonicalize("graR", known_entities=known) == "GraR"
    assert normalizer.canonicalize("GraR", known_entities=known) == "GraR"
    assert normalizer.canonicalize("GraRS", known_entities=known) == "GraRS"

def test_active_matrix_precedence_over_subordinate_modifier():
    extractor = PaperCausalExtractor()
    text = "Additionally, the over-expression of HilD from the plasmid pJB3 containing hilD gene under the control of a lac promoter caused the induction of hilA expression"
    s1 = text.index("HilD")
    e1 = s1 + len("HilD")
    s2 = text.index("hilA")
    e2 = s2 + len("hilA")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "FORWARD"
    assert rel_type == CausalRelationType.UPREGULATES

def test_genetics_mutant_enhanced_inversion():
    extractor = PaperCausalExtractor()
    text = "slo expression was enhanced in the csrS mutant"
    s1 = text.index("slo")
    e1 = s1 + len("slo")
    s2 = text.index("csrS")
    e2 = s2 + len("csrS")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "BACKWARD"
    assert rel_type == CausalRelationType.DOWNREGULATES

def test_genetics_mutant_defect_grammar():
    extractor = PaperCausalExtractor()
    text = "the cheB1 mutant was no longer able to move towards the attractant, and thus showed a defect in chemotaxis"
    s1 = text.index("cheB1")
    e1 = s1 + len("cheB1")
    s2 = text.index("chemotaxis")
    e2 = s2 + len("chemotaxis")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "FORWARD"
    assert rel_type == CausalRelationType.UPREGULATES

def test_anti_factor_release_inhibition():
    extractor = PaperCausalExtractor()
    text = "Release of σE from its inner membrane anchored anti-sigma factor, RseA, leads to induction of genes required"
    s1 = text.index("σE")
    e1 = s1 + len("σE")
    s2 = text.index("RseA")
    e2 = s2 + len("RseA")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "BACKWARD"
    assert rel_type == CausalRelationType.DOWNREGULATES

def test_structural_composition_pattern():
    extractor = PaperCausalExtractor()
    text = "The short fimbriae are made up of a 67 kDa protein (Mfa1)."
    s1 = text.index("short fimbriae")
    e1 = s1 + len("short fimbriae")
    s2 = text.index("Mfa1")
    e2 = s2 + len("Mfa1")
    rel_tuple = extractor._match_relation(text, s1, e1, s2, e2)
    assert rel_tuple is not None
    rel_type, direction, conf = rel_tuple
    assert direction == "BACKWARD"
    assert rel_type == CausalRelationType.UPREGULATES

def test_tcsts_operon_regulator_coupling():
    extractor = PaperCausalExtractor()
    sent_text = "The graRS regulatory genes have recently been implicated in the control of D-alanylation in Staphylococcus aureus."
    doc = ScientificDocument(
        doc_id="PMC2430206",
        file_path="PMC2430206.xml",
        full_text=sent_text,
        metadata=PaperMetadata(title="Test TCSTS Operon"),
        sentences=[
            SentenceSpan(
                sentence_id="sec_1_s1",
                text=sent_text,
                start_char=0,
                end_char=len(sent_text),
                page_number=1,
                section_title="Introduction",
                paragraph_id="p_1",
            )
        ],
    )
    known = ["GraRS", "GraR", "dltA", "LL-37", "Virulence"]
    asrt = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical) for a in asrt]
    assert ("GraRS", "GraR") in pairs
