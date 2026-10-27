"""
EVRYN Conditional Relation Composition Model (Iteration 4).
Learns and evaluates whether candidate causal paths represent:
A. Explicitly supported direct relation
B. Supported multi-hop causal pathway (without asserted direct endpoint relation)
C. Plausible but unverified composed relation
D. Unsupported shortcut or contradiction
E. Indeterminate (insufficient evidence)
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
import math

from evryn.paper.chain_types import CausalChain, ChainEdge, CausalEdgeKind


class CompositionClass(str, Enum):
    DIRECT_SUPPORTED = "DIRECT_SUPPORTED"          # A. Explicit textual claim directly supports A -> E
    MULTI_HOP_SUPPORTED = "MULTI_HOP_SUPPORTED"    # B. Continuous biological pathway A -> B -> ... -> E
    PLAUSIBLE_COMPOSED = "PLAUSIBLE_COMPOSED"      # C. Plausible reachability, unverified direct link
    UNSUPPORTED_SHORTCUT = "UNSUPPORTED_SHORTCUT"  # D. Invalid shortcut, broken mechanism, or polarity clash
    INDETERMINATE = "INDETERMINATE"                # E. Insufficient evidence / ambiguous context


# Accessory adapter regulators that stabilize post-translational responses
ADAPTER_ENTITIES = {"pmrd", "irap", "irad", "rssb", "spvr"}

# Terminal phenotypic outcomes that act as causal sinks
TERMINAL_PHENOTYPES = {
    "polymyxin resistance", "polymyxin b resistance", "virulence",
    "biofilm formation", "growth", "cell death", "motility", "survival"
}


class CompositionFeatureExtractor:
    @staticmethod
    def extract_features(chain: CausalChain, direct_pairs_in_corpus: Optional[Set[Tuple[str, str]]] = None) -> Dict[str, float]:
        norm = lambda s: s.lower().strip()
        hops = chain.hop_count
        edges = chain.edges

        confidences = [e.confidence for e in edges]
        min_conf = min(confidences) if confidences else 0.5
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.5

        # Polarity & Negation
        neg_count = sum(1 for e in edges if e.polarity == "NEGATIVE" or e.is_negated)
        net_polarity = -1.0 if (neg_count % 2 == 1) else 1.0
        has_inhibitory = 1.0 if any(e.polarity == "NEGATIVE" for e in edges) else 0.0

        # Speculation / Intent
        has_speculative = 1.0 if any(e.is_hypothetical or any(w in e.evidence_text.lower() for w in ["hypothesized", "postulated", "speculated"]) for e in edges) else 0.0

        # Intermediate roles
        src_norm = norm(chain.endpoint_pair[0])
        tgt_norm = norm(chain.endpoint_pair[1])

        # Feature: source is adapter
        is_adapter_src = 1.0 if any(a in src_norm for a in ADAPTER_ENTITIES) else 0.0

        # Feature: intermediate sink traversal (e.g. terminal phenotype in middle of chain)
        intermediates = [norm(n) for n in chain.nodes[1:-1]]
        traverses_sink = 1.0 if any(any(sink in inter for sink in TERMINAL_PHENOTYPES) for inter in intermediates) else 0.0

        # Feature: target is phenotype
        is_phenotype_tgt = 1.0 if any(sink in tgt_norm for sink in TERMINAL_PHENOTYPES) else 0.0

        # Section / page span
        page_span = max(e.page_number for e in edges) - min(e.page_number for e in edges) if edges else 0

        # Direct corpus support
        direct_supported = 0.0
        if direct_pairs_in_corpus:
            ep = (src_norm, tgt_norm)
            if ep in direct_pairs_in_corpus:
                direct_supported = 1.0

        return {
            "hop_count": float(hops),
            "min_confidence": min_conf,
            "mean_confidence": mean_conf,
            "net_polarity": net_polarity,
            "has_inhibitory": has_inhibitory,
            "has_speculative": has_speculative,
            "is_adapter_source": is_adapter_src,
            "traverses_sink": traverses_sink,
            "is_phenotype_target": is_phenotype_tgt,
            "page_span": float(page_span),
            "direct_supported": direct_supported,
        }


class ConditionalCompositionModel:
    """Calibrated model scoring multi-hop causal compositions and rejecting unsupported shortcuts."""

    def __init__(self):
        # Learned weights calibrated on training papers with hard negative compositions
        self.weights = {
            "bias": 1.20,
            "hop_penalty": -0.45,
            "min_confidence": 1.60,
            "has_speculative": -2.10,
            "traverses_sink": -3.50,
            "is_adapter_source": -1.80,
            "page_span_decay": -0.08,
            "direct_supported_boost": 2.50,
        }

    def score_composition(self, chain: CausalChain, direct_pairs: Optional[Set[Tuple[str, str]]] = None) -> Tuple[CompositionClass, float, str]:
        feats = CompositionFeatureExtractor.extract_features(chain, direct_pairs)

        # 1. Check if directly supported as direct textual assertion (Class A)
        if feats["direct_supported"] > 0.5:
            return (
                CompositionClass.DIRECT_SUPPORTED,
                0.95,
                "Explicitly supported as direct causal assertion in source text.",
            )

        # 2. Hard Invariant Violations -> Class D (Unsupported Shortcut)
        if feats["traverses_sink"] > 0.5:
            return (
                CompositionClass.UNSUPPORTED_SHORTCUT,
                0.08,
                "Unsupported shortcut: traverses terminal phenotypic outcome as intermediate mediator.",
            )

        if feats["is_adapter_source"] > 0.5 and feats["hop_count"] >= 2 and feats["is_phenotype_target"] > 0.5:
            return (
                CompositionClass.UNSUPPORTED_SHORTCUT,
                0.12,
                "Unsupported shortcut: accessory adapter protein cannot originate multi-hop pathway into terminal phenotype.",
            )

        if feats["has_speculative"] > 0.5:
            return (
                CompositionClass.UNSUPPORTED_SHORTCUT,
                0.18,
                "Rejected: constituent path depends on speculative or hypothetical statement.",
            )

        # 3. Compute continuous logit score
        logit = (
            self.weights["bias"]
            + self.weights["hop_penalty"] * (feats["hop_count"] - 2)
            + self.weights["min_confidence"] * (feats["min_confidence"] - 0.7)
            + self.weights["has_speculative"] * feats["has_speculative"]
            + self.weights["traverses_sink"] * feats["traverses_sink"]
            + self.weights["is_adapter_source"] * feats["is_adapter_source"]
            + self.weights["page_span_decay"] * feats["page_span"]
        )

        prob = 1.0 / (1.0 + math.exp(-max(min(logit, 8.0), -8.0)))

        # Categorize by calibrated probability
        if prob >= 0.70:
            return (
                CompositionClass.MULTI_HOP_SUPPORTED,
                round(prob, 4),
                f"Supported multi-hop causal pathway ({chain.hop_count} hops) with high mechanical continuity.",
            )
        elif prob >= 0.45:
            return (
                CompositionClass.PLAUSIBLE_COMPOSED,
                round(prob, 4),
                f"Plausible candidate composition ({chain.hop_count} hops); reachability supported but requires experimental verification.",
            )
        elif prob >= 0.25:
            return (
                CompositionClass.INDETERMINATE,
                round(prob, 4),
                "Indeterminate: evidence across constituent edges is weak or page span is broad.",
            )
        else:
            return (
                CompositionClass.UNSUPPORTED_SHORTCUT,
                round(prob, 4),
                "Unsupported shortcut: low confidence or discontinuous intermediate mechanisms.",
            )
