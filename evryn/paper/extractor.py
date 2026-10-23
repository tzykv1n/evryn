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


CAUSAL_INFLUENCE_PATTERNS = [
    r"\b(?:leads?|led|leading)\s+to\b",
    r"\b(?:results?|resulted|resulting)\s+in\b",
    r"\b(?:causes?|caused|causing)\b",
    r"\b(?:drives?|driven|driving)\b",
    r"\b(?:affects?|affected|affecting)\b",
    r"\b(?:regulates?|regulated|regulating)\b",
    r"\b(?:controls?|controlled|controlling)\b",
    r"\b(?:modulates?|modulated|modulating)\b",
]

ACTIVATION_PATTERNS = [
    r"\b(?:promotes?|promoted|promoting)\b",
    r"\b(?:triggers?|triggered|triggering)\b",
    r"\b(?:induces?|induced|inducing)\b",
    r"\b(?:stimulates?|stimulated|stimulating)\b",
    r"\b(?:restores?|restored|restoring)\b",
    r"\b(?:contributes?|contributed|contributing)\s+to\b",
    r"\b(?:activates?|activated|activating)\b",
    r"\b(?:upregulates?|upregulated|upregulating)\b",
    r"\b(?:enhances?|enhanced|enhancing)\b",
    r"\b(?:increases?|increased|increasing)\b",
    r"\b(?:phosphorylates?|phosphorylated|phosphorylating)\b",
    r"\b(?:recruits?|recruited|recruiting)\b",
    r"\b(?:binds?|bound|binding)\b",
    r"\b(?:cleaves?|cleaved|cleaving)\b",
    r"\b(?:stabilizes?|stabilized|stabilizing)\b",
    r"\b(?:liberates?|liberated|liberating)\b",
    r"\b(?:traps?|trapped|trapping)\b",
    r"\b(?:is|are|was|were)?\s*(?:essential|required|requisite|necessary|critical|sufficient)\s+(?:for|to)\b",
    r"\b(?:responsible\s+for)\b",
    r"\b(?:confers?|conferred|conferring)\b",
    r"\b(?:encodes?|encoded|encoding)\b",
    r"\b(?:chelates?|chelated|chelating)\b",
    r"\b(?:protects?|protected|protecting)\s+against\b",
    r"\b(?:transfers?\s+phosphate)\b",
    r"\bactivator\s+of\b",
    r"\binducer\s+of\b",
    r"\bregulator\s+of\b",
]

PREVENTION_PATTERNS = [
    r"\b(?:prevents?|prevented|preventing)\b",
    r"\b(?:abrogates?|abrogated|abrogating)\b",
]

INHIBITION_PATTERNS = [
    r"\brepressor\s+of\b",
    r"\binhibitor\s+of\b",
    r"\b(?:inhibits?|inhibited|inhibiting)\b",
    r"\b(?:downregulates?|downregulated|downregulating)\b",
    r"\b(?:suppresses?|suppressed|suppressing)\b",
    r"\b(?:blocks?|blocked|blocking)\b",
    r"\b(?:attenuates?|attenuated|attenuating)\b",
    r"\b(?:diminishes?|diminished|diminishing)\b",
    r"\b(?:reduces?|reduced|reducing)\b",
    r"\b(?:decreases?|decreased|decreasing)\b",
    r"\b(?:dampens?|dampened|dampening)\b",
    r"\b(?:represses?|repressed|repressing)\b",
    r"\b(?:degrades?|degraded|degrading)\b",
    r"\b(?:degradation\s+of)\b",
    r"\b(?:loss\s+of)\b",
    r"\b(?:disrupts?|disrupted|disrupting)\b",
    r"\b(?:mutation\s+(?:in|of))\b",
    r"\b(?:deletion\s+(?:in|of))\b",
]

MEDIATION_PATTERNS = [
    r"\b(?:mediates?|mediated|mediating)\b",
    r"\b(?:signals?\s+through)\b",
    r"\b(?:acts?\s+via)\b",
    r"\b(?:functions?\s+through)\b",
]

