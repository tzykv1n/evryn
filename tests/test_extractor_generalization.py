import pytest
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.extractor import PaperCausalExtractor
from evryn.web.document_parser import DocumentParser


@pytest.fixture
def extractor():
    norm = PaperEntityNormalizer()
    return PaperCausalExtractor(normalizer=norm)


@pytest.fixture
def parser():
    return DocumentParser()


def test_example_1_direct_receptor_activation(parser, extractor):
    text = "Epidermal growth factor receptor (EGFR) activation directly stimulates the downstream MAPK pathway."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 1
    a = assertions[0]
    assert "EGFR" in a.cause_canonical
    assert "MAPK" in a.effect_canonical
    assert a.is_negated is False
    assert a.relation_type.value == "UPREGULATES"


def test_example_2_multi_hop_causal_chain(parser, extractor):
    text = "Interleukin-6 activates STAT3 phosphorylation. Subsequently, activated STAT3 stimulates the transcription of SOCS3, which downregulates JAK kinase activity."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
    assert ("IL-6", "STAT3") in pairs or any("IL-6" in p[0] for p in pairs)
    assert ("STAT3", "SOCS3") in pairs or any("SOCS3" in p[1] for p in pairs)


def test_example_3_scientific_mechanism(parser, extractor):
    text = "Under hypoxic stress, cellular Hypoxia-Inducible Factor 1-alpha (HIF-1alpha) is stabilized and drives the transcription of VEGF. In turn, elevated VEGF promotes tumor angiogenesis, while Von Hippel-Lindau tumor suppressor (VHL) promotes the ubiquitin-mediated degradation of HIF-1alpha under normoxic conditions."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2
    pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
    assert any("HIF-1alpha" in p[0] and "VEGF" in p[1] for p in pairs)
    assert any("VEGF" in p[0] and "Angiogenesis" in p[1] for p in pairs) or any("VEGF" in p[0] for p in pairs)


def test_example_4_negation_and_uncertainty(parser, extractor):
    text = "Administration of Compound X did not induce p53 phosphorylation in wild-type cells. We hypothesize that elevated ROS might activate Caspase-3 under prolonged oxidative stress."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2
    # Verify negation
    neg_asserts = [a for a in assertions if a.is_negated]
    assert len(neg_asserts) >= 1
    assert "Compound X" in neg_asserts[0].cause_canonical
    assert neg_asserts[0].evidence_status.value == "REFUTED_NEGATION"

    # Verify speculative / hypothesis
    hypo_asserts = [a for a in assertions if a.evidence_status.value == "HYPOTHESIS_CLAIM"]
    assert len(hypo_asserts) >= 1
    assert "ROS" in hypo_asserts[0].cause_canonical
    assert "Caspase-3" in hypo_asserts[0].effect_canonical


def test_example_5_multi_paragraph_autophagy(parser, extractor):
    text = (
        "Severe glucose deprivation triggers the rapid activation of AMP-activated protein kinase (AMPK).\n\n"
        "Once activated, AMPK directly phosphorylates and activates the TSC2 complex, thereby inhibiting mammalian target of rapamycin complex 1 (mTORC1).\n\n"
        "The inhibition of mTORC1 liberates ULK1 from repressive phosphorylation, ultimately promoting macroautophagy and cellular survival."
    )
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 3
    entities_involved = {a.cause_canonical for a in assertions} | {a.effect_canonical for a in assertions}
    assert "AMPK" in entities_involved
    assert "mTORC1" in entities_involved or "mTOR" in entities_involved


def test_example_7_multiple_causes_and_effects(parser, extractor):
    text = "Extracellular Wnt3a ligand binding recruits Dishevelled. Consequently, beta-catenin activates both Cyclin D1 and c-Myc expression."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2
    effects = {a.effect_canonical for a in assertions}
    assert any("Cyclin D1" in e for e in effects)
    assert any("c-Myc" in e for e in effects)


def test_example_8_ambiguous_correlation_vs_causation(parser, extractor):
    text = "Serum biomarker Protein Alpha was found to be strongly correlated with Patient Age (r = 0.82, p < 0.001). However, multivariate regression demonstrated that advanced age does not cause elevated Protein Alpha; rather, chronic systemic inflammation independently increases both aging markers and Protein Alpha levels."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    # Correlation must NOT produce a positive causal relation between Protein Alpha and Age
    pos_asserts = [a for a in assertions if not a.is_negated]
    assert not any(a.cause_canonical == "Protein Alpha" and a.effect_canonical == "Patient Age" for a in pos_asserts)
    assert not any(a.cause_canonical == "Patient Age" and a.effect_canonical == "Protein Alpha" for a in pos_asserts)
    # Negation correctly captured
    neg_asserts = [a for a in assertions if a.is_negated]
    assert len(neg_asserts) >= 1
    assert "advanced age" in neg_asserts[0].cause_canonical
    assert "Protein Alpha" in neg_asserts[0].effect_canonical


def test_example_10_open_domain_causality(parser, extractor):
    text = "High central bank interest rates increase borrowing costs, which dampens corporate capital expenditure and reduces overall consumer spending. Meanwhile, elevated atmospheric carbon dioxide traps thermal radiation, driving global surface temperature anomalies."
    doc = parser.parse_raw_text(text)
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2
    causes = {a.cause_canonical for a in assertions}
    effects = {a.effect_canonical for a in assertions}
    assert any("interest rates" in c.lower() for c in causes)
    assert any("borrowing costs" in e.lower() for e in effects)
