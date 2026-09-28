# evryn graph
# evryn -s graph

import re
from typing import List, Dict, Set, Tuple, Optional, Any

from .types import (
    CausalGraphEdge,
    MultiSentenceDocument,
    GraphHigherOrderCandidate,
    CandidatePattern,
)
from .graph_builder import DocumentCausalGraph
from ..nlp.higher_order.types import HigherOrderCategory


COMBINATION_LEXICON = [
    "together", "combination", "combined", "combinatorial",
    "co-administration", "co-treatment", "cooperative",
    "synergistic", "synergistically", "jointly", "in combination with",
    "interact with", "interaction between", "modifies the effect",
    "under condition", "enhances", "potentiates",
]


class CrossSentenceCandidateGenerator:

    def __init__(self, max_graph_distance: int = 3, max_candidates_per_doc: int = 40):
        self.max_graph_distance = max_graph_distance
        self.max_candidates_per_doc = max_candidates_per_doc

    def _matches_lexicon(self, text: str, lexicon: List[str]) -> List[str]:
        lower = text.lower()
        matched = []
        for word in lexicon:
            if re.search(r"\b" + re.escape(word) + r"\b", lower):
                matched.append(word)
        return matched

    def generate_candidates(
        self,
        doc: MultiSentenceDocument,
        graph: DocumentCausalGraph,
    ) -> List[GraphHigherOrderCandidate]:
        candidates: List[GraphHigherOrderCandidate] = []
        seen_triples: Set[Tuple[str, str, str]] = set()

        all_text = " ".join(doc.sentences)
        doc_synergy_cues = self._matches_lexicon(all_text, COMBINATION_LEXICON)

        node_ids = sorted(list(graph.entities.keys()))
        n_nodes = len(node_ids)

        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                node_a = node_ids[i]
                node_b = node_ids[j]

                name_a = graph.get_entity_name(node_a)
                name_b = graph.get_entity_name(node_b)

                shared_targets = graph.get_shared_targets(node_a, node_b)
                for target_c, edge_a, edge_b in shared_targets:
                    triple_key = (min(node_a, node_b), max(node_a, node_b), target_c)
                    if triple_key in seen_triples:
                        continue
                    seen_triples.add(triple_key)

                    supporting = [edge_a.edge_id, edge_b.edge_id]
                    dist_a = graph.shortest_path_distance(node_a, target_c)
                    dist_b = graph.shortest_path_distance(node_b, target_c)
                    graph_dist = max(dist_a, dist_b)

                    target_name = graph.get_entity_name(target_c)

                    combined_sent = f"{edge_a.sentence_text} {edge_b.sentence_text}"
                    edge_synergy = self._matches_lexicon(combined_sent, COMBINATION_LEXICON)

                    if edge_synergy:
                        pattern = CandidatePattern.PATTERN_E_EXPLICIT_SYNERGY
                        reason = f"Explicit combination cues: {', '.join(edge_synergy)}"
                    elif doc_synergy_cues and (name_a.lower() in all_text.lower() and name_b.lower() in all_text.lower()):
                        pattern = CandidatePattern.PATTERN_B_COMBINATION
                        reason = f"Document-level combination context: {', '.join(doc_synergy_cues[:2])}"
                    else:
                        pattern = CandidatePattern.LOCAL_NEIGHBORHOOD
                        reason = f"Shared direct convergence on {target_name}"

                    temporal_ok = graph.check_temporal_consistency(node_a, node_b, target_c)

                    cand = GraphHigherOrderCandidate(
                        candidate_id=f"ho_cand_{len(candidates) + 1:04d}",
                        document_id=doc.doc_id,
                        sources=(node_a, node_b),
                        source_names=(name_a, name_b),
                        target=target_c,
                        target_name=target_name,
                        generation_pattern=pattern,
                        generation_reason=reason,
                        supporting_edge_ids=supporting,
                        graph_distance=graph_dist,
                        temporal_valid=temporal_ok,
                        order=2,
                    )
                    candidates.append(cand)
                    if len(candidates) >= self.max_candidates_per_doc:
                        return candidates

                shared_mediators = graph.get_shared_mediators(node_a, node_b)
                for mediator_p, target_c, edges_path in shared_mediators:
                    triple_key = (min(node_a, node_b), max(node_a, node_b), target_c)
                    if triple_key in seen_triples:
                        continue
                    seen_triples.add(triple_key)

                    supporting = [e.edge_id for e in edges_path]
                    p_name = graph.get_entity_name(mediator_p)
                    target_name = graph.get_entity_name(target_c)

                    dist_a = graph.shortest_path_distance(node_a, target_c)
                    dist_b = graph.shortest_path_distance(node_b, target_c)
                    graph_dist = max(dist_a, dist_b)

                    if graph_dist > self.max_graph_distance:
                        continue

                    path_text = " ".join([e.sentence_text for e in edges_path])
                    path_synergy = self._matches_lexicon(path_text, COMBINATION_LEXICON)

                    if "pathway" in p_name.lower() or "mechanism" in p_name.lower():
                        pattern = CandidatePattern.PATTERN_D_SHARED_MECHANISM
                        reason = f"Shared pathway mediator {p_name} -> {target_name}"
                    elif path_synergy:
                        pattern = CandidatePattern.PATTERN_E_EXPLICIT_SYNERGY
                        reason = f"Pathway with explicit synergy: {', '.join(path_synergy)}"
                    else:
                        pattern = CandidatePattern.PATTERN_A_CONVERGENT
                        reason = f"Two-hop convergence through mediator {p_name} -> {target_name}"

                    temporal_ok = graph.check_temporal_consistency(node_a, node_b, target_c)

                    cand = GraphHigherOrderCandidate(
                        candidate_id=f"ho_cand_{len(candidates) + 1:04d}",
                        document_id=doc.doc_id,
                        sources=(node_a, node_b),
                        source_names=(name_a, name_b),
                        target=target_c,
                        target_name=target_name,
                        generation_pattern=pattern,
                        generation_reason=reason,
                        supporting_edge_ids=supporting,
                        graph_distance=graph_dist,
                        shared_mediator_id=mediator_p,
                        shared_mediator_name=p_name,
                        temporal_valid=temporal_ok,
                        order=2,
                    )
                    candidates.append(cand)
                    if len(candidates) >= self.max_candidates_per_doc:
                        return candidates

                for edge in doc.edges:
                    sent = edge.sentence_text.lower()
                    if name_a.lower() in sent and name_b.lower() in sent:
                        target_c = edge.target_id
                        if target_c not in (node_a, node_b):
                            triple_key = (min(node_a, node_b), max(node_a, node_b), target_c)
                            if triple_key not in seen_triples:
                                seen_triples.add(triple_key)
                                target_name = graph.get_entity_name(target_c)
                                supporting = [edge.edge_id]
                                pattern = CandidatePattern.PATTERN_C_CROSS_SENTENCE
                                reason = f"Sentence copresence with modification: {name_a} & {name_b} on {target_name}"
                                cand = GraphHigherOrderCandidate(
                                    candidate_id=f"ho_cand_{len(candidates) + 1:04d}",
                                    document_id=doc.doc_id,
                                    sources=(node_a, node_b),
                                    source_names=(name_a, name_b),
                                    target=target_c,
                                    target_name=target_name,
                                    generation_pattern=pattern,
                                    generation_reason=reason,
                                    supporting_edge_ids=supporting,
                                    graph_distance=1,
                                    temporal_valid=True,
                                    order=2,
                                )
                                candidates.append(cand)
                                if len(candidates) >= self.max_candidates_per_doc:
                                    return candidates

        return candidates