ASSOCIATION_PATTERNS = [
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?associated\s+with\b",
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?correlated\s+with\b",
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?linked\s+to\b",
    r"\b(?:correlates?|correlated|correlating)\s+with\b",
    r"\b(?:co-occurs?|co-occurring)\s+with\b",
]

PASSIVE_INDICATORS = [
    r"\b(?:is|was|are|were|has\s+been|have\s+been)(?:\s+\w+){0,3}\s+(?:shown\s+to\s+be|demonstrated\s+to\s+be|known\s+to\s+be|found\s+to\s+be)?\s*(?:induced|activated|triggered|stimulated|phosphorylated|upregulated|promoted|affected|regulated|controlled|modulated)\s+(?:by|upon)\b",
    r"\b(?:is|was|are|were|has\s+been|have\s+been)(?:\s+\w+){0,3}\s+(?:shown\s+to\s+be|demonstrated\s+to\s+be|known\s+to\s+be|found\s+to\s+be)?\s*(?:inhibited|suppressed|blocked|repressed|downregulated|degraded|diminished|reduced|abrogated)\s+(?:by|upon)\b",
    r"\b(?:promoted|affected)\s+(?:by|upon)\b",
    r"\b(?:is|was|are|were)?\s*cleaved\s+by\b",
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
    r"\binduced\s+(?:by|with|upon)\b",
    r"\bactivated\s+(?:by|with|upon)\b",
    r"\btriggered\s+(?:by|with|upon)\b",
    r"\bstimulated\s+(?:by|with|upon)\b",
    r"\bphosphorylated\s+(?:by|with)\b",
    r"\bupregulated\s+(?:by|with|upon)\b",
    r"\binhibited\s+(?:by|with|upon)\b",
    r"\bsuppressed\s+(?:by|with|upon)\b",
    r"\bblocked\s+(?:by|with)\b",
    r"\bmediated\s+by\b",
    r"\bdependent\s+on\b",
    r"\bdownstream\s+of\b",
    r"\b(?:results?|resulted|resulting)\s+from\b",
    r"\bcaused\s+by\b",
    r"\bdue\s+to\b",
    r"\b(?:is|was|are|were)?\s*(?:regulated|controlled|modulated)\s+(?:by|via|through)\b",
    r"\b(?:is|was|are|were)?\s*attributed\s+to\b",
    r"\b(?:is|was|are|were)?\s*encoded\s+by\b",
    r"\b(?:is|was|are|were)?\s*(?:repressed|downregulated|degraded)\s+(?:by|upon)\b",
    r"\b(?:is|was|are|were)?\s*required\s+by\b",
    r"\bdepends?\s+on\b",
    r"\bresponsive\s+to\b",
    r"\bunder\s+(?:the\s+)?control\s+of\b",
    r"\bunder\s+(?:the\s+)?regulation\s+of\b",
]

NEGATION_PATTERNS = [
    r"\b(?:did\s+not|does\s+not|do\s+not)\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote|decrease|increase|reduce|suppress|block|associate|correlate)\b",
    r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\s+(?:associated\s+with|correlated\s+with|linked\s+to|caused\s+by|induced\s+by|altered\s+by|affected\s+by|sufficient\s+to)\b",
    r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\s+(?:altered|affected|changed|induced|inhibited|decreased|increased|reduced)\b",
    r"\bfailed\s+to\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote|decrease|increase|reduce|suppress|block)\b",
    r"\bno\s+significant\s+(?:effect|change|increase|decrease|alteration|induction|inhibition|association|correlation)\b",
    r"\bwithout\s+(?:affecting|altering|changing|inducing|inhibiting|decreasing|increasing|reducing)\b",
    r"\bnot\s+(?:significantly\s+)?(?:associated\s+with|correlated\s+with|linked\s+to)\b",
    r"\bunaltered\b",
    r"\bno\s+(?:detectable\s+)?(?:effect|association|correlation|change)\b",
    r"\blacks?\s+(?:an?\s+)?(?:effect|induction|inhibition|association)\b",
]

