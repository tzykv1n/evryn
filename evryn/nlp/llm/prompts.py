"""
Version-Controlled Extraction Prompts and Adversarial In-Context Examples for EVRYN Phase 2.2.
"""

from typing import Dict, Any, List

PROMPT_VERSION = "v2.2.0"

SYSTEM_PROMPT = """You are EVRYN, a precision scientific causal extraction system for peer-reviewed biomedical literature.
Your task is to extract only verified, direct causal relationships between entities that are explicitly supported by the supplied scientific text.

CRITICAL EXTRACTION RULES:
1. STRICT TEXTUAL GROUNDING: Extract ONLY relationships where the cause, effect, and causal mechanism are directly stated in the text. DO NOT extrapolate or use external world knowledge to connect unlinked concepts.
2. VERBATIM EVIDENCE: You MUST extract the exact verbatim sentence substring supporting the causal claim. Never paraphrase or rewrite the evidence.
3. CAUSAL DIRECTIONALITY: Carefully distinguish the Cause (the regulator, trigger, or upstream perturbation) from the Effect (the outcome, target gene, phenotype, or downstream response).
   - In passive constructions ("Y is induced by X"), X is Cause, Y is Effect.
   - In loss-of-function phenotypes ("mutation in X abolished Y"), wild-type X is Cause promoting Y.
4. COORDINATED AND MULTI-CLAUSE CAUSES:
   - "Requires both A and B to activate C": Output two separate relations: (A -> C) and (B -> C).
   - "A activates B, which subsequently represses C": Output two separate chained relations: (A -> B, UPREGULATES) and (B -> C, DOWNREGULATES). DO NOT output a direct (A -> C) shortcut unless explicitly stated.
5. NEGATION AND SPECULATION:
   - If a claim is negated ("X does not activate Y"), set polarity to "NEGATIVE" and note negation.
   - If a claim is speculative ("X might regulate Y", "We hypothesize that X affects Y"), classify modality as "SPECULATIVE".
6. DISCRIMINATE CAUSATION FROM CORRELATION & CO-OCCURRENCE:
   - DO NOT extract relations from co-occurrence in citations ("as seen in Smith et al., 2004").
   - DO NOT extract relations from mere statistical correlation or co-expression without causal language ("X correlated with Y").
   - DO NOT extract relations from physical proximity or protein-protein complex composition unless a causal or regulatory consequence is asserted.
7. RELATION TYPES:
   - DIRECT_CAUSE: General direct causal action.
   - UPREGULATES: Activation, induction, stimulation, enhancement, phosphorylation leading to activity.
   - DOWNREGULATES: Inhibition, repression, suppression, degradation, attenuation.
   - PREVENTS: Blocking or preventing an outcome/phenotype.
   - MEDIATES: Acting as an intermediate mechanism or pathway.
8. RETURN VALID JSON ONLY: Return an array of extracted relations adhering strictly to the JSON schema. If no causal relation is explicitly stated, return an empty array `[]`. Do not include conversational remarks or explanations outside the JSON.
"""

USER_PROMPT_TEMPLATE = """Document ID: {doc_id}
Available Canonical Entities in Paper (for normalization when applicable):
{canonical_entities}

Passage Text (Page {page_number}, Section: {section_title}):
\"\"\"
{text}
\"\"\"

Extract all causal relationships from this passage strictly conforming to the JSON schema:
[
  {{
    "cause_entity": "Exact canonical cause entity name",
    "effect_entity": "Exact canonical effect entity name",
    "relation_type": "DIRECT_CAUSE | UPREGULATES | DOWNREGULATES | PREVENTS | MEDIATES",
    "polarity": "POSITIVE | NEGATIVE",
    "modality": "FACTUAL | HYPOTHETICAL | SPECULATIVE | EXPERIMENTAL_OBSERVATION",
    "evidence_text": "Exact verbatim quote from the text",
    "confidence": 0.0 to 1.0
  }}
]
"""

# Adversarial few-shot examples for calibration
ADVERSARIAL_EXAMPLES = [
    {
        "input": "We tested whether protein kinase A might regulate transcription of gene B, but observed no significant change in expression.",
        "explanation": "Hypothesis tested with negative outcome; must NOT extract positive activation.",
        "expected_output": [],
    },
    {
        "input": "Levels of both PmrA and PhoP were elevated during stationary phase growth as previously described (Groisman et al., 1999).",
        "explanation": "Co-occurrence in citation without causal assertion; must return empty.",
        "expected_output": [],
    },
    {
        "input": "Wild-type Salmonella grown at pH 5.8 were > 100,000-fold more resistant to polymyxin B than organisms grown at pH 7.7.",
        "explanation": "Contrastive environmental condition asserting acid pH promotes polymyxin B resistance.",
        "expected_output": [
            {
                "cause_entity": "Acid pH",
                "effect_entity": "Polymyxin B",
                "relation_type": "UPREGULATES",
                "polarity": "POSITIVE",
                "modality": "EXPERIMENTAL_OBSERVATION",
                "evidence_text": "Wild-type Salmonella grown at pH 5.8 were > 100,000-fold more resistant to polymyxin B than organisms grown at pH 7.7.",
                "confidence": 0.95,
            }
        ],
    },
    {
        "input": "This activation requires both PmrA's cognate sensor kinase PmrB and PmrA's post-translational activator PmrD.",
        "explanation": "Coordinated requirements; must emit two distinct relations to PmrA.",
        "expected_output": [
            {
                "cause_entity": "PmrB",
                "effect_entity": "PmrA",
                "relation_type": "UPREGULATES",
                "polarity": "POSITIVE",
                "modality": "FACTUAL",
                "evidence_text": "This activation requires both PmrA's cognate sensor kinase PmrB and PmrA's post-translational activator PmrD.",
                "confidence": 0.95,
            },
            {
                "cause_entity": "PmrD",
                "effect_entity": "PmrA",
                "relation_type": "UPREGULATES",
                "polarity": "POSITIVE",
                "modality": "FACTUAL",
                "evidence_text": "This activation requires both PmrA's cognate sensor kinase PmrB and PmrA's post-translational activator PmrD.",
                "confidence": 0.95,
            },
        ],
    },
    {
        "input": "Apoptosis was significantly inhibited by sustained treatment with compound C.",
        "explanation": "Passive construction: compound C is Cause, Apoptosis is Effect; DOWNREGULATES.",
        "expected_output": [
            {
                "cause_entity": "compound C",
                "effect_entity": "Apoptosis",
                "relation_type": "DOWNREGULATES",
                "polarity": "NEGATIVE",
                "modality": "EXPERIMENTAL_OBSERVATION",
                "evidence_text": "Apoptosis was significantly inhibited by sustained treatment with compound C.",
                "confidence": 0.90,
            }
        ],
    },
]
