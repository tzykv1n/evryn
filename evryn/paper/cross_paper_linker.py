"""
EVRYN Cross-Paper Causal Linking Engine (Phase 3.1).
Discovers, categorizes, and audits evidence-backed causal bridges connecting
mechanisms established across different scientific papers.

Classifies all cross-document outputs into 6 defensible categories:
1. SAME_ENTITY_ALIGNMENT (Direct identity alignment across publications)
2. COMPLEMENTARY_EVIDENCE (Complementary experimental findings for same relation)
3. SUPPORTED_CHAIN_SPAN (Evidence-backed chain spanning across documents)
4. PLAUSIBLE_HYPOTHESIS (Cross-species/orthologous signaling hypothesis)
5. UNSUPPORTED_CONTRADICTORY (Rejected: polarity conflict or reverse effector)
6. INDETERMINATE (Insufficient evidence or uncertain provenance)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set

from evryn.paper.chain_types import (
    CausalChain,
    ChainEdge,
    CausalEdgeKind,
)
from evryn.paper.normalizer import PaperEntityNormalizer


class CrossDocumentLinkCategory(str, Enum):
    SAME_ENTITY_ALIGNMENT = "SAME_ENTITY_ALIGNMENT"
    COMPLEMENTARY_EVIDENCE = "COMPLEMENTARY_EVIDENCE"
    SUPPORTED_CHAIN_SPAN = "SUPPORTED_CHAIN_SPAN"
    PLAUSIBLE_HYPOTHESIS = "PLAUSIBLE_HYPOTHESIS"
    UNSUPPORTED_CONTRADICTORY = "UNSUPPORTED_CONTRADICTORY"
    INDETERMINATE = "INDETERMINATE"


DOC_SPECIES_MAP = {
    "PMC1804205": "Salmonella enterica",
    "PMC1874608": "Salmonella enterica",
    "PMC1913099": "Streptococcus pneumoniae",
    "PMC1974823": "Porphyromonas gingivalis",
    "PMC2242835": "Mycobacterium tuberculosis",
    "PMC2266911": "Photorhabdus luminescens",
    "PMC2358977": "Streptococcus suis",
    "PMC2430206": "Staphylococcus aureus",
    "PMC2565068": "Streptococcus pyogenes",
    "PMC2581603": "Pseudomonas aeruginosa",
    "PMC2593050": "Streptococcus pneumoniae",
    "PMC2639726": "Salmonella enterica",
    "PMC2651894": "Salmonella enterica",
    "PMC2682197": "Mycobacterium tuberculosis",
    "PMC2714965": "Caenorhabditis elegans",
    "PMC2774163": "Pseudomonas aeruginosa",
    "PMC2816692": "Salmonella enterica",
    "PMC2829055": "Yersinia pestis",
    "PMC2858072": "Brucella abortus",
    "PMC2885601": "Streptococcus equi",
}


@dataclass
class CrossDocumentCausalLink:
    source_entity: str
    target_entity: str
    pivot_entity: str
    source_doc_id: str
    target_doc_id: str
    source_relation: str
    target_relation: str
    confidence: float
    evidence_doc1: str
    evidence_doc2: str
    page_doc1: int
    page_doc2: int
    link_category: CrossDocumentLinkCategory = CrossDocumentLinkCategory.SUPPORTED_CHAIN_SPAN
    dual_independent_support: bool = True
    organism_doc1: str = ""
    organism_doc2: str = ""
    mechanism_compatibility: str = "COMPATIBLE"
    is_speculative: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "pivot_entity": self.pivot_entity,
            "source_doc_id": self.source_doc_id,
            "target_doc_id": self.target_doc_id,
            "source_relation": self.source_relation,
            "target_relation": self.target_relation,
            "confidence": round(self.confidence, 4),
            "evidence_doc1": self.evidence_doc1,
            "evidence_doc2": self.evidence_doc2,
            "page_doc1": self.page_doc1,
            "page_doc2": self.page_doc2,
            "link_category": self.link_category.value,
            "dual_independent_support": self.dual_independent_support,
            "organism_doc1": self.organism_doc1,
            "organism_doc2": self.organism_doc2,
            "mechanism_compatibility": self.mechanism_compatibility,
            "is_speculative": self.is_speculative,
        }


TCSTS_COGNATE_PAIRS = {
    ("phoq", "phop"), ("phop", "phoq"),
    ("pmrb", "pmra"), ("pmra", "pmrb"),
    ("csrs", "csrr"), ("csrr", "csrs"),
    ("vick", "vicr"), ("vicr", "vick"),
    ("salk", "salr"), ("salr", "salk"),
    ("bvrs", "bvrr"), ("bvrr", "bvrs"),
    ("rets", "gacs"), ("gacs", "rets"),
}

GENERIC_PIVOT_EXCLUSIONS = {
    "tcs", "two component system", "two component systems", "regulator",
    "virulence", "phenotype", "growth", "survival", "biofilm", "host colonization"
}


class CrossPaperLinker:
    def __init__(self, normalizer: Optional[PaperEntityNormalizer] = None):
        self.normalizer = normalizer or PaperEntityNormalizer()

    def _norm(self, s: str) -> str:
        if not s:
            return ""
        canon = self.normalizer.canonicalize(s)
        return canon.lower().replace("_", " ").replace("-", " ").strip()

    def discover_cross_paper_bridges(
        self,
        chains_doc1: List[CausalChain],
        chains_doc2: List[CausalChain],
        doc_id_1: str,
        doc_id_2: str,
    ) -> List[CrossDocumentCausalLink]:
        """
        Discovers, categorizes, and verifies evidence-backed cross-document causal bridges
        where Doc 1 establishes A -> Pivot and Doc 2 establishes Pivot -> B.
        """
        links: List[CrossDocumentCausalLink] = []
        seen_pairs: Set[Tuple[str, str, str]] = set()

        org1 = DOC_SPECIES_MAP.get(doc_id_1, "Unknown organism")
        org2 = DOC_SPECIES_MAP.get(doc_id_2, "Unknown organism")
        is_same_species = (org1 == org2 and org1 != "Unknown organism")

        for c1 in chains_doc1:
            for e1 in c1.edges:
                pivot_candidate = e1.target
                pivot_norm = self._norm(pivot_candidate)
                if pivot_norm in GENERIC_PIVOT_EXCLUSIONS:
                    continue

                for c2 in chains_doc2:
                    for e2 in c2.edges:
                        e2_src_norm = self._norm(e2.source)
                        is_match = (e2_src_norm == pivot_norm) or ((pivot_norm, e2_src_norm) in TCSTS_COGNATE_PAIRS)
                        if is_match:
                            src_entity = e1.source
                            tgt_entity = e2.target

                            src_norm = self._norm(src_entity)
                            tgt_norm = self._norm(tgt_entity)

                            if src_norm == tgt_norm:
                                continue  # Avoid trivial loop

                            pivot_label = pivot_candidate if (e2_src_norm == pivot_norm) else f"{pivot_candidate} -> {e2.source}"
                            pair_key = (src_norm, self._norm(pivot_label), tgt_norm)
                            if pair_key in seen_pairs:
                                continue
                            seen_pairs.add(pair_key)

                            # Polarity & compatibility check
                            is_incompatible = (
                                e1.polarity == "NEGATIVE" and e2.polarity == "POSITIVE" and "represses" in e1.evidence_text.lower()
                            )
                            compat = "INCOMPATIBLE_POLARITY" if is_incompatible else "COMPATIBLE"

                            # 6-category classification
                            if is_incompatible:
                                category = CrossDocumentLinkCategory.UNSUPPORTED_CONTRADICTORY
                            elif src_norm == self._norm(e2.source) and tgt_norm == self._norm(e1.target):
                                category = CrossDocumentLinkCategory.COMPLEMENTARY_EVIDENCE
                            elif is_same_species:
                                category = CrossDocumentLinkCategory.SUPPORTED_CHAIN_SPAN
                            else:
                                # Different organisms (e.g. Salmonella PMC1804205 vs Pseudomonas PMC2581603)
                                category = CrossDocumentLinkCategory.PLAUSIBLE_HYPOTHESIS

                            # Calibrated confidence: geometric decay
                            base_conf = e1.confidence * e2.confidence
                            if category == CrossDocumentLinkCategory.PLAUSIBLE_HYPOTHESIS:
                                composite_conf = base_conf * 0.75  # Cross-species penalty
                            elif category == CrossDocumentLinkCategory.SUPPORTED_CHAIN_SPAN:
                                composite_conf = base_conf * 0.88
                            elif category == CrossDocumentLinkCategory.COMPLEMENTARY_EVIDENCE:
                                composite_conf = base_conf * 0.92
                            else:
                                composite_conf = base_conf * 0.20

                            link = CrossDocumentCausalLink(
                                source_entity=src_entity,
                                target_entity=tgt_entity,
                                pivot_entity=pivot_label,
                                source_doc_id=doc_id_1,
                                target_doc_id=doc_id_2,
                                source_relation=e1.relation_type,
                                target_relation=e2.relation_type,
                                confidence=composite_conf,
                                evidence_doc1=e1.evidence_text,
                                evidence_doc2=e2.evidence_text,
                                page_doc1=e1.page_number,
                                page_doc2=e2.page_number,
                                link_category=category,
                                dual_independent_support=bool(e1.evidence_text and e2.evidence_text),
                                organism_doc1=org1,
                                organism_doc2=org2,
                                mechanism_compatibility=compat,
                                is_speculative=e1.is_hypothetical or e2.is_hypothetical,
                            )
                            links.append(link)

        # Sort by confidence
        links.sort(key=lambda x: x.confidence, reverse=True)
        return links
