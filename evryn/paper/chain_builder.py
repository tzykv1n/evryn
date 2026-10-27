"""
EVRYN Multi-Hop Causal Chain Discovery & Path Traversal Engine (Phase 3).
Discovers, evaluates, and ranks causal chains spanning 2 to 6+ hops across
sentences, sections, and documents with cycle detection and beam search.
"""

import math
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx

from evryn.paper.chain_types import (
    CausalEdgeKind,
    ChainEdge,
    CausalChain,
)
from evryn.paper.normalizer import PaperEntityNormalizer


class CausalChainBuilder:
    def __init__(
        self,
        max_hops: int = 6,
        beam_width: int = 50,
        min_path_confidence: float = 0.35,
        normalizer: Optional[PaperEntityNormalizer] = None,
    ):
        self.max_hops = max_hops
        self.beam_width = beam_width
        self.min_path_confidence = min_path_confidence
        self.normalizer = normalizer or PaperEntityNormalizer()

    def _canonical(self, name: str) -> str:
        if not name:
            return ""
        return self.normalizer.canonicalize(name)

    def build_graph_from_assertions_and_links(
        self,
        assertions: List[Any],
        cross_links: Optional[List[Any]] = None,
        doc_id: str = "",
    ) -> nx.DiGraph:
        """Constructs a directed graph with rich edge provenance from assertions and cross-page links."""
        G = nx.DiGraph()

        # 1. Add direct intra-sentence/intra-paragraph assertions
        for a in assertions:
            if getattr(a, "is_negated", False):
                continue
            src = self._canonical(getattr(a, "cause_canonical", None) or getattr(a, "cause_name", None) or getattr(a, "cause", ""))
            tgt = self._canonical(getattr(a, "effect_canonical", None) or getattr(a, "effect_name", None) or getattr(a, "effect", ""))

            if not src or not tgt or src == tgt:
                continue

            rel_type = getattr(a, "relation_type", "UPREGULATES")
            if hasattr(rel_type, "value"):
                rel_type = rel_type.value

            edge = ChainEdge(
                source=src,
                target=tgt,
                relation_type=str(rel_type),
                edge_kind=CausalEdgeKind.DIRECT_LOCAL,
                polarity="POSITIVE" if str(rel_type) not in ["INHIBITS", "REPRESSES", "BLOCKS"] else "NEGATIVE",
                confidence=float(getattr(a, "confidence", 0.90)),
                evidence_text=getattr(a, "evidence_quote", "") or getattr(a, "sentence_text", "") or "",
                page_number=int(getattr(a, "page_number", 1)),
                section_title=getattr(a, "section_title", "Results") or "Results",
                doc_id=doc_id or getattr(a, "doc_id", ""),
                provenance_rule="Intra-sentence syntactic assertion",
            )

            # Store the highest-confidence edge between src and tgt
            if G.has_edge(src, tgt):
                existing_edge = G[src][tgt]["edge"]
                if edge.confidence > existing_edge.confidence:
                    G[src][tgt]["edge"] = edge
            else:
                G.add_edge(src, tgt, edge=edge)

        # 2. Add verified cross-page / cross-section links
        for l in (cross_links or []):
            src = self._canonical(getattr(l, "source_entity", None) or getattr(l, "source", ""))
            tgt = self._canonical(getattr(l, "target_entity", None) or getattr(l, "target", ""))

            if not src or not tgt or src == tgt:
                continue

            # If direct edge already exists, do not overwrite with inferred link
            if G.has_edge(src, tgt) and G[src][tgt]["edge"].edge_kind == CausalEdgeKind.DIRECT_LOCAL:
                continue

            dist = int(getattr(l, "distance_pages", 1))
            edge = ChainEdge(
                source=src,
                target=tgt,
                relation_type="REGULATES",
                edge_kind=CausalEdgeKind.CROSS_SECTION_LINK if dist >= 1 else CausalEdgeKind.DIRECT_LOCAL,
                polarity="POSITIVE",
                confidence=float(getattr(l, "confidence", 0.75)),
                evidence_text=getattr(l, "linking_mechanism", "") or "Inferred cross-page regulatory pathway",
                page_number=dist,
                section_title="Cross-Page Linking",
                doc_id=doc_id,
                provenance_rule=f"Cross-page path search (distance {dist} pages)",
            )
            G.add_edge(src, tgt, edge=edge)

        return G

    def discover_chains(
        self,
        G: Any,
        doc_id: str = "",
        min_hops: int = 2,
        max_hops: Optional[int] = None,
    ) -> List[CausalChain]:
        """Discovers multi-hop causal chains up to max_hops with cycle avoidance and beam ranking."""
        if isinstance(G, list):
            G = self.build_graph_from_assertions_and_links(G, doc_id=doc_id)
        limit_hops = max_hops or self.max_hops
        nodes = list(G.nodes())
        discovered: List[CausalChain] = []
        seen_paths: Set[Tuple[str, ...]] = set()

        chain_id_counter = 0

        for start_node in nodes:
            # Beam search queue: (current_node, visited_nodes_tuple, edges_list, current_confidence)
            frontier = [(start_node, (start_node,), [], 1.0)]

            for depth in range(1, limit_hops + 1):
                next_frontier = []
                for curr, visited, path_edges, conf in frontier:
                    for neighbor in G.successors(curr):
                        if neighbor in visited:
                            continue  # Cycle avoidance

                        edge_data: ChainEdge = G[curr][neighbor]["edge"]
                        new_edges = path_edges + [edge_data]
                        new_visited = visited + (neighbor,)

                        # Composite confidence: harmonic/geometric penalty per hop
                        hop_decay = 0.95
                        new_conf = conf * edge_data.confidence * hop_decay

                        if new_conf < self.min_path_confidence:
                            continue

                        # If path length >= min_hops, emit chain
                        if len(new_edges) >= min_hops and new_visited not in seen_paths:
                            seen_paths.add(new_visited)
                            chain_id_counter += 1

                            lineage = [f"{e.source} -[{e.relation_type}]-> {e.target} (p.{e.page_number})" for e in new_edges]
                            chain = CausalChain(
                                chain_id=f"{doc_id}_chain_{chain_id_counter:04d}",
                                nodes=list(new_visited),
                                edges=new_edges,
                                composite_confidence=new_conf,
                                derivation_lineage=lineage,
                                doc_ids=[doc_id] if doc_id else [],
                                is_composed=True,
                            )
                            discovered.append(chain)

                        next_frontier.append((neighbor, new_visited, new_edges, new_conf))

                # Beam pruning: keep top-scoring paths for next depth
                next_frontier.sort(key=lambda x: x[3], reverse=True)
                frontier = next_frontier[: self.beam_width]
                if not frontier:
                    break

        # Sort all discovered chains by composite confidence and hop count
        discovered.sort(key=lambda c: (c.composite_confidence, -c.hop_count), reverse=True)
        return discovered
