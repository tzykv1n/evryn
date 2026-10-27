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

TERMINAL_PHENOTYPES = {
    "virulence",
    "pathogenicity",
    "host survival",
    "protective immunity",
    "mortality",
    "lethality",
    "host colonization",
    "equine strangles",
    "biofilm",
    "biofilms",
    "cytotoxicity",
    "spi1",
    "spi-1",
    "spi2",
    "spi-2",
    "opsonophagocytosis",
    "polymyxin b",
    "polymyxin",
    "antimicrobial resistance",
    "antibiotic resistance",
}

ADAPTER_PROTEINS = {
    "pmrd",
    "irap",
    "irad",
    "iram",
    "rssb",
}

TCSTS_REVERSE_PAIRS = {
    ("fimr", "fims"),
    ("pmra", "pmrb"),
    ("phop", "phoq"),
    ("vicr", "vick"),
    ("grar", "gras"),
    ("salr", "salk"),
    ("csrr", "csrs"),
    ("covr", "covs"),
    ("ssrb", "slya"),
    ("invf", "hila"),
    ("espa", "phop"),
    ("esx-1", "phop"),
    ("esat-6", "phop"),
    ("esat-6", "espa"),
}


class CrossPageLinker:

    def __init__(
        self,
        min_page_distance: int = 1,
        max_transitive_hops: int = 2,
        min_confidence: float = 0.58,
        enable_transitive_invariants: bool = True,
        enable_adapter_invariants: bool = True,
    ):
        self.min_page_distance = min_page_distance
        self.max_transitive_hops = max_transitive_hops
        self.min_confidence = min_confidence
        self.enable_transitive_invariants = enable_transitive_invariants
        self.enable_adapter_invariants = enable_adapter_invariants

    def find_cross_page_links(
        self,
        doc_or_assertions: Any,
        assertions: Optional[List[CausalAssertion]] = None,
    ) -> List[CrossPageLink]:
        if assertions is not None:
            target_assertions = assertions
        elif isinstance(doc_or_assertions, list):
            target_assertions = doc_or_assertions
        else:
            target_assertions = []

        valid_assertions = [a for a in target_assertions if not a.is_negated]
        links: List[CrossPageLink] = []
        best_links: Dict[Tuple[str, str], CrossPageLink] = {}
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
                    evidence_quote=a.evidence_quote,
                    cause_raw=a.cause,
                    effect_raw=a.effect,
                )
            else:
                if a.confidence > g.edges[src, tgt]["confidence"]:
                    g.edges[src, tgt]["confidence"] = a.confidence
                    g.edges[src, tgt]["assertion_id"] = a.assertion_id
                    g.edges[src, tgt]["page"] = a.page_number
                    g.edges[src, tgt]["section"] = a.section_title
                    g.edges[src, tgt]["evidence_quote"] = a.evidence_quote
                    g.edges[src, tgt]["cause_raw"] = a.cause
                    g.edges[src, tgt]["effect_raw"] = a.effect

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
                    # Hops = len(path) - 2 intermediate hops (e.g. 1 intermediate node = 1 hop, 2 intermediate nodes = 2 hops)
                    if len(path) <= 2 or (len(path) - 2) > self.max_transitive_hops:
                        continue

                    if self.enable_transitive_invariants:
                        # Invariant 1: Intermediate nodes cannot be terminal sink phenotypes
                        if any(node.lower() in TERMINAL_PHENOTYPES for node in path[1:-1]):
                            continue
                        # Invariant 2: Terminal phenotypes cannot be upstream causes of non-phenotype targets
                        if path[0].lower() in TERMINAL_PHENOTYPES and path[-1].lower() not in TERMINAL_PHENOTYPES:
                            continue
                        # Invariant 3: Directional biological invariants (TCSTS reverse pairs)
                        if (path[0].lower(), path[-1].lower()) in TCSTS_REVERSE_PAIRS:
                            continue
                        # Invariant 4: Post-translational adapter proteins should not initiate transitive chains to terminal phenotypes
                        if self.enable_adapter_invariants and path[0].lower() in ADAPTER_PROTEINS and path[-1].lower() in TERMINAL_PHENOTYPES:
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

                    path_conf = round(path_conf * (0.95 ** max(0, dist - 1)), 3)
                    if path_conf < self.min_confidence:
                        continue

                    inter_str = " -> ".join(path[1:-1])

                    constituent_edges = []
                    for k in range(len(path) - 1):
                        edge_data = g.edges[path[k], path[k + 1]]
                        constituent_edges.append({
                            "hop": k + 1,
                            "source": path[k],
                            "target": path[k + 1],
                            "assertion_id": edge_data["assertion_id"],
                            "page_number": edge_data["page"],
                            "section_title": edge_data["section"],
                            "evidence_quote": edge_data.get("evidence_quote", ""),
                            "confidence": edge_data["confidence"],
                        })

                    link_id = f"cplink_trans_{link_idx:04d}"
                    link_idx += 1

                    candidate_link = CrossPageLink(
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
                        constituent_edges=constituent_edges,
                        inference_rule="transitive_path_composition",
                        validation_status="validated",
                    )
                    pair_key = (u, v)
                    existing = best_links.get(pair_key)
                    if existing is None or candidate_link.confidence > existing.confidence:
                        best_links[pair_key] = candidate_link

        links.extend(best_links.values())

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

                    constituent_edges = [
                        {
                            "hop": 1,
                            "source": a1.cause_canonical,
                            "target": a1.effect_canonical,
                            "assertion_id": a1.assertion_id,
                            "page_number": a1.page_number,
                            "section_title": a1.section_title,
                            "evidence_quote": a1.evidence_quote,
                            "confidence": a1.confidence,
                        },
                        {
                            "hop": 2,
                            "source": a2.cause_canonical,
                            "target": a2.effect_canonical,
                            "assertion_id": a2.assertion_id,
                            "page_number": a2.page_number,
                            "section_title": a2.section_title,
                            "evidence_quote": a2.evidence_quote,
                            "confidence": a2.confidence,
                        },
                    ]
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
                            constituent_edges=constituent_edges,
                            inference_rule="cross_section_grounding" if is_claim_grounding else "multi_page_corroboration",
                            validation_status="validated",
                        )
                    )

        dedup_links: List[CrossPageLink] = []
        seen_keys: Set[Tuple[str, str]] = set()

        for l in sorted(links, key=lambda x: x.confidence, reverse=True):
            if l.source_entity == l.target_entity:
                continue
            if self.enable_transitive_invariants:
                s_low = l.source_entity.lower()
                t_low = l.target_entity.lower()
                if (s_low, t_low) in TCSTS_REVERSE_PAIRS:
                    continue
                if s_low in TERMINAL_PHENOTYPES and t_low not in TERMINAL_PHENOTYPES:
                    continue
            key = (l.source_entity, l.target_entity)
            if key not in seen_keys:
                seen_keys.add(key)
                dedup_links.append(l)

        return dedup_links

    link_cross_page_relations = find_cross_page_links
