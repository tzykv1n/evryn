# meflux --help

"""Causal Graph Abstraction and Targeted Compression.

Implements the causal abstraction concept discussed in Section 4:
"In the context of causal models in CL scenarios, abstractions are a promising
alternative to forgetting. Finding abstractions corresponds to summarizing multiple
variables of a causal graph into one variable and adapting the mechanisms between
the summarized variable and its neighbors. This way, a trade-off between model
complexity and predictive performance can be achieved..."
"""

from typing import List, Tuple, Dict, Set, Optional
import networkx as nx
import numpy as np


class CausalAbstraction:
    """Manages causal graph abstractions to compress models in continual learning."""

    def __init__(self):
        pass

    def abstract_graph(
        self,
        graph: nx.DiGraph,
        cluster_mapping: Dict[str, str],
    ) -> nx.DiGraph:
        """Abstract a fine-grained causal graph into a coarser abstracted graph.

        Args:
            graph: detailed graph G
            cluster_mapping: dict mapping fine variable names to abstract variable names,
                             e.g. {'X1': 'Macro_A', 'X2': 'Macro_A', 'X3': 'Macro_B'}

        Returns:
            abstracted_graph: coarse causal graph with macro-variables.
        """
        abstracted = nx.DiGraph()
        macro_nodes = set(cluster_mapping.values())
        abstracted.add_nodes_from(macro_nodes)

        for u, v in graph.edges():
            macro_u = cluster_mapping.get(u, u)
            macro_v = cluster_mapping.get(v, v)
            if macro_u != macro_v:
                abstracted.add_edge(macro_u, macro_v)

        return abstracted

    def compress_memory_representations(
        self,
        representations: np.ndarray,
        labels: List[int],
        target_size: int,
    ) -> Tuple[np.ndarray, List[int]]:
        """Cluster and compress memory representations to preserve capacity.

        Uses prototype abstraction to summarize multiple evidence items into representative
        macro-prototypes per class, balancing capacity and predictive fidelity.
        """
        if len(representations) <= target_size:
            return representations, labels

        compressed_reps = []
        compressed_labels = []

        unique_labels = sorted(list(set(labels)))
        quota_per_class = max(1, target_size // len(unique_labels))

        for l in unique_labels:
            indices = [i for i, y in enumerate(labels) if y == l]
            class_reps = representations[indices]

            if len(class_reps) <= quota_per_class:
                for idx in indices:
                    compressed_reps.append(representations[idx])
                    compressed_labels.append(l)
            else:
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=quota_per_class, random_state=42, n_init=5)
                kmeans.fit(class_reps)
                for center in kmeans.cluster_centers_:
                    compressed_reps.append(center)
                    compressed_labels.append(l)

        return np.vstack(compressed_reps), compressed_labels
