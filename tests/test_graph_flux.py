# pytest tests/test_graph_flux.py

import os
import pytest
from typing import List

from evryn.core.types import NormalizedEntity, ScientificDomain
from evryn.nlp.higher_order.types import HigherOrderCategory
from evryn.graph_flux.types import (
    CausalGraphEdge,
    MultiSentenceDocument,
    GraphHigherOrderCandidate,
    CandidatePattern,
)
from evryn.graph_flux.graph_builder import DocumentGraphBuilder, DocumentCausalGraph
from evryn.graph_flux.candidate_generator import CrossSentenceCandidateGenerator
from evryn.graph_flux.evidence_model import GraphFluxEvidenceExtractor
from evryn.graph_flux.baselines import GraphFluxBaselineSuite
from evryn.graph_flux.synthetic_corpus import MultiSentenceBenchmarkGenerator
from evryn.graph_flux.evaluator import GraphFluxEvaluator
from evryn.pipelines.graph_pipeline import run_graph_flux_pipeline


def test_document_causal_graph_construction():
    builder = DocumentGraphBuilder()
    doc_id = "test_doc_01"
    ent_a = builder.normalizer.create_entity("Gene_A")
    ent_b = builder.normalizer.create_entity("Gene_B")
    ent_p = builder.normalizer.create_entity("Pathway_P")
    ent_c = builder.normalizer.create_entity("Phenotype_C")

    edges = [
        CausalGraphEdge(
            edge_id="e1",
            source_id=ent_a.entity_id,
            target_id=ent_p.entity_id,
            source_name="Gene_A",
            target_name="Pathway_P",
            relation_type="FORWARD",
            confidence=0.9,
            sentence_id="s1",
            sentence_text="Gene A activates Pathway P.",
            document_id=doc_id,
            source_span=(0, 6),
            target_span=(17, 26),
            temporal_order=1,
        ),
        CausalGraphEdge(
            edge_id="e2",
            source_id=ent_b.entity_id,
            target_id=ent_p.entity_id,
            source_name="Gene_B",
            target_name="Pathway_P",
            relation_type="FORWARD",
            confidence=0.88,
            sentence_id="s2",
            sentence_text="Gene B activates Pathway P.",
            document_id=doc_id,
            source_span=(0, 6),
            target_span=(17, 26),
            temporal_order=1,
        ),
        CausalGraphEdge(
            edge_id="e3",
            source_id=ent_p.entity_id,
            target_id=ent_c.entity_id,
            source_name="Pathway_P",
            target_name="Phenotype_C",
            relation_type="FORWARD",
            confidence=0.95,
            sentence_id="s3",
            sentence_text="Pathway P induces Phenotype C.",
            document_id=doc_id,
            source_span=(0, 9),
            target_span=(18, 29),
            temporal_order=2,
        ),
    ]

    doc = MultiSentenceDocument(
        doc_id=doc_id,
        title="Test Document",
        sentences=["Gene A activates Pathway P.", "Gene B activates Pathway P.", "Pathway P induces Phenotype C."],
        entities=[ent_a, ent_b, ent_p, ent_c],
        edges=edges,
    )

    graph = builder.build_from_document(doc)
    assert len(graph.entities) == 4
    assert graph.shortest_path_distance(ent_a.entity_id, ent_c.entity_id) == 2
    assert graph.shortest_path_distance(ent_b.entity_id, ent_c.entity_id) == 2

    shared_mediators = graph.get_shared_mediators(ent_a.entity_id, ent_b.entity_id)
    assert len(shared_mediators) == 1
    p_id, c_id, supporting = shared_mediators[0]
    assert p_id == ent_p.entity_id
    assert c_id == ent_c.entity_id
    assert len(supporting) == 3


