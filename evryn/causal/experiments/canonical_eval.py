# python cli.py adaptive_benchmark
# meflux adaptive_benchmark

import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from ..scm.mixed_graph import MixedCausalGraph, RelationType, evaluate_hypergraph
from ..scm.independent_hcam_generator import IndependentHCAMGenerator
from ..features.higher_order_features import HigherOrderFeatureExtractor
from .robustness_metrics import compute_distribution_statistics, paired_significance_test


def get_canonical_seeds(num_seeds: int = 20) -> List[int]:
    return [42 + i * 13 for i in range(num_seeds)]


def build_classifier(name: str, seed: int = 42) -> Any:
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        )
    elif name == "MLP":
        return make_pipeline(
            StandardScaler(),
            MLPClassifier(
                hidden_layer_sizes=(64, 32),
                max_iter=450,
                random_state=seed,
                early_stopping=False,
            ),
        )
    elif name == "ExtraTrees":
        return ExtraTreesClassifier(
            n_estimators=100,
            max_depth=6,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        )
    elif name == "Logistic Regression":
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed),
        )
    elif name == "SVM-RBF":
        return make_pipeline(
            StandardScaler(),
            CalibratedClassifierCV(
                SVC(kernel="rbf", C=1.0, class_weight="balanced", random_state=seed),
                ensemble=False,
            ),
        )
    elif name == "HistGradientBoosting":
        return HistGradientBoostingClassifier(max_iter=100, class_weight="balanced", random_state=seed)
    else:
        raise ValueError(f"Unknown classifier architecture: {name}")


