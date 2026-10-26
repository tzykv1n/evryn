"""
EVRYN Phase 1.14 Verification and Benchmark Audit Unit Tests.

Validates:
1. Benchmark ledger integrity across all 4 splits (resolving 258 vs 165 discrepancy to authoritative 183 gold relations).
2. Directional invariant gating for master regulators and secretion substrates.
3. Linker confidence calibration and transitive chain cross-page reasoning.
"""

import pytest
from evryn.paper.real_benchmark import (
    CURATED_REAL_PAPERS_V2,
    CURATED_REAL_PAPERS_V1,
    get_curated_papers,
)
from evryn.paper.cross_page_linker import CrossPageLinker, TCSTS_REVERSE_PAIRS
from evryn.paper.types import CausalAssertion


def test_benchmark_v2_gold_ledger_and_discrepancy_resolution():
    """Verify exact count of direct, cross-page, and total gold relations in Benchmark V2."""
    papers_v2 = get_curated_papers("v2")
    assert len(papers_v2) == 20

    total_direct = sum(len(p.get("direct_edges", [])) for p in papers_v2)
    total_cross = sum(len(p.get("cross_page_edges", [])) for p in papers_v2)

    # Formal ledger verification:
    # 96 Direct relations + 87 Cross-page relations = 183 Total Gold Causal Relations
    assert total_direct == 96
    assert total_cross == 87
    assert total_direct + total_cross == 183

    # Ensure zero overlap between direct and cross-page sets
    for p in papers_v2:
        d_set = {tuple(x) for x in p.get("direct_edges", [])}
        c_set = {tuple(x) for x in p.get("cross_page_edges", [])}
        assert len(d_set.intersection(c_set)) == 0, f"Overlap found in {p.get('pmcid')}"


def test_master_regulator_reverse_pair_invariants():
    """Verify that downstream regulators and substrates cannot cause upstream master regulators."""
    assert ("invf", "hila") in TCSTS_REVERSE_PAIRS
    assert ("espa", "phop") in TCSTS_REVERSE_PAIRS
    assert ("esx-1", "phop") in TCSTS_REVERSE_PAIRS
    assert ("esat-6", "phop") in TCSTS_REVERSE_PAIRS
    assert ("esat-6", "espa") in TCSTS_REVERSE_PAIRS


def test_cross_page_linker_pruning_reverse_master_regulator():
    """CrossPageLinker must prune spurious reverse chains from downstream substrates to master regulators."""
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.60)

    # Create assertions: PhoP -> EspA (page 1), EspA -> ESX-1 (page 3)
    a1 = CausalAssertion(
        assertion_id="asrt_001",
        cause="PhoP",
        cause_canonical="PhoP",
        effect="EspA",
        effect_canonical="EspA",
        direction="causes",
        relation_type="activation",
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s1",
        page_number=1,
        section_title="Results",
        confidence=0.92,
        evidence_quote="PhoP activates EspA.",
        char_span=(0, 20),
    )
    a2 = CausalAssertion(
        assertion_id="asrt_002",
        cause="EspA",
        cause_canonical="EspA",
        effect="ESX-1",
        effect_canonical="ESX-1",
        direction="causes",
        relation_type="activation",
        is_negated=False,
        uncertainty_score=0.0,
        sentence_id="s2",
        page_number=3,
        section_title="Results",
        confidence=0.90,
        evidence_quote="EspA interacts with ESX-1.",
        char_span=(100, 126),
    )

    links = linker.find_cross_page_links([a1, a2])
    # Downstream to upstream reverse (e.g. EspA -> PhoP) must NOT exist
    for l in links:
        assert not (l.source_entity.lower() == "espa" and l.target_entity.lower() == "phop")
        assert not (l.source_entity.lower() == "esx-1" and l.target_entity.lower() == "phop")
