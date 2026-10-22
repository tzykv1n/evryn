# evryn paper extract <pdf_path>
# pytest tests/test_paper_pipeline.py

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple

from .types import (
    ScientificDocument,
    SentenceSpan,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
    ScientificSectionType,
)
from .normalizer import PaperEntityNormalizer


ACTIVATION_PATTERNS = [
    r"\b(?:activates?|activated|activating)\b",
    r"\b(?:upregulates?|upregulated|upregulating)\b",
    r"\b(?:stimulates?|stimulated|stimulating)\b",
    r"\b(?:enhances?|enhanced|enhancing)\b",
    r"\b(?:promotes?|promoted|promoting)\b",
    r"\b(?:triggers?|triggered|triggering)\b",
    r"\b(?:induces?|induced|inducing)\b",
    r"\b(?:drives?|driven|driving)\b",
    r"\b(?:causes?|caused|causing)\b",
    r"\b(?:increases?|increased|increasing)\b",
    r"\b(?:phosphorylates?|phosphorylated|phosphorylating)\b",
    r"\b(?:recruits?|recruited|recruiting)\b",
    r"\b(?:binds?|bound|binding)\b",
    r"\b(?:cleaves?|cleaved|cleaving)\b",
    r"\b(?:stabilizes?|stabilized|stabilizing)\b",
    r"\b(?:liberates?|liberated|liberating)\b",
]

INHIBITION_PATTERNS = [
    r"\b(?:inhibits?|inhibited|inhibiting)\b",
    r"\b(?:downregulates?|downregulated|downregulating)\b",
    r"\b(?:suppresses?|suppressed|suppressing)\b",
    r"\b(?:blocks?|blocked|blocking)\b",
    r"\b(?:attenuates?|attenuated|attenuating)\b",
    r"\b(?:prevents?|prevented|preventing)\b",
    r"\b(?:diminishes?|diminished|diminishing)\b",
    r"\b(?:reduces?|reduced|reducing)\b",
    r"\b(?:decreases?|decreased|decreasing)\b",
    r"\b(?:abrogates?|abrogated|abrogating)\b",
]

MEDIATION_PATTERNS = [
    r"\b(?:mediates?|mediated|mediating)\b",
    r"\b(?:signals?\s+through)\b",
    r"\b(?:acts?\s+via)\b",
    r"\b(?:functions?\s+through)\b",
]

PASSIVE_INDICATORS = [
    r"\bis\s+induced\s+by\b",
    r"\bwas\s+induced\s+by\b",
    r"\bare\s+induced\s+by\b",
    r"\bwere\s+induced\s+by\b",
    r"\bis\s+activated\s+by\b",
    r"\bwas\s+activated\s+by\b",
    r"\bis\s+triggered\s+by\b",
    r"\bwas\s+triggered\s+by\b",
    r"\bis\s+upregulated\s+by\b",
    r"\bwas\s+upregulated\s+by\b",
    r"\bis\s+inhibited\s+by\b",
    r"\bwas\s+inhibited\s+by\b",
    r"\bis\s+suppressed\s+by\b",
    r"\bwas\s+suppressed\s+by\b",
    r"\bis\s+blocked\s+by\b",
    r"\bwas\s+blocked\s+by\b",
]

NEGATION_PATTERNS = [
    r"\b(?:did\s+not|does\s+not|do\s+not)\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote)\b",
    r"\bfailed\s+to\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote)\b",
    r"\bno\s+significant\s+(?:effect|change|increase|decrease|alteration|induction|inhibition)\b",
    r"\bwithout\s+(?:affecting|altering|changing|inducing|inhibiting)\b",
    r"\bunaltered\b",
    r"\bwas\s+not\s+(?:altered|affected|changed|induced|inhibited)\b",
    r"\bwere\s+not\s+(?:altered|affected|changed|induced|inhibited)\b",
]

UNCERTAINTY_PATTERNS = [
    r"\b(?:may|might|could|potentially|possibly|presumably)\b",
    r"\b(?:we\s+hypothesize|we\s+speculate|it\s+is\s+postulated)\b",
    r"\b(?:suggests?\s+that|indicates?\s+a\s+potential)\b",
    r"\b(?:remains?\s+unclear|remains?\s+elusive|to\s+be\s+determined)\b",
]


