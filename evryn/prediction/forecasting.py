# evryn predict --help

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import hashlib

from ..core.types import NormalizedEntity, NormalizedRelation, RelationType, Provenance
from ..core.config import PredictionConfig
from ..temporal.evolution import TemporalRelationSequence


@dataclass
class FutureRelationForecast:
    forecast_id: str
    source_names: List[str]
    target_name: str
    forecasted_family: str
    horizon_year: int
    probability: float
    confidence_interval: Tuple[float, float]
    rationale: str
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.provenance:
            d["provenance"] = self.provenance.to_dict()
        return d


class FutureRelationForecaster:

    def __init__(self, config: Optional[PredictionConfig] = None):
        self.config = config or PredictionConfig()

    def forecast_relations(
        self,
        relations: List[NormalizedRelation],
        temporal_sequences: Dict[str, TemporalRelationSequence],
        current_year: int = 2026,
    ) -> List[FutureRelationForecast]:
        forecasts: List[FutureRelationForecast] = []
        forward_graph: Dict[str, Dict[str, float]] = {}
        pair_to_rel: Dict[Tuple[str, str], NormalizedRelation] = {}

        for r in relations:
            if r.relation_type in (RelationType.FORWARD, RelationType.HIGHER_ORDER_JOINT):
                for s in r.source_entities:
                    for t in r.target_entities:
                        src_name = s.canonical_name
                        tgt_name = t.canonical_name
                        forward_graph.setdefault(src_name, {})[tgt_name] = r.confidence
                        pair_to_rel[(src_name, tgt_name)] = r

        nodes = list(forward_graph.keys())
        for a in nodes:
            for b, conf_ab in forward_graph[a].items():
                if b in forward_graph:
                    for c, conf_bc in forward_graph[b].items():
                        if a != c and c not in forward_graph.get(a, {}):
                            trans_score = conf_ab * conf_bc
                            seq_ab = temporal_sequences.get(f"{a}->{b}")
                            seq_bc = temporal_sequences.get(f"{b}->{c}")

                            v_ab = seq_ab.velocity if seq_ab else 0.0
                            v_bc = seq_bc.velocity if seq_bc else 0.0
                            avg_velocity = (v_ab + v_bc) / 2.0

                            prob = min(0.98, max(0.20, float(trans_score * 0.8 + avg_velocity * 0.2)))
                            if prob >= self.config.min_path_confidence:
                                f_id = f"fc_{hashlib.sha256(f'{a}->{c}_trans'.encode('utf-8')).hexdigest()[:12]}"
                                margin = float(0.08 * (1.0 - prob))
                                ci = (round(max(0.0, prob - margin), 3), round(min(1.0, prob + margin), 3))
                                rationale = (
                                    f"Transitive discovery via bridge entity '{b}': "
                                    f"'{a}' -> '{b}' (conf {conf_ab:.2f}) and '{b}' -> '{c}' (conf {conf_bc:.2f}) "
                                    f"with mean evidence velocity {avg_velocity:+.3f}/yr"
                                )
                                prov = Provenance(
                                    source_id=f"forecast_{a}_{c}",
                                    citation=rationale,
                                    confidence=prob,
                                    extractor_model="evryn-forecaster-v1",
                                )
                                forecasts.append(
                                    FutureRelationForecast(
                                        forecast_id=f_id,
                                        source_names=[a],
                                        target_name=c,
                                        forecasted_family="CAUSAL_PRODUCTION",
                                        horizon_year=current_year + self.config.transitivity_weight > 0.5 and 2028 or 2029,
                                        probability=round(prob, 4),
                                        confidence_interval=ci,
                                        rationale=rationale,
                                        provenance=prov,
                                    )
                                )

        for tgt, parents in self._find_converging_parents(forward_graph).items():
            if len(parents) >= 2:
                for i in range(len(parents)):
                    for j in range(i + 1, len(parents)):
                        p1, c1 = parents[i]
                        p2, c2 = parents[j]
                        joint_prob = float(min(0.95, (c1 + c2) / 2.0 * 0.9))
                        if joint_prob >= self.config.min_path_confidence:
                            f_id = f"fc_{hashlib.sha256(f'{{{p1},{p2}}}->{tgt}'.encode('utf-8')).hexdigest()[:12]}"
                            rationale = (
                                f"Higher-Order Synergy Hypothesis: '{p1}' (conf {c1:.2f}) and '{p2}' (conf {c2:.2f}) "
                                f"both independently regulate '{tgt}'. High probability of joint synergy {{{p1}, {p2}}} -> {tgt}."
                            )
                            prov = Provenance(
                                source_id=f"synergy_forecast_{p1}_{p2}_{tgt}",
                                citation=rationale,
                                confidence=joint_prob,
                                extractor_model="evryn-forecaster-v1",
                            )
                            forecasts.append(
                                FutureRelationForecast(
                                    forecast_id=f_id,
                                    source_names=[p1, p2],
                                    target_name=tgt,
                                    forecasted_family="SYNERGISTIC_CO_ACTION",
                                    horizon_year=current_year + 3,
                                    probability=round(joint_prob, 4),
                                    confidence_interval=(round(joint_prob - 0.05, 3), round(joint_prob + 0.05, 3)),
                                    rationale=rationale,
                                    provenance=prov,
                                )
                            )

        forecasts.sort(key=lambda x: x.probability, reverse=True)
        return forecasts[: self.config.top_k_forecasts]

    def _find_converging_parents(self, graph: Dict[str, Dict[str, float]]) -> Dict[str, List[Tuple[str, float]]]:
        incoming: Dict[str, List[Tuple[str, float]]] = {}
        for src, tgts in graph.items():
            for tgt, conf in tgts.items():
                incoming.setdefault(tgt, []).append((src, conf))
        return incoming
