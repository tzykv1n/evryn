# evryn paper graph <pdf_path>
# pytest tests/test_paper_pipeline.py

import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx

from .types import (
    CausalAssertion,
    CrossPageLink,
    EvidenceStatus,
    CausalRelationType,
)


class CrossPageLinker:

    def __init__(self, min_page_distance: int = 0, max_transitive_hops: int = 4):
        self.min_page_distance = min_page_distance
        self.max_transitive_hops = max_transitive_hops

    def find_cross_page_links(
        self,
        assertions: List[CausalAssertion],
    ) -> List[CrossPageLink]:
        valid_assertions = [a for a in assertions if not a.is_negated]
        links: List[CrossPageLink] = []
        link_idx = 1

        g = nx.DiGraph()
        for a in valid_assertions:
            src = a.cause_canonical
            tgt = a.effect_canonical
            if not g.has_edge(src, tgt):
                g.add_edge(
                    src,
                    tgt,
                    page=a.page_number,
                    assertion_id=a.assertion_id,
                    confidence=a.confidence,
                    section=a.section_title,
                )

        nodes = list(g.nodes())
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i == j:
                    continue
                u = nodes[i]
                v = nodes[j]

                try:
                    paths = list(nx.all_simple_paths(g, u, v, cutoff=self.max_transitive_hops + 1))
                except Exception:
                    paths = []

                for path in paths:
                    if len(path) <= 2:
                        continue

                    e_first = g.edges[path[0], path[1]]
                    e_last = g.edges[path[-2], path[-1]]

                    start_page = e_first["page"]
                    end_page = e_last["page"]
                    dist = abs(start_page - end_page)

                    if dist < self.min_page_distance:
                        continue

                    asrt_chain = []
                    path_conf = 1.0
                    for k in range(len(path) - 1):
                        edge_data = g.edges[path[k], path[k + 1]]
                        asrt_chain.append(edge_data["assertion_id"])
                        path_conf *= edge_data["confidence"]

                    path_conf = round(path_conf * (0.96 ** max(0, dist - 1)), 3)
                    inter_str = " -> ".join(path[1:-1])

                    link_id = f"cplink_trans_{link_idx:04d}"
                    link_idx += 1

                    links.append(
                        CrossPageLink(
                            link_id=link_id,
                            cause_assertion_id=asrt_chain[0],
                            effect_assertion_id=asrt_chain[-1],
                            source_entity=u,
                            intermediate_entity=inter_str,
                            target_entity=v,
                            cause_page=start_page,
                            effect_page=end_page,
                            distance_pages=dist,
                            cause_section=e_first["section"],
                            effect_section=e_last["section"],
                            linking_mechanism="transitive_chain",
                            confidence=path_conf,
                            provenance_chain=asrt_chain,
                        )
                    )

        for i, a1 in enumerate(valid_assertions):
            for j, a2 in enumerate(valid_assertions):
                if i >= j:
                    continue
                if (
                    a1.cause_canonical == a2.cause_canonical
                    and a1.effect_canonical == a2.effect_canonical
                    and a1.page_number != a2.page_number
                ):
                    dist = abs(a1.page_number - a2.page_number)
                    is_claim_grounding = (
                        ("result" in a1.section_title.lower() and "discussion" in a2.section_title.lower())
                        or ("discussion" in a1.section_title.lower() and "result" in a2.section_title.lower())
                    )
                    mechanism = "claim_to_evidence_grounding" if is_claim_grounding else "multi_page_corroboration"
                    conf = round(min(1.0, (a1.confidence + a2.confidence) / 1.7), 3)
                    link_id = f"cplink_ground_{link_idx:04d}"
                    link_idx += 1

                    links.append(
                        CrossPageLink(
                            link_id=link_id,
                            cause_assertion_id=a1.assertion_id,
                            effect_assertion_id=a2.assertion_id,
                            source_entity=a1.cause_canonical,
                            intermediate_entity="",
                            target_entity=a1.effect_canonical,
                            cause_page=a1.page_number,
                            effect_page=a2.page_number,
                            distance_pages=dist,
                            cause_section=a1.section_title,
                            effect_section=a2.section_title,
                            linking_mechanism=mechanism,
                            confidence=conf,
                            provenance_chain=[a1.assertion_id, a2.assertion_id],
                        )
                    )

        dedup_links: List[CrossPageLink] = []
        seen_keys: Set[Tuple[str, str, int, int]] = set()

        for l in sorted(links, key=lambda x: x.confidence, reverse=True):
            key = (l.source_entity, l.target_entity, l.cause_page, l.effect_page)
            if key not in seen_keys:
                seen_keys.add(key)
                dedup_links.append(l)

        return dedup_links
