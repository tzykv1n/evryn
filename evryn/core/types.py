# evryn --help

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import time
import json


class ScientificDomain(str, Enum):
    BIOMEDICINE = "biomedicine"
    EPIDEMIOLOGY = "epidemiology"
    CLIMATE = "climate"
    NEUROSCIENCE = "neuroscience"
    PHYSICS = "physics"
    GENERAL_SCIENCE = "general_science"


class RelationType(str, Enum):
    NO_RELATION = "NO_RELATION"
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    CONFOUNDED = "CONFOUNDED"
    INDEPENDENT = "INDEPENDENT"
    BIDIRECTIONAL = "BIDIRECTIONAL"
    HIGHER_ORDER_JOINT = "HIGHER_ORDER_JOINT"
    INDIRECT_CHAIN = "INDIRECT_CHAIN"
    COLLIDER = "COLLIDER"
    FORK = "FORK"


class EvidenceModality(str, Enum):
    TEXTUAL_LITERATURE = "textual_literature"
    EXPERIMENTAL_OBSERVATIONAL = "experimental_observational"
    INTERVENTIONAL = "interventional"
    SIMULATED = "simulated"


@dataclass
class Provenance:
    source_id: str
    citation: str = ""
    timestamp: str = ""
    extractor_model: str = "evryn-engine-v1"
    extractor_version: str = "1.0.0"
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Provenance":
        return cls(**data)


@dataclass
class NormalizedEntity:
    entity_id: str
    canonical_name: str
    surface_forms: List[str] = field(default_factory=list)
    entity_type: str = "concept"
    domain: ScientificDomain = ScientificDomain.GENERAL_SCIENCE
    ontology_ids: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["domain"] = self.domain.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedEntity":
        d = dict(data)
        if "domain" in d and isinstance(d["domain"], str):
            d["domain"] = ScientificDomain(d["domain"])
        return cls(**d)


@dataclass
class EvidenceSpan:
    text: str
    start_char: int
    end_char: int
    sentence: str
    document_id: str = ""
    section: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceSpan":
        return cls(**data)


@dataclass
class NormalizedRelation:
    relation_id: str
    source_entities: List[NormalizedEntity]
    target_entities: List[NormalizedEntity]
    relation_type: RelationType
    relation_family: Optional[str] = None
    evidence_spans: List[EvidenceSpan] = field(default_factory=list)
    confidence: float = 1.0
    provenance: Optional[Provenance] = None
    temporal_year: Optional[int] = None
    domain: ScientificDomain = ScientificDomain.GENERAL_SCIENCE
    higher_order_order: int = 2
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_entities": [e.to_dict() for e in self.source_entities],
            "target_entities": [e.to_dict() for e in self.target_entities],
            "relation_type": self.relation_type.value,
            "relation_family": self.relation_family,
            "evidence_spans": [s.to_dict() for s in self.evidence_spans],
            "confidence": float(self.confidence),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "temporal_year": self.temporal_year,
            "domain": self.domain.value,
            "higher_order_order": self.higher_order_order,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedRelation":
        sources = [NormalizedEntity.from_dict(e) for e in data.get("source_entities", [])]
        targets = [NormalizedEntity.from_dict(e) for e in data.get("target_entities", [])]
        spans = [EvidenceSpan.from_dict(s) for s in data.get("evidence_spans", [])]
        prov = Provenance.from_dict(data["provenance"]) if data.get("provenance") else None
        return cls(
            relation_id=data["relation_id"],
            source_entities=sources,
            target_entities=targets,
            relation_type=RelationType(data["relation_type"]),
            relation_family=data.get("relation_family"),
            evidence_spans=spans,
            confidence=float(data.get("confidence", 1.0)),
            provenance=prov,
            temporal_year=data.get("temporal_year"),
            domain=ScientificDomain(data.get("domain", ScientificDomain.GENERAL_SCIENCE.value)),
            higher_order_order=int(data.get("higher_order_order", 2)),
            properties=data.get("properties", {}),
        )


@dataclass
class HigherOrderRelation:
    relation_id: str
    sources: List[NormalizedEntity]
    targets: List[NormalizedEntity]
    interaction_type: str
    synergy_score: float
    confidence: float
    order: int
    provenance: Optional[Provenance] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "sources": [e.to_dict() for e in self.sources],
            "targets": [e.to_dict() for e in self.targets],
            "interaction_type": self.interaction_type,
            "synergy_score": float(self.synergy_score),
            "confidence": float(self.confidence),
            "order": self.order,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HigherOrderRelation":
        sources = [NormalizedEntity.from_dict(e) for e in data.get("sources", [])]
        targets = [NormalizedEntity.from_dict(e) for e in data.get("targets", [])]
        prov = Provenance.from_dict(data["provenance"]) if data.get("provenance") else None
        return cls(
            relation_id=data["relation_id"],
            sources=sources,
            targets=targets,
            interaction_type=data.get("interaction_type", "joint_synergy"),
            synergy_score=float(data.get("synergy_score", 0.0)),
            confidence=float(data.get("confidence", 1.0)),
            order=int(data.get("order", len(sources))),
            provenance=prov,
            properties=data.get("properties", {}),
        )
