# evryn paper graph <pdf_path>
# pytest tests/test_paper_pipeline.py

from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx

from .types import (
    CausalAssertion,
    CrossPageLink,
    PaperCausalGraph,
    EvidenceStatus,
    CausalRelationType,
)


class PaperGraphBuilder:

    def __init__(self, include_inferred_cross_page_edges: bool = True):
        self.include_inferred_cross_page_edges = include_inferred_cross_page_edges

    def build_graph(
        self,
        doc_id: str,
        title: str,
        assertions: List[CausalAssertion],
        cross_page_links: List[CrossPageLink],
    ) -> PaperCausalGraph:
        g = nx.DiGraph()
        provenance_map: Dict[str, Any] = {}

        for a in assertions:
            for ent in [a.cause_canonical, a.effect_canonical]:
                if not g.has_node(ent):
                    g.add_node(ent, name=ent, mention_count=0, pages=set())
                g.nodes[ent]["mention_count"] += 1
                g.nodes[ent]["pages"].add(a.page_number)

            src = a.cause_canonical
            tgt = a.effect_canonical

            if not g.has_edge(src, tgt):
                g.add_edge(
                    src,
                    tgt,
                    relation_type=a.relation_type.value,
                    is_direct=True,
                    is_negated=a.is_negated,
                    confidence=a.confidence,
                    pages={a.page_number},
                    evidence_status=a.evidence_status.value,
                    sentence_ids=[a.sentence_id],
                    quotes=[a.evidence_quote],
                    assertion_ids=[a.assertion_id],
                )
            else:
                ed = g.edges[src, tgt]
                ed["pages"].add(a.page_number)
                if a.sentence_id not in ed["sentence_ids"]:
                    ed["sentence_ids"].append(a.sentence_id)
                if a.evidence_quote not in ed["quotes"]:
                    ed["quotes"].append(a.evidence_quote)
                if a.assertion_id not in ed["assertion_ids"]:
                    ed["assertion_ids"].append(a.assertion_id)
                ed["confidence"] = max(ed["confidence"], a.confidence)

            provenance_map[a.assertion_id] = {
                "source": src,
                "target": tgt,
                "page": a.page_number,
                "section": a.section_title,
                "sentence_id": a.sentence_id,
                "quote": a.evidence_quote,
                "status": a.evidence_status.value,
                "negated": a.is_negated,
            }

        if self.include_inferred_cross_page_edges:
            for link in cross_page_links:
                if link.linking_mechanism == "transitive_chain" and link.target_entity:
                    src = link.source_entity
                    tgt = link.target_entity
                    
                    if not g.has_node(src):
                        g.add_node(src, name=src, mention_count=1, pages={link.cause_page})
                    if not g.has_node(tgt):
                        g.add_node(tgt, name=tgt, mention_count=1, pages={link.effect_page})

                    if not g.has_edge(src, tgt):
                        g.add_edge(
                            src,
                            tgt,
                            relation_type=CausalRelationType.DIRECT_CAUSE.value,
                            is_direct=False,
                            is_negated=False,
                            confidence=link.confidence,
                            pages={link.cause_page, link.effect_page},
                            evidence_status=EvidenceStatus.CROSS_PAGE_INFERENCE.value,
                            sentence_ids=[],
                            quotes=[f"Transitive inference via {link.intermediate_entity} spanning pages {link.cause_page} and {link.effect_page}"],
                            assertion_ids=link.provenance_chain,
                        )

                    provenance_map[link.link_id] = {
                        "source": src,
                        "target": tgt,
                        "intermediate": link.intermediate_entity,
                        "cause_page": link.cause_page,
                        "effect_page": link.effect_page,
                        "distance_pages": link.distance_pages,
                        "status": EvidenceStatus.CROSS_PAGE_INFERENCE.value,
                        "provenance_chain": link.provenance_chain,
                    }

        nodes_list: List[Dict[str, Any]] = []
        for n, data in g.nodes(data=True):
            nodes_list.append({
                "id": n,
                "name": data.get("name", n),
                "mention_count": data.get("mention_count", 1),
                "pages": sorted(list(data.get("pages", []))),
            })

        edges_list: List[Dict[str, Any]] = []
        for u, v, data in g.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "relation_type": data.get("relation_type", "DIRECT_CAUSE"),
                "is_direct": data.get("is_direct", True),
                "is_negated": data.get("is_negated", False),
                "confidence": data.get("confidence", 0.5),
                "pages": sorted(list(data.get("pages", []))),
                "evidence_status": data.get("evidence_status", "MEASURED_FACT"),
                "sentence_ids": data.get("sentence_ids", []),
                "quotes": data.get("quotes", []),
                "assertion_ids": data.get("assertion_ids", []),
            })

        return PaperCausalGraph(
            doc_id=doc_id,
            title=title,
            nodes=nodes_list,
            edges=edges_list,
            cross_page_links=cross_page_links,
            provenance_map=provenance_map,
        )
