# python cli.py --help

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional


class CausalRelationType(IntEnum):
    NO_RELATION = 0
    FORWARD = 1
    BACKWARD = 2

    @classmethod
    def from_str(cls, label: str) -> "CausalRelationType":
        clean = label.strip()
        if "Cause-Effect(e1,e2)" in clean or clean == "FORWARD":
            return cls.FORWARD
        elif "Cause-Effect(e2,e1)" in clean or clean == "BACKWARD":
            return cls.BACKWARD
        else:
            return cls.NO_RELATION

    def to_symbol(self) -> str:
        if self == CausalRelationType.FORWARD:
            return "e1 -> e2"
        elif self == CausalRelationType.BACKWARD:
            return "e1 <- e2"
        else:
            return "e1 ⟂ e2"


@dataclass
class RelationExample:
    example_id: str
    sentence: str
    entity1_text: str
    entity2_text: str
    entity1_span: Tuple[int, int]
    entity2_span: Tuple[int, int]
    relation_type: CausalRelationType
    raw_label: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_causal(self) -> bool:
        return self.relation_type != CausalRelationType.NO_RELATION

    @property
    def middle_context(self) -> str:
        s1, e1 = self.entity1_span
        s2, e2 = self.entity2_span
        if e1 <= s2:
            return self.sentence[e1:s2].strip()
        elif e2 <= s1:
            return self.sentence[e2:s1].strip()
        return ""

    @property
    def marked_sentence(self) -> str:
        s1, e1 = self.entity1_span
        s2, e2 = self.entity2_span
        if s1 < s2:
            part1 = self.sentence[:s1]
            e1_txt = self.sentence[s1:e1]
            mid = self.sentence[e1:s2]
            e2_txt = self.sentence[s2:e2]
            rest = self.sentence[e2:]
            return f"{part1}<e1>{e1_txt}</e1>{mid}<e2>{e2_txt}</e2>{rest}"
        else:
            part1 = self.sentence[:s2]
            e2_txt = self.sentence[s2:e2]
            mid = self.sentence[e2:s1]
            e1_txt = self.sentence[s1:e1]
            rest = self.sentence[e1:]
            return f"{part1}<e2>{e2_txt}</e2>{mid}<e1>{e1_txt}</e1>{rest}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id,
            "sentence": self.sentence,
            "entity1_text": self.entity1_text,
            "entity2_text": self.entity2_text,
            "entity1_span": self.entity1_span,
            "entity2_span": self.entity2_span,
            "relation_type": int(self.relation_type),
            "relation_name": self.relation_type.name,
            "raw_label": self.raw_label,
            "metadata": self.metadata,
        }
