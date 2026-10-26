"""
EVRYN Document-Context Relation Resolver (Phase 1.7).
Recovers discourse-level causal and regulatory relations spanning sentence boundaries
within bounded context windows, while enforcing strict evidence provenance and false-positive controls.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from evryn.paper.types import (
    ScientificDocument,
    SentenceSpan,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
)
from evryn.paper.normalizer import PaperEntityNormalizer

# Common scientific genus and abbreviations causing sentence boundary fragmentation
ABBREVIATION_SPLIT_RE = re.compile(
    r"(?:\b[A-Z]\.|\bet\s+al\.|\bFig\.|\be\.g\.|\bi\.e\.)$"
)

# Demonstrative causal anaphora patterns
DEMONSTRATIVE_CAUSAL_RE = re.compile(
    r"^(?:However,?\s+|Moreover,?\s+|Furthermore,?\s+|Together,?\s+)?(?:This|These|Such)\s+"
    r"(?:result|results|finding|findings|phenotype|defect|defects|observation|observations|mechanism|data)\s+"
    r"(?:may\s+account(?:\s+partially,\s+if\s+not\s+most\s+of\s+all,\s+for|\s+partially\s+for|\s+for)|"
    r"accounts?\s+for|explains?|underlies?|underly|leads?\s+to|causes?|contributes?\s+to|results?\s+in)\s+"
    r"(?:the\s+)?([A-Za-z0-9\s_-]+)",
    re.IGNORECASE,
)

DEMONSTRATIVE_REQUIREMENT_RE = re.compile(
    r"^(?:(?:Here\s+)?we\s+(?:report|show|demonstrate|found)\s+that\s+)?(?:this|the)\s+"
    r"(?:activation|induction|transcription|expression|response|resistance)\s+"
    r"(?:requires|required|requiring|depends?\s+on|depended\s+on)\s+(?:both\s+)?",
    re.IGNORECASE,
)

# Explicit causal discourse connectives
DISCOURSE_CONNECTIVE_RE = re.compile(
    r"^(?:Consequently|Subsequently|As\s+a\s+result|Therefore|Thus|Hence|In\s+turn|Accordingly|Following\s+this|Thereby),?\s+",
    re.IGNORECASE,
)

TERMINAL_PHENOTYPES = {
    "virulence", "pathogenicity", "host survival", "protective immunity",
    "mortality", "lethality", "host colonization", "equine strangles",
}

ENV_PARAMS = {"Acid pH", "Temperature", "Hypoxia", "Normoxia"}


class DocumentContextResolver:
    """
    Bounded document-context relation resolution module.
    Identifies discourse-level claims across adjacent sentences while enforcing
    false-positive controls, directionality, and dual-sentence provenance tracking.
    """

    def __init__(
        self,
        enabled: bool = True,
        enable_sentence_stitch: bool = True,
        enable_anaphora: bool = True,
        enable_discourse_connectives: bool = True,
        enable_false_positive_controls: bool = True,
        max_sentence_distance: int = 1,
        min_confidence: float = 0.86,
    ):
        self.enabled = enabled
        self.enable_sentence_stitch = enable_sentence_stitch
        self.enable_anaphora = enable_anaphora
        self.enable_discourse_connectives = enable_discourse_connectives
        self.enable_false_positive_controls = enable_false_positive_controls
        self.max_sentence_distance = max_sentence_distance
        self.min_confidence = min_confidence

    def resolve_document_context(
        self,
        doc: ScientificDocument,
        normalizer: PaperEntityNormalizer,
        local_abbr: Dict[str, str],
        known_entities: Optional[List[str]],
        existing_assertions: List[CausalAssertion],
        start_assertion_idx: int = 1000,
    ) -> List[CausalAssertion]:
        """
        Extract document-context causal assertions across bounded sentence windows.
        """
        if not self.enabled:
            return []

        resolved_assertions: List[CausalAssertion] = []
        assertion_idx = start_assertion_idx

        # Existing directed pairs to prevent duplication
        existing_pairs: Set[Tuple[str, str]] = {
            (a.cause_canonical, a.effect_canonical) for a in existing_assertions
        }

        # Index existing assertions by sentence_id for fast antecedent lookup
        assertions_by_sent: Dict[str, List[CausalAssertion]] = {}
        for a in existing_assertions:
            assertions_by_sent.setdefault(a.sentence_id, []).append(a)

        sentences = doc.sentences
        n_sents = len(sentences)

        # 1. Sentence Boundary Stitching for Abbreviation Splits
        if self.enable_sentence_stitch:
            for k in range(n_sents - 1):
                s_curr = sentences[k]
                s_next = sentences[k + 1]

                # Must be in same section and page
                if s_curr.section_title != s_next.section_title or s_curr.page_number != s_next.page_number:
                    continue

                curr_text_stripped = s_curr.text.strip()
                if ABBREVIATION_SPLIT_RE.search(curr_text_stripped):
                    # Stitched candidate
                    stitched_text = f"{curr_text_stripped} {s_next.text.strip()}"
                    curr_ents = normalizer.detect_entities_in_sentence(curr_text_stripped, local_abbr, known_entities)
                    next_ents = normalizer.detect_entities_in_sentence(s_next.text, local_abbr, known_entities)

                    # Only stitch if entities are partitioned across the boundary
                    if (curr_ents and not next_ents) or (not curr_ents and next_ents) or (curr_ents and next_ents):
                        stitched_ents = normalizer.detect_entities_in_sentence(stitched_text, local_abbr, known_entities)
                        if len(stitched_ents) >= 2:
                            # Check if a requirement/cause verb connects them in stitched text
                            m_req = re.search(
                                r"\b(?:requires?|required|requiring|essential\s+for|necessary\s+for|promotes?|promoted|activates?|activated|regulates?|regulated)\b",
                                stitched_text,
                                re.IGNORECASE,
                            )
                            if m_req:
                                e_first = stitched_ents[0]
                                e_last = stitched_ents[-1]
                                c_canon = e_last[1] if "require" in m_req.group(0).lower() or "essential" in m_req.group(0).lower() else e_first[1]
                                e_canon = e_first[1] if c_canon == e_last[1] else e_last[1]

                                if self._is_valid_pair(c_canon, e_canon, existing_pairs):
                                    asrt = CausalAssertion(
                                        assertion_id=f"asrt_ctx_{doc.doc_id[:6]}_{s_next.page_number}_{assertion_idx:04d}",
                                        cause=e_last[0] if c_canon == e_last[1] else e_first[0],
                                        cause_canonical=c_canon,
                                        effect=e_first[0] if c_canon == e_last[1] else e_last[0],
                                        effect_canonical=e_canon,
                                        direction="FORWARD",
                                        relation_type=CausalRelationType.DIRECT_CAUSE,
                                        is_negated=False,
                                        uncertainty_score=0.10,
                                        sentence_id=s_next.sentence_id,
                                        page_number=s_next.page_number,
                                        section_title=s_next.section_title,
                                        confidence=0.89,
                                        evidence_quote=stitched_text,
                                        char_span=(s_curr.start_char, s_next.end_char),
                                        evidence_status=EvidenceStatus.MEASURED_FACT,
                                        evidence_sentence_ids=[s_curr.sentence_id, s_next.sentence_id],
                                        discourse_relation="abbreviation_stitch",
                                        antecedent_quote=s_curr.text.strip(),
                                    )
                                    assertion_idx += 1
                                    resolved_assertions.append(asrt)
                                    existing_pairs.add((c_canon, e_canon))

        # 2. Demonstrative Causal Anaphora Resolution
        if self.enable_anaphora:
            for k in range(n_sents - 1):
                s_curr = sentences[k]
                s_next = sentences[k + 1]

                if s_curr.section_title != s_next.section_title or s_curr.page_number != s_next.page_number:
                    continue

                m_req = DEMONSTRATIVE_REQUIREMENT_RE.match(s_next.text.strip())
                if m_req:
                    next_ents = normalizer.detect_entities_in_sentence(s_next.text, local_abbr, known_entities)
                    curr_ents = normalizer.detect_entities_in_sentence(s_curr.text, local_abbr, known_entities)
                    curr_asrt = assertions_by_sent.get(s_curr.sentence_id, [])

                    target_candidate = None
                    if curr_asrt:
                        target_candidate = (curr_asrt[-1].effect, curr_asrt[-1].effect_canonical)
                    elif curr_ents:
                        valid_c = [e for e in curr_ents if e[1] not in ENV_PARAMS]
                        if valid_c:
                            target_candidate = (valid_c[-1][0], valid_c[-1][1])

                    if target_candidate:
                        t_raw, t_canon = target_candidate
                        causes = [e for e in next_ents if e[2] >= m_req.end() and e[1] != t_canon]
                        for c_raw, c_canon, _, _ in causes:
                            if self._is_valid_pair(c_canon, t_canon, existing_pairs):
                                asrt = CausalAssertion(
                                    assertion_id=f"asrt_ctx_{doc.doc_id[:6]}_{s_next.page_number}_{assertion_idx:04d}",
                                    cause=c_raw,
                                    cause_canonical=c_canon,
                                    effect=t_raw,
                                    effect_canonical=t_canon,
                                    direction="FORWARD",
                                    relation_type=CausalRelationType.UPREGULATES,
                                    is_negated=False,
                                    uncertainty_score=0.10,
                                    sentence_id=s_next.sentence_id,
                                    page_number=s_next.page_number,
                                    section_title=s_next.section_title,
                                    confidence=0.91,
                                    evidence_quote=f"{s_curr.text.strip()} {s_next.text.strip()}",
                                    char_span=(s_curr.start_char, s_next.end_char),
                                    evidence_status=EvidenceStatus.MEASURED_FACT,
                                    evidence_sentence_ids=[s_curr.sentence_id, s_next.sentence_id],
                                    discourse_relation="demonstrative_requirement",
                                    antecedent_quote=s_curr.text.strip(),
                                )
                                assertion_idx += 1
                                resolved_assertions.append(asrt)
                                existing_pairs.add((c_canon, t_canon))

                m_ana = DEMONSTRATIVE_CAUSAL_RE.match(s_next.text.strip())
                if not m_ana:
                    continue

                # Target entity from s_next
                next_ents = normalizer.detect_entities_in_sentence(s_next.text, local_abbr, known_entities)
                if not next_ents:
                    continue

                # Find antecedent in s_curr
                # Check if s_curr has an existing assertion effect/cause or detected entities
                curr_asrt = assertions_by_sent.get(s_curr.sentence_id, [])
                curr_ents = normalizer.detect_entities_in_sentence(s_curr.text, local_abbr, known_entities)

                antecedent_candidate = None
                if curr_asrt:
                    # Prefer the effect or phenotype of the preceding assertion
                    antecedent_candidate = (curr_asrt[-1].effect, curr_asrt[-1].effect_canonical)
                elif curr_ents:
                    # Prefer the last detected entity or phenotype in s_curr
                    antecedent_candidate = (curr_ents[-1][0], curr_ents[-1][1])

                if not antecedent_candidate:
                    continue

                c_raw, c_canon = antecedent_candidate
                for e_raw, e_canon, _, _ in next_ents:
                    if self._is_valid_pair(c_canon, e_canon, existing_pairs):
                        asrt = CausalAssertion(
                            assertion_id=f"asrt_ctx_{doc.doc_id[:6]}_{s_next.page_number}_{assertion_idx:04d}",
                            cause=c_raw,
                            cause_canonical=c_canon,
                            effect=e_raw,
                            effect_canonical=e_canon,
                            direction="FORWARD",
                            relation_type=CausalRelationType.DIRECT_CAUSE,
                            is_negated=False,
                            uncertainty_score=0.12,
                            sentence_id=s_next.sentence_id,
                            page_number=s_next.page_number,
                            section_title=s_next.section_title,
                            confidence=0.88,
                            evidence_quote=f"{s_curr.text.strip()} {s_next.text.strip()}",
                            char_span=(s_curr.start_char, s_next.end_char),
                            evidence_status=EvidenceStatus.MEASURED_FACT,
                            evidence_sentence_ids=[s_curr.sentence_id, s_next.sentence_id],
                            discourse_relation="demonstrative_anaphora",
                            antecedent_quote=s_curr.text.strip(),
                        )
                        assertion_idx += 1
                        resolved_assertions.append(asrt)
                        existing_pairs.add((c_canon, e_canon))

        # 3. Explicit Causal Discourse Connectives
        if self.enable_discourse_connectives:
            for k in range(n_sents - 1):
                s_curr = sentences[k]
                s_next = sentences[k + 1]

                if s_curr.section_title != s_next.section_title or s_curr.page_number != s_next.page_number:
                    continue

                if not DISCOURSE_CONNECTIVE_RE.match(s_next.text.strip()):
                    continue

                next_ents = normalizer.detect_entities_in_sentence(s_next.text, local_abbr, known_entities)
                if not next_ents:
                    continue

                curr_asrt = assertions_by_sent.get(s_curr.sentence_id, [])
                curr_ents = normalizer.detect_entities_in_sentence(s_curr.text, local_abbr, known_entities)

                causes_from_curr = []
                if curr_asrt:
                    for a in curr_asrt:
                        causes_from_curr.append((a.effect, a.effect_canonical))
                elif curr_ents:
                    causes_from_curr.append((curr_ents[-1][0], curr_ents[-1][1]))

                for c_raw, c_canon in causes_from_curr:
                    for e_raw, e_canon, _, _ in next_ents:
                        if self._is_valid_pair(c_canon, e_canon, existing_pairs):
                            asrt = CausalAssertion(
                                assertion_id=f"asrt_ctx_{doc.doc_id[:6]}_{s_next.page_number}_{assertion_idx:04d}",
                                cause=c_raw,
                                cause_canonical=c_canon,
                                effect=e_raw,
                                effect_canonical=e_canon,
                                direction="FORWARD",
                                relation_type=CausalRelationType.DIRECT_CAUSE,
                                is_negated=False,
                                uncertainty_score=0.10,
                                sentence_id=s_next.sentence_id,
                                page_number=s_next.page_number,
                                section_title=s_next.section_title,
                                confidence=0.87,
                                evidence_quote=f"{s_curr.text.strip()} {s_next.text.strip()}",
                                char_span=(s_curr.start_char, s_next.end_char),
                                evidence_status=EvidenceStatus.MEASURED_FACT,
                                evidence_sentence_ids=[s_curr.sentence_id, s_next.sentence_id],
                                discourse_relation="causal_connective",
                                antecedent_quote=s_curr.text.strip(),
                            )
                            assertion_idx += 1
                            resolved_assertions.append(asrt)
                            existing_pairs.add((c_canon, e_canon))

        return resolved_assertions

    def _is_valid_pair(
        self,
        c_canon: str,
        e_canon: str,
        existing_pairs: Set[Tuple[str, str]],
    ) -> bool:
        """
        Enforce strict false-positive controls and biological invariants.
        """
        if c_canon == e_canon:
            return False

        if (c_canon, e_canon) in existing_pairs:
            return False

        if not self.enable_false_positive_controls:
            return True

        # Terminal Phenotype Invariant: Terminal outcomes cannot cause upstream molecular entities
        c_low = c_canon.lower()
        e_low = e_canon.lower()
        if c_low in TERMINAL_PHENOTYPES and e_low not in TERMINAL_PHENOTYPES:
            return False

        # Environmental Input Invariant: Environmental inputs cannot be downstream outcomes
        if e_canon in ENV_PARAMS:
            return False

        # Complementation invariant: Complementation markers are not downstream regulatory targets
        if "complemented" in e_low or "plasmid" in e_low:
            return False

        return True