class CanonicalEvaluator:

    def __init__(
        self,
        extractor: Optional[HigherOrderFeatureExtractor] = None,
        generator: Optional[IndependentHCAMGenerator] = None,
        threshold: float = 0.50,
        random_state: int = 42,
    ):
        self.random_state = random_state
        self.threshold = threshold
        self.extractor = extractor or HigherOrderFeatureExtractor(random_state=random_state)
        self.generator = generator or IndependentHCAMGenerator(seed=random_state)

    def extract_training_dataset(
        self,
        num_samples: int = 800,
        feature_group: str = "mechanism_aware",
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        train_tasks = self.generator.generate_training_set(num_samples=num_samples, seed=seed)
        t3_train = self.generator.generate_threeway_hcam(num_samples=num_samples, seed=seed)

        X_o2, y_o2 = [], []
        for task in train_tasks:
            nodes = task.variable_names
            d = len(nodes)
            if d < 3:
                continue
            gt_hyper = set()
            for r in task.graph.hyper_relations:
                if len(r.sources) == 2 and r.relation_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
                    gt_hyper.add((frozenset(r.sources), r.target))

            for i in range(d):
                for j in range(i + 1, d):
                    for k in range(d):
                        if k != i and k != j:
                            src_pair = frozenset([nodes[i], nodes[j]])
                            tgt = nodes[k]
                            is_joint = 1 if (src_pair, tgt) in gt_hyper else 0
                            f_dict = self.extractor.extract_triple_features(task.observations, i, j, k)
                            v = self.extractor.vector_from_dict(f_dict, feature_group)
                            X_o2.append(v)
                            y_o2.append(is_joint)

        X_o3, y_o3 = [], []
        nodes3 = t3_train.variable_names
        d3 = len(nodes3)
        gt3 = set()
        for r in t3_train.graph.hyper_relations:
            if len(r.sources) == 3 and r.relation_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
                gt3.add((frozenset(r.sources), r.target))

        for i in range(d3):
            for j in range(i + 1, d3):
                for k in range(j + 1, d3):
                    for l in range(d3):
                        if l not in (i, j, k):
                            is_joint3 = 1 if (frozenset([nodes3[i], nodes3[j], nodes3[k]]), nodes3[l]) in gt3 else 0
                            f3d = self.extractor.extract_order3_features(t3_train.observations, i, j, k, l)
                            v3 = [
                                f3d["mi_ad"], f3d["mi_bd"], f3d["mi_cd"],
                                f3d["mi_joint_3way"], f3d["ii_3way"],
                                f3d["r2_gain_3way"], f3d["bic_gain_3way"], f3d["hsic_3way"]
                            ]
                            X_o3.append(v3)
                            y_o3.append(is_joint3)

        return (
            np.array(X_o2, dtype=np.float32),
            np.array(y_o2, dtype=int),
            np.array(X_o3, dtype=np.float32),
            np.array(y_o3, dtype=int),
        )

    def evaluate_task(
        self,
        task: Any,
        clf_o2: Any,
        clf_o3: Optional[Any] = None,
        feature_group: str = "mechanism_aware",
        max_order: int = 3,
    ) -> Tuple[MixedCausalGraph, Dict[str, float]]:
        nodes = task.variable_names
        d = len(nodes)
        pred_g = MixedCausalGraph(nodes)

        cand_keys = []
        cand_vecs = []
        cand_meta = []
        env_data = task.meta_info.get("environments_data") if hasattr(task, "meta_info") else None
        for i in range(d):
            for j in range(i + 1, d):
                for k in range(d):
                    if k != i and k != j:
                        f_dict = self.extractor.extract_triple_features(task.observations, i, j, k, environments_data=env_data)
                        vec = self.extractor.vector_from_dict(f_dict, feature_group)
                        cand_keys.append((i, j, k))
                        cand_vecs.append(vec)
                        cand_meta.append((f_dict.get("bic_gain", 0.0), f_dict.get("delta_r2_nonparam", 0.0)))

        cands2 = []
        if cand_vecs:
            if hasattr(clf_o2, "predict_proba"):
                probs = clf_o2.predict_proba(np.array(cand_vecs, dtype=np.float32))[:, 1]
            else:
                probs = np.full(len(cand_vecs), 0.5)
            for idx_c, key in enumerate(cand_keys):
                cands2.append((key, float(probs[idx_c]), cand_meta[idx_c][0], cand_meta[idx_c][1]))

        triplet_groups = {}
        for (i, j, k), p, bic, dr2 in cands2:
            trip_set = frozenset([i, j, k])
            if trip_set not in triplet_groups:
                triplet_groups[trip_set] = []
            triplet_groups[trip_set].append(((i, j, k), p, bic, dr2))

        for trip_set, group in triplet_groups.items():
            if feature_group in ("cond_A", "pairwise_only", "pairwise"):
                passed = [item for item in group if item[1] >= self.threshold]
            else:
                passed = [item for item in group if item[1] >= self.threshold and (item[2] >= 5.0 or item[3] >= 0.05)]
            if passed:
                passed.sort(key=lambda x: x[2], reverse=True)
                best = passed[0]
                (bi, bj, bk) = best[0]
                pred_g.add_hyperedge([nodes[bi], nodes[bj]], nodes[bk], RelationType.JOINT_CAUSAL)

        if max_order >= 3 and d >= 4 and clf_o3 is not None:
            cands3_keys = []
            cands3_vecs = []
            cands3_meta = []
            for i in range(d):
                for j in range(i + 1, d):
                    for k in range(j + 1, d):
                        for l in range(d):
                            if l not in (i, j, k):
                                f3d = self.extractor.extract_order3_features(task.observations, i, j, k, l)
                                v3 = [
                                    f3d["mi_ad"], f3d["mi_bd"], f3d["mi_cd"],
                                    f3d["mi_joint_3way"], f3d["ii_3way"],
                                    f3d["r2_gain_3way"], f3d["bic_gain_3way"], f3d["hsic_3way"]
                                ]
                                cands3_keys.append((i, j, k, l))
                                cands3_vecs.append(v3)
                                cands3_meta.append(f3d.get("bic_gain_3way", 0.0))

            cands3 = []
            if cands3_vecs:
                if hasattr(clf_o3, "predict_proba"):
                    probs3 = clf_o3.predict_proba(np.array(cands3_vecs, dtype=np.float32))[:, 1]
                else:
                    probs3 = np.full(len(cands3_vecs), 0.5)
                for idx_3, k3 in enumerate(cands3_keys):
                    cands3.append((k3, float(probs3[idx_3]), cands3_meta[idx_3]))

            passed3 = [c for c in cands3 if c[1] >= self.threshold and c[2] >= 5.0]
            if passed3:
                passed3.sort(key=lambda x: x[2], reverse=True)
                best3 = passed3[0]
                (bi, bj, bk, bl) = best3[0]
                pred_g.add_hyperedge([nodes[bi], nodes[bj], nodes[bk]], nodes[bl], RelationType.JOINT_CAUSAL)
                src_set3 = set([nodes[bi], nodes[bj], nodes[bk]])
                pred_g.hyper_relations = [
                    hr for hr in pred_g.hyper_relations
                    if not (hr.target == nodes[bl] and set(hr.sources).issubset(src_set3) and len(hr.sources) < 3)
                ]

        metrics = evaluate_hypergraph(task.graph, pred_g, nodes)
        return pred_g, metrics
