# evryn hypothesize --help

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import hashlib

from ..core.types import (
    NormalizedEntity,
    NormalizedRelation,
    RelationType,
    Provenance,
    ScientificDomain,
)
from ..core.config import HypothesisConfig
from ..prediction.forecasting import FutureRelationForecast
from ..transfer.cross_domain import CrossDomainAnalogy
from ..temporal.evolution import TemporalRelationSequence


@dataclass
class ScientificHypothesis:
    hypothesis_id: str
    title: str
    statement: str
    hypothesis_type: str
    involved_entities: List[NormalizedEntity]
    plausibility_score: float
    reasoning_chain: List[str]
    supporting_relation_ids: List[str]
    provenance: Provenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "statement": self.statement,
            "hypothesis_type": self.hypothesis_type,
            "involved_entities": [e.to_dict() for e in self.involved_entities],
            "plausibility_score": round(float(self.plausibility_score), 4),
            "reasoning_chain": self.reasoning_chain,
            "supporting_relation_ids": self.supporting_relation_ids,
            "provenance": self.provenance.to_dict(),
        }


class HypothesisGenerator:

    def __init__(self, config: Optional[HypothesisConfig] = None):
        self.config = config or HypothesisConfig()

    def generate_hypotheses(
        self,
        relations: List[NormalizedRelation],
        forecasts: Optional[List[FutureRelationForecast]] = None,
        analogies: Optional[List[CrossDomainAnalogy]] = None,
        temporal_sequences: Optional[Dict[str, TemporalRelationSequence]] = None,
        joint_cause_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ScientificHypothesis]:
        hypotheses: List[ScientificHypothesis] = []
        forecasts = forecasts or []
        analogies = analogies or []
        temporal_sequences = temporal_sequences or {}
        joint_cause_candidates = joint_cause_candidates or []

        for jc in joint_cause_candidates[:5]:
            e1 = jc.get("e1", "factor_A")
            e2 = jc.get("e2", "factor_B")
            text = jc.get("text", "")
            h_id = f"hyp_ho_{hashlib.sha256(f'{e1}_{e2}'.encode('utf-8')).hexdigest()[:10]}"
            statement = f"Synergistic co-action {{{e1}, {e2}}} exhibits joint causal interaction beyond independent additive effects."
            reasoning = [
                f"Linguistic co-occurrence identified nominal coordination in text: '{text[:90]}...'",
                f"Entities '{e1}' and '{e2}' co-regulate downstream outcome.",
                "Partial Information Decomposition (PID) candidate test flags potential non-zero synergistic information gain.",
            ]
            prov = Provenance(
                source_id="higher_order_nlp_screening",
                citation=text[:80],
                confidence=0.74,
                extractor_model="evryn-hypothesis-generator-v1",
            )
            ent1 = NormalizedEntity(entity_id=f"ent_{e1}", canonical_name=e1)
            ent2 = NormalizedEntity(entity_id=f"ent_{e2}", canonical_name=e2)

            hypotheses.append(
                ScientificHypothesis(
                    hypothesis_id=h_id,
                    title=f"Higher-Order Synergy: {{{e1}, {e2}}}",
                    statement=statement,
                    hypothesis_type="HIGHER_ORDER_SYNERGY",
                    involved_entities=[ent1, ent2],
                    plausibility_score=0.74,
                    reasoning_chain=reasoning,
                    supporting_relation_ids=[jc.get("id", "nlp_candidate")],
                    provenance=prov,
                )
            )

        for fc in forecasts[:5]:
            h_id = f"hyp_fc_{fc.forecast_id[:10]}"
            src_str = " + ".join(fc.source_names)
            statement = f"Predicted future causal link: {src_str} -> {fc.target_name} ({fc.forecasted_family}) by {fc.horizon_year}."
            reasoning = [
                fc.rationale,
                f"Calibrated path confidence: {fc.probability:.3f} within 95% CI [{fc.confidence_interval[0]}, {fc.confidence_interval[1]}].",
                f"Forecast horizon targeted for year {fc.horizon_year}.",
            ]
            prov = Provenance(
                source_id=fc.forecast_id,
                citation=fc.rationale,
                confidence=fc.probability,
                extractor_model="evryn-hypothesis-generator-v1",
            )
            ents = [NormalizedEntity(entity_id=f"ent_{s}", canonical_name=s) for s in fc.source_names]
            ents.append(NormalizedEntity(entity_id=f"ent_{fc.target_name}", canonical_name=fc.target_name))

            hypotheses.append(
                ScientificHypothesis(
                    hypothesis_id=h_id,
                    title=f"Emerging Link Prediction: {src_str} -> {fc.target_name}",
                    statement=statement,
                    hypothesis_type="TEMPORAL_EXTRAPOLATION",
                    involved_entities=ents,
                    plausibility_score=fc.probability,
                    reasoning_chain=reasoning,
                    supporting_relation_ids=[],
                    provenance=prov,
                )
            )

        for ana in analogies[:3]:
            h_id = f"hyp_trans_{ana.analogy_id[:10]}"
            statement = f"Cross-domain structural transfer: {ana.source_domain} motif ({ana.source_relation_repr}) transfers to {ana.target_domain} ({ana.candidate_target_repr})."
            reasoning = [
                f"Structural isomorphism score: {ana.structural_isomorphism_score:.3f}",
                f"Mechanism match score: {ana.mechanism_match_score:.3f}",
                ana.transferable_hypothesis,
            ]
            prov = Provenance(
                source_id=ana.analogy_id,
                citation=ana.transferable_hypothesis,
                confidence=(ana.structural_isomorphism_score + ana.mechanism_match_score) / 2.0,
                extractor_model="evryn-hypothesis-generator-v1",
            )
            hypotheses.append(
                ScientificHypothesis(
                    hypothesis_id=h_id,
                    title=f"Cross-Domain Analogy: {ana.source_domain} -> {ana.target_domain}",
                    statement=statement,
                    hypothesis_type="CROSS_DOMAIN_TRANSFER",
                    involved_entities=[],
                    plausibility_score=(ana.structural_isomorphism_score + ana.mechanism_match_score) / 2.0,
                    reasoning_chain=reasoning,
                    supporting_relation_ids=[],
                    provenance=prov,
                )
            )

        for key, seq in temporal_sequences.items():
            if seq.is_contradicted:
                h_id = f"hyp_contra_{seq.sequence_id}"
                statement = f"Hypothesis of context-dependent bifurcation for relation '{key}' exhibiting conflicting causal polarities."
                reasoning = [
                    f"Temporal sequence for '{key}' exhibits simultaneous positive and negative/confounded evidence reports.",
                    "Suggests presence of an unmeasured latent modifier or cell-type specific regulatory switch.",
                    f"First observed in {seq.emergence_year} with {sum(seq.evidence_counts)} total observations.",
                ]
                prov = Provenance(
                    source_id=f"contradiction_{seq.sequence_id}",
                    citation=statement,
                    confidence=0.82,
                    extractor_model="evryn-hypothesis-generator-v1",
                )
                hypotheses.append(
                    ScientificHypothesis(
                        hypothesis_id=h_id,
                        title=f"Contradiction Resolution: '{key}'",
                        statement=statement,
                        hypothesis_type="CONTRADICTION_RESOLUTION",
                        involved_entities=[
                            NormalizedEntity(entity_id=f"ent_{seq.source_name}", canonical_name=seq.source_name),
                            NormalizedEntity(entity_id=f"ent_{seq.target_name}", canonical_name=seq.target_name),
                        ],
                        plausibility_score=0.82,
                        reasoning_chain=reasoning,
                        supporting_relation_ids=[],
                        provenance=prov,
                    )
                )

        hypotheses.sort(key=lambda x: x.plausibility_score, reverse=True)
        return hypotheses[: self.config.max_hypotheses]
