# meflux higher_order
# python -m causality_in_flux.experiments.run_higher_order_benchmark

from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from ..scm.mixed_graph import MixedCausalGraph, RelationType, HyperCausalRelation
from ..features.multivariate_features import MultivariateMetaFeatureExtractor
from ..features.higher_order_features import HigherOrderFeatureExtractor
from .storage import RepresentationStorage
from .distance import compute_distances


class HigherOrderEvidenceMatchingFramework:

    def __init__(
        self,
        memory_capacity: Optional[int] = 50,
        k_neighbors: int = 2,
        uncertainty_threshold: float = 0.80,
        max_order: int = 2,
        ablation_group: str = "all_features",
        class_weight: Optional[str] = "balanced",
        hyperedge_prob_threshold: float = 0.50,
        classifier_type: str = "rf",
        random_state: int = 42,
    ):
        self.k_neighbors = k_neighbors
        self.uncertainty_threshold = uncertainty_threshold
        self.max_order = max_order
        self.ablation_group = ablation_group
        self.class_weight = class_weight
        self.hyperedge_prob_threshold = hyperedge_prob_threshold
        self.classifier_type = classifier_type
        self.random_state = random_state

        self.pairwise_extractor = MultivariateMetaFeatureExtractor(random_state=random_state)
        self.higher_order_extractor = HigherOrderFeatureExtractor(random_state=random_state)

        self.storage = RepresentationStorage(
            capacity=memory_capacity,
            retention_policy="reservoir",
            seed=random_state,
        )
        self.stored_graphs: List[MixedCausalGraph] = []

        self.pairwise_clf: Optional[Any] = None
        self.order2_clf: Optional[Any] = None
        self.order3_clf: Optional[Any] = None

    def fit_classifiers(self, training_tasks: List[Any]) -> None:
        X_pair, y_pair = [], []
        for task in training_tasks:
            nodes = task.variable_names
            d = len(nodes)
            for i in range(d):
                for j in range(i + 1, d):
                    f_ij = self.pairwise_extractor.extract_pair_features(task.observations, i, j)
                    rel_ij = task.graph.get_relation(nodes[i], nodes[j])
                    X_pair.append(f_ij)
                    y_pair.append(rel_ij)

                    f_ji = self.pairwise_extractor.extract_pair_features(task.observations, j, i)
                    rel_ji = task.graph.get_relation(nodes[j], nodes[i])
                    X_pair.append(f_ji)
                    y_pair.append(rel_ji)

        if X_pair:
            self.pairwise_clf = RandomForestClassifier(
                n_estimators=100,
                max_depth=7,
                class_weight=self.class_weight,
                random_state=self.random_state,
                n_jobs=-1,
            )
            self.pairwise_clf.fit(np.array(X_pair, dtype=np.float32), np.array(y_pair, dtype=int))

        X_ho2, y_ho2 = [], []
        for task in training_tasks:
            nodes = task.variable_names
            d = len(nodes)
            if d < 3:
                continue

            gt_hyper = set()
            for r in task.graph.hyper_relations:
                if len(r.sources) == 2 and r.relation_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
                    gt_hyper.add((frozenset(r.sources), r.target))

            candidates = self.generate_order2_candidates(task.observations, nodes)
            for (i, j), k in candidates:
                src_names = frozenset([nodes[i], nodes[j]])
                tgt_name = nodes[k]
                is_joint = 1 if (src_names, tgt_name) in gt_hyper else 0

                f_dict = self.higher_order_extractor.extract_triple_features(task.observations, i, j, k)
                vec = self.higher_order_extractor.vector_from_dict(f_dict, self.ablation_group)
                X_ho2.append(vec)
                y_ho2.append(is_joint)

        if X_ho2 and len(np.unique(y_ho2)) > 1:
            X_arr = np.array(X_ho2, dtype=np.float32)
            y_arr = np.array(y_ho2, dtype=int)
            if self.classifier_type == "mlp":
                self.order2_clf = make_pipeline(
                    StandardScaler(),
                    MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=450, random_state=self.random_state),
                )
            elif self.classifier_type == "extratrees":
                self.order2_clf = ExtraTreesClassifier(
                    n_estimators=100,
                    max_depth=6,
                    class_weight=self.class_weight,
                    random_state=self.random_state,
                    n_jobs=-1,
                )
            else:
                self.order2_clf = RandomForestClassifier(
                    n_estimators=120,
                    max_depth=6,
                    min_samples_leaf=2,
                    class_weight=self.class_weight,
                    random_state=self.random_state,
                    n_jobs=-1,
                )
            self.order2_clf.fit(X_arr, y_arr)

        if self.max_order >= 3:
            X_ho3, y_ho3 = [], []
            for task in training_tasks:
                nodes = task.variable_names
                d = len(nodes)
                if d < 4:
                    continue

                gt_hyper3 = set()
                for r in task.graph.hyper_relations:
                    if len(r.sources) == 3 and r.relation_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
                        gt_hyper3.add((frozenset(r.sources), r.target))

                candidates3 = self.generate_order3_candidates(task.observations, nodes)
                for (i, j, k), l in candidates3:
                    src_names = frozenset([nodes[i], nodes[j], nodes[k]])
                    tgt_name = nodes[l]
                    is_joint = 1 if (src_names, tgt_name) in gt_hyper3 else 0

                    f3_dict = self.higher_order_extractor.extract_order3_features(task.observations, i, j, k, l)
                    vals = [
                        f3_dict["mi_ad"], f3_dict["mi_bd"], f3_dict["mi_cd"],
                        f3_dict["mi_joint_3way"], f3_dict["ii_3way"],
                        f3_dict["r2_gain_3way"], f3_dict["bic_gain_3way"], f3_dict["hsic_3way"]
                    ]
                    X_ho3.append(vals)
                    y_ho3.append(is_joint)

            if X_ho3 and len(np.unique(y_ho3)) > 1:
                X3_arr = np.array(X_ho3, dtype=np.float32)
                y3_arr = np.array(y_ho3, dtype=int)
                if self.classifier_type == "mlp":
                    self.order3_clf = make_pipeline(
                        StandardScaler(),
                        MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=400, random_state=self.random_state),
                    )
                else:
                    self.order3_clf = RandomForestClassifier(
                        n_estimators=80,
                        max_depth=5,
                        class_weight=self.class_weight,
                        random_state=self.random_state,
                        n_jobs=-1,
                    )
                self.order3_clf.fit(X3_arr, y3_arr)

    def generate_order2_candidates(
        self,
        data: np.ndarray,
        var_names: List[str],
        max_sources_per_target: int = 5,
    ) -> List[Tuple[Tuple[int, int], int]]:
        d = len(var_names)
        candidates = []

        for target_idx in range(d):
            corr_scores = []
            for src_idx in range(d):
                if src_idx != target_idx:
                    std_s = np.std(data[:, src_idx])
                    std_t = np.std(data[:, target_idx])
                    if std_s > 1e-9 and std_t > 1e-9:
                        r = abs(float(np.corrcoef(data[:, src_idx], data[:, target_idx])[0, 1]))
                        r = r if np.isfinite(r) else 0.0
                    else:
                        r = 0.0
                    corr_scores.append((src_idx, r))

            corr_scores.sort(key=lambda x: x[1], reverse=True)
            top_sources = [s for s, _ in corr_scores[:max_sources_per_target]]

            for m in range(len(top_sources)):
                for n in range(m + 1, len(top_sources)):
                    i, j = top_sources[m], top_sources[n]
                    candidates.append(((min(i, j), max(i, j)), target_idx))

        return candidates

    def generate_order3_candidates(
        self,
        data: np.ndarray,
        var_names: List[str],
        max_sources_per_target: int = 4,
    ) -> List[Tuple[Tuple[int, int, int], int]]:
        d = len(var_names)
        candidates = []
        if d < 4:
            return candidates

        for target_idx in range(d):
            corr_scores = []
            for src_idx in range(d):
                if src_idx != target_idx:
                    std_s = np.std(data[:, src_idx])
                    std_t = np.std(data[:, target_idx])
                    if std_s > 1e-9 and std_t > 1e-9:
                        r = abs(float(np.corrcoef(data[:, src_idx], data[:, target_idx])[0, 1]))
                        r = r if np.isfinite(r) else 0.0
                    else:
                        r = 0.0
                    corr_scores.append((src_idx, r))

            corr_scores.sort(key=lambda x: x[1], reverse=True)
            top_sources = [s for s, _ in corr_scores[:max_sources_per_target]]

            for m in range(len(top_sources)):
                for n in range(m + 1, len(top_sources)):
                    for p in range(n + 1, len(top_sources)):
                        trip = tuple(sorted([top_sources[m], top_sources[n], top_sources[p]]))
                        candidates.append((trip, target_idx))

        return candidates

    def identify_from_scratch(self, data: np.ndarray, var_names: List[str]) -> MixedCausalGraph:
        d = len(var_names)
        graph = MixedCausalGraph(var_names)

        if self.pairwise_clf is not None:
            for i in range(d):
                for j in range(i + 1, d):
                    f_ij = self.pairwise_extractor.extract_pair_features(data, i, j)
                    f_ji = self.pairwise_extractor.extract_pair_features(data, j, i)
                    p_ij = self.pairwise_clf.predict_proba([f_ij])[0]
                    p_ji = self.pairwise_clf.predict_proba([f_ji])[0]

                    p_ij_full = np.zeros(4)
                    p_ji_full = np.zeros(4)
                    for idx, c in enumerate(self.pairwise_clf.classes_):
                        p_ij_full[c] = p_ij[idx]
                        p_ji_full[c] = p_ji[idx]

                    p_none = (p_ij_full[0] + p_ji_full[0]) / 2.0
                    p_conf = (p_ij_full[3] + p_ji_full[3]) / 2.0
                    p_fwd = (p_ij_full[1] + p_ji_full[2]) / 2.0
                    p_bwd = (p_ij_full[2] + p_ji_full[1]) / 2.0

                    p_edge = p_fwd + p_bwd + p_conf
                    if p_edge >= 0.45:
                        rel = 1 + int(np.argmax([p_fwd, p_bwd, p_conf]))
                        u, v = var_names[i], var_names[j]
                        if rel == RelationType.FORWARD:
                            graph.add_directed_edge(u, v)
                        elif rel == RelationType.BACKWARD:
                            graph.add_directed_edge(v, u)
                        elif rel == RelationType.BIDIRECTED:
                            graph.add_bidirected_edge(u, v)

        if self.order2_clf is not None and d >= 3:
            candidates2 = self.generate_order2_candidates(data, var_names)
            cands_scored = []
            for (i, j), k in candidates2:
                f_dict = self.higher_order_extractor.extract_triple_features(data, i, j, k)
                vec = self.higher_order_extractor.vector_from_dict(f_dict, self.ablation_group)
                probs = self.order2_clf.predict_proba([vec])[0]
                prob_joint = probs[1] if len(probs) > 1 else (1.0 if self.order2_clf.classes_[0] == 1 else 0.0)
                cands_scored.append(((i, j, k), prob_joint, f_dict.get("bic_gain", 0.0), f_dict.get("delta_r2_nonparam", 0.0), f_dict))

            triplet_groups = {}
            for (i, j, k), p, bic, dr2, fd in cands_scored:
                trip_set = frozenset([i, j, k])
                if trip_set not in triplet_groups:
                    triplet_groups[trip_set] = []
                triplet_groups[trip_set].append(((i, j, k), p, bic, dr2, fd))

            for trip_set, group in triplet_groups.items():
                if self.ablation_group in ("cond_A", "pairwise_only", "pairwise"):
                    passed = [item for item in group if item[1] >= self.hyperedge_prob_threshold]
                else:
                    passed = [item for item in group if item[1] >= self.hyperedge_prob_threshold and (item[2] >= 5.0 or item[3] >= 0.05)]
                if passed:
                    passed.sort(key=lambda x: x[2], reverse=True)
                    best = passed[0]
                    bi, bj, bk = best[0]
                    graph.add_hyperedge(
                        sources=[var_names[bi], var_names[bj]],
                        target=var_names[bk],
                        relation_type=RelationType.JOINT_CAUSAL,
                        mechanism="synergistic_joint",
                        meta_info={"synergy": best[4].get("synergy", 0.0), "bic_gain": best[2], "delta_r2": best[3]},
                    )

        if self.max_order >= 3 and self.order3_clf is not None and d >= 4:
            candidates3 = self.generate_order3_candidates(data, var_names)
            cands3_scored = []
            for (i, j, k), l in candidates3:
                f3_dict = self.higher_order_extractor.extract_order3_features(data, i, j, k, l)
                vec3 = [
                    f3_dict["mi_ad"], f3_dict["mi_bd"], f3_dict["mi_cd"],
                    f3_dict["mi_joint_3way"], f3_dict["ii_3way"],
                    f3_dict["r2_gain_3way"], f3_dict.get("bic_gain_3way", 0.0), f3_dict.get("hsic_3way", 0.0)
                ]
                probs3 = self.order3_clf.predict_proba([vec3])[0]
                prob_joint3 = probs3[1] if len(probs3) > 1 else (1.0 if self.order3_clf.classes_[0] == 1 else 0.0)
                cands3_scored.append(((i, j, k, l), prob_joint3, f3_dict.get("bic_gain_3way", 0.0)))

            passed3 = [c for c in cands3_scored if c[1] >= self.hyperedge_prob_threshold and c[2] >= 5.0]
            if passed3:
                passed3.sort(key=lambda x: x[2], reverse=True)
                best3 = passed3[0]
                bi, bj, bk, bl = best3[0]
                graph.add_hyperedge(
                    sources=[var_names[bi], var_names[bj], var_names[bk]],
                    target=var_names[bl],
                    relation_type=RelationType.JOINT_CAUSAL,
                    mechanism="3way_joint",
                    meta_info={"bic_gain": best3[2]},
                )

        return graph

    def adapt(
        self,
        prior_graph: MixedCausalGraph,
        new_data: np.ndarray,
        var_names: List[str],
    ) -> MixedCausalGraph:
        scratch_g = self.identify_from_scratch(new_data, var_names)
        adapted_g = MixedCausalGraph(var_names)

        d = len(var_names)
        for i in range(d):
            for j in range(i + 1, d):
                u, v = var_names[i], var_names[j]
                rel_prior = prior_graph.get_relation(u, v)
                rel_scratch = scratch_g.get_relation(u, v)

                if rel_prior == rel_scratch:
                    final_rel = rel_scratch
                elif rel_scratch != RelationType.NONE:
                    final_rel = rel_scratch
                else:
                    final_rel = rel_prior

                if final_rel == RelationType.FORWARD:
                    adapted_g.add_directed_edge(u, v)
                elif final_rel == RelationType.BACKWARD:
                    adapted_g.add_directed_edge(v, u)
                elif final_rel == RelationType.BIDIRECTED:
                    adapted_g.add_bidirected_edge(u, v)

        for hr in scratch_g.hyper_relations:
            if len(hr.sources) > 1:
                adapted_g.add_hyperedge(hr.sources, hr.target, hr.relation_type, hr.mechanism, hr.meta_info)

        return adapted_g

    def encode_observations(self, X: np.ndarray) -> np.ndarray:
        return self.pairwise_extractor.extract_dataset_representation(X)

    def process_task(
        self,
        observations: np.ndarray,
        var_names: List[str],
        task_id: str = "",
        domain: str = "higher_order",
    ) -> Dict[str, Any]:
        r = self.encode_observations(observations)

        matched = False
        min_dist = float("inf")
        uncertainty = 1.0

        if len(self.stored_graphs) > 0 and not self.storage.is_empty():
            matrix, _ = self.storage.get_representations_matrix()
            distances = compute_distances(r, matrix)
            k = min(self.k_neighbors, len(self.stored_graphs))
            nearest_idx = np.argsort(distances)[:k]

            min_dist = float(distances[nearest_idx[0]])
            norm_factor = np.sqrt(len(r)) + 1e-9
            uncertainty = float(1.0 - np.exp(-min_dist / norm_factor))

            if uncertainty < self.uncertainty_threshold:
                prior_graph = self.stored_graphs[nearest_idx[0]]
                g_local = self.adapt(prior_graph, observations, var_names)
                source = "matched_and_adapted"
                matched = True

        if not matched:
            g_local = self.identify_from_scratch(observations, var_names)
            source = "scratch_discovery"

        import networkx as nx
        dummy_nx = nx.DiGraph()
        self.storage.add(
            representation=r,
            graph=dummy_nx,
            label=0,
            task_id=task_id,
            domain=domain,
            confidence=float(1.0 - uncertainty),
        )
        self.stored_graphs.append(g_local)

        return {
            "graph": g_local,
            "uncertainty": uncertainty,
            "source": source,
            "min_distance": min_dist,
            "task_id": task_id,
        }

    def remember(self, graph: MixedCausalGraph, data: np.ndarray, var_names: List[str]) -> None:
        r = self.encode_observations(data)
        import networkx as nx
        dummy_nx = nx.DiGraph()
        self.storage.add(
            representation=r,
            graph=dummy_nx,
            label=0,
            task_id="",
            domain="higher_order",
            confidence=1.0,
        )
        self.stored_graphs.append(graph)
