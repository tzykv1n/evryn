"""
System C: Hybrid LLM + Deterministic Validation Causal Extraction Backend.
Orchestrates LLM candidate proposition followed by multi-stage deterministic validation.
"""

from typing import List, Dict, Any, Optional, Tuple

from evryn.paper.types import (
    ScientificDocument,
    CausalAssertion,
)
from evryn.nlp.llm.schema import CausalRelationRecord, ValidationStatus
from evryn.nlp.llm.extractor import LLMCausalExtractor
from evryn.nlp.llm.validator import DeterministicCausalValidator
from evryn.paper.normalizer import PaperEntityNormalizer


class HybridCausalExtractor:
    """
    Hybrid LLM + Deterministic Validation Causal Extractor (System C).
    """
    def __init__(
        self,
        llm_extractor: Optional[LLMCausalExtractor] = None,
        validator: Optional[DeterministicCausalValidator] = None,
        normalizer: Optional[PaperEntityNormalizer] = None,
    ):
        self.normalizer = normalizer or PaperEntityNormalizer()
        self.llm_extractor = llm_extractor or LLMCausalExtractor()
        self.validator = validator or DeterministicCausalValidator(normalizer=self.normalizer)

        # Audit storage
        self.last_accepted: List[CausalRelationRecord] = []
        self.last_rejected: List[CausalRelationRecord] = []
        self.last_candidates: List[CausalRelationRecord] = []

    def extract_document_records(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> Tuple[List[CausalRelationRecord], List[CausalRelationRecord]]:
        """
        Extracts candidates via LLM, then passes them through deterministic validation.
        Returns (accepted_records, rejected_records).
        """
        # Step 1: Candidate Generation via LLM
        candidates = self.llm_extractor.extract_document_records(doc, known_entities=known_entities)
        for cand in candidates:
            cand.extraction_method = "hybrid_candidate"

        self.last_candidates = candidates

        # Step 2: Multi-Stage Deterministic Validation
        accepted, rejected = self.validator.validate_candidates(
            candidates=candidates,
            doc=doc,
            canonical_entities=known_entities,
        )

        for a in accepted:
            a.extraction_method = "hybrid_validated"

        self.last_accepted = accepted
        self.last_rejected = rejected

        return accepted, rejected

    def extract_assertions(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> List[CausalAssertion]:
        """
        Public extraction entrypoint conforming to PaperCausalExtractor interface.
        Returns only validated CausalAssertion objects with exact textual grounding.
        """
        accepted, _ = self.extract_document_records(doc, known_entities=known_entities)
        return [rec.to_causal_assertion() for rec in accepted]

    def get_audit_summary(self) -> Dict[str, Any]:
        """Summary of candidate proposals, acceptance rate, and rejection breakdown."""
        rejection_breakdown: Dict[str, int] = {}
        for r in self.last_rejected:
            for reason in r.rejection_reasons:
                rejection_breakdown[reason] = rejection_breakdown.get(reason, 0) + 1

        total = len(self.last_candidates)
        accepted_cnt = len(self.last_accepted)
        rejected_cnt = len(self.last_rejected)

        return {
            "total_candidates": total,
            "accepted_count": accepted_cnt,
            "rejected_count": rejected_cnt,
            "acceptance_rate": round(accepted_cnt / max(1, total), 4),
            "rejection_breakdown": rejection_breakdown,
            "llm_metrics": self.llm_extractor.get_metrics(),
        }
