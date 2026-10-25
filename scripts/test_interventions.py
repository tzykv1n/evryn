#!/usr/bin/env python3
"""
Controlled ablation tests for Phase 1.8 extraction improvements.
Tests each intervention independently and in combination on Train (4) and Dev (8).
"""

import os
import sys
import re
import json
from typing import Dict, Any, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from evryn.paper.extractor import (
    PaperCausalExtractor,
    CausalRelationType,
    COMPILED_PASSIVE_INDICATORS,
    COMPILED_INHIBITION_PATTERNS,
    COMPILED_ACTIVATION_PATTERNS,
    COMPILED_MEDIATION_PATTERNS,
    COMPILED_ASSOCIATION_PATTERNS,
    COORDINATING_BOUNDARY_RE,
    BY_MEANS_RE,
    ACTIVATION_PATTERNS,
    INHIBITION_PATTERNS,
    CAUSAL_INFLUENCE_PATTERNS,
)
from evryn.paper.types import CausalAssertion, EvidenceStatus
import importlib.util

spec = importlib.util.spec_from_file_location("eval_splits", os.path.join(REPO_ROOT, "scripts", "evaluate_phase2_splits.py"))
eval_splits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_splits)

ACTIVE_MATRIX_CAUSATIVE_VERBS = re.compile(
    r"\b(?:causes?|caused|causing|leads?\s+to|led\s+to|leading\s+to|results?\s+in|resulted\s+in|resulting\s+in|"
    r"induces?|induced|inducing|activates?|activated|activating|promotes?|promoted|promoting|"
    r"stimulates?|stimulated|stimulating|represses?|repressed|repressing|inhibits?|inhibited|inhibiting|"
    r"downregulates?|downregulated|downregulating|upregulates?|upregulated|upregulating|"
    r"triggers?|triggered|triggering)\b",
    re.IGNORECASE,
)

SUBORDINATE_PREP_MODIFIERS = re.compile(
    r"\b(?:under\s+(?:the\s+)?(?:control|regulation)\s+of|in\s+response\s+to|responsive\s+to|"
    r"following\s+(?:treatment|stimulation|exposure|activation|addition)\s+(?:with|to|of)|"
    r"as\s+a\s+(?:result|consequence)\s+of)\b",
    re.IGNORECASE,
)

COMPILED_GENETICS_MUTANT_UP_EXP = re.compile(
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*"
    r"(?:upregulated|increased|elevated|higher|induced|activated|derepressed|enhanced|augmented|greater|promoted|hyper-?induced|hyper-?activated|accumulated|over-?expressed)\s*"
    r"(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
    re.IGNORECASE,
)

COMPILED_GENETICS_MUTANT_DOWN_EXP = re.compile(
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*"
    r"(?:downregulated|reduced|repressed|decreased|attenuated|lower|diminished|abolished|lost|eliminated|less|suppressed|inhibited|impaired|defective|lacking)\s*"
    r"(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
    re.IGNORECASE,
)

COMPILED_GENETICS_MUTANT_DEFECT = re.compile(
    r"\b(?:mutant|mutation|null|deletion|deficiency)\b(?:\s+\w+){0,6}\s+(?:showed|exhibited|displayed|caused|led\s+to|resulted\s+in)\s+(?:a\s+)?(?:defect|impairment|loss|reduction)\s+in\s+",
    re.IGNORECASE,
)

FORWARD_CONNECTIVE_RE = re.compile(r"\b(?:and\s+)?(?:thus|thereby|hence)\b", re.IGNORECASE)
ANTI_FACTOR_RE = re.compile(r"\b(?:from\s+(?:its\s+)?(?:[a-z-]+\s+){0,3}anti-(?:sigma\s+)?factor|anti-sigma\s+factor\s*,?\s*)\b", re.IGNORECASE)

EXPANDED_ACTIVATION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in ACTIVATION_PATTERNS
] + [
    re.compile(r"\b(?:plays?\s+(?:an?\s+)?(?:primary|key|crucial|essential|major|critical|central|important|pivotal|significant)?\s*role\s+in\s+(?:(?:the\s+)?(?:activation|induction|expression|regulation|stimulation|control)\s+of|(?:regulating|controlling|activating|inducing|promoting|stimulating)))\b", re.IGNORECASE),
    re.compile(r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:involved\s+in|implicated\s+in|participates?\s+in)\s+(?:(?:the\s+)?(?:fine-tuning|regulation|control|modulation|expression|activation|induction)\s+(?:of\s+)?|(?:fine-tuning|regulating|controlling|modulating|activating|inducing|promoting))\b", re.IGNORECASE),
]

