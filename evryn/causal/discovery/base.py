# meflux --help

"""Base class for causal discovery algorithms."""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
import numpy as np
import networkx as nx


class BaseCausalDiscovery(ABC):
    """Abstract interface for causal discovery algorithms."""

    @abstractmethod
    def fit(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> nx.DiGraph:
        """Infer causal DAG from observational data matrix [num_samples, num_vars]."""
        pass

    @abstractmethod
    def predict_direction(self, data: np.ndarray) -> Tuple[int, float]:
        """Predict causal direction for bivariate data (N, 2).

        Returns:
            (direction, confidence)
            direction: 0 if X0 -> X1, 1 if X1 -> X0
            confidence: value in [0, 1]
        """
        pass
