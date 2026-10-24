# evryn paper environmental_extractor
# Targeted extraction component for physical/environmental parameter changes

import re
from typing import List, Dict, Any, Optional, Tuple, Set

from .types import (
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
    SentenceSpan,
)
from .normalizer import PaperEntityNormalizer


ENV_PARAM_TERMS: Dict[str, str] = {
    "temperature": "Temperature",
    "temperatures": "Temperature",
    "temperature shift": "Temperature",
    "temperature-shift": "Temperature",
    "low temperature": "Temperature",
    "high temperature": "Temperature",
    "ambient temperature": "Temperature",
    "thermal": "Temperature",
    "heat": "Temperature",
    "cold": "Temperature",
    "acid ph": "Acid pH",
    "acidic ph": "Acid pH",
    "low ph": "Acid pH",
    "hypoxia": "Hypoxia",
    "normoxia": "Normoxia",
}

ENV_METHOD_EXCLUDE_RE = re.compile(
    r"\b(?:centrifuged|incubated|resuspended|diluted|washed|fixed|injected|shaken|maintained|stored|frozen|autoclaved|harvested|pelleted|dissolved|recorded|grown|cultured|optical\s+density|reading\s+frame)\b",
    re.IGNORECASE,
)

ENV_FORWARD_SHIFT_RE = re.compile(
    r"\b(?:"
    r"(?P<env>temperature|thermal|heat|cold|acid\s+pH|low\s+pH|pH)\b"
    r"(?:-shift|\s+shift|\s+transition|\s+increase|\s+elevation|\s+change|\s+shock)?"
    r"(?:\s*(?:from\s+[^,]+)?\s*(?:to\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?|\s*to\s+[0-9]+(?:\.[0-9]+)?))?"
    r"|"
    r"(?:a\s+)?shift\s+from\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?\s+to\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?"
    r"|"
    r"(?:when\s+(?:the\s+)?temperature\s+was\s+(?:raised|increased|shifted|elevated|lowered)\s+to\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?)"
    r"|"
    r"(?:increasing|raising|elevating|shifting|lowering|decreasing)\s+(?:the\s+)?(?:temperature|pH)\s*(?:from\s+[^,]+)?\s*(?:to\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?|\s*to\s+[0-9]+(?:\.[0-9]+)?)?"
    r")\s*"
    r"(?:,\s*which\s+[^,]+,\s*)?"
    r"(?:\s+(?:directly|specifically|rapidly|substantially|significantly))?"
    r"(?:,\s*(?:[A-Za-z0-9_-]+\s+)?(?:expression|levels?|transcription)?\s*)?"
    r"\s*(?P<trigger>induces?|induced|inducing|triggers?|triggered|triggering|promotes?|promoted|promoting|stimulates?|stimulated|stimulating|activates?|activated|activating|upregulates?|upregulated|upregulating|causes?|caused|causing|increases?|increased|increasing|represses?|repressed|repressing|suppresses?|suppressed|suppressing|reduces?|reduced|reducing|downregulates?|downregulated|downregulating|leads?\s+to|results?\s+in)\b",
    re.IGNORECASE,
)

ENV_PASSIVE_INDUCED_BY_RE = re.compile(
    r"\b(?P<trigger>induced|activated|triggered|stimulated|upregulated|repressed|suppressed|downregulated|inhibited|controlled|regulated)\s+(?:\w+\s+)?by\s+(?:a\s+)?(?P<env>temperature\s+shift|shift\s+in\s+temperature|temperature|low\s+temperature|high\s+temperature|elevated\s+temperature|acid\s+pH|low\s+pH|acidic\s+pH)\b",
    re.IGNORECASE,
)

ENV_COMPOUND_ADJ_RE = re.compile(
    r"\b(?P<env>temperature|heat-shock|cold-shock|acid|low-pH|pH)(?:-shift)?-(?P<trigger>induced|activated|regulated|stimulated|repressed|suppressed)\b",
    re.IGNORECASE,
)

