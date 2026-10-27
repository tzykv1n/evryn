"""
Chain-Aware Evaluation and Matching Engine (Phase 3).
Evaluates causal pathways across 8 deterministic matching levels:
1. Exact chain match
2. Exact edge-set match with alias equivalence
3. Partial contiguous path match
4. Partial non-contiguous match with explicit missing bridges
5. Subpath matched inside longer predicted path
6. Common endpoints with incorrect intermediate path (false shortcuts)
7. Entity pair matched with inverted direction/polarity
8. Candidate requiring human adjudication
"""

import re
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Set

from evryn.paper.chain_types import (
    CausalEdgeKind,
    ChainMatchLevel,
    ChainEdge,
    CausalChain,
    ChainMatchResult,
)
from evryn.paper.normalizer import PaperEntityNormalizer


class ChainEvaluator:
    def __init__(self, normalizer: Optional[PaperEntityNormalizer] = None):
        self.normalizer = normalizer or PaperEntityNormalizer()

    def norm_entity(self, text: str) -> str:
        if not text:
            return ""
        canon = self.normalizer.canonicalize(text)
        return re.sub(r"[^a-zA-Z0-9]+", "", canon).lower()

    def edges_equal(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> bool:
        return self.norm_entity(e1[0]) == self.norm_entity(e2[0]) and self.norm_entity(e1[1]) == self.norm_entity(e2[1])

    def extract_gold_chains_from_spec(self, paper_spec: Dict[str, Any], max_length: int = 5) -> List[CausalChain]:
        """Builds all valid simple directed chains from reference gold standard direct and cross edges."""
        pmcid = paper_spec.get("pmcid", "")
        direct_edges = [tuple(e) for e in paper_spec.get("direct_edges", [])]
        ents = paper_spec.get("canonical_entities", [])

        G = nx.DiGraph()
        G.add_nodes_from(ents)
        for u, v in direct_edges:
            G.add_edge(u, v)

        chains = []
        chain_idx = 0
        nodes = list(G.nodes())

        for s in nodes:
            for t in nodes:
                if s != t:
                    for path in nx.all_simple_paths(G, s, t, cutoff=max_length):
                        if len(path) >= 3:  # At least 2 hops (3 nodes)
                            edges = []
                            for i in range(len(path) - 1):
                                edges.append(
                                    ChainEdge(
                                        source=path[i],
                                        target=path[i + 1],
                                        relation_type="UPREGULATES",
                                        edge_kind=CausalEdgeKind.DIRECT_LOCAL,
                                        polarity="POSITIVE",
                                        confidence=1.0,
                                        evidence_text=f"Direct reference annotation in {pmcid}",
                                        doc_id=pmcid,
                                    )
                                )
                            chain_idx += 1
                            chain = CausalChain(
                                chain_id=f"{pmcid}_gold_chain_{chain_idx:03d}",
                                nodes=path,
                                edges=edges,
                                composite_confidence=1.0,
                                doc_ids=[pmcid],
                            )
                            chains.append(chain)

        return chains

    def evaluate_chain_match(self, gold: CausalChain, pred: CausalChain) -> ChainMatchResult:
        """Compares a single gold chain against a candidate predicted chain across the 8 matching levels."""
        gold_norm_nodes = [self.norm_entity(n) for n in gold.nodes]
        pred_norm_nodes = [self.norm_entity(n) for n in pred.nodes]

        gold_edge_tuples = [(e.source, e.target) for e in gold.edges]
        pred_edge_tuples = [(e.source, e.target) for e in pred.edges]

        matched_edges = [ge for ge in gold_edge_tuples if any(self.edges_equal(ge, pe) for pe in pred_edge_tuples)]
        missing_edges = [ge for ge in gold_edge_tuples if not any(self.edges_equal(ge, pe) for pe in pred_edge_tuples)]

        matched_nodes = [gn for gn in gold.nodes if any(self.norm_entity(gn) == pn for pn in pred_norm_nodes)]
        missing_nodes = [gn for gn in gold.nodes if not any(self.norm_entity(gn) == pn for pn in pred_norm_nodes)]

        # 1. Exact Chain Match (Level 1)
        if gold_norm_nodes == pred_norm_nodes and len(missing_edges) == 0 and len(pred_edge_tuples) == len(gold_edge_tuples):
            return ChainMatchResult(
                gold_chain=gold,
                predicted_chain=pred,
                match_level=ChainMatchLevel.EXACT_CHAIN_MATCH,
                matched_nodes=gold.nodes,
                matched_edges=gold_edge_tuples,
                missing_nodes=[],
                missing_edges=[],
                match_score=1.0,
                diagnostic_note="Exact node-for-node and edge-for-edge chain sequence match.",
            )

        # 2. Exact Edge Set Match (Level 2)
        if len(gold_edge_tuples) == len(matched_edges) and len(pred_edge_tuples) == len(matched_edges):
            return ChainMatchResult(
                gold_chain=gold,
                predicted_chain=pred,
                match_level=ChainMatchLevel.EXACT_EDGE_SET_MATCH,
                matched_nodes=gold.nodes,
                matched_edges=gold_edge_tuples,
                missing_nodes=[],
                missing_edges=[],
                match_score=0.98,
                diagnostic_note="Exact edge-set match under alias equivalence.",
            )

        # 5. Subpath inside longer predicted path (Level 5)
        if len(gold_norm_nodes) < len(pred_norm_nodes):
            gold_seq = " -> ".join(gold_norm_nodes)
            pred_seq = " -> ".join(pred_norm_nodes)
            if gold_seq in pred_seq:
                return ChainMatchResult(
                    gold_chain=gold,
                    predicted_chain=pred,
                    match_level=ChainMatchLevel.SUBPATH_INSIDE_LONGER,
                    matched_nodes=gold.nodes,
                    matched_edges=gold_edge_tuples,
                    missing_nodes=[],
                    missing_edges=[],
                    match_score=0.90,
                    diagnostic_note=f"Complete gold path ({gold.hop_count} hops) matched as subpath inside longer predicted chain ({pred.hop_count} hops).",
                )

        # 3. Partial Contiguous Subpath (Level 3)
        if len(gold_norm_nodes) > len(pred_norm_nodes):
            gold_seq = " -> ".join(gold_norm_nodes)
            pred_seq = " -> ".join(pred_norm_nodes)
            if pred_seq in gold_seq:
                score = len(pred.edges) / len(gold.edges)
                return ChainMatchResult(
                    gold_chain=gold,
                    predicted_chain=pred,
                    match_level=ChainMatchLevel.PARTIAL_CONTIGUOUS_MATCH,
                    matched_nodes=matched_nodes,
                    matched_edges=matched_edges,
                    missing_nodes=missing_nodes,
                    missing_edges=missing_edges,
                    match_score=score,
                    diagnostic_note=f"Contiguous subpath of {len(pred.edges)}/{len(gold.edges)} edges matched.",
                )

        # 4. Partial Non-Contiguous Match with missing intermediate bridges (Level 4)
        if len(matched_edges) >= 2 and len(missing_edges) >= 1:
            # Find the missing bridges between matched segments
            bridges = []
            for i in range(len(gold.nodes) - 1):
                edge_t = (gold.nodes[i], gold.nodes[i + 1])
                if not any(self.edges_equal(edge_t, pe) for pe in pred_edge_tuples):
                    bridges.append(edge_t)

            score = len(matched_edges) / len(gold.edges)
            return ChainMatchResult(
                gold_chain=gold,
                predicted_chain=pred,
                match_level=ChainMatchLevel.PARTIAL_NON_CONTIGUOUS_MATCH,
                matched_nodes=matched_nodes,
                matched_edges=matched_edges,
                missing_nodes=missing_nodes,
                missing_edges=missing_edges,
                missing_bridges=bridges,
                match_score=score,
                diagnostic_note=f"Non-contiguous chain recovered ({len(matched_edges)}/{len(gold.edges)} edges). Missing bridge(s): {bridges}.",
            )

        # 6. Common Endpoints but incorrect intermediate path (Level 6: False Shortcut / Divergence)
        if (
            self.norm_entity(gold.endpoint_pair[0]) == self.norm_entity(pred.endpoint_pair[0])
            and self.norm_entity(gold.endpoint_pair[1]) == self.norm_entity(pred.endpoint_pair[1])
        ):
            return ChainMatchResult(
                gold_chain=gold,
                predicted_chain=pred,
                match_level=ChainMatchLevel.ENDPOINT_MATCH_INCORRECT_PATH,
                matched_nodes=[gold.endpoint_pair[0], gold.endpoint_pair[1]],
                matched_edges=matched_edges,
                missing_nodes=gold.nodes[1:-1],
                missing_edges=missing_edges,
                competing_shortcuts=[pred.endpoint_pair],
                match_score=0.15,
                diagnostic_note=f"Endpoint overlap matched ({gold.endpoint_pair[0]} -> {gold.endpoint_pair[1]}), but intermediate path diverged (Gold intermediates: {gold.nodes[1:-1]} vs Pred: {pred.nodes[1:-1]}).",
            )

        # 7. Semantic direction / polarity mismatch (Level 7)
        if (
            self.norm_entity(gold.endpoint_pair[0]) == self.norm_entity(pred.endpoint_pair[1])
            and self.norm_entity(gold.endpoint_pair[1]) == self.norm_entity(pred.endpoint_pair[0])
        ):
            return ChainMatchResult(
                gold_chain=gold,
                predicted_chain=pred,
                match_level=ChainMatchLevel.SEMANTIC_POLARITY_MISMATCH,
                matched_nodes=matched_nodes,
                matched_edges=[],
                missing_nodes=[],
                missing_edges=gold_edge_tuples,
                match_score=0.05,
                diagnostic_note="Inverted causal direction detected between endpoints.",
            )

        # 8. Unmatched / Adjudication candidate (Level 8)
        score = len(matched_nodes) / max(len(gold.nodes), 1) * 0.1
        return ChainMatchResult(
            gold_chain=gold,
            predicted_chain=pred,
            match_level=ChainMatchLevel.CANDIDATE_REQUIRING_ADJUDICATION,
            matched_nodes=matched_nodes,
            matched_edges=matched_edges,
            missing_nodes=missing_nodes,
            missing_edges=missing_edges,
            match_score=score,
            diagnostic_note="Fragmentary overlap requiring context adjudication.",
        )

    def evaluate_paper_chains(
        self,
        gold_chains: List[CausalChain],
        predicted_chains: List[CausalChain],
    ) -> Dict[str, Any]:
        """Evaluates extracted chains against reference gold chains, computing multi-level recovery metrics."""
        results_by_gold: List[ChainMatchResult] = []

        level_counts: Dict[str, int] = {lvl.value: 0 for lvl in ChainMatchLevel}
        by_length_stats: Dict[int, Dict[str, int]] = {2: {"total": 0, "exact": 0, "partial": 0, "shortcuts": 0},
                                                      3: {"total": 0, "exact": 0, "partial": 0, "shortcuts": 0},
                                                      4: {"total": 0, "exact": 0, "partial": 0, "shortcuts": 0},
                                                      5: {"total": 0, "exact": 0, "partial": 0, "shortcuts": 0}}

        for gold in gold_chains:
            hop = min(gold.hop_count, 5)
            if hop not in by_length_stats:
                by_length_stats[hop] = {"total": 0, "exact": 0, "partial": 0, "shortcuts": 0}
            by_length_stats[hop]["total"] += 1

            best_res: Optional[ChainMatchResult] = None
            for pred in predicted_chains:
                res = self.evaluate_chain_match(gold, pred)
                if best_res is None or res.match_score > best_res.match_score:
                    best_res = res
                    if res.match_level in [ChainMatchLevel.EXACT_CHAIN_MATCH, ChainMatchLevel.EXACT_EDGE_SET_MATCH]:
                        break

            if best_res is None:
                best_res = ChainMatchResult(
                    gold_chain=gold,
                    predicted_chain=None,
                    match_level=ChainMatchLevel.CANDIDATE_REQUIRING_ADJUDICATION,
                    missing_nodes=gold.nodes,
                    missing_edges=[(e.source, e.target) for e in gold.edges],
                    match_score=0.0,
                    diagnostic_note="Unrecovered gold chain.",
                )

            results_by_gold.append(best_res)
            level_counts[best_res.match_level.value] += 1

            if best_res.match_level in [ChainMatchLevel.EXACT_CHAIN_MATCH, ChainMatchLevel.EXACT_EDGE_SET_MATCH]:
                by_length_stats[hop]["exact"] += 1
            elif best_res.match_level in [ChainMatchLevel.PARTIAL_CONTIGUOUS_MATCH, ChainMatchLevel.PARTIAL_NON_CONTIGUOUS_MATCH, ChainMatchLevel.SUBPATH_INSIDE_LONGER]:
                by_length_stats[hop]["partial"] += 1
            elif best_res.match_level == ChainMatchLevel.ENDPOINT_MATCH_INCORRECT_PATH:
                by_length_stats[hop]["shortcuts"] += 1

        total_gold = max(len(gold_chains), 1)
        exact_recovered = level_counts[ChainMatchLevel.EXACT_CHAIN_MATCH.value] + level_counts[ChainMatchLevel.EXACT_EDGE_SET_MATCH.value]
        partial_recovered = level_counts[ChainMatchLevel.PARTIAL_CONTIGUOUS_MATCH.value] + level_counts[ChainMatchLevel.PARTIAL_NON_CONTIGUOUS_MATCH.value] + level_counts[ChainMatchLevel.SUBPATH_INSIDE_LONGER.value]
        false_shortcuts = level_counts[ChainMatchLevel.ENDPOINT_MATCH_INCORRECT_PATH.value]

        exact_recall = exact_recovered / total_gold
        any_recovery_rate = (exact_recovered + partial_recovered) / total_gold

        total_pred = max(len(predicted_chains), 1)
        exact_precision = exact_recovered / total_pred if predicted_chains else 0.0
        exact_f1 = (2 * exact_precision * exact_recall / (exact_precision + exact_recall)) if (exact_precision + exact_recall) > 0 else 0.0

        return {
            "total_gold_chains": len(gold_chains),
            "total_predicted_chains": len(predicted_chains),
            "exact_chain_recall": round(exact_recall, 4),
            "exact_chain_precision": round(exact_precision, 4),
            "exact_chain_f1": round(exact_f1, 4),
            "partial_chain_recovery_rate": round(partial_recovered / total_gold, 4),
            "any_chain_recovery_rate": round(any_recovery_rate, 4),
            "false_shortcut_rate": round(false_shortcuts / total_gold, 4),
            "matching_level_distribution": level_counts,
            "performance_by_length": by_length_stats,
            "chain_evaluations": [r.to_dict() for r in results_by_gold],
        }