EXPANDED_INHIBITION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in INHIBITION_PATTERNS
] + [
    re.compile(r"\b(?:plays?\s+(?:an?\s+)?(?:primary|key|crucial|essential|major|critical|central|important|pivotal|significant)?\s*role\s+in\s+(?:(?:the\s+)?(?:repression|inhibition|suppression)\s+of|(?:repressing|inhibiting|suppressing)))\b", re.IGNORECASE),
]

COMPILED_CAUSAL_INFLUENCE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CAUSAL_INFLUENCE_PATTERNS]

INDIRECT_MODIFIER_RE = re.compile(r"\b(?:indirectly|indirect)\b", re.IGNORECASE)
ENCODED_WITHIN_LOCUS_RE = re.compile(r"\b(?:encoded\s+within|encoded\s+by)\s+(?:the\s+)?(?:pathogenicity\s+island|island|operon|cluster|spi\s*[-0-9]*)\b", re.IGNORECASE)

class Phase18Extractor(PaperCausalExtractor):
    def __init__(
        self,
        enable_active_precedence: bool = True,
        enable_expanded_genetics: bool = True,
        enable_expanded_triggers: bool = True,
        enable_indirect_filter: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.enable_active_precedence = enable_active_precedence
        self.enable_expanded_genetics = enable_expanded_genetics
        self.enable_expanded_triggers_phase18 = enable_expanded_triggers
        self.enable_indirect_filter = enable_indirect_filter

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

        # Reject relations crossing coordinating boundaries without a causative bridge
        if COORDINATING_BOUNDARY_RE.search(between_text):
            return None

        # Reject genomic locus encoding as causal edge
        if ENCODED_WITHIN_LOCUS_RE.search(between_text):
            return None

        # Check for means clauses: e.g. "represses hilA by inhibiting HilD"
        m_means = BY_MEANS_RE.search(between_text)
        if m_means:
            is_inhib = bool(re.search(r"\b(?:inhibiting|repressing|suppressing|blocking|reducing)\b", m_means.group(0), re.IGNORECASE))
            rel = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return rel, inv_dir, 0.91

        # Intervention 2: Expanded genetics mutant syntax
        mut_down = COMPILED_GENETICS_MUTANT_DOWN_EXP if self.enable_expanded_genetics else re.compile(
            r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*(?:downregulated|reduced|repressed|decreased|attenuated|lower|diminished|abolished|lost|eliminated)\s*(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
            re.IGNORECASE,
        )
        mut_up = COMPILED_GENETICS_MUTANT_UP_EXP if self.enable_expanded_genetics else re.compile(
            r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*(?:upregulated|increased|elevated|higher|induced|activated|derepressed)\s*(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
            re.IGNORECASE,
        )

        if mut_down.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.UPREGULATES, inv_dir, 0.93

        if mut_up.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.DOWNREGULATES, inv_dir, 0.93

        if self.enable_expanded_genetics and COMPILED_GENETICS_MUTANT_DEFECT.search(between_text):
            return CausalRelationType.UPREGULATES, direction, 0.93

        # Anti-factor release
        if self.enable_expanded_triggers_phase18 and ANTI_FACTOR_RE.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.DOWNREGULATES, inv_dir, 0.92

        # Forward connectives (and thus, and thereby)
        if self.enable_expanded_triggers_phase18 and FORWARD_CONNECTIVE_RE.search(between_text):
            return CausalRelationType.UPREGULATES, direction, 0.88

        # Intervention 1: Active Matrix Verb Precedence over Subordinate Prepositional Phrases
        m_sub = SUBORDINATE_PREP_MODIFIERS.search(between_text)
        m_act = ACTIVE_MATRIX_CAUSATIVE_VERBS.search(between_text)

        # Check Passive Indicators
        for pat_re, is_inhib in COMPILED_PASSIVE_INDICATORS:
            if not getattr(self, "enable_extended_triggers", True):
                if any(k in pat_re.pattern for k in ["requires", "promoted", "abolished"]):
                    continue
            if not getattr(self, "enable_passive_restore", True):
                if "restored" in pat_re.pattern or "rescued" in pat_re.pattern:
                    continue
            m_pass = pat_re.search(between_text)
            if m_pass:
                # If this passive match is within a subordinate modifier and an active verb is present, let active verb govern!
                if self.enable_active_precedence and m_sub and m_act:
                    if m_pass.start() >= m_sub.start() and m_pass.end() <= m_sub.end():
                        continue

                rel = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
                return rel, inv_dir, 0.92

        # Check Active Patterns
        inhib_pats = EXPANDED_INHIBITION_PATTERNS if self.enable_expanded_triggers_phase18 else COMPILED_INHIBITION_PATTERNS
        for pat_re in inhib_pats:
            if not getattr(self, "enable_extended_triggers", True):
                if "abolish" in pat_re.pattern:
                    continue
            if pat_re.search(between_text):
                return CausalRelationType.DOWNREGULATES, direction, 0.90

        activ_pats = EXPANDED_ACTIVATION_PATTERNS if self.enable_expanded_triggers_phase18 else COMPILED_ACTIVATION_PATTERNS
        for pat_re in activ_pats:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for pat_re in COMPILED_CAUSAL_INFLUENCE_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for pat_re in COMPILED_MEDIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.MEDIATES, direction, 0.85

        for pat_re in COMPILED_ASSOCIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.ASSOCIATED, direction, 0.80

        return None

def test_run(name, extractor):
    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ingester = eval_splits.PMCOAIngester(cache_dir=os.path.join(REPO_ROOT, "data", "real_papers", "xml"))
    evaluator = eval_splits.PaperBenchmarkEvaluator()
    evaluator.extractor = extractor
    biocause = eval_splits.BioCauseDataset().load()

    papers_by_split: Dict[str, List[Dict[str, Any]]] = {}
    for p in manifest["papers"]:
        s = p["split"]
        papers_by_split.setdefault(s, []).append(p)

    print(f"\n==================== {name} ====================")
    for s_name in ["train", "dev"]:
        papers = papers_by_split.get(s_name, [])
        split_res = eval_splits.evaluate_split(s_name, papers, evaluator, ingester, biocause, version="v2")
        m = split_res["macro_metrics"]
        print(f"[{s_name.upper()}] Direct F1: {m['direct_f1_mean']:.4f} [CI: {m['direct_f1_ci'][0]:.4f}, {m['direct_f1_ci'][1]:.4f}] | Cross F1: {m['cross_f1_mean']:.4f} | Struct: {m['structural_match_mean']:.4f}")
        for p in split_res["per_paper"]:
            print(f"    {p['pmcid']}: TP={p['tp_direct']} FP={p['fp_direct']} FN={p['fn_direct']} P={p['direct_precision']:.3f} R={p['direct_recall']:.3f} F1={p['direct_f1']:.3f}")

if __name__ == "__main__":
    # Test Baseline
    test_run("E0: BASELINE (HEAD a85a81a)", PaperCausalExtractor())

    # Test E1: Active Matrix Precedence
    test_run("E1: ACTIVE MATRIX PRECEDENCE", Phase18Extractor(
        enable_active_precedence=True,
        enable_expanded_genetics=False,
        enable_expanded_triggers=False,
    ))

    # Test E2: Expanded Genetics
    test_run("E2: EXPANDED GENETICS", Phase18Extractor(
        enable_active_precedence=False,
        enable_expanded_genetics=True,
        enable_expanded_triggers=False,
    ))

    # Test E3: Expanded Triggers
    test_run("E3: EXPANDED TRIGGERS", Phase18Extractor(
        enable_active_precedence=False,
        enable_expanded_genetics=False,
        enable_expanded_triggers=True,
    ))

    # Test E4: Full Phase 1.8 Combination (E1 + E2 + E3)
    test_run("E4: FULL COMBINATION", Phase18Extractor(
        enable_active_precedence=True,
        enable_expanded_genetics=True,
        enable_expanded_triggers=True,
    ))
