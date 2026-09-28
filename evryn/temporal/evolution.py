# evryn temporal --help

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import numpy as np

from ..core.types import NormalizedRelation, RelationType
from ..core.config import TemporalConfig


@dataclass
class TemporalRelationSequence:
    sequence_id: str
    relation_key: str
    source_name: str
    target_name: str
    relation_family: str
    years: List[int]
    confidences: List[float]
    evidence_counts: List[int]
    status: str
    emergence_year: int
    velocity: float
    is_contradicted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TemporalEvolutionTracker:

    def __init__(self, config: Optional[TemporalConfig] = None):
        self.config = config or TemporalConfig()

    def track_evolution(
        self,
        relations: List[NormalizedRelation],
    ) -> Dict[str, TemporalRelationSequence]:
        grouped: Dict[str, List[NormalizedRelation]] = {}
        for r in relations:
            src = "_".join(sorted(s.canonical_name for s in r.source_entities))
            tgt = "_".join(sorted(t.canonical_name for t in r.target_entities))
            key = f"{src}->{tgt}"
            grouped.setdefault(key, []).append(r)

        sequences: Dict[str, TemporalRelationSequence] = {}
        seq_idx = 0

        for key, rel_list in grouped.items():
            year_dict: Dict[int, List[float]] = {}
            fam_dict: Dict[str, int] = {}
            has_contradiction = False

            for r in rel_list:
                yr = r.temporal_year or 2024
                year_dict.setdefault(yr, []).append(r.confidence)
                fam = r.relation_family or "CAUSAL_PRODUCTION"
                fam_dict[fam] = fam_dict.get(fam, 0) + 1

                if r.relation_type == RelationType.CONFOUNDED or r.properties.get("conflicted", False):
                    has_contradiction = True

            sorted_years = sorted(year_dict.keys())
            if not sorted_years:
                continue

            conf_trajectory = [float(np.mean(year_dict[yr])) for yr in sorted_years]
            vol_trajectory = [len(year_dict[yr]) for yr in sorted_years]

            if len(conf_trajectory) > 1:
                velocity = float((conf_trajectory[-1] - conf_trajectory[0]) / (sorted_years[-1] - sorted_years[0]))
            else:
                velocity = 0.0

            total_evidence = sum(vol_trajectory)
            if has_contradiction:
                status = "CONTRADICTED"
            elif total_evidence >= 3 and conf_trajectory[-1] >= 0.80:
                status = "CONSOLIDATED"
            elif velocity > 0.05:
                status = "EMERGING"
            elif velocity < -0.05:
                status = "DECAYING"
            else:
                status = "STABLE"

            primary_fam = max(fam_dict.items(), key=lambda x: x[1])[0]
            src_name = "_".join(s.canonical_name for s in rel_list[0].source_entities)
            tgt_name = "_".join(t.canonical_name for t in rel_list[0].target_entities)

            seq = TemporalRelationSequence(
                sequence_id=f"seq_{seq_idx:04d}",
                relation_key=key,
                source_name=src_name,
                target_name=tgt_name,
                relation_family=primary_fam,
                years=sorted_years,
                confidences=conf_trajectory,
                evidence_counts=vol_trajectory,
                status=status,
                emergence_year=sorted_years[0],
                velocity=velocity,
                is_contradicted=has_contradiction,
            )
            sequences[key] = seq
            seq_idx += 1

        return sequences
