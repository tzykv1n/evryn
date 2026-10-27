"""
EVRYN Phase 2.5: False-Positive Adjudication & Gold Comparison Regression Tests.
Verifies that:
1. Environmental induction syntax ("was promoted in media of...") extracts UPREGULATES rather than inverted DOWNREGULATES.
2. Speculative modal hedges ("could be due to") and research-intent hypotheses ("we hypothesized that...") are filtered.
3. Directional gold standard matching protocol correctly preserves causal direction (cause -> effect).
4. Reviewer overrides are stored and applied in GoldComparisonService without mutating frozen reference standards.
"""

import pytest
from evryn.paper.extractor import PaperCausalExtractor, CausalRelationType
from evryn.web.gold_comparison_service import GoldComparisonService, match_edge


@pytest.fixture
def extractor():
    return PaperCausalExtractor()


@pytest.fixture
def gold_svc():
    return GoldComparisonService.get_instance()


def test_environmental_media_polarity_fix(extractor):
    """Verifies that 'promoted in media of mild acid pH' is extracted as UPREGULATES, not inverted DOWNREGULATES."""
    text = "Consistent with its role in acid pH activation, expression of the pmrD gene was promoted in media of mild acid pH (Fig. 4)."
    s_pmrd = text.find("pmrD")
    e_pmrd = s_pmrd + len("pmrD")
    s_ph = text.rfind("acid pH")
    e_ph = s_ph + len("acid pH")

    res = extractor._match_relation(text, s_pmrd, e_pmrd, s_ph, e_ph)
    assert res is not None
    rel_type, direction, conf = res
    assert rel_type == CausalRelationType.UPREGULATES
    assert direction == "BACKWARD"  # cause is acid pH, effect is pmrD


def test_speculative_modal_hedge_suppressed(extractor):
    """Verifies that 'could be due to' speculative hedge prevents factual extraction."""
    text = "The transcriptional activation of PmrA-regulated genes taking place at pH 5.8 could be due to trace amounts of metals such as Fe3+."
    s_ph = text.find("pH 5.8")
    e_ph = s_ph + len("pH 5.8")
    s_fe = text.find("Fe3+")
    e_fe = s_fe + len("Fe3+")

    res = extractor._match_relation(text, s_ph, e_ph, s_fe, e_fe)
    assert res is None


def test_hypothesis_clause_suppressed(extractor):
    """Verifies that 'we hypothesized that mild acid pH could induce this resistance' is filtered as speculative intent."""
    text = "Because the PmrA/PmrB system is required for resistance, we hypothesized that mild acid pH could induce this resistance."
    s_ph = text.find("mild acid pH")
    e_ph = s_ph + len("mild acid pH")
    s_res = text.rfind("resistance")
    e_res = s_res + len("resistance")

    res = extractor._match_relation(text, s_ph, e_ph, s_res, e_res)
    assert res is None


def test_directional_edge_matching():
    """Verifies direction-preserving matching protocol."""
    # Correct forward direction
    assert match_edge("Acid pH", "PmrB", "Acid pH", "PmrB") is True
    # Inverted direction must NOT match
    assert match_edge("PmrB", "Acid pH", "Acid pH", "PmrB") is False
    # Substring normalization
    assert match_edge("mild acid pH", "pmrB sensor kinase", "Acid pH", "PmrB") is True


def test_gold_comparison_service_adjudication(gold_svc):
    """Verifies GoldComparisonService categorization and reviewer overrides."""
    session_id = "test_adjudication_session"
    session_data = {
        "title": "Acid pH activation of PmrA/PmrB (PMC1804205)",
        "relations": [
            {
                "id": "rel_001",
                "cause_name": "Acid pH",
                "effect_name": "PmrB",
                "relation_type": "UPREGULATES",
                "sentence_text": "PmrB is required to respond to acid pH.",
            },
            {
                "id": "rel_002",
                "cause_name": "PmrA",
                "effect_name": "Polymyxin B",
                "relation_type": "UPREGULATES",
                "sentence_text": "we hypothesized that mild acid pH could induce this resistance",
            },
        ],
    }

    report = gold_svc.compare_session_with_gold(session_id, session_data)
    assert report["gold_available"] is True
    assert report["pmcid"] == "PMC1804205"
    assert report["counts"]["tp"] >= 1
    assert len(report["matched_relations"]) >= 1
    assert len(report["unmatched_predictions"]) >= 1

    # Check that rel_002 is categorized as Genuine false positive due to hypothesis language
    unmatched_hyp = next(r for r in report["unmatched_predictions"] if r["relation_id"] == "rel_002")
    assert unmatched_hyp["adjudication_category"] == "Genuine false positive"

    # Test reviewer override
    res = gold_svc.record_adjudication_override(
        session_id=session_id,
        relation_id="rel_002",
        category="Ambiguous",
        note="Reviewer classified as ambiguous phenotype link.",
    )
    assert res["status"] == "success"

    # Re-run comparison and verify override was respected
    updated_report = gold_svc.compare_session_with_gold(session_id, session_data)
    unmatched_updated = next(r for r in updated_report["unmatched_predictions"] if r["relation_id"] == "rel_002")
    assert unmatched_updated["adjudication_category"] == "Ambiguous"
    assert unmatched_updated["is_reviewed"] is True
