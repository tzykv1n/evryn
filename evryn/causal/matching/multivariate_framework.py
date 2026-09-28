# meflux flux
# python -m causality_in_flux.experiments.run_multivariate_flux

"""Multivariate Evidence Matching Framework for Mixed Causal Graphs.

Implements Algorithm 1 extended to multivariate networks with:
- Cause-effect directed edges (u -> v and u <- v)
- Unobserved confounding bidirected edges (u <-> v)
- Independent / no-relation pairs (none)
- Class-balanced relational classifier with stratified sampling and class-weighted loss
- Hierarchical edge decision rule resolving the multi-class split-vote collapse
- Bayesian evidence refinement without minority-class suppression

Follows Seng et al. (PMLR 2024/2025): "Causality in Flux: Continual Adaptation
of Causal Knowledge via Evidence Matching".
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from ..scm.mixed_graph import MixedCausalGraph, RelationType
from ..features.multivariate_features import MultivariateMetaFeatureExtractor
from .storage import RepresentationStorage
from .distance import compute_distances


class MultivariateEvidenceMatchingFramework:
    """Algorithm 1 framework extended to multivariate graphs with mixed relations."""

    def __init__(
        self,
        memory_capacity: Optional[int] = 50,
        k_neighbors: int = 3,
        uncertainty_threshold: float = 0.70,
        class_weight: Optional[str] = "balanced",
        balanced_sampling: bool = True,
        edge_threshold: float = 0.45,
        decision_mode: str = "hierarchical",
        refinement_enabled: bool = True,
        random_state: int = 42,
    ):
        self.k_neighbors = k_neighbors
        self.uncertainty_threshold = uncertainty_threshold
        self.class_weight = class_weight
        self.balanced_sampling = balanced_sampling
        self.edge_threshold = edge_threshold
        self.decision_mode = decision_mode
        self.refinement_enabled = refinement_enabled
        self.random_state = random_state

        self.extractor = MultivariateMetaFeatureExtractor(random_state=random_state)
        self.storage = RepresentationStorage(
            capacity=memory_capacity,
            retention_policy="reservoir",
            seed=random_state,
        )
        self.stored_graphs: List[MixedCausalGraph] = []
        self.classifier: Optional[RandomForestClassifier] = None
        self.class_priors: Optional[np.ndarray] = None

    def fit_relational_classifier(self, training_tasks: List[Any]) -> None:
        """Pre-train relational meta-classifier on reference tasks with optional balanced sampling."""
        X_feats, y_labels = [], []
        for task in training_tasks:
            nodes = task.variable_names
            d = len(nodes)
            for i in range(d):
                for j in range(i + 1, d):
                    f_ij = self.extractor.extract_pair_features(task.observations, i, j)
                    rel_ij = task.graph.get_relation(nodes[i], nodes[j])
                    X_feats.append(f_ij)
                    y_labels.append(rel_ij)

                    f_ji = self.extractor.extract_pair_features(task.observations, j, i)
                    rel_ji = task.graph.get_relation(nodes[j], nodes[i])
                    X_feats.append(f_ji)
                    y_labels.append(rel_ji)

        X_train = np.array(X_feats, dtype=np.float32)
        y_train = np.array(y_labels, dtype=int)

        if self.balanced_sampling and len(y_train) > 0:
            rng = np.random.default_rng(self.random_state)
            classes = [np.where(y_train == c)[0] for c in range(4)]
            counts = [len(idx) for idx in classes]
            if min(counts) > 0:
                target_per_class = max(150, int(np.mean(counts)))
                bal_idx = np.concatenate([
                    rng.choice(idx, size=target_per_class, replace=True)
                    for idx in classes
                ])
                X_train = X_train[bal_idx]
                y_train = y_train[bal_idx]

        unique, counts = np.unique(y_train, return_counts=True)
        total = float(len(y_train))
        priors = np.zeros(4, dtype=np.float64)
        for u, c in zip(unique, counts):
            priors[u] = c / total
        self.class_priors = priors

        self.classifier = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=4,
            class_weight=self.class_weight,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.classifier.fit(X_train, y_train)

    def encode_observations(self, X: np.ndarray) -> np.ndarray:
        """Compute multivariate meta-representation vector r."""
        return self.extractor.extract_dataset_representation(X)

    def _predict_pair_probs(self, X: np.ndarray, i: int, j: int) -> np.ndarray:
        """Compute symmetrized relational probabilities [p_none, p_fwd, p_bwd, p_conf]."""
        f_ij = self.extractor.extract_pair_features(X, i, j)
        f_ji = self.extractor.extract_pair_features(X, j, i)

        if self.classifier is None:
            return np.array([0.5, 0.2, 0.2, 0.1], dtype=np.float64)

        p_ij = self.classifier.predict_proba([f_ij])[0]
        p_ji = self.classifier.predict_proba([f_ji])[0]

        p_ij_full = np.zeros(4, dtype=np.float64)
        p_ji_full = np.zeros(4, dtype=np.float64)
        classes_ = self.classifier.classes_
        for idx, c in enumerate(classes_):
            p_ij_full[c] = p_ij[idx]
            p_ji_full[c] = p_ji[idx]

        p_none = (p_ij_full[0] + p_ji_full[0]) / 2.0
        p_conf = (p_ij_full[3] + p_ji_full[3]) / 2.0
        p_fwd = (p_ij_full[1] + p_ji_full[2]) / 2.0
        p_bwd = (p_ij_full[2] + p_ji_full[1]) / 2.0

        probs = np.array([p_none, p_fwd, p_bwd, p_conf], dtype=np.float64)
        total = np.sum(probs)
        return probs / total if total > 0 else np.array([0.25, 0.25, 0.25, 0.25])

    def _decide_relation(self, probs: np.ndarray) -> int:
        """Apply decision rule: either argmax or hierarchical edge thresholding."""
        if self.decision_mode == "argmax":
            return int(np.argmax(probs))

        p_none, p_fwd, p_bwd, p_conf = probs
        p_edge = p_fwd + p_bwd + p_conf

        if p_edge < self.edge_threshold:
            return RelationType.NONE

        rel_choice = 1 + int(np.argmax([p_fwd, p_bwd, p_conf]))
        return rel_choice

    def identify_from_scratch(self, X: np.ndarray, var_names: List[str]) -> MixedCausalGraph:
        """Infer mixed graph from scratch using relational classifier."""
        d = len(var_names)
        graph = MixedCausalGraph(var_names)

        for i in range(d):
            for j in range(i + 1, d):
                probs = self._predict_pair_probs(X, i, j)
                pred = self._decide_relation(probs)

                u, v = var_names[i], var_names[j]
                if pred == RelationType.FORWARD:
                    graph.add_directed_edge(u, v)
                elif pred == RelationType.BACKWARD:
                    graph.add_directed_edge(v, u)
                elif pred == RelationType.BIDIRECTED:
                    graph.add_bidirected_edge(u, v)

        return graph

    def adapt(
        self,
        prior_graph: MixedCausalGraph,
        observations: np.ndarray,
        var_names: List[str],
        uncertainty: float = 0.5,
    ) -> MixedCausalGraph:
        """Adapt matched prior graph to local observations with Bayesian evidence refinement."""
        if not self.refinement_enabled:
            return MixedCausalGraph.from_relation_matrix(prior_graph.relation_matrix, var_names)

        refined_graph = MixedCausalGraph(var_names)
        d = len(var_names)
        confidence = float(np.clip(1.0 - uncertainty, 0.1, 0.95))

        for i in range(d):
            for j in range(i + 1, d):
                u, v = var_names[i], var_names[j]
                prior_rel = prior_graph.get_relation(u, v)
                local_probs = self._predict_pair_probs(observations, i, j)

                if prior_rel == RelationType.NONE:
                    prior_probs = np.array([0.40, 0.20, 0.20, 0.20], dtype=np.float64)
                else:
                    prior_probs = np.full(4, (1.0 - confidence) / 3.0, dtype=np.float64)
                    prior_probs[prior_rel] = confidence

                post_probs = local_probs * prior_probs
                total = np.sum(post_probs)
                post_probs = post_probs / total if total > 0 else local_probs

                pred = self._decide_relation(post_probs)

                if pred == RelationType.FORWARD:
                    refined_graph.add_directed_edge(u, v)
                elif pred == RelationType.BACKWARD:
                    refined_graph.add_directed_edge(v, u)
                elif pred == RelationType.BIDIRECTED:
                    refined_graph.add_bidirected_edge(u, v)

        return refined_graph

    def process_task(
        self,
        observations: np.ndarray,
        var_names: List[str],
        task_id: str = "",
        domain: str = "multivariate",
    ) -> Dict[str, Any]:
        """Execute Algorithm 1: Evidence Matching & Continual Adaptation."""
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
                g_local = self.adapt(prior_graph, observations, var_names, uncertainty=uncertainty)
                source = "matched_and_refined" if self.refinement_enabled else "matched_no_refinement"
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
            "distance": min_dist,
            "source": source,
            "summary": g_local.summary(),
        }
