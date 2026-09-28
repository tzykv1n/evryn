# evryn graph
# evryn -s graph

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from ..core.types import NormalizedEntity, NormalizedRelation, Provenance
from ..nlp.higher_order.types import HigherOrderCategory


class CandidatePattern(str, Enum):
    PATTERN_A_CONVERGENT = "PATTERN_A_CONVERGENT"
    PATTERN_B_COMBINATION = "PATTERN_B_COMBINATION"
    PATTERN_C_CROSS_SENTENCE = "PATTERN_C_CROSS_SENTENCE"
    PATTERN_D_SHARED_MECHANISM = "PATTERN_D_SHARED_MECHANISM"
    PATTERN_E_EXPLICIT_SYNERGY = "PATTERN_E_EXPLICIT_SYNERGY"
    LOCAL_NEIGHBORHOOD = "LOCAL_NEIGHBORHOOD"


@dataclass
class CausalGraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    source_name: str
    target_name: str
    relation_type: str
    confidence: float
    sentence_id: str
    sentence_text: str
    document_id: str
    source_span: Tuple[int, int]
    target_span: Tuple[int, int]
    temporal_order: Optional[int] = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalGraphEdge":
        d = dict(data)
        if isinstance(d.get("source_span"), list):
            d["source_span"] = tuple(d["source_span"])
        if isinstance(d.get("target_span"), list):
            d["target_span"] = tuple(d["target_span"])
        return cls(**d)


@dataclass
class MultiSentenceDocument:
    doc_id: str
    title: str
    sentences: List[str]
    entities: List[NormalizedEntity]
    edges: List[CausalGraphEdge]
    ground_truth_higher_order: List[Dict[str, Any]] = field(default_factory=list)
    mechanism_label: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "sentences": self.sentences,
            "entities": [e.to_dict() for e in self.entities],
            "edges": [e.to_dict() for e in self.edges],
            "ground_truth_higher_order": self.ground_truth_higher_order,
            "mechanism_label": self.mechanism_label,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiSentenceDocument":
        entities = [NormalizedEntity.from_dict(e) for e in data.get("entities", [])]
        edges = [CausalGraphEdge.from_dict(e) for e in data.get("edges", [])]
        return cls(
            doc_id=data["doc_id"],
            title=data.get("title", ""),
            sentences=data.get("sentences", []),
            entities=entities,
            edges=edges,
            ground_truth_higher_order=data.get("ground_truth_higher_order", []),
            mechanism_label=data.get("mechanism_label", "general"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GraphHigherOrderCandidate:
    candidate_id: str
    document_id: str
    sources: Tuple[str, ...]
    source_names: Tuple[str, ...]
    target: str
    target_name: str
    generation_pattern: CandidatePattern
    generation_reason: str
    supporting_edge_ids: List[str]
    graph_distance: int
    shared_mediator_id: Optional[str] = None
    shared_mediator_name: Optional[str] = None
    order: int = 2
    temporal_valid: bool = True
    ground_truth_category: Optional[HigherOrderCategory] = None
    predicted_category: Optional[HigherOrderCategory] = None
    validation_status: str = "UNVALIDATED_HYPOTHESIS"
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["generation_pattern"] = self.generation_pattern.value
        d["ground_truth_category"] = self.ground_truth_category.value if self.ground_truth_category else None
        d["predicted_category"] = self.predicted_category.value if self.predicted_category else None
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphHigherOrderCandidate":
        d = dict(data)
        d["generation_pattern"] = CandidatePattern(d["generation_pattern"])
        if d.get("ground_truth_category"):
            d["ground_truth_category"] = HigherOrderCategory(d["ground_truth_category"])
        if d.get("predicted_category"):
            d["predicted_category"] = HigherOrderCategory(d["predicted_category"])
        if isinstance(d.get("sources"), list):
            d["sources"] = tuple(d["sources"])
        if isinstance(d.get("source_names"), list):
            d["source_names"] = tuple(d["source_names"])
        return cls(**d)


@dataclass
class GraphFluxBenchmarkResult:
    baseline_name: str
    candidate_recall: float
    joint_precision: float
    joint_recall: float
    joint_f1: float
    interaction_f1: float
    macro_f1: float
    exact_structural_match: float
    false_joint_rate: float
    cascade_as_joint_error_rate: float
    confounder_as_joint_error_rate: float
    temporal_contradiction_rate: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
