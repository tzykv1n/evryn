# meflux --help

"""Match and Infer module for Evidence Matching.

Implements match_and_infer(r, R) from Algorithm 1:
Given representation r of new evidence and representation storage R:
1. Computes similarity to past evidence items.
2. Retrieves top-k closest matches.
3. Infers causal graph via distance-weighted voting.
4. Estimates predictive uncertainty (distance-based and entropy-based).
"""

from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import networkx as nx
from .storage import RepresentationStorage, EvidenceItem
from .distance import compute_distances


class EvidenceMatcher:
    """Matches new evidence representation r against storage R and infers causal graph."""

    def __init__(
        self,
        k_neighbors: int = 3,
        metric: str = "euclidean",
        distance_weighting: bool = True,
    ):
        self.k_neighbors = k_neighbors
        self.metric = metric
        self.distance_weighting = distance_weighting

    def match_and_infer(
        self,
        representation: np.ndarray,
        storage: RepresentationStorage,
    ) -> Tuple[nx.DiGraph, int, float, float, List[Dict[str, Any]]]:
        """Infer causal graph and uncertainty from representation storage R.

        Args:
            representation: vector r of shape (D,)
            storage: RepresentationStorage instance R

        Returns:
            (inferred_graph, predicted_label, confidence, uncertainty, top_matches)
        """
        if storage.is_empty():
            raise ValueError("Storage R is empty. Cannot match and infer.")

        matrix, items = storage.get_representations_matrix()
        distances = compute_distances(representation, matrix, metric=self.metric)

        k = min(self.k_neighbors, len(items))
        top_k_indices = np.argsort(distances)[:k]

        weights = []
        labels = []
        top_matches = []

        for idx in top_k_indices:
            dist = float(distances[idx])
            item = items[idx]
            w = 1.0 / (dist + 1e-4) if self.distance_weighting else 1.0
            weights.append(w)
            labels.append(item.label)
            top_matches.append({
                "task_id": item.task_id,
                "domain": item.domain,
                "distance": dist,
                "label": item.label,
                "graph": item.graph,
            })

        unique_labels = sorted(list(set(labels)))
        label_weights = {l: 0.0 for l in [0, 1]}
        for l, w in zip(labels, weights):
            label_weights[l] += w

        total_weight = sum(label_weights.values()) + 1e-9
        p0 = label_weights[0] / total_weight
        p1 = label_weights[1] / total_weight

        best_label = 0 if p0 >= p1 else 1
        confidence = float(max(p0, p1))

        entropy = - (p0 * np.log2(max(p0, 1e-12)) + p1 * np.log2(max(p1, 1e-12)))
        min_dist = float(distances[top_k_indices[0]])
        dist_factor = float(1.0 - np.exp(-min_dist))
        uncertainty = float(np.clip(0.6 * entropy + 0.4 * dist_factor, 0.0, 1.0))

        best_graph = None
        for match in top_matches:
            if match["label"] == best_label:
                best_graph = match["graph"].copy()
                break
        if best_graph is None:
            best_graph = items[top_k_indices[0]].graph.copy()

        return best_graph, best_label, confidence, uncertainty, top_matches
