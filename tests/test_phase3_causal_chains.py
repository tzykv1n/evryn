"""
Tests for EVRYN Phase 3: Generalizable Causal Chains, Partial-Path Matching,
and Cross-Paper Linking.
"""

import os
import hashlib
import pytest
import networkx as nx

from evryn.paper.chain_types import (
    CausalEdgeKind,
    ChainMatchLevel,
    ChainEdge,
    CausalChain,
    ChainMatchResult,
)
from evryn.paper.chain_evaluator import ChainEvaluator
from evryn.paper.chain_builder import CausalChainBuilder
from evryn.paper.composition_model import (
    ConditionalCompositionModel,
    CompositionFeatureExtractor,
    CompositionClass,
)
from evryn.paper.partial_chain_matcher import PartialChainMatcher
from evryn.paper.cross_paper_linker import CrossPaperLinker, CrossDocumentCausalLink
from evryn.paper.normalizer import PaperEntityNormalizer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_phase1_hashes_preserved_in_phase3():
    expected_main = "4e7eb0ffb6390260b4d0e8bea70abc420237d7a952ebd7fa977ad2db8b8fce5d"
    expected_pres = "dfeafd264a583442d9cf8a647db5f0465d5cbeaf3f488135eb10138ebefc822b"

    main_path = os.path.join(REPO_ROOT, "docs", "phase1", "main.pdf")
    pres_path = os.path.join(REPO_ROOT, "docs", "phase1", "Temporal_Causal_Knowledge_Phase1_Presentation.pdf")

    with open(main_path, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == expected_main
    with open(pres_path, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == expected_pres


def test_causal_chain_types_and_serialization():
    e1 = ChainEdge(
        source="PhoP",
        target="PmrD",
        relation_type="UPREGULATES",
        edge_kind=CausalEdgeKind.DIRECT_LOCAL,
        polarity="POSITIVE",
        confidence=0.92,
        evidence_text="PhoP activates PmrD expression.",
        page_number=2,
        section_title="Results",
        doc_id="PMC1804205",
    )
    e2 = ChainEdge(
        source="PmrD",
        target="PmrA",
        relation_type="UPREGULATES",
        edge_kind=CausalEdgeKind.DIRECT_LOCAL,
        polarity="POSITIVE",
        confidence=0.88,
        evidence_text="PmrD binds and stabilizes PmrA.",
        page_number=3,
        section_title="Results",
        doc_id="PMC1804205",
    )
    chain = CausalChain(
        chain_id="chain_001",
        nodes=["PhoP", "PmrD", "PmrA"],
        edges=[e1, e2],
        composite_confidence=0.81,
        doc_ids=["PMC1804205"],
    )

    d = chain.to_dict()
    assert d["chain_id"] == "chain_001"
    assert d["hop_count"] == 2
    assert tuple(d["endpoint_pair"]) == ("PhoP", "PmrA")
    assert len(d["edges"]) == 2
    assert d["edges"][0]["edge_kind"] == "DIRECT_LOCAL"

    chain_back = CausalChain.from_dict(d)
    assert chain_back.chain_id == "chain_001"
    assert chain_back.hop_count == 2
    assert chain_back.edges[0].source == "PhoP"
    assert chain_back.edges[1].target == "PmrA"


def test_chain_evaluator_8_matching_levels():
    evaluator = ChainEvaluator()

    # Base gold chain: A -> B -> C
    e_gold = [
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="doc1"),
        ChainEdge("B", "C", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="doc1"),
    ]
    gold = CausalChain("gold_1", ["A", "B", "C"], e_gold, 1.0, ["doc1"])

    # 1. Level 1: Exact Chain Match
    pred_exact = CausalChain("p1", ["A", "B", "C"], e_gold, 0.95, ["doc1"])
    res1 = evaluator.evaluate_chain_match(gold, pred_exact)
    assert res1.match_level == ChainMatchLevel.EXACT_CHAIN_MATCH
    assert res1.match_score > 0.90

    # 2. Level 2: Exact Edge Set with alias
    e_alias = [
        ChainEdge("a", "b", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("b", "c", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_alias = CausalChain("p2", ["a", "b", "c"], e_alias, 0.90, ["doc1"])
    res2 = evaluator.evaluate_chain_match(gold, pred_alias)
    assert res2.match_level in (ChainMatchLevel.EXACT_CHAIN_MATCH, ChainMatchLevel.EXACT_EDGE_SET_MATCH)

    # 3. Level 3: Partial Contiguous Match (A -> B only)
    e_partial = [
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_partial = CausalChain("p3", ["A", "B"], e_partial, 0.90, ["doc1"])
    res3 = evaluator.evaluate_chain_match(gold, pred_partial)
    assert res3.match_level == ChainMatchLevel.PARTIAL_CONTIGUOUS_MATCH
    assert "C" in res3.missing_nodes

    # 4. Level 4: Partial Non-Contiguous with missing bridge
    # Gold: A -> B -> C -> D
    e_gold4 = [
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="doc1"),
        ChainEdge("B", "C", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="doc1"),
        ChainEdge("C", "D", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="doc1"),
    ]
    gold4 = CausalChain("gold_4", ["A", "B", "C", "D"], e_gold4, 1.0, ["doc1"])
    # Pred has A -> B and C -> D (missing B -> C bridge)
    e_gap = [
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("C", "D", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_gap = CausalChain("p4", ["A", "B", "C", "D"], e_gap, 0.85, ["doc1"])
    res4 = evaluator.evaluate_chain_match(gold4, pred_gap)
    assert res4.match_level == ChainMatchLevel.PARTIAL_NON_CONTIGUOUS_MATCH
    assert ("B", "C") in res4.missing_bridges

    # 5. Level 5: Subpath matched inside longer predicted path
    e_longer = [
        ChainEdge("X", "A", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("B", "C", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("C", "Y", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_longer = CausalChain("p5", ["X", "A", "B", "C", "Y"], e_longer, 0.80, ["doc1"])
    res5 = evaluator.evaluate_chain_match(gold, pred_longer)
    assert res5.match_level == ChainMatchLevel.SUBPATH_INSIDE_LONGER

    # 6. Level 6: Divergent intermediate path (A -> Z -> C vs A -> B -> C)
    e_divergent = [
        ChainEdge("A", "Z", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("Z", "C", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_divergent = CausalChain("p6", ["A", "Z", "C"], e_divergent, 0.80, ["doc1"])
    res6 = evaluator.evaluate_chain_match(gold, pred_divergent)
    assert res6.match_level == ChainMatchLevel.ENDPOINT_MATCH_INCORRECT_PATH

    # 7. Level 7: Inverted Direction (C -> B -> A)
    e_inverted = [
        ChainEdge("C", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
        ChainEdge("B", "A", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="doc1"),
    ]
    pred_inverted = CausalChain("p7", ["C", "B", "A"], e_inverted, 0.80, ["doc1"])
    res7 = evaluator.evaluate_chain_match(gold, pred_inverted)
    assert res7.match_level == ChainMatchLevel.SEMANTIC_POLARITY_MISMATCH


def test_causal_chain_builder_multi_hop():
    builder = CausalChainBuilder(max_hops=5, min_path_confidence=0.20)

    # Mock assertions forming: PhoP -> PmrD -> PmrA -> arn Operon -> Polymyxin Resistance
    class MockAssertion:
        def __init__(self, c, e, p=1, conf=0.90):
            self.cause_canonical = c
            self.effect_canonical = e
            self.page_number = p
            self.confidence = conf
            self.relation_type = "UPREGULATES"
            self.evidence_quote = f"{c} activates {e}"
            self.section_title = "Results"
            self.is_negated = False

    assertions = [
        MockAssertion("PhoP", "PmrD", 1, 0.95),
        MockAssertion("PmrD", "PmrA", 2, 0.92),
        MockAssertion("PmrA", "arn Operon", 3, 0.90),
        MockAssertion("arn Operon", "Polymyxin B", 4, 0.88),
    ]

    chains = builder.discover_chains(assertions, doc_id="PMC1804205")
    assert len(chains) > 0

    # Verify a 4-hop chain (5 nodes) is found from PhoP to Polymyxin B
    pho_to_res = [c for c in chains if c.nodes[0] == "PhoP" and c.nodes[-1] == "Polymyxin B"]
    assert len(pho_to_res) >= 1
    longest_chain = pho_to_res[0]
    assert longest_chain.hop_count == 4
    assert longest_chain.nodes == ["PhoP", "PmrD", "PmrA", "arn Operon", "Polymyxin B"]
    assert longest_chain.composite_confidence > 0.40


def test_conditional_composition_model_and_classes():
    model = ConditionalCompositionModel()

    # Valid multi-hop biological pathway
    valid_chain = CausalChain(
        chain_id="v1",
        nodes=["PhoP", "PmrD", "PmrA"],
        edges=[
            ChainEdge("PhoP", "PmrD", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.95, "PhoP activates PmrD", 1, doc_id="PMC1804205"),
            ChainEdge("PmrD", "PmrA", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.92, "PmrD activates PmrA", 2, doc_id="PMC1804205"),
        ],
        composite_confidence=0.87,
        doc_ids=["PMC1804205"],
    )
    c_class, score, expl = model.score_composition(valid_chain)
    assert c_class == CompositionClass.MULTI_HOP_SUPPORTED
    assert score >= 0.70

    # Invalid shortcut traversing terminal sink phenotype: Sensor -> Virulence -> Target
    sink_chain = CausalChain(
        chain_id="s1",
        nodes=["Sensor", "Virulence", "Kinase"],
        edges=[
            ChainEdge("Sensor", "Virulence", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 1, doc_id="d1"),
            ChainEdge("Virulence", "Kinase", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "", 2, doc_id="d1"),
        ],
        composite_confidence=0.81,
        doc_ids=["d1"],
    )
    c_class2, score2, expl2 = model.score_composition(sink_chain)
    assert c_class2 == CompositionClass.UNSUPPORTED_SHORTCUT
    assert score2 < 0.20
    assert "traverses terminal phenotypic outcome" in expl2


def test_partial_chain_matcher_cases():
    matcher = PartialChainMatcher()

    # Case A: Missing bridge detection (Gold: A -> B -> C -> D, Extracted has A -> B and C -> D)
    gold = CausalChain(
        chain_id="g1",
        nodes=["PhoP", "PmrD", "PmrA", "arn Operon"],
        edges=[
            ChainEdge("PhoP", "PmrD", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="d1"),
            ChainEdge("PmrD", "PmrA", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="d1"),
            ChainEdge("PmrA", "arn Operon", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 1.0, "", 1, doc_id="d1"),
        ],
        composite_confidence=1.0,
        doc_ids=["d1"],
    )

    extracted_edges = [
        ("PhoP", "PmrD"),
        ("PmrA", "arn Operon"),
    ]

    bridge_info = matcher.discover_missing_bridge(gold, extracted_edges)
    assert bridge_info is not None
    assert bridge_info["case"] == "Case A (Missing Bridge)"
    assert ("PmrD", "PmrA") in bridge_info["missing_bridges"]


def test_cross_paper_linking_engine():
    linker = CrossPaperLinker()

    # Paper 1 (PMC1804205): Acid pH -> PmrB -> PmrA
    p1_chains = [
        CausalChain(
            chain_id="p1_c1",
            nodes=["Acid pH", "PmrB", "PmrA"],
            edges=[
                ChainEdge("Acid pH", "PmrB", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.95, "Acid pH activates PmrB", 1, doc_id="PMC1804205"),
                ChainEdge("PmrB", "PmrA", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.90, "PmrB phosphorylates PmrA", 2, doc_id="PMC1804205"),
            ],
            composite_confidence=0.855,
            doc_ids=["PMC1804205"],
        )
    ]

    # Paper 2 (PMC2581603): PmrA -> arn Operon -> Polymyxin Resistance
    p2_chains = [
        CausalChain(
            chain_id="p2_c1",
            nodes=["PmrA", "arn Operon", "Polymyxin Resistance"],
            edges=[
                ChainEdge("PmrA", "arn Operon", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.92, "PmrA binds arn promoter", 3, doc_id="PMC2581603"),
                ChainEdge("arn Operon", "Polymyxin Resistance", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.88, "arn modifies LPS to confer resistance", 4, doc_id="PMC2581603"),
            ],
            composite_confidence=0.809,
            doc_ids=["PMC2581603"],
        )
    ]

    cross_links = linker.discover_cross_paper_bridges(p1_chains, p2_chains, "PMC1804205", "PMC2581603")
    assert len(cross_links) >= 1
    top_link = cross_links[0]
    assert "pmra" in top_link.pivot_entity.lower()
    assert top_link.source_entity in ("Acid pH", "PmrB")
    assert top_link.target_entity in ("arn Operon", "Polymyxin Resistance")
    assert top_link.source_doc_id == "PMC1804205"
    assert top_link.target_doc_id == "PMC2581603"
    assert top_link.mechanism_compatibility == "COMPATIBLE"
    assert top_link.organism_doc1 == "Salmonella enterica"
    assert top_link.organism_doc2 == "Pseudomonas aeruginosa"
    assert top_link.link_category == "PLAUSIBLE_HYPOTHESIS"
    assert top_link.dual_independent_support is True


def test_learned_composition_model_and_dataset():
    from evryn.paper.learned_composition_model import (
        LeakageResistantCompositionDataset,
        LearnedCompositionClassifier,
    )

    X, y, labels = LeakageResistantCompositionDataset.generate_training_data()
    assert len(y) >= 25
    assert X.shape[1] == 12

    clf = LearnedCompositionClassifier("random_forest")
    clf.fit(X, y)
    assert clf.is_fitted is True

    # Test prediction on direct chain
    e1 = ChainEdge("Rv2623", "ATP-Binding", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.95, "", 1)
    ch_direct = CausalChain("ch_d", ["Rv2623", "ATP-Binding"], [e1], 0.95, ["doc"])
    c_cls, conf, expl = clf.predict_class(ch_direct)
    assert c_cls in (CompositionClass.DIRECT_SUPPORTED, CompositionClass.MULTI_HOP_SUPPORTED)

    # Test rejection of sink traversal hard negative
    e_s1 = ChainEdge("RetS", "Biofilm", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.85, "", 1)
    e_s2 = ChainEdge("Biofilm", "GacS", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.80, "", 2)
    ch_sink = CausalChain("ch_sink", ["RetS", "Biofilm", "GacS"], [e_s1, e_s2], 0.80, ["doc"])
    c_cls_sink, conf_sink, _ = clf.predict_class(ch_sink)
    assert c_cls_sink == CompositionClass.UNSUPPORTED_SHORTCUT


def test_partial_chain_recovery_and_bridge_ranking():
    from evryn.paper.partial_chain_matcher import BridgeStatus
    from types import SimpleNamespace

    matcher = PartialChainMatcher()
    edges = [
        ChainEdge("A", "B", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.9, "", 1),
        ChainEdge("B", "C", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.9, "", 1),
        ChainEdge("C", "D", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.9, "", 1),
    ]
    gold = CausalChain("gold_4", ["A", "B", "C", "D"], edges, 0.9, ["doc"])

    # Simulate extraction where B->C is missing
    extracted = [
        SimpleNamespace(cause_canonical="A", effect_canonical="B", is_negated=False),
        SimpleNamespace(cause_canonical="C", effect_canonical="D", is_negated=False),
    ]

    recovery = matcher.evaluate_gold_chain_recovery(gold, extracted)
    assert recovery["gold_hop_count"] == 3
    assert recovery["recovered_edges_count"] == 2
    assert recovery["missing_edges"] == [("B", "C")]
    assert recovery["longest_contiguous_subpath_hops"] == 1
    assert recovery["is_complete_ordered_path_recovered"] is False
    assert len(recovery["candidate_bridges"]) == 1
    assert recovery["candidate_bridges"][0]["status"] == BridgeStatus.CANDIDATE_MISSING_EDGE.value

