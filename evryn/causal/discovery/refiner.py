# meflux --help

"""Graph Refinement for Evidence Matching (Algorithm 1).

Implements refine_local_graph(G_local, X_i):
Validates and refines a candidate causal graph G_local (retrieved via evidence matching)
against the actual observed data X_i. Warm-starts causal discovery and resolves
uncertainties.
"""

from typing import Tuple, Optional, List
import numpy as np
import networkx as nx
from .anm import AdditiveNoiseModel
from .lingam import LiNGAM


class LocalGraphRefiner:
    """Refines a candidate causal graph G_local against observations X_i."""

    def __init__(
        self,
        contradiction_threshold: float = 0.25,
        discovery_method: str = "anm",
        random_state: int = 42,
    ):
        self.contradiction_threshold = contradiction_threshold
        if discovery_method == "lingam":
            self.discovery = LiNGAM(random_state=random_state)
        else:
            self.discovery = AdditiveNoiseModel(random_state=random_state)

    def refine(
        self,
        candidate_graph: nx.DiGraph,
        observations: np.ndarray,
        candidate_confidence: float = 0.8,
        variable_names: Optional[List[str]] = None,
    ) -> Tuple[nx.DiGraph, float, bool]:
        """Refine the candidate graph using observations X_i.

        Args:
            candidate_graph: graph predicted from prior evidence matching.
            observations: data matrix [num_samples, num_vars].
            candidate_confidence: confidence score of the matched graph [0, 1].
            variable_names: list of variable names.

        Returns:
            (refined_graph, updated_confidence, was_modified)
        """
        var_names = variable_names or list(candidate_graph.nodes())
        if len(var_names) < 2:
            return candidate_graph.copy(), candidate_confidence, False

        refined_g = candidate_graph.copy()
        was_modified = False

        if len(var_names) == 2:
            v0, v1 = var_names[0], var_names[1]
            prior_dir = 0 if candidate_graph.has_edge(v0, v1) else 1

            data_dir, data_conf = self.discovery.predict_direction(observations)

            if prior_dir == data_dir:
                updated_conf = min(1.0, candidate_confidence * 0.5 + data_conf * 0.5 + 0.1)
            else:
                if data_conf - candidate_confidence > self.contradiction_threshold:
                    refined_g.clear_edges()
                    if data_dir == 0:
                        refined_g.add_edge(v0, v1)
                    else:
                        refined_g.add_edge(v1, v0)
                    updated_conf = data_conf
                    was_modified = True
                else:
                    updated_conf = max(0.5, candidate_confidence - 0.15)

            return refined_g, updated_conf, was_modified

        return refined_g, candidate_confidence, False
