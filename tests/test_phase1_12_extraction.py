import pytest
from evryn.paper.extractor import (
    PaperCausalExtractor,
    PAT_AGENT_NOMINAL_ACT,
    PAT_AGENT_NOMINAL_INHIB,
    METHOD_HOMOLOGY_RE,
)
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import (
    ScientificDocument,
    SentenceSpan,
    PaperMetadata,
    CausalRelationType,
)


@pytest.fixture
def normalizer():
    return PaperEntityNormalizer()


@pytest.fixture
def extractor(normalizer):
    return PaperCausalExtractor(normalizer=normalizer)


def _make_doc(text: str) -> ScientificDocument:
    meta = PaperMetadata(pmcid="TEST001", title="Test Paper", authors=[], year=2026, journal="Test")
    sent = SentenceSpan(
        sentence_id="s1",
        page_number=1,
        section_title="results",
        paragraph_id="p1",
        start_char=0,
        end_char=len(text),
        text=text,
    )
    return ScientificDocument(
        doc_id="TEST001",
        file_path="/dummy/test.xml",
        metadata=meta,
        full_text=text,
        sentences=[sent],
    )


def test_agent_nominal_activation_regex():
    assert PAT_AGENT_NOMINAL_ACT.search("activation of")
    assert PAT_AGENT_NOMINAL_ACT.search("direct activation of")
    assert PAT_AGENT_NOMINAL_ACT.search("induction of")
    assert PAT_AGENT_NOMINAL_ACT.search("stimulation of")
    assert PAT_AGENT_NOMINAL_ACT.search("up-regulation of")
    assert PAT_AGENT_NOMINAL_ACT.search("activation of the")
    assert PAT_AGENT_NOMINAL_ACT.search("activation of transcription of")
    assert PAT_AGENT_NOMINAL_ACT.search("activation of expression of")

    assert not PAT_AGENT_NOMINAL_ACT.search("activation of something else entirely in another place")


def test_agent_nominal_inhibition_regex():
    assert PAT_AGENT_NOMINAL_INHIB.search("repression of")
    assert PAT_AGENT_NOMINAL_INHIB.search("inhibition of")
    assert PAT_AGENT_NOMINAL_INHIB.search("suppression of")
    assert PAT_AGENT_NOMINAL_INHIB.search("down-regulation of")
    assert PAT_AGENT_NOMINAL_INHIB.search("repression of transcription of")
    assert PAT_AGENT_NOMINAL_INHIB.search("inhibition of expression of")


def test_agent_nominal_activation_extraction(extractor):
    text = "The complementation result suggests that many of the regulators may function on SPI-2 through SlyA activation of ssrB."
    doc = _make_doc(text)
    known = ["SlyA", "SsrB", "SPI-2"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    pairs = [(a.cause_canonical, a.effect_canonical, a.relation_type) for a in assertions]
    assert ("SlyA", "SsrB", CausalRelationType.UPREGULATES) in pairs


def test_homology_and_cloning_filtering():
    assert METHOD_HOMOLOGY_RE.search("equi mac gene encoding mature SeMac was cloned")
    assert METHOD_HOMOLOGY_RE.search("mac was subcloned into pET28a")
    assert METHOD_HOMOLOGY_RE.search("suggesting that SeMac functions like GAS M1 Mac")
    assert METHOD_HOMOLOGY_RE.search("SeMac is a homologue of GAS M1 Mac")
    assert METHOD_HOMOLOGY_RE.search("exhibits 95% amino acid identity")


def test_homology_filter_suppresses_false_positives(extractor):
    text = "The mac gene encoding mature SeMac was cloned by PCR."
    doc = _make_doc(text)
    known = ["Mac", "SeMac"]
    assertions = extractor.extract_assertions(doc, known_entities=known)
    assert len(assertions) == 0


def test_extractor_parameter_ablation_toggles(normalizer):
    ext_default = PaperCausalExtractor(normalizer=normalizer)
    assert ext_default.enable_agent_nominal_activation is True
    assert ext_default.enable_homology_filter is True
    assert ext_default.enable_relative_clause_barrier is False

    ext_disabled = PaperCausalExtractor(
        normalizer=normalizer,
        enable_agent_nominal_activation=False,
        enable_homology_filter=False,
        enable_relative_clause_barrier=True,
    )
    assert ext_disabled.enable_agent_nominal_activation is False
    assert ext_disabled.enable_homology_filter is False
    assert ext_disabled.enable_relative_clause_barrier is True
