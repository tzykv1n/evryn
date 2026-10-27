"""
EVRYN Pipeline Tracer & Diagnostic Provenance Instrumentation (Phase 3).
Provides stage-by-stage tracing for causal extraction, candidate filtering,
gold-miss attribution, and false-positive root-cause tracing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set


class RejectionStage(str, Enum):
    MENTION_NER = "MENTION_NER"
    ENTITY_NORMALIZATION = "ENTITY_NORMALIZATION"
    SYNTACTIC_PATTERN = "SYNTACTIC_PATTERN"
    DISCOURSE_FILTER = "DISCOURSE_FILTER"
    CITATION_PREAMBLE = "CITATION_PREAMBLE"
    SPECULATION_FILTER = "SPECULATION_FILTER"
    NEGATION_FILTER = "NEGATION_FILTER"
    DEDUPLICATION = "DEDUPLICATION"
    CROSS_PAGE_SEARCH = "CROSS_PAGE_SEARCH"
    TRANSITIVITY_INVARIANT = "TRANSITIVITY_INVARIANT"
    CONFIDENCE_GATE = "CONFIDENCE_GATE"


@dataclass
class CandidateRejection:
    cause: str
    effect: str
    stage: RejectionStage
    reason_code: str
    rule_or_model: str
    evidence_text: str
    sentence_id: str
    page_number: int
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "stage": self.stage.value if isinstance(self.stage, Enum) else str(self.stage),
            "reason_code": self.reason_code,
            "rule_or_model": self.rule_or_model,
            "evidence_text": self.evidence_text,
            "sentence_id": self.sentence_id,
            "page_number": self.page_number,
            "details": self.details,
        }


class PipelineExecutionTracer:
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.stage_counts: Dict[str, int] = {
            "sentences_segmented": 0,
            "entities_detected": 0,
            "entities_normalized": 0,
            "syntax_candidates": 0,
            "preambles_rejected": 0,
            "hypotheses_rejected": 0,
            "negations_filtered": 0,
            "direct_assertions_emitted": 0,
            "cross_paths_evaluated": 0,
            "transitive_invariants_blocked": 0,
            "cross_links_emitted": 0,
        }
        self.rejections: List[CandidateRejection] = []
        self.recognized_entities: Set[str] = set()
        self.sentence_map: Dict[str, str] = {}

    def log_sentence(self, sent_id: str, text: str):
        self.sentence_map[sent_id] = text
        self.stage_counts["sentences_segmented"] += 1

    def log_entity(self, entity_name: str):
        self.recognized_entities.add(entity_name.lower())
        self.stage_counts["entities_detected"] += 1

    def record_rejection(
        self,
        cause: str,
        effect: str,
        stage: RejectionStage,
        reason_code: str,
        rule_or_model: str,
        evidence_text: str,
        sentence_id: str = "",
        page_number: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ):
        rejection = CandidateRejection(
            cause=cause,
            effect=effect,
            stage=stage,
            reason_code=reason_code,
            rule_or_model=rule_or_model,
            evidence_text=evidence_text,
            sentence_id=sentence_id,
            page_number=page_number,
            details=details or {},
        )
        self.rejections.append(rejection)
        if stage == RejectionStage.CITATION_PREAMBLE:
            self.stage_counts["preambles_rejected"] += 1
        elif stage == RejectionStage.SPECULATION_FILTER:
            self.stage_counts["hypotheses_rejected"] += 1
        elif stage == RejectionStage.NEGATION_FILTER:
            self.stage_counts["negations_filtered"] += 1
        elif stage == RejectionStage.TRANSITIVITY_INVARIANT:
            self.stage_counts["transitive_invariants_blocked"] += 1

    def generate_gold_miss_report(
        self,
        gold_edges: List[Tuple[str, str]],
        extracted_edges: List[Tuple[str, str]],
        paper_text: str,
    ) -> List[Dict[str, Any]]:
        """Identifies the exact loss stage for every missing gold edge."""
        miss_report = []

        norm = lambda s: s.lower().replace("_", " ").strip()

        for g_cause, g_effect in gold_edges:
            gc_norm = norm(g_cause)
            ge_norm = norm(g_effect)

            is_recovered = any(
                (gc_norm in norm(ec) or norm(ec) in gc_norm) and (ge_norm in norm(ee) or norm(ee) in ge_norm)
                for ec, ee in extracted_edges
            )

            if is_recovered:
                continue

            # Trace why missing:
            # 1. Did cause and effect exist in document text?
            cause_in_text = gc_norm in paper_text.lower()
            effect_in_text = ge_norm in paper_text.lower()

            if not cause_in_text and not effect_in_text:
                loss_stage = RejectionStage.MENTION_NER
                reason = f"Neither entity '{g_cause}' nor '{g_effect}' was mentioned in document text."
            elif not cause_in_text:
                loss_stage = RejectionStage.MENTION_NER
                reason = f"Cause entity '{g_cause}' was not mentioned in document text."
            elif not effect_in_text:
                loss_stage = RejectionStage.MENTION_NER
                reason = f"Effect entity '{g_effect}' was not mentioned in document text."
            else:
                # 2. Check if filtered by an explicit rule
                matching_rej = next(
                    (
                        r
                        for r in self.rejections
                        if (gc_norm in norm(r.cause) or norm(r.cause) in gc_norm)
                        and (ge_norm in norm(r.effect) or norm(r.effect) in ge_norm)
                    ),
                    None,
                )

                if matching_rej:
                    loss_stage = matching_rej.stage
                    reason = f"Rejected at {matching_rej.stage.value} by {matching_rej.rule_or_model}: {matching_rej.reason_code}"
                else:
                    loss_stage = RejectionStage.SYNTACTIC_PATTERN
                    reason = "Entities co-occur but syntax did not match causal dependency pattern or crossed distant sentences without cross-page path."

            miss_report.append({
                "gold_cause": g_cause,
                "gold_effect": g_effect,
                "loss_stage": loss_stage.value if isinstance(loss_stage, Enum) else str(loss_stage),
                "diagnostic_explanation": reason,
                "cause_in_text": cause_in_text,
                "effect_in_text": effect_in_text,
            })

        return miss_report

    def generate_false_positive_report(
        self,
        extracted_predictions: List[Dict[str, Any]],
        gold_edges: List[Tuple[str, str]],
    ) -> List[Dict[str, Any]]:
        """Traces each unsupported prediction back to sentence and rule provenance."""
        fp_report = []
        norm = lambda s: s.lower().replace("_", " ").strip()

        for pred in extracted_predictions:
            p_cause = pred.get("cause_name", pred.get("cause", ""))
            p_effect = pred.get("effect_name", pred.get("effect", ""))
            pc_norm = norm(p_cause)
            pe_norm = norm(p_effect)

            is_gold = any(
                (pc_norm in norm(gc) or norm(gc) in pc_norm) and (pe_norm in norm(ge) or norm(ge) in pe_norm)
                for gc, ge in gold_edges
            )

            if is_gold:
                continue

            quote = pred.get("evidence_quote") or pred.get("sentence_text") or ""
            is_cross = bool(pred.get("is_transitive", False))

            # Classify FP origin
            if is_cross:
                root_cause = "Cross-page transitive inference across non-adjacent sections without direct assertion."
            elif any(w in quote.lower() for w in ["hypothesized", "postulated", "speculated", "whether"]):
                root_cause = "Speculative/hypothesis intent clause extracted as empirical assertion."
            elif any(w in quote.lower() for w in ["because", "since"]) and "(" in quote:
                root_cause = "Literature background premise clause."
            else:
                root_cause = "Intra-sentence syntactic dependency over-generalization."

            fp_report.append({
                "predicted_cause": p_cause,
                "predicted_effect": p_effect,
                "relation_type": pred.get("relation_type", "UPREGULATES"),
                "is_cross_page": is_cross,
                "evidence_quote": quote,
                "page_number": pred.get("page_number", 1),
                "rule_source": pred.get("rule_source", "Syntactic Pattern"),
                "root_cause_diagnosis": root_cause,
            })

        return fp_report

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "stage_counts": self.stage_counts,
            "rejections_count": len(self.rejections),
            "rejections": [r.to_dict() for r in self.rejections],
        }
