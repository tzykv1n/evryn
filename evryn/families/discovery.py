# evryn discover --help

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
import numpy as np

from ..core.types import NormalizedRelation, RelationType
from ..core.config import FamilyDiscoveryConfig


@dataclass
class RelationFamily:
    family_id: str
    canonical_name: str
    description: str
    polarity: int
    keywords: List[str]
    prototype_verbs: List[str]
    member_relation_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RelationFamilyRegistry:

    @staticmethod
    def get_standard_families() -> Dict[str, RelationFamily]:
        return {
            "POSITIVE_REGULATION": RelationFamily(
                family_id="fam_pos_reg",
                canonical_name="Positive Regulation",
                description="Increases, activates, enhances, or upregulates the target process or quantity",
                polarity=1,
                keywords=["increases", "promotes", "enhances", "upregulates", "activates", "stimulates", "amplifies", "accelerates", "elevates"],
                prototype_verbs=["increase", "promote", "enhance", "activate"],
            ),
            "NEGATIVE_REGULATION": RelationFamily(
                family_id="fam_neg_reg",
                canonical_name="Negative Regulation",
                description="Decreases, suppresses, inhibits, or downregulates the target process or quantity",
                polarity=-1,
                keywords=["inhibits", "decreases", "suppresses", "downregulates", "blocks", "attenuates", "dampens", "prevents", "reduces"],
                prototype_verbs=["inhibit", "decrease", "suppress", "block"],
            ),
            "CAUSAL_PRODUCTION": RelationFamily(
                family_id="fam_causal_prod",
                canonical_name="Causal Production / Genesis",
                description="Directly creates, generates, synthesizes, produces, or triggers the target entity",
                polarity=1,
                keywords=["causes", "caused", "produces", "generates", "yields", "synthesizes", "creates", "triggers", "induces", "results in", "leads to"],
                prototype_verbs=["cause", "produce", "generate", "trigger"],
            ),
            "PHYSICAL_INTERACTION": RelationFamily(
                family_id="fam_phys_int",
                canonical_name="Physical Binding / Complex Formation",
                description="Direct physical association, binding, or complex formation without net production",
                polarity=0,
                keywords=["binds", "associates with", "forms complex with", "complexes with", "interacts with", "attaches to"],
                prototype_verbs=["bind", "associate", "interact"],
            ),
            "SYNERGISTIC_CO_ACTION": RelationFamily(
                family_id="fam_synergy",
                canonical_name="Synergistic Co-Action / Joint Causation",
                description="Multiple sources act conjunctively or nonlinearly to generate an effect",
                polarity=1,
                keywords=["synergizes with", "cooperates with", "co-regulates", "jointly induces", "interacts with", "combined effect"],
                prototype_verbs=["cooperate", "synergize", "co-regulate"],
            ),
            "METABOLIC_CONVERSION": RelationFamily(
                family_id="fam_metab_conv",
                canonical_name="Metabolic / Chemical Transformation",
                description="Direct chemical conversion or catalytic breakdown from substrate to product",
                polarity=0,
                keywords=["converts into", "metabolizes to", "cleaves into", "transforms into", "hydrolyzes to", "degrades into"],
                prototype_verbs=["convert", "metabolize", "cleave", "transform"],
            ),
        }


class RelationFamilyDiscoverer:

    def __init__(self, config: Optional[FamilyDiscoveryConfig] = None):
        self.config = config or FamilyDiscoveryConfig()
        self.registry = RelationFamilyRegistry.get_standard_families()

    def assign_family(self, relation: NormalizedRelation) -> str:
        if relation.relation_type == RelationType.HIGHER_ORDER_JOINT:
            family_name = "SYNERGISTIC_CO_ACTION"
            relation.relation_family = family_name
            self.registry[family_name].member_relation_ids.append(relation.relation_id)
            return family_name

        combined_text = " ".join([span.sentence.lower() for span in relation.evidence_spans])
        if not combined_text and "evidence_text" in relation.properties:
            combined_text = relation.properties["evidence_text"].lower()

        best_family = "CAUSAL_PRODUCTION"
        best_score = 0.0

        for f_name, fam in self.registry.items():
            score = sum(1.0 for kw in fam.keywords if kw in combined_text)
            if score > best_score:
                best_score = score
                best_family = f_name

        relation.relation_family = best_family
        self.registry[best_family].member_relation_ids.append(relation.relation_id)
        return best_family

    def discover_families(self, relations: List[NormalizedRelation]) -> Dict[str, Dict[str, Any]]:
        counts: Dict[str, int] = {k: 0 for k in self.registry}
        members: Dict[str, List[NormalizedRelation]] = {k: [] for k in self.registry}

        for rel in relations:
            fam_name = self.assign_family(rel)
            counts[fam_name] = counts.get(fam_name, 0) + 1
            members[fam_name].append(rel)

        results = {}
        for f_name, fam in self.registry.items():
            results[f_name] = {
                "family_id": fam.family_id,
                "canonical_name": fam.canonical_name,
                "description": fam.description,
                "polarity": fam.polarity,
                "count": counts[f_name],
                "sample_relations": [r.to_dict() for r in members[f_name][:3]],
            }
        return results