def test_causal_cascade_rejection():
    builder = DocumentGraphBuilder()
    doc_id = "test_cascade_doc"
    ent_a = builder.normalizer.create_entity("Gene_A")
    ent_b = builder.normalizer.create_entity("Gene_B")
    ent_c = builder.normalizer.create_entity("Gene_C")

    edges = [
        CausalGraphEdge(
            edge_id="e1",
            source_id=ent_a.entity_id,
            target_id=ent_b.entity_id,
            source_name="Gene_A",
            target_name="Gene_B",
            relation_type="FORWARD",
            confidence=0.9,
            sentence_id="s1",
            sentence_text="A causes B.",
            document_id=doc_id,
            source_span=(0, 1),
            target_span=(9, 10),
            temporal_order=1,
        ),
        CausalGraphEdge(
            edge_id="e2",
            source_id=ent_b.entity_id,
            target_id=ent_c.entity_id,
            source_name="Gene_B",
            target_name="Gene_C",
            relation_type="FORWARD",
            confidence=0.9,
            sentence_id="s2",
            sentence_text="B causes C.",
            document_id=doc_id,
            source_span=(0, 1),
            target_span=(9, 10),
            temporal_order=2,
        ),
    ]

    doc = MultiSentenceDocument(
        doc_id=doc_id,
        title="Cascade Doc",
        sentences=["A causes B.", "B causes C."],
        entities=[ent_a, ent_b, ent_c],
        edges=edges,
    )
    graph = builder.build_from_document(doc)
    is_casc, path_str = graph.is_causal_cascade(ent_a.entity_id, ent_b.entity_id, ent_c.entity_id)
    assert is_casc is True
    assert "->" in path_str


def test_confounding_rejection():
    builder = DocumentGraphBuilder()
    doc_id = "test_confound_doc"
    ent_u = builder.normalizer.create_entity("Confounder_U")
    ent_a = builder.normalizer.create_entity("Gene_A")
    ent_c = builder.normalizer.create_entity("Gene_C")

    edges = [
        CausalGraphEdge(
            edge_id="e1",
            source_id=ent_u.entity_id,
            target_id=ent_a.entity_id,
            source_name="Confounder_U",
            target_name="Gene_A",
            relation_type="FORWARD",
            confidence=0.9,
            sentence_id="s1",
            sentence_text="U causes A.",
            document_id=doc_id,
            source_span=(0, 1),
            target_span=(10, 11),
        ),
        CausalGraphEdge(
            edge_id="e2",
            source_id=ent_u.entity_id,
            target_id=ent_c.entity_id,
            source_name="Confounder_U",
            target_name="Gene_C",
            relation_type="FORWARD",
            confidence=0.9,
            sentence_id="s2",
            sentence_text="U causes C.",
            document_id=doc_id,
            source_span=(0, 1),
            target_span=(10, 11),
        ),
    ]

    doc = MultiSentenceDocument(
        doc_id=doc_id,
        title="Confounding Doc",
        sentences=["U causes A.", "U causes C."],
        entities=[ent_u, ent_a, ent_c],
        edges=edges,
    )
    graph = builder.build_from_document(doc)
    u_found = graph.find_common_confounder(ent_a.entity_id, ent_c.entity_id)
    assert u_found == ent_u.entity_id


def test_temporal_consistency():
    builder = DocumentGraphBuilder()
    doc_id = "test_temporal_doc"
    ent_a = builder.normalizer.create_entity("Gene_A")
    ent_b = builder.normalizer.create_entity("Gene_B")
    ent_c = builder.normalizer.create_entity("Phenotype_C")

    edges = [
        CausalGraphEdge(
            edge_id="e1",
            source_id=ent_a.entity_id,
            target_id=ent_c.entity_id,
            source_name="Gene_A",
            target_name="Phenotype_C",
            relation_type="FORWARD",
            confidence=0.8,
            sentence_id="s1",
            sentence_text="A followed C.",
            document_id=doc_id,
            source_span=(0, 1),
            target_span=(12, 13),
            temporal_order=-1,
        )
    ]

    doc = MultiSentenceDocument(
        doc_id=doc_id,
        title="Temporal Doc",
        sentences=["A followed C."],
        entities=[ent_a, ent_b, ent_c],
        edges=edges,
    )
    graph = builder.build_from_document(doc)
    valid = graph.check_temporal_consistency(ent_a.entity_id, ent_b.entity_id, ent_c.entity_id)
    assert valid is False


def test_synthetic_benchmark_corpus_generation():
    generator = MultiSentenceBenchmarkGenerator(seed=42)
    docs = generator.generate_corpus(n_documents=22)
    assert len(docs) == 22

    mechs = {d.mechanism_label for d in docs}
    assert "multiplicative_interaction" in mechs
    assert "causal_cascade" in mechs
    assert "latent_confounding" in mechs
    assert "additive_pathway" in mechs

    for d in docs:
        assert len(d.sentences) >= 2
        assert len(d.ground_truth_higher_order) >= 1


