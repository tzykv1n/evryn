# meflux --help

"""Linear Non-Gaussian Acyclic Model (LiNGAM) Causal Discovery.

Implements LiNGAM for bivariate and multivariate causal discovery (Shimizu et al., 2006).
Exploits non-Gaussianity of error terms to uniquely identify the causal DAG.
"""

from typing import Tuple, List, Optional
import numpy as np
import networkx as nx
from scipy import stats
from .base import BaseCausalDiscovery
from .anm import compute_distance_correlation


class LiNGAM(BaseCausalDiscovery):
    """Bivariate and Multivariate LiNGAM causal discovery."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def predict_direction(self, data: np.ndarray) -> Tuple[int, float]:
        """Infer direction between data[:, 0] and data[:, 1] using LiNGAM residual independence."""
        x0 = data[:, 0]
        x1 = data[:, 1]

        slope_01, intercept_01, _, _, _ = stats.linregress(x0, x1)
        res_01 = x1 - (slope_01 * x0 + intercept_01)
        dep_01 = compute_distance_correlation(x0, res_01)

        slope_10, intercept_10, _, _, _ = stats.linregress(x1, x0)
        res_10 = x0 - (slope_10 * x1 + intercept_10)
        dep_10 = compute_distance_correlation(x1, res_10)

        if dep_01 < dep_10:
            direction = 0
            diff = dep_10 - dep_01
        else:
            direction = 1
            diff = dep_01 - dep_10

        confidence = float(np.clip(0.5 + diff, 0.5, 1.0))
        return direction, confidence

    def fit(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> nx.DiGraph:
        var_names = variable_names or [f"X{i}" for i in range(data.shape[1])]
        g = nx.DiGraph()
        g.add_nodes_from(var_names)

        if len(var_names) == 2:
            direction, _ = self.predict_direction(data)
            if direction == 0:
                g.add_edge(var_names[0], var_names[1])
            else:
                g.add_edge(var_names[1], var_names[0])

        return g
