# python cli.py evaluate

from typing import List, Dict, Any, Optional
import numpy as np
from ..core.types import RelationExample, CausalRelationType
from ..features.tfidf_extractor import FORWARD_CONNECTIVES, BACKWARD_CONNECTIVES


class ErrorAnalyzer:

    def __init__(self, examples: List[RelationExample], y_true: np.ndarray, y_pred: np.ndarray):
        self.examples = examples
        self.y_true = y_true
        self.y_pred = y_pred

    def analyze(self) -> Dict[str, Any]:
        n = len(self.examples)
        reversals = []
        false_positives = []
        false_negatives = []
        correct_causal = []

        fp_by_raw_label: Dict[str, int] = {}
        fn_explicit = 0
        fn_implicit = 0
        temporal_confusions = 0
        negation_errors = 0
        long_distance_errors = 0
        joint_cause_candidates = []

        temporal_words = {"when", "while", "before", "after", "during", "then", "until", "since"}
        negation_words = {"not", "never", "no", "neither", "nor", "without", "hardly", "seldom"}
        joint_markers = {"and", "both", "together", "plus", "combined with", "along with", "as well as"}

        for i in range(n):
            ex = self.examples[i]
            yt = int(self.y_true[i])
            yp = int(self.y_pred[i])
            sent_lower = ex.sentence.lower()
            mid_lower = ex.middle_context.lower()
            tokens_mid = mid_lower.split()

            has_temporal = any(w in sent_lower.split() for w in temporal_words)
            has_negation = any(w in sent_lower.split() for w in negation_words)
            is_long_dist = len(tokens_mid) > 5
            has_joint_markers = any(m in sent_lower for m in joint_markers)

            has_explicit_trigger = any(c in mid_lower or c in sent_lower for c in FORWARD_CONNECTIVES + BACKWARD_CONNECTIVES)

            if yt > 0 and yp > 0 and yt != yp:
                reversals.append({
                    "id": ex.example_id,
                    "sentence": ex.sentence,
                    "true_direction": CausalRelationType(yt).name,
                    "pred_direction": CausalRelationType(yp).name,
                    "e1": ex.entity1_text,
                    "e2": ex.entity2_text,
                    "middle": ex.middle_context,
                })

            elif yt == 0 and yp > 0:
                raw = ex.raw_label.split("(")[0]
                fp_by_raw_label[raw] = fp_by_raw_label.get(raw, 0) + 1
                if has_temporal:
                    temporal_confusions += 1
                if has_negation:
                    negation_errors += 1
                if is_long_dist:
                    long_distance_errors += 1
                false_positives.append({
                    "id": ex.example_id,
                    "sentence": ex.sentence,
                    "raw_relation": ex.raw_label,
                    "pred_direction": CausalRelationType(yp).name,
                    "e1": ex.entity1_text,
                    "e2": ex.entity2_text,
                    "middle": ex.middle_context,
                })

            elif yt > 0 and yp == 0:
                if has_explicit_trigger:
                    fn_explicit += 1
                else:
                    fn_implicit += 1
                if has_negation:
                    negation_errors += 1
                if is_long_dist:
                    long_distance_errors += 1
                false_negatives.append({
                    "id": ex.example_id,
                    "sentence": ex.sentence,
                    "true_direction": CausalRelationType(yt).name,
                    "e1": ex.entity1_text,
                    "e2": ex.entity2_text,
                    "middle": ex.middle_context,
                    "is_implicit": not has_explicit_trigger,
                })

            elif yt > 0 and yp == yt:
                correct_causal.append(ex)

            if has_joint_markers and (yt > 0 or yp > 0):
                matched_jm = [m for m in joint_markers if m in sent_lower]
                matched_tm = [t for t in temporal_words if t in sent_lower]
                joint_cause_candidates.append({
                    "id": ex.example_id,
                    "sentence": ex.sentence,
                    "true_relation": CausalRelationType(yt).name,
                    "pred_relation": CausalRelationType(yp).name,
                    "e1": ex.entity1_text,
                    "e2": ex.entity2_text,
                    "e1_span": ex.entity1_span,
                    "e2_span": ex.entity2_span,
                    "middle": ex.middle_context,
                    "raw_label": ex.raw_label,
                    "joint_markers": matched_jm,
                    "temporal_markers": matched_tm,
                    "has_explicit_trigger": has_explicit_trigger,
                })

        total_errors = len(reversals) + len(false_positives) + len(false_negatives)
        return {
            "total_examples": n,
            "total_errors": total_errors,
            "reversal_count": len(reversals),
            "reversals": reversals[:5],
            "false_positive_count": len(false_positives),
            "fp_by_raw_relation": fp_by_raw_label,
            "false_negative_count": len(false_negatives),
            "fn_explicit_trigger_count": fn_explicit,
            "fn_implicit_causality_count": fn_implicit,
            "temporal_confusion_count": temporal_confusions,
            "negation_error_count": negation_errors,
            "long_distance_error_count": long_distance_errors,
            "joint_cause_candidate_count": len(joint_cause_candidates),
            "joint_cause_samples": joint_cause_candidates[:6],
            "all_joint_cause_candidates": joint_cause_candidates,
        }
