# evryn paper --help
# pytest tests/test_paper_pipeline.py

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple


class ScientificSectionType(str, Enum):
    TITLE = "TITLE"
    ABSTRACT = "ABSTRACT"
    INTRODUCTION = "INTRODUCTION"
    BACKGROUND = "BACKGROUND"
    METHODS = "METHODS"
    RESULTS = "RESULTS"
    DISCUSSION = "DISCUSSION"
    CONCLUSION = "CONCLUSION"
    REFERENCES = "REFERENCES"
    OTHER = "OTHER"


class CausalRelationType(str, Enum):
    DIRECT_CAUSE = "DIRECT_CAUSE"
    UPREGULATES = "UPREGULATES"
    DOWNREGULATES = "DOWNREGULATES"
    PREVENTS = "PREVENTS"
    MEDIATES = "MEDIATES"
    ASSOCIATED = "ASSOCIATED"
    CONFOUNDED = "CONFOUNDED"


class EvidenceStatus(str, Enum):
    MEASURED_FACT = "MEASURED_FACT"
    CROSS_PAGE_INFERENCE = "CROSS_PAGE_INFERENCE"
    HYPOTHESIS_CLAIM = "HYPOTHESIS_CLAIM"
    REFUTED_NEGATION = "REFUTED_NEGATION"


@dataclass
class PageBoundary:
    page_number: int
    start_char: int
    end_char: int
    char_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageBoundary":
        return cls(**data)


@dataclass
class SectionSpan:
    section_title: str
    section_type: ScientificSectionType
    page_number: int
    start_char: int
    end_char: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["section_type"] = self.section_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionSpan":
        d = dict(data)
        d["section_type"] = ScientificSectionType(d["section_type"])
        return cls(**d)


@dataclass
class ParagraphSpan:
    paragraph_id: str
    page_number: int
    section_title: str
    start_char: int
    end_char: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParagraphSpan":
        return cls(**data)


@dataclass
class SentenceSpan:
    sentence_id: str
    page_number: int
    section_title: str
    paragraph_id: str
    start_char: int
    end_char: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SentenceSpan":
        return cls(**data)


@dataclass
class PaperMetadata:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    year: Optional[int] = None
    journal: str = ""
    page_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperMetadata":
        return cls(**data)


@dataclass
class ScientificDocument:
    doc_id: str
    file_path: str
    metadata: PaperMetadata
    full_text: str
    pages: List[PageBoundary] = field(default_factory=list)
    sections: List[SectionSpan] = field(default_factory=list)
    paragraphs: List[ParagraphSpan] = field(default_factory=list)
    sentences: List[SentenceSpan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "file_path": self.file_path,
            "metadata": self.metadata.to_dict(),
            "full_text": self.full_text,
            "pages": [p.to_dict() for p in self.pages],
            "sections": [s.to_dict() for s in self.sections],
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "sentences": [s.to_dict() for s in self.sentences],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScientificDocument":
        return cls(
            doc_id=data["doc_id"],
            file_path=data.get("file_path", ""),
            metadata=PaperMetadata.from_dict(data.get("metadata", {})),
            full_text=data.get("full_text", ""),
            pages=[PageBoundary.from_dict(p) for p in data.get("pages", [])],
            sections=[SectionSpan.from_dict(s) for s in data.get("sections", [])],
            paragraphs=[ParagraphSpan.from_dict(p) for p in data.get("paragraphs", [])],
            sentences=[SentenceSpan.from_dict(s) for s in data.get("sentences", [])],
        )


@dataclass
class CausalAssertion:
    assertion_id: str
    cause: str
    cause_canonical: str
    effect: str
    effect_canonical: str
    direction: str
    relation_type: CausalRelationType
    is_negated: bool
    uncertainty_score: float
    sentence_id: str
    page_number: int
    section_title: str
    confidence: float
    evidence_quote: str
    char_span: Tuple[int, int]
    evidence_status: EvidenceStatus = EvidenceStatus.MEASURED_FACT

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["relation_type"] = self.relation_type.value
        d["evidence_status"] = self.evidence_status.value
        d["char_span"] = list(self.char_span)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalAssertion":
        d = dict(data)
        d["relation_type"] = CausalRelationType(d["relation_type"])
        d["evidence_status"] = EvidenceStatus(d["evidence_status"])
        if isinstance(d.get("char_span"), list):
            d["char_span"] = tuple(d["char_span"])
        return cls(**d)


@dataclass
class CrossPageLink:
    link_id: str
    cause_assertion_id: str
    effect_assertion_id: str
    source_entity: str
    intermediate_entity: str
    target_entity: str
    cause_page: int
    effect_page: int
    distance_pages: int
    cause_section: str
    effect_section: str
    linking_mechanism: str
    confidence: float
    provenance_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrossPageLink":
        return cls(**data)


@dataclass
class PaperCausalGraph:
    doc_id: str
    title: str
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    cross_page_links: List[CrossPageLink] = field(default_factory=list)
    provenance_map: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "nodes": self.nodes,
            "edges": self.edges,
            "cross_page_links": [l.to_dict() for l in self.cross_page_links],
            "provenance_map": self.provenance_map,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperCausalGraph":
        return cls(
            doc_id=data["doc_id"],
            title=data.get("title", ""),
            nodes=data.get("nodes", []),
            edges=data.get("edges", []),
            cross_page_links=[CrossPageLink.from_dict(l) for l in data.get("cross_page_links", [])],
            provenance_map=data.get("provenance_map", {}),
        )
