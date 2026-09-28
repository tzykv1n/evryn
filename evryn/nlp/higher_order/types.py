# evryn higher-order
# evryn -s higher-order

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple


class HigherOrderCategory(str, Enum):
    PAIRWISE_DECOMPOSABLE = "PAIRWISE_DECOMPOSABLE"
    JOINT_CAUSE = "JOINT_CAUSE"
    HIGHER_ORDER_INTERACTION = "HIGHER_ORDER_INTERACTION"
    CAUSAL_CASCADE = "CAUSAL_CASCADE"
    CONFOUNDED = "CONFOUNDED"
    LINGUISTIC_COORDINATION = "LINGUISTIC_COORDINATION"
    TEMPORAL_RELATION = "TEMPORAL_RELATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass
class HigherOrderCandidate:
    candidate_id: str
    sentence: str
    entity1_text: str
    entity2_text: str
    entity1_span: Tuple[int, int]
    entity2_span: Tuple[int, int]
    candidate_participants: Tuple[str, ...]
    candidate_target: str
    relation_trigger: str
    relation_direction: str
    pairwise_pred: str
    pairwise_conf: float
    temporal_cues: List[str]
    coordination_cues: List[str]
    generation_rule: str
    category: HigherOrderCategory
    validation_status: str = "VALIDATED"
    source_dataset: str = "SemEval-2010_Task8"
    source_split: str = "test"
    document_id: str = "semeval2010_held_out"
    higher_order_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HigherOrderCandidate":
        d = dict(data)
        d["category"] = HigherOrderCategory(d["category"])
        if isinstance(d.get("candidate_participants"), list):
            d["candidate_participants"] = tuple(d["candidate_participants"])
        if isinstance(d.get("entity1_span"), list):
            d["entity1_span"] = tuple(d["entity1_span"])
        if isinstance(d.get("entity2_span"), list):
            d["entity2_span"] = tuple(d["entity2_span"])
        return cls(**d)


@dataclass
class HigherOrderBenchmarkResult:
    baseline_name: str
    pairwise_decomposition_f1: float
    joint_cause_precision: float
    joint_cause_recall: float
    joint_cause_f1: float
    higher_order_interaction_f1: float
    macro_f1: float
    false_joint_cause_rate: float
    exact_structural_match: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
