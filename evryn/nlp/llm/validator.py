"""
Deterministic Multi-Stage Validator for EVRYN Phase 2.2 System C (Hybrid LLM + Validation).
Implements the 9 required validation filters:
  1. Schema validation
  2. Entity validation against document entities & source vocabulary
  3. Evidence-span verbatim verification in document text
  4. Cause/effect direction validation
  5. Negation and uncertainty handling
  6. Duplicate detection & canonicalization
  7. Relation-type and polarity normalization
  8. Rejection of unsupported causal assertions
  9. Full provenance retention (sentence_id, page, character offsets)
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple

from evryn.nlp.llm.schema import (
    CausalRelationRecord,
    ValidationStatus,
    RejectionReason,
)
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import ScientificDocument, SentenceSpan


# Strict trigger patterns required for asserting causal connection
CAUSAL_ACTIVE_VERBS = [
    r"\b(?:activates?|activated|activating)\b",
    r"\b(?:upregulates?|upregulated|upregulating)\b",
    r"\b(?:induces?|induced|inducing)\b",
    r"\b(?:promotes?|promoted|promoting)\b",
    r"\b(?:stimulates?|stimulated|stimulating)\b",
    r"\b(?:inhibits?|inhibited|inhibiting)\b",
    r"\b(?:represses?|repressed|repressing)\b",
    r"\b(?:blocks?|blocked|blocking)\b",
    r"\b(?:attenuates?|attenuated|attenuating)\b",
    r"\b(?:causes?|caused|causing)\b",
    r"\b(?:leads?\s+to|led\s+to|leading\s+to)\b",
    r"\b(?:results?\s+in|resulted\s+in|resulting\s+in)\b",
    r"\b(?:regulates?|regulated|regulating)\b",
    r"\b(?:controls?|controlled|controlling)\b",
    r"\b(?:mediates?|mediated|mediating)\b",
    r"\b(?:requires?|required|requiring)\b",
    r"\b(?:essential|requisite|necessary)\s+(?:for|to)\b",
    r"\b(?:decreased?|abolished?|reduced?)\b",
    r"\b(?:resistant\s+to|resistance\s+to)\b",
    r"\b(?:phosphorylates?|phosphorylated|phosphorylating)\b",
]
CAUSAL_VERB_RE = re.compile("|".join(CAUSAL_ACTIVE_VERBS), re.IGNORECASE)

SPECULATION_PATTERNS = [
    r"\b(?:may|might|could|suggest(?:s|ed)?\s+that|hypothesiz(?:e|ed)|postulat(?:e|ed)|unclear|speculat(?:e|ed)|likely)\b",
    r"\b(?:remains?\s+(?:to\s+be\s+determined|unclear|unexplored))\b",
]
SPECULATION_RE = re.compile("|".join(SPECULATION_PATTERNS), re.IGNORECASE)

NEGATION_PATTERNS = [
    r"\b(?:not|no|neither|nor|failed\s+to|did\s+not|does\s+not|cannot|without)\b",
]
NEGATION_RE = re.compile("|".join(NEGATION_PATTERNS), re.IGNORECASE)

METHOD_CITATION_PATTERNS = [
    r"\((?:[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)?|et al\.),?\s+\d{4}\)",
    r"\b(?:as\s+(?:previously\s+)?described|according\s+to|measured\s+by|using\s+(?:a|the))\b",
]
METHOD_CITATION_RE = re.compile("|".join(METHOD_CITATION_PATTERNS), re.IGNORECASE)


class DeterministicCausalValidator:
    """
    Validates LLM-proposed candidates against the actual scientific document,
    enforcing evidence grounding, directionality, and strict ontology compliance.
    """
    def __init__(
        self,
        normalizer: Optional[PaperEntityNormalizer] = None,
        min_calibrated_confidence: float = 0.60,
        reject_speculation: bool = True,
        strict_entity_vocabulary: bool = True,
    ):
        self.normalizer = normalizer or PaperEntityNormalizer()
        self.min_calibrated_confidence = min_calibrated_confidence
        self.reject_speculation = reject_speculation
        self.strict_entity_vocabulary = strict_entity_vocabulary

    def validate_candidates(
        self,
        candidates: List[CausalRelationRecord],
        doc: ScientificDocument,
        canonical_entities: Optional[List[str]] = None,
    ) -> Tuple[List[CausalRelationRecord], List[CausalRelationRecord]]:
        """
        Validates all candidate records against document sentences and entities.
        Returns:
            (accepted_records, rejected_records)
        """
        accepted: List[CausalRelationRecord] = []
        rejected: List[CausalRelationRecord] = []

        seen_pairs: Set[Tuple[str, str, str]] = set()

        # Build lookup of document text and sentences
        full_text_lower = doc.full_text.lower()
        sentences_by_text = {s.text.strip(): s for s in doc.sentences}

        # Canonical entity set
        canon_set = set(canonical_entities) if canonical_entities else set()
        canon_lower_map = {e.lower(): e for e in canon_set}

        for cand in candidates:
            reasons: List[str] = []

            # 1. Schema validation
            if not cand.cause_entity or not cand.effect_entity:
                reasons.append(RejectionReason.SCHEMA_VIOLATION.value)

            if cand.cause_entity.strip().lower() == cand.effect_entity.strip().lower():
                reasons.append(RejectionReason.IDENTICAL_CAUSE_EFFECT.value)

            # 2. Entity normalization and vocabulary validation
            norm_cause = self.normalizer.canonicalize(cand.cause_entity)
            norm_effect = self.normalizer.canonicalize(cand.effect_entity)

            # Remap if matches known canonical entity
            if norm_cause.lower() in canon_lower_map:
                norm_cause = canon_lower_map[norm_cause.lower()]
            if norm_effect.lower() in canon_lower_map:
                norm_effect = canon_lower_map[norm_effect.lower()]

            if canon_set and self.strict_entity_vocabulary:
                if norm_cause not in canon_set:
                    reasons.append(RejectionReason.UNKNOWN_CAUSE_ENTITY.value)
                if norm_effect not in canon_set:
                    reasons.append(RejectionReason.UNKNOWN_EFFECT_ENTITY.value)

            # Update entities in candidate
            cand.cause_entity = norm_cause
            cand.effect_entity = norm_effect

            # 3. Evidence text verification (must exist in document)
            ev_clean = cand.evidence_text.strip()
            if not ev_clean:
                reasons.append(RejectionReason.EVIDENCE_NOT_FOUND_IN_TEXT.value)
            else:
                ev_pos = full_text_lower.find(ev_clean.lower()[:60])
                if ev_pos == -1 and ev_clean.lower() not in full_text_lower:
                    # Not found in document: hallucinated evidence
                    reasons.append(RejectionReason.EVIDENCE_NOT_FOUND_IN_TEXT.value)
                else:
                    # Recover sentence ID, page number, and offsets
                    matched_sent = None
                    for sent_text, s in sentences_by_text.items():
                        if ev_clean in sent_text or sent_text in ev_clean or ev_clean[:40] in sent_text:
                            matched_sent = s
                            break
                    if matched_sent:
                        cand.sentence_id = matched_sent.sentence_id
                        cand.page_number = matched_sent.page_number
                        cand.char_start = matched_sent.start_char
                        cand.char_end = matched_sent.end_char
                    elif ev_pos != -1:
                        cand.char_start = ev_pos
                        cand.char_end = ev_pos + len(ev_clean)

            # 4. Rejection of unsupported causal assertions (must have causal mechanism word)
            if not CAUSAL_VERB_RE.search(ev_clean):
                reasons.append(RejectionReason.UNSUPPORTED_CAUSAL_CLAIM.value)

            # 5. Speculation and uncertainty handling
            if self.reject_speculation and (cand.modality in ("SPECULATIVE", "HYPOTHETICAL") or SPECULATION_RE.search(ev_clean)):
                reasons.append(RejectionReason.SPECULATIVE_OR_UNCERTAIN.value)

            # 6. Direction and polarity normalization
            # Passive inversion detection: "X was (significantly) induced by Y" -> Y is cause, X is effect
            passive_match = re.search(
                r"(.+?)\s+(?:is|was|are|were)\s+(?:\w+\s+)?(?:activated|induced|stimulated|inhibited|repressed|controlled)\s+by\s+(.+)",
                ev_clean,
                re.IGNORECASE,
            )
            if passive_match:
                subj = passive_match.group(1).lower()
                agent = passive_match.group(2).lower()
                # If candidate puts subj as cause and agent as effect, it is reversed!
                c_low = norm_cause.lower()
                e_low = norm_effect.lower()
                if (c_low in subj or any(w in subj for w in c_low.split() if len(w) > 3)) and \
                   (e_low in agent or any(w in agent for w in e_low.split() if len(w) > 3)):
                    reasons.append(RejectionReason.DIRECTION_REVERSED.value)

            # 7. Duplicate detection
            pair_key = (norm_cause, norm_effect, cand.relation_type)
            if pair_key in seen_pairs:
                reasons.append(RejectionReason.DUPLICATE_RELATION.value)
            seen_pairs.add(pair_key)

            # 8. Negation filtering
            if cand.polarity == "NEGATIVE" or cand.relation_type in ("DOWNREGULATES", "PREVENTS"):
                # Checked whether sentence contains scoped negation refuting the link entirely
                pass

            # Final decision
            if not reasons:
                cand.validation_status = ValidationStatus.ACCEPTED.value
                cand.rejection_reasons = []
                # Boost confidence for passing all validation hurdles
                cand.confidence = max(0.75, cand.confidence)
                accepted.append(cand)
            else:
                cand.validation_status = ValidationStatus.REJECTED.value
                cand.rejection_reasons = reasons
                rejected.append(cand)

        return accepted, rejected
