"""Unit and regression tests for EVRYN Phase 1.11 extraction mechanisms:
1. Preceding TCSTS slash list and slash-system coupling
2. Expanded TCSTS operon suffixes (VicRK -> VicK -> VicR)
3. Enzymatic activity coupling (SeMac -> IgG Endopeptidase)
4. Chaperone-cargo binding coupling (SrcA -> PipB2, SseL)
5. Modular flag controllability
6. Negative control sentences (anti-spurious)
"""

import pytest
from evryn.paper.types import ScientificDocument, SentenceSpan, PaperMetadata, CausalRelationType
from evryn.paper.extractor import PaperCausalExtractor


def create_single_sentence_doc(text: str, doc_id: str = "PMC_TEST_001") -> ScientificDocument:
    sent = SentenceSpan(
        sentence_id="s_1_001",
        page_number=1,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=len(text),
        text=text,
    )
    return ScientificDocument(
        doc_id=doc_id,
        file_path="/tmp/test.xml",
        metadata=PaperMetadata(title="Test Document", authors=["Author"]),
        sentences=[sent],
        full_text=text,
    )


def test_preceding_tcsts_slash_list():
    extractor = PaperCausalExtractor()
    text = (
        "These 14 regulators are very diverse including alternative sigma factors "
        "and two-component regulators (ompR/envZ, phoP/phoQ, arcA/arcB, and ssrA/ssrB)."
    )
    doc = create_single_sentence_doc(text)
    known = ["EnvZ", "OmpR", "PhoQ", "PhoP", "ArcB", "ArcA", "SsrA", "SsrB"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}

    assert ("EnvZ", "OmpR") in pairs
    assert ("PhoQ", "PhoP") in pairs
    assert ("ArcB", "ArcA") in pairs
    assert ("SsrA", "SsrB") in pairs


def test_tcsts_regulator_to_system_coupling():
    extractor = PaperCausalExtractor()
    text = "We characterized the two-component BvrR/BvrS system in Brucella."
    doc = create_single_sentence_doc(text)
    known = ["BvrR", "BvrS", "BvrR/BvrS"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}

    assert ("BvrS", "BvrR") in pairs
    assert ("BvrR", "BvrR/BvrS") in pairs


def test_expanded_tcsts_operon_rk():
    extractor = PaperCausalExtractor()
    text = "The two-component regulatory system VicRK or YycFG is specific to low G+C bacteria."
    doc = create_single_sentence_doc(text)
    known = ["VicK", "VicR", "YycF", "YycG"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}

    assert ("VicK", "VicR") in pairs


def test_enzymatic_activity_coupling():
    extractor = PaperCausalExtractor()
    text = "SeMac has IgG endopeptidase activity that promotes immune evasion."
    doc = create_single_sentence_doc(text)
    known = ["SeMac", "IgG Endopeptidase", "Immune Evasion"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}

    assert ("SeMac", "IgG Endopeptidase") in pairs


def test_chaperone_cargo_binding():
    extractor = PaperCausalExtractor()
    text = (
        "Further biochemical data revealed three protein interactions with SrcA, "
        "including two effector cargos (SseL and PipB2)."
    )
    doc = create_single_sentence_doc(text)
    known = ["SrcA", "SseL", "PipB2"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}

    assert ("SrcA", "SseL") in pairs
    assert ("SrcA", "PipB2") in pairs


def test_modular_flags_disable():
    doc1 = create_single_sentence_doc("two-component regulators (ompR/envZ, phoP/phoQ)")
    doc2 = create_single_sentence_doc("The two-component system VicRK is essential.")
    doc3 = create_single_sentence_doc("SeMac has IgG endopeptidase activity.")
    doc4 = create_single_sentence_doc("interactions with SrcA including two effector cargos (SseL and PipB2).")

    ext_disabled = PaperCausalExtractor(
        enable_preceding_tcsts=False,
        enable_operon_tcsts_rk=False,
        enable_enzymatic_activity_coupling=False,
        enable_chaperone_cargo_coupling=False,
    )

    k1 = ["EnvZ", "OmpR", "PhoQ", "PhoP"]
    k2 = ["VicK", "VicR"]
    k3 = ["SeMac", "IgG Endopeptidase"]
    k4 = ["SrcA", "SseL", "PipB2"]

    assert len(ext_disabled.extract_assertions(doc1, known_entities=k1)) == 0
    assert len(ext_disabled.extract_assertions(doc2, known_entities=k2)) == 0
    assert len(ext_disabled.extract_assertions(doc3, known_entities=k3)) == 0
    assert len(ext_disabled.extract_assertions(doc4, known_entities=k4)) == 0


def test_negative_control_sentences():
    extractor = PaperCausalExtractor()
    text = "In contrast to previous studies, no two-component proteins were detected in the supernatant."
    doc = create_single_sentence_doc(text)
    known = ["VicK", "VicR", "PhoP", "PhoQ"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    assert len(assertions) == 0
