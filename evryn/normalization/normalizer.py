# evryn normalize --help

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple

from ..core.types import (
    NormalizedEntity,
    EvidenceSpan,
    NormalizedRelation,
    HigherOrderRelation,
    RelationType,
    ScientificDomain,
    Provenance,
)
from ..core.config import NormalizationConfig


ENTITY_ALIAS_MAP = {
    "covid-19": "SARS-CoV-2",
    "coronavirus": "SARS-CoV-2",
    "h5n1 virus": "avian influenza A (H5N1)",
    "myocardial infarction": "heart attack",
    "hypertension": "high blood pressure",
    "alzheimer's disease": "Alzheimer disease",
    "depressive disorder": "major depression",
}


class RelationNormalizer:

    def __init__(self, config: Optional[NormalizationConfig] = None):
        self.config = config or NormalizationConfig()

    def canonicalize_entity_name(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text.strip().lower())
        cleaned = re.sub(r"^the\s+|^a\s+|^an\s+", "", cleaned)
        return ENTITY_ALIAS_MAP.get(cleaned, cleaned)

    def create_entity(
        self,
        name: str,
        entity_type: str = "concept",
        domain: ScientificDomain = ScientificDomain.GENERAL_SCIENCE,
    ) -> NormalizedEntity:
        canon = self.canonicalize_entity_name(name) if self.config.canonicalize_entities else name.strip()
        e_id = f"ent_{hashlib.sha256(canon.encode('utf-8')).hexdigest()[:12]}"
        return NormalizedEntity(
            entity_id=e_id,
            canonical_name=canon,
            surface_forms=[name],
            entity_type=entity_type,
            domain=domain,
        )

    def normalize_pairwise(
        self,
        e1_text: str,
        e2_text: str,
        pred_type: str,
        confidence: float,
        sentence: str,
        e1_span: Tuple[int, int],
        e2_span: Tuple[int, int],
        source_doc: str = "doc_unknown",
        domain: ScientificDomain = ScientificDomain.GENERAL_SCIENCE,
        temporal_year: Optional[int] = None,
    ) -> NormalizedRelation:
        ent1 = self.create_entity(e1_text, domain=domain)
        ent2 = self.create_entity(e2_text, domain=domain)

        span1 = EvidenceSpan(
            text=e1_text,
            start_char=e1_span[0],
            end_char=e1_span[1],
            sentence=sentence,
            document_id=source_doc,
        )
        span2 = EvidenceSpan(
            text=e2_text,
            start_char=e2_span[0],
            end_char=e2_span[1],
            sentence=sentence,
            document_id=source_doc,
        )

        if pred_type == "FORWARD":
            sources = [ent1]
            targets = [ent2]
            rel_type = RelationType.FORWARD
        elif pred_type == "BACKWARD":
            sources = [ent2]
            targets = [ent1]
            rel_type = RelationType.FORWARD
        elif pred_type == "CONFOUNDED":
            sources = [ent1]
            targets = [ent2]
            rel_type = RelationType.CONFOUNDED
        else:
            sources = [ent1]
            targets = [ent2]
            rel_type = RelationType.NO_RELATION

        prov = Provenance(
            source_id=source_doc,
            citation=sentence[:60],
            confidence=confidence,
            extractor_model="evryn-normalizer-v1",
        )

        r_id = f"rel_{hashlib.sha256(f'{sources[0].canonical_name}->{targets[0].canonical_name}_{rel_type.value}'.encode('utf-8')).hexdigest()[:12]}"
        return NormalizedRelation(
            relation_id=r_id,
            source_entities=sources,
            target_entities=targets,
            relation_type=rel_type,
            evidence_spans=[span1, span2],
            confidence=confidence,
            provenance=prov,
            temporal_year=temporal_year,
            domain=domain,
            higher_order_order=2,
        )

    def normalize_higher_order(
        self,
        source_names: List[str],
        target_name: str,
        interaction_type: str,
        synergy_score: float,
        confidence: float,
        evidence_text: str = "",
        domain: ScientificDomain = ScientificDomain.GENERAL_SCIENCE,
        temporal_year: Optional[int] = None,
    ) -> Tuple[NormalizedRelation, HigherOrderRelation]:
        sources = [self.create_entity(name, domain=domain) for name in source_names]
        target = self.create_entity(target_name, domain=domain)

        prov = Provenance(
            source_id="higher_order_discovery",
            citation=evidence_text[:80],
            confidence=confidence,
            extractor_model="evryn-higher-order-flux",
        )

        src_repr = "_".join(sorted(s.canonical_name for s in sources))
        r_id = f"ho_{hashlib.sha256(f'{{{src_repr}}}->{target.canonical_name}'.encode('utf-8')).hexdigest()[:12]}"

        span = EvidenceSpan(
            text=f"{{{', '.join(source_names)}}} -> {target_name}",
            start_char=0,
            end_char=len(evidence_text),
            sentence=evidence_text,
        ) if evidence_text else None

        norm_rel = NormalizedRelation(
            relation_id=r_id,
            source_entities=sources,
            target_entities=[target],
            relation_type=RelationType.HIGHER_ORDER_JOINT,
            relation_family="SYNERGISTIC_CO_ACTION",
            evidence_spans=[span] if span else [],
            confidence=confidence,
            provenance=prov,
            temporal_year=temporal_year,
            domain=domain,
            higher_order_order=len(sources),
            properties={"synergy_score": synergy_score, "interaction_type": interaction_type},
        )

        ho_rel = HigherOrderRelation(
            relation_id=r_id,
            sources=sources,
            targets=[target],
            interaction_type=interaction_type,
            synergy_score=synergy_score,
            confidence=confidence,
            order=len(sources),
            provenance=prov,
            properties={"synergy_score": synergy_score},
        )

        return norm_rel, ho_rel
