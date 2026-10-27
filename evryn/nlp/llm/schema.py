"""
Strict Causal Relation Schema for EVRYN Phase 2.2.

Defines the canonical candidate and verified relation schemas, validation statuses,
rejection reasons, and seamless two-way adapters to EVRYN's CausalAssertion.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from evryn.paper.types import (
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
)


class ValidationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"
    PENDING = "PENDING"


class CausalPolarity(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    AMBIGUOUS = "AMBIGUOUS"


class CausalModality(str, Enum):
    FACTUAL = "FACTUAL"
    HYPOTHETICAL = "HYPOTHETICAL"
    SPECULATIVE = "SPECULATIVE"
    CORRELATIONAL = "CORRELATIONAL"
    EXPERIMENTAL_OBSERVATION = "EXPERIMENTAL_OBSERVATION"
    BACKGROUND_CITATION = "BACKGROUND_CITATION"


class RejectionReason(str, Enum):
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    UNKNOWN_CAUSE_ENTITY = "UNKNOWN_CAUSE_ENTITY"
    UNKNOWN_EFFECT_ENTITY = "UNKNOWN_EFFECT_ENTITY"
    IDENTICAL_CAUSE_EFFECT = "IDENTICAL_CAUSE_EFFECT"
    EVIDENCE_NOT_FOUND_IN_TEXT = "EVIDENCE_NOT_FOUND_IN_TEXT"
    DIRECTION_REVERSED = "DIRECTION_REVERSED"
    SPECULATIVE_OR_UNCERTAIN = "SPECULATIVE_OR_UNCERTAIN"
    UNSUPPORTED_CAUSAL_CLAIM = "UNSUPPORTED_CAUSAL_CLAIM"
    DUPLICATE_RELATION = "DUPLICATE_RELATION"
    UNGROUNDED_INTERMEDIATE_PATH = "UNGROUNDED_INTERMEDIATE_PATH"
    METHOD_OR_CITATION_NOISE = "METHOD_OR_CITATION_NOISE"
    NEGATED_CLAIM = "NEGATED_CLAIM"


@dataclass
class CausalRelationRecord:
    """Strict relation schema conforming to Phase 2.2 requirements."""
    cause_entity: str
    effect_entity: str
    relation_type: str  # DIRECT_CAUSE, UPREGULATES, DOWNREGULATES, PREVENTS, MEDIATES, ASSOCIATED
    polarity: str       # POSITIVE, NEGATIVE, NEUTRAL, AMBIGUOUS
    modality: str       # FACTUAL, HYPOTHETICAL, SPECULATIVE, CORRELATIONAL, EXPERIMENTAL_OBSERVATION
    evidence_text: str
    document_id: str
    page_number: int = 1
    sentence_id: str = ""
    char_start: int = 0
    char_end: int = 0
    extraction_method: str = "llm_candidate"  # nlp_baseline, llm_only, hybrid_validated
    direct_or_inferred: str = "direct"        # direct, inferred
    intermediate_path: Optional[List[str]] = None
    validation_status: str = "PENDING"        # ACCEPTED, REJECTED, UNRESOLVED, PENDING
    rejection_reasons: List[str] = field(default_factory=list)
    confidence: float = 0.50
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalRelationRecord":
        return cls(**data)

    def to_causal_assertion(self, assertion_id: Optional[str] = None) -> CausalAssertion:
        """Convert to EVRYN's internal CausalAssertion for graph construction and evaluation."""
        # Map string relation_type to CausalRelationType
        try:
            rel_type = CausalRelationType(self.relation_type)
        except ValueError:
            rel_type = CausalRelationType.DIRECT_CAUSE

        # Map modality and direct_or_inferred to EvidenceStatus
        if self.direct_or_inferred == "inferred":
            ev_status = EvidenceStatus.CROSS_PAGE_INFERENCE
        elif self.modality in ("HYPOTHETICAL", "SPECULATIVE"):
            ev_status = EvidenceStatus.HYPOTHESIS_CLAIM
        else:
            ev_status = EvidenceStatus.MEASURED_FACT

        is_neg = (self.polarity == "NEGATIVE" or "NEGATED" in self.rejection_reasons)

        aid = assertion_id or f"assert_{self.document_id}_{abs(hash((self.cause_entity, self.effect_entity, self.evidence_text))) % 1000000:06d}"

        return CausalAssertion(
            assertion_id=aid,
            cause=self.cause_entity,
            cause_canonical=self.cause_entity,
            effect=self.effect_entity,
            effect_canonical=self.effect_entity,
            direction="forward",
            relation_type=rel_type,
            is_negated=is_neg,
            uncertainty_score=1.0 - self.confidence if self.modality != "FACTUAL" else 0.05,
            sentence_id=self.sentence_id,
            page_number=self.page_number,
            section_title="Extracted Knowledge",
            confidence=self.confidence,
            evidence_quote=self.evidence_text,
            char_span=(self.char_start, self.char_end),
            evidence_status=ev_status,
        )

    @classmethod
    def from_causal_assertion(
        cls,
        assertion: CausalAssertion,
        document_id: str,
        extraction_method: str = "nlp_baseline",
    ) -> "CausalRelationRecord":
        """Convert from EVRYN's CausalAssertion to strict CausalRelationRecord."""
        polarity = "NEGATIVE" if assertion.is_negated or assertion.relation_type in (
            CausalRelationType.DOWNREGULATES, CausalRelationType.PREVENTS
        ) else "POSITIVE"

        modality = "FACTUAL"
        if assertion.evidence_status == EvidenceStatus.HYPOTHESIS_CLAIM:
            modality = "HYPOTHETICAL"
        elif assertion.evidence_status == EvidenceStatus.CROSS_PAGE_INFERENCE:
            modality = "EXPERIMENTAL_OBSERVATION"

        direct_or_inferred = "inferred" if assertion.evidence_status == EvidenceStatus.CROSS_PAGE_INFERENCE else "direct"

        return cls(
            cause_entity=assertion.cause_canonical or assertion.cause,
            effect_entity=assertion.effect_canonical or assertion.effect,
            relation_type=assertion.relation_type.value,
            polarity=polarity,
            modality=modality,
            evidence_text=assertion.evidence_quote,
            document_id=document_id,
            page_number=assertion.page_number,
            sentence_id=assertion.sentence_id,
            char_start=assertion.char_span[0] if assertion.char_span else 0,
            char_end=assertion.char_span[1] if assertion.char_span else 0,
            extraction_method=extraction_method,
            direct_or_inferred=direct_or_inferred,
            intermediate_path=None,
            validation_status=ValidationStatus.ACCEPTED.value if not assertion.is_negated else ValidationStatus.REJECTED.value,
            rejection_reasons=[RejectionReason.NEGATED_CLAIM.value] if assertion.is_negated else [],
            confidence=assertion.confidence,
        )
