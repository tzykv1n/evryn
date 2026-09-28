# evryn transfer --help

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import hashlib

from ..core.types import (
    NormalizedRelation,
    NormalizedEntity,
    ScientificDomain,
    RelationType,
    Provenance,
)
from ..core.config import TransferConfig


@dataclass
class CrossDomainAnalogy:
    analogy_id: str
    source_domain: str
    target_domain: str
    source_relation_repr: str
    candidate_target_repr: str
    structural_isomorphism_score: float
    mechanism_match_score: float
    transferable_hypothesis: str
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.provenance:
            d["provenance"] = self.provenance.to_dict()
        return d


class CrossDomainTransferEngine:

    def __init__(self, config: Optional[TransferConfig] = None):
        self.config = config or TransferConfig()

    def discover_cross_domain_analogies(
        self,
        source_relations: List[NormalizedRelation],
        target_relations: List[NormalizedRelation],
        source_domain_name: str = "biomedicine",
        target_domain_name: str = "epidemiology",
    ) -> List[CrossDomainAnalogy]:
        analogies: List[CrossDomainAnalogy] = []

        src_motifs = self._extract_domain_motifs(source_relations)
        tgt_motifs = self._extract_domain_motifs(target_relations)

        for s_type, s_items in src_motifs.items():
            if s_type in tgt_motifs:
                t_items = tgt_motifs[s_type]
                for s_item in s_items[:3]:
                    for t_item in t_items[:3]:
                        iso_score = 0.85 if s_type == "higher_order_synergy" else 0.78
                        mech_score = 0.80 if s_item["family"] == t_item["family"] else 0.65

                        if (
                            iso_score >= self.config.min_structural_isomorphism
                            and mech_score >= self.config.min_mechanism_similarity
                        ):
                            a_id = f"ana_{hashlib.sha256(f'{s_item['repr']}::{t_item['repr']}'.encode('utf-8')).hexdigest()[:12]}"
                            hypo_text = (
                                f"Structural Cross-Domain Transfer: Motif '{s_type}' in {source_domain_name} "
                                f"({s_item['repr']}) maps structurally to {target_domain_name} ({t_item['repr']}). "
                                f"Predicts parallel mechanism conservation under {s_item['family']} dynamics."
                            )
                            prov = Provenance(
                                source_id=f"transfer_{source_domain_name}_{target_domain_name}",
                                citation=hypo_text,
                                confidence=(iso_score + mech_score) / 2.0,
                                extractor_model="evryn-transfer-engine-v1",
                            )
                            analogies.append(
                                CrossDomainAnalogy(
                                    analogy_id=a_id,
                                    source_domain=source_domain_name,
                                    target_domain=target_domain_name,
                                    source_relation_repr=s_item["repr"],
                                    candidate_target_repr=t_item["repr"],
                                    structural_isomorphism_score=round(iso_score, 3),
                                    mechanism_match_score=round(mech_score, 3),
                                    transferable_hypothesis=hypo_text,
                                    provenance=prov,
                                )
                            )

        analogies.sort(key=lambda x: (x.structural_isomorphism_score + x.mechanism_match_score), reverse=True)
        return analogies

    def _extract_domain_motifs(self, relations: List[NormalizedRelation]) -> Dict[str, List[Dict[str, Any]]]:
        motifs: Dict[str, List[Dict[str, Any]]] = {
            "higher_order_synergy": [],
            "linear_cascade": [],
            "converging_regulation": [],
        }

        for r in relations:
            src_str = " + ".join(s.canonical_name for s in r.source_entities)
            tgt_str = " + ".join(t.canonical_name for t in r.target_entities)
            fam = r.relation_family or "CAUSAL_PRODUCTION"

            if r.higher_order_order > 2 or r.relation_type == RelationType.HIGHER_ORDER_JOINT:
                motifs["higher_order_synergy"].append({
                    "repr": f"{{{src_str}}} -> {tgt_str}",
                    "family": fam,
                    "confidence": r.confidence,
                })
            else:
                motifs["linear_cascade"].append({
                    "repr": f"{src_str} -> {tgt_str}",
                    "family": fam,
                    "confidence": r.confidence,
                })
        return motifs
