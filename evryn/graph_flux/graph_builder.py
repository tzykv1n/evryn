# evryn graph
# evryn -s graph

from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Optional, Any

from ..core.types import NormalizedEntity, ScientificDomain
from ..normalization.normalizer import RelationNormalizer
from .types import CausalGraphEdge, MultiSentenceDocument


class DocumentCausalGraph:

    def __init__(self, doc_id: str, entities: List[NormalizedEntity], edges: List[CausalGraphEdge]):
        self.doc_id = doc_id
        self.entities = {e.entity_id: e for e in entities}
        self.edges = edges
        self.edge_map = {e.edge_id: e for e in edges}

        self.outgoing: Dict[str, List[CausalGraphEdge]] = defaultdict(list)
        self.incoming: Dict[str, List[CausalGraphEdge]] = defaultdict(list)

        for edge in edges:
            if edge.relation_type in ("FORWARD", "DIRECT_CAUSE"):
                self.outgoing[edge.source_id].append(edge)
                self.incoming[edge.target_id].append(edge)
            elif edge.relation_type == "BACKWARD":
                self.outgoing[edge.target_id].append(edge)
                self.incoming[edge.source_id].append(edge)

    def get_entity_name(self, entity_id: str) -> str:
        if entity_id in self.entities:
            return self.entities[entity_id].canonical_name
        return entity_id

    def shortest_path(self, start_id: str, end_id: str, max_depth: int = 4) -> Optional[List[str]]:
        if start_id == end_id:
            return [start_id]
        queue = deque([(start_id, [start_id])])
        visited = {start_id}
        while queue:
            curr, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for edge in self.outgoing.get(curr, []):
                nxt = edge.target_id
                if nxt == end_id:
                    return path + [nxt]
                if nxt not in visited and len(path) < max_depth:
                    visited.add(nxt)
                    queue.append((nxt, path + [nxt]))
        return None

    def shortest_path_distance(self, start_id: str, end_id: str, max_depth: int = 4) -> int:
        path = self.shortest_path(start_id, end_id, max_depth=max_depth)
        if path is not None:
            return len(path) - 1
        return 999

    def get_shared_targets(self, node_a: str, node_b: str) -> List[Tuple[str, CausalGraphEdge, CausalGraphEdge]]:
        targets_a = {e.target_id: e for e in self.outgoing.get(node_a, [])}
        targets_b = {e.target_id: e for e in self.outgoing.get(node_b, [])}
        common = set(targets_a.keys()) & set(targets_b.keys())
        common.discard(node_a)
        common.discard(node_b)
        return [(t, targets_a[t], targets_b[t]) for t in common]

    def get_shared_mediators(self, node_a: str, node_b: str) -> List[Tuple[str, str, List[CausalGraphEdge]]]:
        results = []
        mediators_a = {e.target_id: e for e in self.outgoing.get(node_a, [])}
        mediators_b = {e.target_id: e for e in self.outgoing.get(node_b, [])}
        common_p = set(mediators_a.keys()) & set(mediators_b.keys())
        common_p.discard(node_a)
        common_p.discard(node_b)

        for p in common_p:
            for down_edge in self.outgoing.get(p, []):
                target_c = down_edge.target_id
                if target_c not in (node_a, node_b, p):
                    results.append((p, target_c, [mediators_a[p], mediators_b[p], down_edge]))
        return results

    def is_causal_cascade(self, node_a: str, node_b: str, target_c: str) -> Tuple[bool, Optional[str]]:
        path_a_b = self.shortest_path(node_a, node_b, max_depth=2)
        if path_a_b and len(path_a_b) == 2:
            path_b_c = self.shortest_path(node_b, target_c, max_depth=2)
            if path_b_c and len(path_b_c) == 2:
                return True, f"{self.get_entity_name(node_a)} -> {self.get_entity_name(node_b)} -> {self.get_entity_name(target_c)}"

        path_b_a = self.shortest_path(node_b, node_a, max_depth=2)
        if path_b_a and len(path_b_a) == 2:
            path_a_c = self.shortest_path(node_a, target_c, max_depth=2)
            if path_a_c and len(path_a_c) == 2:
                return True, f"{self.get_entity_name(node_b)} -> {self.get_entity_name(node_a)} -> {self.get_entity_name(target_c)}"

        return False, None

    def find_common_confounder(self, node_a: str, target_c: str) -> Optional[str]:
        parents_a = {e.source_id for e in self.incoming.get(node_a, [])}
        parents_c = {e.source_id for e in self.incoming.get(target_c, [])}
        common = parents_a & parents_c
        return next(iter(common)) if common else None

    def check_temporal_consistency(self, node_a: str, node_b: str, target_c: str) -> bool:
        edges_to_c = [e for e in self.edges if e.target_id == target_c and e.source_id in (node_a, node_b)]
        for e in edges_to_c:
            if e.temporal_order is not None and e.temporal_order < 0:
                return False
        return True


class DocumentGraphBuilder:

    def __init__(self, normalizer: Optional[RelationNormalizer] = None):
        self.normalizer = normalizer or RelationNormalizer()

    def build_from_document(self, doc: MultiSentenceDocument) -> DocumentCausalGraph:
        entities = list(doc.entities)
        known_ids = {e.entity_id for e in entities}
        for edge in doc.edges:
            if edge.source_id not in known_ids:
                ent = self.normalizer.create_entity(edge.source_name)
                entities.append(ent)
                known_ids.add(ent.entity_id)
            if edge.target_id not in known_ids:
                ent = self.normalizer.create_entity(edge.target_name)
                entities.append(ent)
                known_ids.add(ent.entity_id)
        return DocumentCausalGraph(doc_id=doc.doc_id, entities=entities, edges=doc.edges)
