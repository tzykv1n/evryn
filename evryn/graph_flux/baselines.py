# evryn graph
# evryn -s graph

from typing import List, Dict, Any, Optional
from ..nlp.higher_order.types import HigherOrderCategory
from .types import GraphHigherOrderCandidate, CandidatePattern


class GraphFluxBaselineSuite:

    def predict_baseline_a_pairwise_only(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            has_direct = ev.get("graph_has_direct_a", 0) > 0 or ev.get("graph_has_direct_b", 0) > 0
            if has_direct:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                predictions.append(HigherOrderCategory.INSUFFICIENT_EVIDENCE)
        return predictions

    def predict_baseline_b_local_graph(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            has_both_direct = ev.get("graph_has_direct_a", 0) > 0 and ev.get("graph_has_direct_b", 0) > 0
            if has_both_direct:
                predictions.append(HigherOrderCategory.JOINT_CAUSE)
            elif ev.get("graph_has_direct_a", 0) > 0 or ev.get("graph_has_direct_b", 0) > 0:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                predictions.append(HigherOrderCategory.INSUFFICIENT_EVIDENCE)
        return predictions

    def predict_baseline_c_cross_sentence_graph(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            max_dist = ev.get("graph_max_distance", 999)
            has_mediator = ev.get("graph_has_mediator", 0) > 0
            has_both_direct = ev.get("graph_has_direct_a", 0) > 0 and ev.get("graph_has_direct_b", 0) > 0

            if has_both_direct or (has_mediator and max_dist <= 2):
                predictions.append(HigherOrderCategory.JOINT_CAUSE)
            elif max_dist <= 3:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
            else:
                predictions.append(HigherOrderCategory.INSUFFICIENT_EVIDENCE)
        return predictions

    def predict_baseline_d_graph_plus_linguistic(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            has_synergy = ev.get("ling_has_synergy", 0) > 0
            has_combo = ev.get("ling_has_combination", 0) > 0
            is_cascade = ev.get("graph_is_cascade", 0) > 0

            if is_cascade:
                predictions.append(HigherOrderCategory.CAUSAL_CASCADE)
            elif has_synergy:
                predictions.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif has_combo:
                predictions.append(HigherOrderCategory.JOINT_CAUSE)
            else:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
        return predictions

    def predict_baseline_e_graph_plus_flux(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            synergy = ev.get("flux_pid_synergy", 0.0)
            delta_r2 = ev.get("flux_delta_r2", 0.0)
            confound = ev.get("flux_confounding_score", 0.0)
            is_cascade = ev.get("graph_is_cascade", 0) > 0

            if confound > 0.50:
                predictions.append(HigherOrderCategory.CONFOUNDED)
            elif is_cascade:
                predictions.append(HigherOrderCategory.CAUSAL_CASCADE)
            elif synergy >= 0.42 and delta_r2 >= 0.25:
                predictions.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif synergy >= 0.15 and delta_r2 >= 0.08:
                predictions.append(HigherOrderCategory.JOINT_CAUSE)
            else:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
        return predictions

    def predict_baseline_f_full_graph_flux(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> List[HigherOrderCategory]:
        predictions = []
        for cand in candidates:
            ev = cand.evidence
            synergy = ev.get("flux_pid_synergy", 0.0)
            delta_r2 = ev.get("flux_delta_r2", 0.0)
            nonparam_r2 = ev.get("flux_delta_r2_nonparam", 0.0)
            confound = ev.get("flux_confounding_score", 0.0)
            temporal_ok = ev.get("graph_temporal_valid", 1.0) > 0
            is_cascade = ev.get("graph_is_cascade", 0) > 0
            has_synergy_ling = ev.get("ling_has_synergy", 0.0) > 0
            has_combo_ling = ev.get("ling_has_combination", 0.0) > 0
            has_negation = ev.get("ling_has_negation", 0.0) > 0

            effective_synergy = synergy + (0.10 if has_synergy_ling else 0.0) - (0.15 if has_negation else 0.0)
            effective_delta_r2 = max(delta_r2, nonparam_r2)

            if not temporal_ok:
                predictions.append(HigherOrderCategory.TEMPORAL_RELATION)
            elif confound > 0.45 or ev.get("graph_has_confounder", 0) > 0:
                predictions.append(HigherOrderCategory.CONFOUNDED)
            elif is_cascade:
                predictions.append(HigherOrderCategory.CAUSAL_CASCADE)
            elif effective_synergy >= 0.42 and effective_delta_r2 >= 0.25:
                predictions.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
            elif effective_synergy >= 0.15 or (has_combo_ling and effective_synergy >= 0.08):
                predictions.append(HigherOrderCategory.JOINT_CAUSE)
            else:
                predictions.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)
        return predictions