class PaperCausalExtractor:

    def __init__(self, normalizer: Optional[PaperEntityNormalizer] = None):
        self.normalizer = normalizer or PaperEntityNormalizer()

    def extract_assertions(self, doc: ScientificDocument) -> List[CausalAssertion]:
        local_abbr = self.normalizer.extract_document_abbreviations(doc.full_text)
        assertions: List[CausalAssertion] = []
        assertion_idx = 1

        seen_keys: Set[Tuple[str, str, str]] = set()
        for sent in doc.sentences:
            text = sent.text
            entities = self.normalizer.detect_entities_in_sentence(text, local_abbr)
            if len(entities) < 2:
                continue

            is_negated = any(re.search(p, text, re.IGNORECASE) for p in NEGATION_PATTERNS)
            uncertainty = self._calculate_uncertainty(text, sent.section_title)

            for i in range(len(entities)):
                for j in range(len(entities)):
                    if i == j:
                        continue
                    e_raw1, e_canon1, s1, e1 = entities[i]
                    e_raw2, e_canon2, s2, e2 = entities[j]
                    if e_canon1 == e_canon2:
                        continue

                    rel_tuple = self._match_relation(text, s1, e1, s2, e2)
                    if not rel_tuple:
                        continue

                    rel_type, direction, confidence = rel_tuple

                    final_cause_canon = e_canon1 if direction == "FORWARD" else e_canon2
                    final_effect_canon = e_canon2 if direction == "FORWARD" else e_canon1
                    dedup_key = (final_cause_canon, final_effect_canon, sent.sentence_id)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    if is_negated:
                        status = EvidenceStatus.REFUTED_NEGATION
                    elif uncertainty >= 0.5:
                        status = EvidenceStatus.HYPOTHESIS_CLAIM
                    else:
                        status = EvidenceStatus.MEASURED_FACT

                    assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                    assertion_idx += 1

                    assertions.append(
                        CausalAssertion(
                            assertion_id=assertion_id,
                            cause=e_raw1 if direction == "FORWARD" else e_raw2,
                            cause_canonical=final_cause_canon,
                            effect=e_raw2 if direction == "FORWARD" else e_raw1,
                            effect_canonical=final_effect_canon,
                            direction="FORWARD",
                            relation_type=rel_type,
                            is_negated=is_negated,
                            uncertainty_score=uncertainty,
                            sentence_id=sent.sentence_id,
                            page_number=sent.page_number,
                            section_title=sent.section_title,
                            confidence=confidence,
                            evidence_quote=text,
                            char_span=(sent.start_char, sent.end_char),
                            evidence_status=status,
                        )
                    )

        return assertions

    def _calculate_uncertainty(self, text: str, section_title: str) -> float:
        score = 0.1
        sec_lower = section_title.lower()
        if any(w in sec_lower for w in ["discussion", "conclusion", "abstract"]):
            score += 0.2
        elif any(w in sec_lower for w in ["introduction", "background"]):
            score += 0.15

        for pattern in UNCERTAINTY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.35

        return min(round(score, 3), 1.0)

    def _match_relation(
        self,
        text: str,
        s1: int,
        e1: int,
        s2: int,
        e2: int,
    ) -> Optional[Tuple[CausalRelationType, str, float]]:
        if s1 < s2:
            between_text = text[e1:s2].strip()
            direction = "FORWARD"
        else:
            between_text = text[e2:s1].strip()
            direction = "BACKWARD"

        if len(between_text) > 80:
            return None

        for p in PASSIVE_INDICATORS:
            if re.search(p, between_text, re.IGNORECASE):
                if any(re.search(a, between_text, re.IGNORECASE) for a in INHIBITION_PATTERNS):
                    rel = CausalRelationType.DOWNREGULATES
                else:
                    rel = CausalRelationType.UPREGULATES
                inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
                return rel, inv_dir, 0.92

        for p in INHIBITION_PATTERNS:
            if re.search(p, between_text, re.IGNORECASE):
                return CausalRelationType.DOWNREGULATES, direction, 0.90

        for p in ACTIVATION_PATTERNS:
            if re.search(p, between_text, re.IGNORECASE):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for p in MEDIATION_PATTERNS:
            if re.search(p, between_text, re.IGNORECASE):
                return CausalRelationType.MEDIATES, direction, 0.85

        return None