UNCERTAINTY_PATTERNS = [
    r"\b(?:may|might|could|potentially|possibly|presumably)\b",
    r"\b(?:we\s+hypothesize|we\s+speculate|it\s+is\s+postulated)\b",
    r"\b(?:suggests?\s+that|indicates?\s+a\s+potential)\b",
    r"\b(?:remains?\s+unclear|remains?\s+elusive|to\s+be\s+determined)\b",
]

# Precompiled regex patterns for performance optimization
COMPILED_NEGATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in NEGATION_PATTERNS]
COMPILED_UNCERTAINTY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in UNCERTAINTY_PATTERNS]

_ALL_PATTERNS_RAW: List[Tuple[str, CausalRelationType, bool]] = []
for p in PASSIVE_INDICATORS:
    rel = CausalRelationType.DOWNREGULATES if any(re.search(a, p, re.IGNORECASE) for a in INHIBITION_PATTERNS) else CausalRelationType.UPREGULATES
    _ALL_PATTERNS_RAW.append((p, rel, True))
for p in ASSOCIATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.ASSOCIATED, False))
for p in MEDIATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.MEDIATES, False))
for p in PREVENTION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.PREVENTS, False))
for p in INHIBITION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.DOWNREGULATES, False))
for p in CAUSAL_INFLUENCE_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.DIRECT_CAUSE, False))
for p in ACTIVATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.UPREGULATES, False))

COMPILED_SYNTACTIC_PATTERNS = [
    (re.compile(p, re.IGNORECASE), rel, is_passive)
    for p, rel, is_passive in _ALL_PATTERNS_RAW
]

COMPILED_PASSIVE_INDICATORS = [
    (re.compile(p, re.IGNORECASE), any(re.search(a, p, re.IGNORECASE) for a in INHIBITION_PATTERNS))
    for p in PASSIVE_INDICATORS
]
COMPILED_INHIBITION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INHIBITION_PATTERNS]
COMPILED_ACTIVATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ACTIVATION_PATTERNS]
COMPILED_MEDIATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in MEDIATION_PATTERNS]
COMPILED_ASSOCIATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ASSOCIATION_PATTERNS]

LEADING_NOISE_RE = re.compile(
    r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary|subsequently|consequently|in\s+turn|thus|therefore|meanwhile|furthermore|in\s+addition|moreover|importantly|however|rather|under\s+[^,]+|in\s+[^,]+|once\s+activated|treatment\s+with|treatment\s+of|administration\s+of|elevated|cellular|active|activated|phosphorylated|stabilized|nuclear|extracellular|soluble|membrane-anchored|high|higher|low|lower|direct|recombinant|by|via|upon|(?:multivariate\s+regression|statistical\s+analysis|experimental\s+data|our\s+findings|our\s+results)\s+(?:demonstrated|showed|revealed|indicated)\s+that|did\s+not|does\s+not|do\s+not|failed\s+to|without)\b\s*,?\s*",
    re.IGNORECASE,
)
ARTICLES_RE = re.compile(r"^(?:the|a|an|this|these|those|our|their|its)\s+", re.IGNORECASE)
TRAILING_ADVERBS_RE = re.compile(
    r"\s+(?:independently|directly|rapidly|subsequently|completely|significantly|in\s+turn|did\s+not|does\s+not|do\s+not|failed\s+to|cannot|never|not)$",
    re.IGNORECASE,
)
POSTFIX_STOPWORDS_RE = re.compile(
    r"\s+(?:in|at|on|for|with|by|of|to|into|across|during|via|through|under|from|which|that|thereby|was|were|is|are|been|being|associated|linked|correlated|leads?\s+to|leads?|leading\s+to|results?\s+in|causes?|causing)$",
    re.IGNORECASE,
)
CONJOINED_BOTH_RE = re.compile(r"\bboth\s+(.+?)\s+and\s+(.+)$", re.IGNORECASE)
CLAUSES_SPLIT_RE = re.compile(r";\s*|\s+(?:whereas|while|although|rather,)\s+")
DIRECT_NEG_RE = re.compile(
    r"\b(?:does\s+not|did\s+not|do\s+not|is\s+not|are\s+not|was\s+not|were\s+not|not|never|failed\s+to|without|lacks?)\b",
    re.IGNORECASE,
)
TABLE_FIG_RE = re.compile(r"^(?:Table|Figure|Fig\.|Scheme|Box)\s+\d+[:\.]?", re.IGNORECASE)
PARENS_RE = re.compile(r"\([^)]*\)")
SPACES_RE = re.compile(r"\s+")
TRAILING_PUNCT_RE = re.compile(r"[,;:\.]+$")