ENV_IN_RESPONSE_TO_RE = re.compile(
    r"\b(?P<trigger>activates?|activated|activating|activation|induces?|induced|inducing|induction|upregulates?|upregulated|upregulating|upregulation|stimulates?|stimulated|stimulating|stimulation)\b"
    r".{1,60}?\b(?:in\s+response\s+to|upon|under)\s+(?P<env>temperature\s+shift|acid\s+pH|low\s+pH|acidic\s+pH|elevated\s+temperature|low\s+temperature|temperatures?\s+(?:below|above)\s+[0-9]+°?[CF]?)\b",
    re.IGNORECASE,
)

ENV_DIFF_COMPARISON_RE = re.compile(
    r"\b(?P<trigger>upregulated|downregulated|expressed|induced|higher|lower|elevated|reduced)\s+at\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?\s*(?:compared\s+(?:to|with)\s+[0-9]+(?:\.[0-9]+)?\s*°?[CF]?)?\b",
    re.IGNORECASE,
)


class EnvironmentalParameterExtractor:
    """Extracts bounded physical and environmental parameter-change causal relations."""

    def __init__(self, normalizer: Optional[PaperEntityNormalizer] = None):
        self.normalizer = normalizer or PaperEntityNormalizer()

    def extract_environmental_assertions(
        self,
        sent: SentenceSpan,
        doc_id: str,
        start_idx: int,
        seen_keys: Set[Tuple[str, str, str]],
        local_abbr: Optional[Dict[str, str]] = None,
        known_entities: Optional[List[str]] = None,
        allowed_variables: Optional[Set[str]] = None,
    ) -> Tuple[List[CausalAssertion], int]:
        assertions: List[CausalAssertion] = []
        assertion_idx = start_idx
        text = sent.text.strip()
        tl = text.lower()

        # Check if sentence mentions any environmental parameter
        env_mentions = [
            term for term in ENV_PARAM_TERMS.keys()
            if term in tl or ("°c" in tl and "temperature" in ENV_PARAM_TERMS)
        ]
        if not env_mentions:
            return assertions, assertion_idx

        # Check adversarial method filter
        if ENV_METHOD_EXCLUDE_RE.search(text):
            # Only allow if there is an explicit biological causal trigger present
            if not any(k in tl for k in ["induces", "induced", "upregulated", "increased", "suppressed", "stimulates"]):
                return assertions, assertion_idx

        entities = self.normalizer.detect_entities_in_sentence(
            text, local_abbr_map=local_abbr, known_entities=known_entities
        )
        if not entities:
            return assertions, assertion_idx

        # Identify environmental entities and biological outcome targets
        env_entities = []
        target_entities = []
        ENV_CANON_SET = {"Temperature", "Acid pH", "Hypoxia", "Normoxia"}

        for ent in entities:
            raw, canon, s, e = ent
            if canon in ENV_CANON_SET:
                # Check variable ablation filter
                var_type = "temperature" if canon == "Temperature" else ("ph" if canon == "Acid pH" else "oxygen")
                if allowed_variables is not None and var_type not in allowed_variables:
                    continue
                env_entities.append(ent)
            else:
                target_entities.append(ent)

        if not env_entities or not target_entities:
            return assertions, assertion_idx

        is_negated = any(re.search(p, text, re.IGNORECASE) for p in [
            r"\b(?:did\s+not|does\s+not|do\s+not)\b",
            r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\b",
            r"\bfailed\s+to\b",
            r"\bnot\s+induced\b",
        ])

        for e_raw, e_canon, s_e, e_e in env_entities:
            for t_raw, t_canon, s_t, e_t in target_entities:
                if e_canon == t_canon:
                    continue

                rel_type: Optional[CausalRelationType] = None
                matched_pattern = False

                m_fwd = ENV_FORWARD_SHIFT_RE.search(text)
                m_pas = ENV_PASSIVE_INDUCED_BY_RE.search(text)
                m_resp = ENV_IN_RESPONSE_TO_RE.search(text)
                m_adj = ENV_COMPOUND_ADJ_RE.search(text)
                m_diff = ENV_DIFF_COMPARISON_RE.search(text)

                # Case 1: Forward Shift (e.g., temperature shift to 37°C induces virulence)
                if m_fwd:
                    if (abs(s_e - m_fwd.start()) < 35 or m_fwd.start() <= s_e <= m_fwd.end()) and (
                        m_fwd.start() <= s_t <= m_fwd.end() or (m_fwd.end() <= s_t <= m_fwd.end() + 80)
                    ):
                        trig = m_fwd.group("trigger").lower()
                        is_inhib = any(w in trig for w in ["repress", "suppress", "reduce", "downreg"])
                        rel_type = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                        matched_pattern = True

                # Case 2: Passive / Induced by (e.g., virulence factors are induced by temperature shift)
                if not matched_pattern and m_pas:
                    if (abs(s_e - m_pas.end()) < 40 or m_pas.start() <= s_e <= m_pas.end() + 40) and (
                        s_t < m_pas.start() and m_pas.start() - e_t < 80
                    ):
                        trig = m_pas.group("trigger").lower()
                        is_inhib = any(w in trig for w in ["repress", "suppress", "downreg", "inhibit"])
                        rel_type = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                        matched_pattern = True

                # Case 3: In Response To (e.g., activates PmrA in response to acid pH)
                if not matched_pattern and m_resp:
                    if (abs(s_e - m_resp.end()) < 40 or m_resp.start() <= s_e <= m_resp.end() + 30) and (
                        s_t <= m_resp.end() and m_resp.start() - 30 <= s_t
                    ):
                        trig = m_resp.group("trigger").lower()
                        is_inhib = any(w in trig for w in ["repress", "suppress", "downreg", "inhibit"])
                        rel_type = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                        matched_pattern = True

                # Case 4: Compound Adjective Modifier (e.g. temperature-induced virulence)
                if not matched_pattern and m_adj:
                    if abs(s_e - m_adj.start()) < 20 and m_adj.end() <= s_t <= m_adj.end() + 50:
                        trig = m_adj.group("trigger").lower()
                        is_inhib = any(w in trig for w in ["repress", "suppress"])
                        rel_type = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                        matched_pattern = True

                # Case 5: Differential comparison (e.g., yfe was upregulated at 37°C)
                if not matched_pattern and m_diff:
                    if (abs(s_e - m_diff.start()) < 50 or m_diff.start() <= s_e <= m_diff.end() + 30) and (
                        s_t < m_diff.start() and m_diff.start() - e_t < 80
                    ):
                        trig = m_diff.group("trigger").lower()
                        is_inhib = any(w in trig for w in ["downreg", "lower", "reduced"])
                        rel_type = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                        matched_pattern = True

                if not matched_pattern or rel_type is None:
                    continue

                dedup_key = (e_canon, t_canon, sent.sentence_id)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                assertion_id = f"asrt_env_{doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                assertion_idx += 1

                assertions.append(
                    CausalAssertion(
                        assertion_id=assertion_id,
                        cause=e_raw,
                        cause_canonical=e_canon,
                        effect=t_raw,
                        effect_canonical=t_canon,
                        direction="FORWARD",
                        relation_type=rel_type,
                        is_negated=is_negated,
                        uncertainty_score=0.10,
                        sentence_id=sent.sentence_id,
                        page_number=sent.page_number,
                        section_title=sent.section_title,
                        confidence=0.92,
                        evidence_quote=text,
                        char_span=(sent.start_char, sent.end_char),
                        evidence_status=EvidenceStatus.REFUTED_NEGATION if is_negated else EvidenceStatus.MEASURED_FACT,
                    )
                )

        return assertions, assertion_idx