def test_candidate_generation_and_evidence():
    generator = MultiSentenceBenchmarkGenerator(seed=42)
    docs = generator.generate_corpus(n_documents=10)
    builder = DocumentGraphBuilder()
    cand_gen = CrossSentenceCandidateGenerator(max_graph_distance=3)
    ev_extractor = GraphFluxEvidenceExtractor(random_state=42)

    all_cands = []
    for doc in docs:
        graph = builder.build_from_document(doc)
        cands = cand_gen.generate_candidates(doc, graph)
        for c in cands:
            ev = ev_extractor.assemble_candidate_evidence(c, doc, graph)
            assert "ling_has_synergy" in ev
            assert "graph_max_distance" in ev
            assert "flux_pid_synergy" in ev
            all_cands.append(c)

    assert len(all_cands) > 0


def test_baseline_predictions():
    suite = GraphFluxBaselineSuite()
    cands = [
        GraphHigherOrderCandidate(
            candidate_id="c1",
            document_id="doc1",
            sources=("a", "b"),
            source_names=("GeneA", "GeneB"),
            target="c",
            target_name="PhenoC",
            generation_pattern=CandidatePattern.PATTERN_E_EXPLICIT_SYNERGY,
            generation_reason="synergy",
            supporting_edge_ids=["e1", "e2"],
            graph_distance=1,
            evidence={
                "flux_pid_synergy": 0.65,
                "flux_delta_r2": 0.40,
                "flux_delta_r2_nonparam": 0.45,
                "flux_confounding_score": 0.05,
                "graph_temporal_valid": 1.0,
                "graph_is_cascade": 0.0,
                "ling_has_synergy": 1.0,
            },
        ),
        GraphHigherOrderCandidate(
            candidate_id="c2",
            document_id="doc2",
            sources=("a", "b"),
            source_names=("GeneA", "GeneB"),
            target="c",
            target_name="PhenoC",
            generation_pattern=CandidatePattern.LOCAL_NEIGHBORHOOD,
            generation_reason="cascade",
            supporting_edge_ids=["e1", "e2"],
            graph_distance=2,
            evidence={
                "flux_pid_synergy": 0.02,
                "flux_delta_r2": 0.01,
                "flux_confounding_score": 0.10,
                "graph_temporal_valid": 1.0,
                "graph_is_cascade": 1.0,
                "ling_has_synergy": 0.0,
            },
        ),
    ]

    preds_f = suite.predict_baseline_f_full_graph_flux(cands)
    assert preds_f[0] == HigherOrderCategory.HIGHER_ORDER_INTERACTION
    assert preds_f[1] == HigherOrderCategory.CAUSAL_CASCADE


def test_evaluator_metrics_calculation():
    evaluator = GraphFluxEvaluator(random_state=42)
    y_true = [
        HigherOrderCategory.JOINT_CAUSE,
        HigherOrderCategory.HIGHER_ORDER_INTERACTION,
        HigherOrderCategory.PAIRWISE_DECOMPOSABLE,
        HigherOrderCategory.CAUSAL_CASCADE,
    ]
    y_pred = [
        HigherOrderCategory.JOINT_CAUSE,
        HigherOrderCategory.HIGHER_ORDER_INTERACTION,
        HigherOrderCategory.PAIRWISE_DECOMPOSABLE,
        HigherOrderCategory.CAUSAL_CASCADE,
    ]

    res = evaluator.evaluate_predictions(y_true, y_pred, "Test Evaluator", 1.0)
    assert res.joint_f1 == 1.0
    assert res.interaction_f1 == 1.0
    assert res.exact_structural_match == 1.0
    assert res.false_joint_rate == 0.0
    assert res.cascade_as_joint_error_rate == 0.0


def test_graph_pipeline_from_scratch_and_cache(tmp_path):
    res1 = run_graph_flux_pipeline(from_scratch=True, n_documents=12)
    assert res1["total_documents"] == 12
    assert len(res1["results"]) == 6
    assert len(res1["figure_paths"]) == 14

    for p in res1["figure_paths"]:
        assert os.path.exists(p)

    res2 = run_graph_flux_pipeline(from_scratch=False, n_documents=12)
    assert res2["total_documents"] == 12
