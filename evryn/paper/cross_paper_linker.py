"""
EVRYN Cross-Paper Causal Linking Engine (Iteration 6).
Discovers and verifies evidence-backed causal bridges connecting mechanisms
established in different scientific papers or distant sections.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set

from evryn.paper.chain_types import (
    CausalChain,
    ChainEdge,
    CausalEdgeKind,
)
from evryn.paper.normalizer import PaperEntityNormalizer


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
        """Discovers verified cross-document causal bridges where Doc 1 establishes A -> Pivot and Doc 2 establishes Pivot -> B."""
        links: List[CrossDocumentCausalLink] = []
        seen_pairs: Set[Tuple[str, str, str]] = set()

        for c1 in chains_doc1:
            for e1 in c1.edges:
                pivot_candidate = e1.target
                pivot_norm = self._norm(pivot_candidate)

                for c2 in chains_doc2:
                    for e2 in c2.edges:
                        e2_src_norm = self._norm(e2.source)
                        is_match = (e2_src_norm == pivot_norm) or ((pivot_norm, e2_src_norm) in TCSTS_COGNATE_PAIRS)
                        if is_match:
                            src_entity = e1.source
                            tgt_entity = e2.target

                            if self._norm(src_entity) == self._norm(tgt_entity):
                                continue  # Avoid trivial loop

                            pivot_label = pivot_candidate if (e2_src_norm == pivot_norm) else f"{pivot_candidate} -> {e2.source}"
                            pair_key = (self._norm(src_entity), self._norm(pivot_label), self._norm(tgt_entity))
                            if pair_key in seen_pairs:
                                continue
                            seen_pairs.add(pair_key)

                            # Polarity & compatibility check
                            is_incompatible = (e1.polarity == "NEGATIVE" and e2.polarity == "POSITIVE" and "represses" in e1.evidence_text.lower())
                            compat = "INCOMPATIBLE_POLARITY" if is_incompatible else "COMPATIBLE"

                            # Calibrated cross-document confidence: geometric decay
                            composite_conf = e1.confidence * e2.confidence * 0.82

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
                                mechanism_compatibility=compat,
                                is_speculative=e1.is_hypothetical or e2.is_hypothetical,
                            )
                            links.append(link)

        # Sort by confidence
        links.sort(key=lambda x: x.confidence, reverse=True)
        return links
