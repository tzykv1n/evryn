# evryn higher-order
# evryn -s higher-order

import numpy as np
from typing import List, Dict, Any
from .types import HigherOrderCandidate, HigherOrderCategory, HigherOrderBenchmarkResult


class HigherOrderBaselineSuite:

    def predict_baseline_a_pairwise(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderCategory]:
        preds = []
        for c in candidates:
            if c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                preds.append(HigherOrderCategory.LINGUISTIC_COORDINATION)
        return preds

    def predict_baseline_b_rule_based(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderCategory]:
        preds = []
        for c in candidates:
            s_low = c.sentence.lower()
            if any(sm in s_low for sm in ["synergistically", "jointly", "combined with"]):
                preds.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif any(jm in s_low for jm in ["and", "both", "together", "plus"]):
                preds.append(HigherOrderCategory.JOINT_CAUSE)
            elif c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                preds.append(HigherOrderCategory.LINGUISTIC_COORDINATION)
        return preds

    def predict_baseline_c_learned_nlp(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderCategory]:
        preds = []
        for c in candidates:
            s_low = c.sentence.lower()
            if any(sm in s_low for sm in ["synergistically", "jointly", "combined with", "co-infection"]):
                preds.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif ("both" in s_low or "together" in s_low) and c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.JOINT_CAUSE)
            elif any(tm in s_low.split() for tm in ["when", "while", "after", "before"]) and c.pairwise_pred == "NO_RELATION":
                preds.append(HigherOrderCategory.TEMPORAL_RELATION)
            elif c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                preds.append(HigherOrderCategory.LINGUISTIC_COORDINATION)
        return preds

    def predict_method_d_flux_evidence(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderCategory]:
        preds = []
        for c in candidates:
            syn = c.higher_order_evidence.get("pid_synergy_estimate", 0.0)
            dr2 = c.higher_order_evidence.get("delta_r2_gain", 0.0)

            if syn >= 0.75:
                preds.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif syn >= 0.50 and dr2 >= 0.35 and c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.JOINT_CAUSE)
            elif c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            elif any(tm in c.sentence.lower().split() for tm in ["when", "while", "after"]):
                preds.append(HigherOrderCategory.TEMPORAL_RELATION)
            else:
                preds.append(HigherOrderCategory.LINGUISTIC_COORDINATION)
        return preds

    def predict_method_e_full_evryn(self, candidates: List[HigherOrderCandidate]) -> List[HigherOrderCategory]:
        preds = []
        for c in candidates:
            syn = c.higher_order_evidence.get("pid_synergy_estimate", 0.0)
            invar = c.higher_order_evidence.get("invariance_score", 0.0)
            dr2 = c.higher_order_evidence.get("delta_r2_gain", 0.0)
            s_low = c.sentence.lower()

            if syn >= 0.70 and any(sm in s_low for sm in ["synergistically", "jointly", "combined with", "co-infection", "interplay"]):
                preds.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif (syn >= 0.45 or invar >= 0.75) and dr2 >= 0.25 and c.pairwise_pred != "NO_RELATION" and any(
                jm in s_low for jm in ["both", "together", "plus", "and"]
            ):
                preds.append(HigherOrderCategory.JOINT_CAUSE)
            elif any(cm in s_low for cm in ["confounded", "co-occurring"]):
                preds.append(HigherOrderCategory.CONFOUNDED)
            elif any(tm in s_low.split() for tm in ["when", "while", "after", "before"]) and c.pairwise_pred == "NO_RELATION":
                preds.append(HigherOrderCategory.TEMPORAL_RELATION)
            elif c.pairwise_pred != "NO_RELATION":
                preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                preds.append(HigherOrderCategory.LINGUISTIC_COORDINATION)
        return preds