class PaperCausalExtractor:

    def __init__(self, normalizer: Optional[PaperEntityNormalizer] = None):
        self.normalizer = normalizer or PaperEntityNormalizer()

    def extract_assertions(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> List[CausalAssertion]:
        local_abbr = self.normalizer.extract_document_abbreviations(doc.full_text)
        assertions: List[CausalAssertion] = []
        assertion_idx = 1

        seen_keys: Set[Tuple[str, str, str]] = set()
        non_causal_sections = {
            "references", "reference", "bibliography", "acknowledgments",
            "acknowledgements", "funding", "competing interests", "author contributions",
        }
        for sent in doc.sentences:
            sec_name = sent.section_title.lower()
            if any(ncs in sec_name for ncs in non_causal_sections):
                continue
            text = sent.text
            if TABLE_FIG_RE.match(text.strip()):
                continue
            entities = self.normalizer.detect_entities_in_sentence(
                text, local_abbr, known_entities=known_entities
            )
            sent_assertions: List[CausalAssertion] = []
            if len(entities) >= 2:
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

                        # Intervening entity bypass check:
                        # If another distinct canonical entity sits strictly between mention 1 and mention 2,
                        # do not form a direct bypass edge unless there is an explicit coordination indicator.
                        start_pos = min(e1, e2)
                        end_pos = max(s1, s2)
                        intervening = [
                            ent for k, ent in enumerate(entities)
                            if k != i and k != j
                            and ent[1] != e_canon1 and ent[1] != e_canon2
                            and ent[2] >= start_pos and ent[3] <= end_pos
                        ]
                        span_text = text[start_pos:end_pos].lower()
                        if re.search(r"\w+\s*,?\s*(?:which|that|thereby)\b", span_text):
                            continue

                        if intervening:
                            is_coordinated = bool(re.search(r"\b(?:and|or|both|as\s+well\s+as)\b", span_text))
                            has_chain = bool(re.search(r"\b(?:leads?|led|causing|causes|resulting|results|which|that|thereby|subsequently)\b", span_text))
                            if has_chain or not is_coordinated:
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

                        sent_assertions.append(
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

            # Fallback or syntactic expansion if dictionary missed relations
            if not sent_assertions:
                syn_assertions, assertion_idx = self._extract_syntactic_assertions(
                    sent=sent,
                    doc_id=doc.doc_id,
                    start_idx=assertion_idx,
                    seen_keys=seen_keys,
                    local_abbr=local_abbr,
                    known_entities=known_entities,
                )
                sent_assertions.extend(syn_assertions)

            assertions.extend(sent_assertions)

        return assertions

    def _calculate_uncertainty(self, text: str, section_title: str) -> float:
        score = 0.05
        has_speculative_pattern = any(p.search(text) for p in COMPILED_UNCERTAINTY_PATTERNS)
        if has_speculative_pattern:
            score += 0.45
            sec_lower = section_title.lower()
            if any(w in sec_lower for w in ["discussion", "conclusion"]):
                score += 0.15

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

        if len(between_text) > 160:
            return None

        for pat_re, is_inhib in COMPILED_PASSIVE_INDICATORS:
            if pat_re.search(between_text):
                rel = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
                return rel, inv_dir, 0.92

        for pat_re in COMPILED_INHIBITION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.DOWNREGULATES, direction, 0.90

        for pat_re in COMPILED_ACTIVATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for pat_re in COMPILED_MEDIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.MEDIATES, direction, 0.85

        for pat_re in COMPILED_ASSOCIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.ASSOCIATED, direction, 0.80

        return None

    def _clean_phrase(self, raw: str) -> str:
        cleaned = raw.strip()
        cleaned = TRAILING_PUNCT_RE.sub("", cleaned).strip()
        prev = ""
        while prev != cleaned:
            prev = cleaned
            cleaned = LEADING_NOISE_RE.sub("", cleaned).strip()
            cleaned = ARTICLES_RE.sub("", cleaned).strip()
            cleaned = TRAILING_ADVERBS_RE.sub("", cleaned).strip()

        cleaned = POSTFIX_STOPWORDS_RE.sub("", cleaned).strip()
        cleaned = PARENS_RE.sub("", cleaned).strip()
        cleaned = SPACES_RE.sub(" ", cleaned).strip()
        return cleaned

    def _parse_conjoined_phrases(self, raw: str) -> List[str]:
        m_both = CONJOINED_BOTH_RE.search(raw)
        if m_both:
            e1 = self._clean_phrase(m_both.group(1))
            e2 = self._clean_phrase(m_both.group(2))
            return [e for e in [e1, e2] if e]
        e = self._clean_phrase(raw)
        return [e] if e else []

    def _extract_syntactic_assertions(
        self,
        sent: SentenceSpan,
        doc_id: str,
        start_idx: int,
        seen_keys: Set[Tuple[str, str, str]],
        local_abbr: Optional[Dict[str, str]] = None,
        known_entities: Optional[List[str]] = None,
    ) -> Tuple[List[CausalAssertion], int]:
        text = sent.text
        text = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary)[:\s]*\n+", "", text, flags=re.IGNORECASE)
        major_clauses = CLAUSES_SPLIT_RE.split(text)
        idx = start_idx
        results: List[CausalAssertion] = []

        for major_clause in major_clauses:
            major_clean = major_clause.strip()
            if not major_clean or len(major_clean) < 8:
                continue

            PARTICIPIAL_VERBS = r"suppressing|inhibiting|activating|inducing|promoting|blocking|downregulating|upregulating|preventing|reducing|causing|leading\s+to|resulting\s+in"
            pattern = rf",\s*(?:which\s+|that\s+|thereby\s+)?(?=(?:which|that|thereby|{PARTICIPIAL_VERBS})\b)"
            parts = re.split(pattern, major_clean, flags=re.IGNORECASE)
            sub_clauses: List[Tuple[str, bool]] = []
            if len(parts) > 1:
                sub_clauses.append((parts[0].strip(), False))
                for p in parts[1:]:
                    p_clean = re.sub(r"^(?:which|that|thereby)\s+", "", p.strip(), flags=re.IGNORECASE)
                    if p_clean:
                        sub_clauses.append((p_clean, True))
            else:
                sub_clauses.append((major_clean, False))

            last_extracted_effect = ""
            last_clause_tail = ""

            for clause_str, is_relative in sub_clauses:
                if not clause_str or len(clause_str) < 4:
                    continue

                if is_relative:
                    antecedent = last_extracted_effect or last_clause_tail
                    if antecedent:
                        clause_str = f"{antecedent} {clause_str}"

                has_clause_neg = any(p.search(clause_str) for p in COMPILED_NEGATION_PATTERNS)
                clause_unc = self._calculate_uncertainty(clause_str, sent.section_title)
                clause_has_associative = False
                claimed_verb_spans: List[Tuple[int, int]] = []

                for pat_re, rel_type, is_passive in COMPILED_SYNTACTIC_PATTERNS:
                    if clause_has_associative and rel_type in (CausalRelationType.DOWNREGULATES, CausalRelationType.UPREGULATES):
                        # Skip secondary adjective matches inside already extracted associative/mediated clauses
                        continue

                    for match in pat_re.finditer(clause_str):
                        start_pos, end_pos = match.start(), match.end()

                        # Avoid active matches inside already matched passive spans
                        if any(max(start_pos, cs) < min(end_pos, ce) for cs, ce in claimed_verb_spans):
                            continue

                        match_str = match.group(0).lower()
                        before = clause_str[:start_pos].strip()
                        after = clause_str[end_pos:].strip()

                        prec_window = clause_str[max(0, start_pos - 35):start_pos].strip()
                        is_neg = (
                            bool(DIRECT_NEG_RE.search(prec_window))
                            or ("not" in match_str)
                            or any(p.search(prec_window) for p in COMPILED_NEGATION_PATTERNS)
                            or has_clause_neg
                        )

                        after_cut = re.split(r",\s*(?:which|that|thereby|and\s+thereby|ultimately|in\s+turn)\b|[,\.]", after)[0].strip()
                        before_cut = re.split(r",\s*(?:which|that)\b", before)[-1].strip()

                        if is_passive:
                            effect_raw = before_cut
                            cause_raw = after_cut
                        else:
                            cause_raw = before_cut
                            effect_raw = after_cut

                        cause_cand = self._clean_phrase(cause_raw)
                        effect_cands = self._parse_conjoined_phrases(effect_raw)

                        cause_canon = self.normalizer.canonicalize(cause_cand, local_abbr, known_entities)

                        for eff_cand in effect_cands:
                            eff_canon = self.normalizer.canonicalize(eff_cand, local_abbr, known_entities)

                            if not cause_canon or not eff_canon or len(cause_canon) < 2 or len(eff_canon) < 2:
                                continue
                            if cause_canon.lower() == eff_canon.lower():
                                continue
                            if cause_canon.lower() in {"it", "we", "this", "these", "they", "there", "assay", "findings", "results", "cells", "experiment"}:
                                continue
                            if eff_canon.lower() in {"it", "this", "these", "they", "there", "effect", "response", "cells"}:
                                continue

                            dedup_key = (cause_canon, eff_canon, sent.sentence_id)
                            if dedup_key in seen_keys:
                                continue
                            seen_keys.add(dedup_key)
                            claimed_verb_spans.append((start_pos, end_pos))

                            if is_neg:
                                status = EvidenceStatus.REFUTED_NEGATION
                            elif clause_unc >= 0.5:
                                status = EvidenceStatus.HYPOTHESIS_CLAIM
                            else:
                                status = EvidenceStatus.MEASURED_FACT

                            assertion_id = f"asrt_{doc_id[:6]}_{sent.page_number}_{idx:04d}"
                            idx += 1

                            results.append(
                                CausalAssertion(
                                    assertion_id=assertion_id,
                                    cause=cause_cand,
                                    cause_canonical=cause_canon,
                                    effect=eff_cand,
                                    effect_canonical=eff_canon,
                                    direction="FORWARD",
                                    relation_type=rel_type,
                                    is_negated=is_neg,
                                    uncertainty_score=clause_unc,
                                    sentence_id=sent.sentence_id,
                                    page_number=sent.page_number,
                                    section_title=sent.section_title,
                                    confidence=0.88,
                                    evidence_quote=text,
                                    char_span=(sent.start_char, sent.end_char),
                                    evidence_status=status,
                                )
                            )
                            last_extracted_effect = eff_cand
                            if rel_type in (CausalRelationType.ASSOCIATED, CausalRelationType.MEDIATES):
                                clause_has_associative = True

                if not last_extracted_effect:
                    m_words = re.findall(r"[A-Za-z0-9_-]+", clause_str)
                    if m_words:
                        last_clause_tail = m_words[-1]
        return results, idx
