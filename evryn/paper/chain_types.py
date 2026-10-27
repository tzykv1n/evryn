"""
EVRYN Chain Reasoning Types & Representation Specification (Phase 3).
Provides formal, backward-compatible data models distinguishing:
1. Direct causal relations (textual claim A -> B)
2. Multi-hop causal paths (sequence A -> B -> C -> ...)
3. Candidate composed relations (higher-level hypothesis A -> E)
4. Evidence-backed cross-document relations (links connecting entities across papers/sections)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set


class CausalEdgeKind(str, Enum):
    DIRECT_LOCAL = "DIRECT_LOCAL"              # A. Direct textual claim directly supporting A -> B
    MULTI_HOP_STEP = "MULTI_HOP_STEP"          # B. Constituent step inside a multi-hop path
    COMPOSED_CANDIDATE = "COMPOSED_CANDIDATE"  # C. Candidate composed relation A -> E suggested by path
    CROSS_SECTION_LINK = "CROSS_SECTION_LINK"  # D1. Cross-section inferred connection in same doc
    CROSS_DOCUMENT_LINK = "CROSS_DOCUMENT_LINK"# D2. Cross-paper link with multi-document provenance


class ChainMatchLevel(str, Enum):
    EXACT_CHAIN_MATCH = "EXACT_CHAIN_MATCH"                              # 1. Exact node and edge sequence match
    EXACT_EDGE_SET_MATCH = "EXACT_EDGE_SET_MATCH"                        # 2. Exact edge-set match with equivalent aliases
    PARTIAL_CONTIGUOUS_MATCH = "PARTIAL_CONTIGUOUS_MATCH"                # 3. Contiguous subpath matched
    PARTIAL_NON_CONTIGUOUS_MATCH = "PARTIAL_NON_CONTIGUOUS_MATCH"        # 4. Partial non-contiguous with missing intermediate bridges
    SUBPATH_INSIDE_LONGER = "SUBPATH_INSIDE_LONGER"                      # 5. Matched subpath inside longer predicted path
    ENDPOINT_MATCH_INCORRECT_PATH = "ENDPOINT_MATCH_INCORRECT_PATH"      # 6. Same endpoints but incorrect intermediate path
    SEMANTIC_POLARITY_MISMATCH = "SEMANTIC_POLARITY_MISMATCH"            # 7. Correct entity pair but inverted direction/polarity
    CANDIDATE_REQUIRING_ADJUDICATION = "CANDIDATE_REQUIRING_ADJUDICATION"# 8. Candidate match requiring human adjudication


@dataclass
class ChainEdge:
    source: str
    target: str
    relation_type: str = "UPREGULATES"
    edge_kind: CausalEdgeKind = CausalEdgeKind.DIRECT_LOCAL
    polarity: str = "POSITIVE"
    confidence: float = 0.90
    evidence_text: str = ""
    page_number: int = 1
    section_title: str = "Results"
    doc_id: str = ""
    provenance_rule: str = "Syntactic Rule"
    is_negated: bool = False
    is_hypothetical: bool = False
    intermediate_intermediates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "edge_kind": self.edge_kind.value if isinstance(self.edge_kind, Enum) else str(self.edge_kind),
            "polarity": self.polarity,
            "confidence": round(self.confidence, 4),
            "evidence_text": self.evidence_text,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "doc_id": self.doc_id,
            "provenance_rule": self.provenance_rule,
            "is_negated": self.is_negated,
            "is_hypothetical": self.is_hypothetical,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainEdge":
        d = dict(data)
        if "edge_kind" in d and isinstance(d["edge_kind"], str):
            d["edge_kind"] = CausalEdgeKind(d["edge_kind"])
        return cls(**d)


@dataclass
class CausalChain:
    chain_id: str
    nodes: List[str]
    edges: List[ChainEdge]
    hop_count: int = field(init=False)
    overall_polarity: str = "POSITIVE"
    composite_confidence: float = 0.85
    derivation_lineage: List[str] = field(default_factory=list)
    doc_ids: List[str] = field(default_factory=list)
    is_composed: bool = False
    endpoint_pair: Tuple[str, str] = field(init=False)

    def __post_init__(self):
        self.hop_count = len(self.edges)
        if self.nodes and len(self.nodes) >= 2:
            self.endpoint_pair = (self.nodes[0], self.nodes[-1])
        elif self.edges:
            self.endpoint_pair = (self.edges[0].source, self.edges[-1].target)
        else:
            self.endpoint_pair = ("", "")

        # Compute net polarity
        neg_count = sum(1 for e in self.edges if e.polarity == "NEGATIVE" or e.is_negated)
        self.overall_polarity = "NEGATIVE" if (neg_count % 2 == 1) else "POSITIVE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "nodes": self.nodes,
            "hop_count": self.hop_count,
            "endpoint_pair": list(self.endpoint_pair),
            "overall_polarity": self.overall_polarity,
            "composite_confidence": round(self.composite_confidence, 4),
            "derivation_lineage": self.derivation_lineage,
            "doc_ids": self.doc_ids,
            "is_composed": self.is_composed,
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalChain":
        edges = [ChainEdge.from_dict(e) if isinstance(e, dict) else e for e in data.get("edges", [])]
        return cls(
            chain_id=data["chain_id"],
            nodes=data["nodes"],
            edges=edges,
            composite_confidence=data.get("composite_confidence", 0.85),
            derivation_lineage=data.get("derivation_lineage", []),
            doc_ids=data.get("doc_ids", []),
            is_composed=data.get("is_composed", False),
        )


@dataclass
class ChainMatchResult:
    gold_chain: CausalChain
    predicted_chain: Optional[CausalChain]
    match_level: ChainMatchLevel
    matched_nodes: List[str] = field(default_factory=list)
    matched_edges: List[Tuple[str, str]] = field(default_factory=list)
    missing_nodes: List[str] = field(default_factory=list)
    missing_edges: List[Tuple[str, str]] = field(default_factory=list)
    missing_bridges: List[Tuple[str, str]] = field(default_factory=list)
    competing_shortcuts: List[Tuple[str, str]] = field(default_factory=list)
    match_score: float = 0.0
    diagnostic_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gold_chain_id": self.gold_chain.chain_id,
            "predicted_chain_id": self.predicted_chain.chain_id if self.predicted_chain else None,
            "match_level": self.match_level.value if isinstance(self.match_level, Enum) else str(self.match_level),
            "gold_nodes": self.gold_chain.nodes,
            "predicted_nodes": self.predicted_chain.nodes if self.predicted_chain else [],
            "hop_count": self.gold_chain.hop_count,
            "matched_nodes": self.matched_nodes,
            "matched_edges": [list(e) for e in self.matched_edges],
            "missing_nodes": self.missing_nodes,
            "missing_edges": [list(e) for e in self.missing_edges],
            "missing_bridges": [list(b) for b in self.missing_bridges],
            "competing_shortcuts": [list(s) for s in self.competing_shortcuts],
            "match_score": round(self.match_score, 4),
            "diagnostic_note": self.diagnostic_note,
        }
