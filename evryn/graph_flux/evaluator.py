# evryn graph
# evryn -s graph

from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from ..nlp.higher_order.types import HigherOrderCategory
from .types import (
    MultiSentenceDocument,
    GraphHigherOrderCandidate,
    GraphFluxBenchmarkResult,
    CandidatePattern,
)
from .graph_builder import DocumentGraphBuilder, DocumentCausalGraph
from .candidate_generator import CrossSentenceCandidateGenerator
from .evidence_model import GraphFluxEvidenceExtractor
from .baselines import GraphFluxBaselineSuite
from .synthetic_corpus import MultiSentenceBenchmarkGenerator


class GraphFluxEvaluator:

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.graph_builder = DocumentGraphBuilder()
        self.candidate_generator = CrossSentenceCandidateGenerator()
        self.evidence_extractor = GraphFluxEvidenceExtractor(random_state=random_state)
        self.baselines = GraphFluxBaselineSuite()

    def process_corpus(
        self, docs: List[MultiSentenceDocument]
    ) -> Tuple[List[GraphHigherOrderCandidate], float, Dict[str, Any]]:
        all_candidates: List[GraphHigherOrderCandidate] = []
        total_gt_joint = 0
        recalled_gt_joint = 0

        for doc in docs:
            graph = self.graph_builder.build_from_document(doc)
            candidates = self.candidate_generator.generate_candidates(doc, graph)

            gt_map = {}
            for gt in doc.ground_truth_higher_order:
                srcs = tuple(sorted(gt["sources"]))
                tgt = gt["target"]
                cat = HigherOrderCategory(gt["category"])
                gt_map[(srcs, tgt)] = cat
                if cat in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION):
                    total_gt_joint += 1

            for cand in candidates:
                cand_srcs = tuple(sorted(cand.sources))
                cand_key = (cand_srcs, cand.target)
                if cand_key in gt_map:
                    cand.ground_truth_category = gt_map[cand_key]
                    if cand.ground_truth_category in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION):
                        recalled_gt_joint += 1
                else:
                    is_casc, _ = graph.is_causal_cascade(cand.sources[0], cand.sources[1], cand.target)
                    is_conf = graph.find_common_confounder(cand.sources[0], cand.target) is not None
                    if is_casc:
                        cand.ground_truth_category = HigherOrderCategory.CAUSAL_CASCADE
                    elif is_conf:
                        cand.ground_truth_category = HigherOrderCategory.CONFOUNDED
                    else:
                        cand.ground_truth_category = HigherOrderCategory.PAIRWISE_DECOMPOSABLE

                self.evidence_extractor.assemble_candidate_evidence(cand, doc, graph)
                all_candidates.append(cand)

        candidate_recall = (recalled_gt_joint / max(1, total_gt_joint)) if total_gt_joint > 0 else 1.0
        stats = {
            "total_documents": len(docs),
            "total_candidates": len(all_candidates),
            "total_gt_joint": total_gt_joint,
            "recalled_gt_joint": recalled_gt_joint,
            "candidate_recall": candidate_recall,
        }
        return all_candidates, candidate_recall, stats

    def evaluate_predictions(
        self,
        y_true: List[HigherOrderCategory],
        y_pred: List[HigherOrderCategory],
        baseline_name: str,
        candidate_recall: float,
    ) -> GraphFluxBenchmarkResult:
        n = len(y_true)
        if n == 0:
            return GraphFluxBenchmarkResult(
                baseline_name=baseline_name,
                candidate_recall=candidate_recall,
                joint_precision=0.0,
                joint_recall=0.0,
                joint_f1=0.0,
                interaction_f1=0.0,
                macro_f1=0.0,
                exact_structural_match=0.0,
                false_joint_rate=0.0,
                cascade_as_joint_error_rate=0.0,
                confounder_as_joint_error_rate=0.0,
                temporal_contradiction_rate=0.0,
            )

        exact_matches = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        exact_match_rate = exact_matches / n

        tp_joint = sum(1 for yt, yp in zip(y_true, y_pred) if yt == HigherOrderCategory.JOINT_CAUSE and yp == HigherOrderCategory.JOINT_CAUSE)
        fp_joint = sum(1 for yt, yp in zip(y_true, y_pred) if yt != HigherOrderCategory.JOINT_CAUSE and yp == HigherOrderCategory.JOINT_CAUSE)
        fn_joint = sum(1 for yt, yp in zip(y_true, y_pred) if yt == HigherOrderCategory.JOINT_CAUSE and yp != HigherOrderCategory.JOINT_CAUSE)

        joint_prec = tp_joint / max(1, tp_joint + fp_joint)
        joint_rec = tp_joint / max(1, tp_joint + fn_joint)
        joint_f1 = (2 * joint_prec * joint_rec / max(1e-9, joint_prec + joint_rec)) if (joint_prec + joint_rec) > 0 else 0.0

        tp_int = sum(1 for yt, yp in zip(y_true, y_pred) if yt == HigherOrderCategory.HIGHER_ORDER_INTERACTION and yp == HigherOrderCategory.HIGHER_ORDER_INTERACTION)
        fp_int = sum(1 for yt, yp in zip(y_true, y_pred) if yt != HigherOrderCategory.HIGHER_ORDER_INTERACTION and yp == HigherOrderCategory.HIGHER_ORDER_INTERACTION)
        fn_int = sum(1 for yt, yp in zip(y_true, y_pred) if yt == HigherOrderCategory.HIGHER_ORDER_INTERACTION and yp != HigherOrderCategory.HIGHER_ORDER_INTERACTION)

        int_prec = tp_int / max(1, tp_int + fp_int)
        int_rec = tp_int / max(1, tp_int + fn_int)
        int_f1 = (2 * int_prec * int_rec / max(1e-9, int_prec + int_rec)) if (int_prec + int_rec) > 0 else 0.0

        non_joint_total = sum(1 for yt in y_true if yt not in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        false_joint_total = sum(1 for yt, yp in zip(y_true, y_pred) if yt not in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION) and yp in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        false_joint_rate = false_joint_total / max(1, non_joint_total)

        cascades = [i for i, yt in enumerate(y_true) if yt == HigherOrderCategory.CAUSAL_CASCADE]
        casc_as_joint = sum(1 for i in cascades if y_pred[i] in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        cascade_err_rate = casc_as_joint / max(1, len(cascades))

        confounders = [i for i, yt in enumerate(y_true) if yt == HigherOrderCategory.CONFOUNDED]
        conf_as_joint = sum(1 for i in confounders if y_pred[i] in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        conf_err_rate = conf_as_joint / max(1, len(confounders))

        temporals = [i for i, yt in enumerate(y_true) if yt == HigherOrderCategory.TEMPORAL_RELATION]
        temp_as_joint = sum(1 for i in temporals if y_pred[i] in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION))
        temp_err_rate = temp_as_joint / max(1, len(temporals))

        all_cats = list(HigherOrderCategory)
        cat_f1s = []
        for c in all_cats:
            c_tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp == c)
            c_fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != c and yp == c)
            c_fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp != c)
            if (c_tp + c_fn) > 0:
                p = c_tp / max(1, c_tp + c_fp)
                r = c_tp / max(1, c_tp + c_fn)
                f = (2 * p * r / max(1e-9, p + r)) if (p + r) > 0 else 0.0
                cat_f1s.append(f)
        macro_f1 = float(np.mean(cat_f1s)) if cat_f1s else 0.0

        return GraphFluxBenchmarkResult(
            baseline_name=baseline_name,
            candidate_recall=float(candidate_recall),
            joint_precision=float(joint_prec),
            joint_recall=float(joint_rec),
            joint_f1=float(joint_f1),
            interaction_f1=float(int_f1),
            macro_f1=float(macro_f1),
            exact_structural_match=float(exact_match_rate),
            false_joint_rate=float(false_joint_rate),
            cascade_as_joint_error_rate=float(cascade_err_rate),
            confounder_as_joint_error_rate=float(conf_err_rate),
            temporal_contradiction_rate=float(temp_err_rate),
        )

    def run_benchmark(
        self, docs: List[MultiSentenceDocument]
    ) -> Tuple[List[GraphFluxBenchmarkResult], List[GraphHigherOrderCandidate]]:
        candidates, recall, stats = self.process_corpus(docs)
        y_true = [c.ground_truth_category or HigherOrderCategory.PAIRWISE_DECOMPOSABLE for c in candidates]

        preds_a = self.baselines.predict_baseline_a_pairwise_only(candidates)
        preds_b = self.baselines.predict_baseline_b_local_graph(candidates)
        preds_c = self.baselines.predict_baseline_c_cross_sentence_graph(candidates)
        preds_d = self.baselines.predict_baseline_d_graph_plus_linguistic(candidates)
        preds_e = self.baselines.predict_baseline_e_graph_plus_flux(candidates)
        preds_f = self.baselines.predict_baseline_f_full_graph_flux(candidates)

        for c, p in zip(candidates, preds_f):
            c.predicted_category = p

        results = [
            self.evaluate_predictions(y_true, preds_a, "A. Pairwise NLP Only", recall),
            self.evaluate_predictions(y_true, preds_b, "B. NLP + Local Graph", recall),
            self.evaluate_predictions(y_true, preds_c, "C. NLP + Cross-Sentence Graph", recall),
            self.evaluate_predictions(y_true, preds_d, "D. NLP + Graph + Linguistic", recall),
            self.evaluate_predictions(y_true, preds_e, "E. NLP + Graph + FLUX", recall),
            self.evaluate_predictions(y_true, preds_f, "F. Full Graph-FLUX", recall),
        ]
        return results, candidates

    def run_noise_robustness_experiment(
        self,
        base_docs: List[MultiSentenceDocument],
        noise_levels: List[float] = [0.0, 0.05, 0.10, 0.20, 0.30],
    ) -> Dict[float, GraphFluxBenchmarkResult]:
        generator = MultiSentenceBenchmarkGenerator(seed=self.random_state)
        noise_results = {}
        for noise in noise_levels:
            noisy_docs = generator.inject_extraction_noise(base_docs, noise_rate=noise)
            res_list, _ = self.run_benchmark(noisy_docs)
            full_res = next(r for r in res_list if "Full Graph-FLUX" in r.baseline_name)
            noise_results[noise] = full_res
        return noise_results

    def run_feature_ablation(
        self, candidates: List[GraphHigherOrderCandidate]
    ) -> Dict[str, float]:
        y_true = [c.ground_truth_category or HigherOrderCategory.PAIRWISE_DECOMPOSABLE for c in candidates]
        ablations = {}

        abl_features = [
            ("all_features", []),
            ("no_graph_distance", ["graph_max_distance", "graph_min_distance"]),
            ("no_shared_target", ["graph_shared_targets_count"]),
            ("no_shared_mechanism", ["graph_shared_mediators_count", "graph_has_mediator"]),
            ("no_interaction_language", ["ling_has_synergy", "ling_has_combination"]),
            ("no_pid_synergy", ["flux_pid_synergy", "flux_interaction_info"]),
            ("no_delta_r2", ["flux_delta_r2", "flux_delta_r2_nonparam"]),
            ("no_invariance", ["flux_cmi_stability", "flux_confounding_score"]),
        ]

        for name, drop_keys in abl_features:
            ablated_preds = []
            for cand in candidates:
                ev = dict(cand.evidence)
                for k in drop_keys:
                    ev[k] = 0.0

                synergy = ev.get("flux_pid_synergy", 0.0)
                delta_r2 = ev.get("flux_delta_r2", 0.0)
                confound = ev.get("flux_confounding_score", 0.0)
                is_cascade = ev.get("graph_is_cascade", 0) > 0
                has_synergy_ling = ev.get("ling_has_synergy", 0.0) > 0
                has_combo_ling = ev.get("ling_has_combination", 0.0) > 0

                effective_synergy = synergy + (0.10 if has_synergy_ling else 0.0)
                if confound > 0.45 or ev.get("graph_has_confounder", 0) > 0:
                    ablated_preds.append(HigherOrderCategory.CONFOUNDED)
                elif is_cascade:
                    ablated_preds.append(HigherOrderCategory.CAUSAL_CASCADE)
                elif effective_synergy >= 0.30 and delta_r2 >= 0.18:
                    ablated_preds.append(HigherOrderCategory.HIGHER_ORDER_INTERACTION)
                elif effective_synergy >= 0.14 or (has_combo_ling and effective_synergy >= 0.08):
                    ablated_preds.append(HigherOrderCategory.JOINT_CAUSE)
                else:
                    ablated_preds.append(HigherOrderCategory.PAIRWISE_DECOMPOSABLE)

            eval_res = self.evaluate_predictions(y_true, ablated_preds, name, 1.0)
            ablations[name] = eval_res.joint_f1

        return ablations
