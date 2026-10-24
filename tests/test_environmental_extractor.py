# pytest tests/test_environmental_extractor.py

import pytest
from evryn.paper.environmental_extractor import (
    EnvironmentalParameterExtractor,
    ENV_FORWARD_SHIFT_RE,
    ENV_PASSIVE_INDUCED_BY_RE,
    ENV_COMPOUND_ADJ_RE,
    ENV_IN_RESPONSE_TO_RE,
    ENV_DIFF_COMPARISON_RE,
    ENV_METHOD_EXCLUDE_RE,
)
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.types import (
    ScientificDocument,
    PaperMetadata,
    SentenceSpan,
    CausalRelationType,
    EvidenceStatus,
)


def test_environmental_regex_forward_shift():
    s1 = "After transmission, the temperature shift to 37°C induces many known virulence factors of Y. pestis."
    assert bool(ENV_FORWARD_SHIFT_RE.search(s1))

    s2 = "A shift from 21°C to 37°C suppressed biofilm formation in vitro."
    assert bool(ENV_FORWARD_SHIFT_RE.search(s2))

    s3 = "When the temperature was raised to 37°C, ybt expression increased significantly."
    assert bool(ENV_FORWARD_SHIFT_RE.search(s3))

    s4 = "Increasing the temperature from 21°C to 37°C increased di-GMP levels."
    assert bool(ENV_FORWARD_SHIFT_RE.search(s4))


def test_environmental_regex_passive_and_compound():
    s_pas = "pestis virulence factors are induced by a temperature shift from <26°C to 37°C"
    assert bool(ENV_PASSIVE_INDUCED_BY_RE.search(s_pas))

    s_adj = "In addition to the known temperature-induced virulence factors, iron acquisition systems..."
    assert bool(ENV_COMPOUND_ADJ_RE.search(s_adj))

    s_resp = "activates the PmrA protein in response to acid pH"
    assert bool(ENV_IN_RESPONSE_TO_RE.search(s_resp))

    s_diff = "yfe was upregulated at 37°C compared with 21°C in culture"
    assert bool(ENV_DIFF_COMPARISON_RE.search(s_diff))


def test_adversarial_method_exclusions():
    methods = [
        "Bacteria were incubated at 37°C overnight without shaking.",
        "Approximately 0.5 ml was centrifuged at 21°C for 5 min prior to RNA extraction.",
        "Fleas were maintained at 21°C and 75% relative humidity.",
        "Cells were fixed in 2.5% paraformaldehyde for 10 min at 37°C and then rewashed.",
        "For in vitro planktonic samples, bacteria were grown in BHI medium at 28°C.",
        "An increase in optical density was observed at room temperature.",
        "The shift in reading frame leads to premature termination of translation.",
        "Temperature was recorded every 10 minutes during the assay.",
    ]
    for text in methods:
        assert bool(ENV_METHOD_EXCLUDE_RE.search(text))


def test_environmental_parameter_extractor_execution():
    norm = PaperEntityNormalizer()
    extractor = EnvironmentalParameterExtractor(norm)
    known = ["Temperature", "Virulence", "di-GMP"]

    sent = SentenceSpan(
        sentence_id="s_test_1",
        page_number=1,
        section_title="Results",
        paragraph_id="p1",
        start_char=0,
        end_char=85,
        text="After transmission, the temperature shift to 37°C induces many known virulence factors.",
    )

    asrt, idx = extractor.extract_environmental_assertions(
        sent=sent,
        doc_id="doc001",
        start_idx=1,
        seen_keys=set(),
        known_entities=known,
    )
    assert len(asrt) == 1
    assert asrt[0].cause_canonical == "Temperature"
    assert asrt[0].effect_canonical == "Virulence"
    assert asrt[0].relation_type == CausalRelationType.UPREGULATES
    assert not asrt[0].is_negated


def test_direction_invariant_in_extractor():
    extractor = PaperCausalExtractor()
    known = ["PmrA", "Acid pH", "Temperature", "Virulence"]

    # Inverted stimulus sentence
    sent1 = SentenceSpan("s1", 1, "Results", "p1", 0, 75, "The signalling pathway activates the PmrA protein in response to acid pH.")
    doc = ScientificDocument(
        doc_id="doc_test",
        file_path="test.txt",
        metadata=PaperMetadata("Test", [], "", "", "", None, "", 1),
        full_text=sent1.text,
        sentences=[sent1],
    )
    asg = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical) for a in asg]
    # Must NOT contain reversed edge PmrA -> Acid pH
    assert ("PmrA", "Acid pH") not in pairs


def test_environmental_variable_ablation():
    norm = PaperEntityNormalizer()
    extractor = EnvironmentalParameterExtractor(norm)
    known = ["Temperature", "Acid pH", "Virulence", "PmrB"]

    sent_temp = SentenceSpan("s1", 1, "Results", "p1", 0, 56, "The temperature shift to 37°C induces virulence factors.")
    sent_ph = SentenceSpan("s2", 1, "Results", "p1", 0, 50, "Acid pH stimulates PmrB activation at the membrane.")

    # Temperature-only ablation
    asrt_t, _ = extractor.extract_environmental_assertions(
        sent=sent_temp, doc_id="d1", start_idx=1, seen_keys=set(), known_entities=known, allowed_variables={"temperature"}
    )
    asrt_ph_in_t, _ = extractor.extract_environmental_assertions(
        sent=sent_ph, doc_id="d1", start_idx=1, seen_keys=set(), known_entities=known, allowed_variables={"temperature"}
    )
    assert len(asrt_t) == 1
    assert len(asrt_ph_in_t) == 0

    # pH-only ablation
    asrt_ph, _ = extractor.extract_environmental_assertions(
        sent=sent_ph, doc_id="d1", start_idx=1, seen_keys=set(), known_entities=known, allowed_variables={"ph"}
    )
    asrt_t_in_ph, _ = extractor.extract_environmental_assertions(
        sent=sent_temp, doc_id="d1", start_idx=1, seen_keys=set(), known_entities=known, allowed_variables={"ph"}
    )
    assert len(asrt_ph) == 1
    assert len(asrt_t_in_ph) == 0
