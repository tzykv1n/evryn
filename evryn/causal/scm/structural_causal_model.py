# meflux --help

r"""Structural Causal Model (SCM) Implementation.

Represents an SCM \xi = (U, V, F, p) where:
- U: exogenous (unmodelled) noise variables with distribution p(U)
- V: endogenous (observed) variables
- F: structural equations Vj = fj(Pa(Vj), Uj)
Each SCM induces a Directed Acyclic Graph (DAG) G.
"""

from typing import Dict, List, Callable, Optional, Tuple, Any
import numpy as np
import networkx as nx


class StructuralEquation:
    """Represents a structural equation Vj = fj(Pa(Vj), Uj)."""

    def __init__(
        self,
        target_var: str,
        parent_vars: List[str],
        func: Callable[..., np.ndarray],
        noise_dist: Optional[Callable[[int], np.ndarray]] = None,
        name: str = "custom",
    ):
        self.target_var = target_var
        self.parent_vars = list(parent_vars)
        self.func = func
        self.noise_dist = noise_dist or (lambda n: np.random.randn(n))
        self.name = name

    def evaluate(self, parent_values: Dict[str, np.ndarray], num_samples: int) -> np.ndarray:
        noise = self.noise_dist(num_samples)
        parents_data = [parent_values[p] for p in self.parent_vars]
        return self.func(*parents_data, noise)


class StructuralCausalModel:
    """Structural Causal Model xi = (U, V, F, p).

    Induces a DAG G and joint distribution p(V).
    """

    def __init__(self, name: str = "scm"):
        self.name = name
        self.graph = nx.DiGraph()
        self.equations: Dict[str, StructuralEquation] = {}

    def add_variable(
        self,
        var_name: str,
        parent_vars: Optional[List[str]] = None,
        func: Optional[Callable[..., np.ndarray]] = None,
        noise_dist: Optional[Callable[[int], np.ndarray]] = None,
        equation_name: str = "equation",
    ) -> None:
        """Add an endogenous variable and its structural equation."""
        parent_vars = parent_vars or []
        self.graph.add_node(var_name)
        for p in parent_vars:
            self.graph.add_edge(p, var_name)

        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_node(var_name)
            raise ValueError(f"Adding variable '{var_name}' with parents {parent_vars} introduces a cycle!")

        if func is None:
            def root_func(noise: np.ndarray) -> np.ndarray:
                return noise

            func = root_func

        self.equations[var_name] = StructuralEquation(
            target_var=var_name,
            parent_vars=parent_vars,
            func=func,
            noise_dist=noise_dist,
            name=equation_name,
        )

    def sample(
        self,
        num_samples: int = 1000,
        interventions: Optional[Dict[str, float]] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, np.ndarray]:
        """Sample observational or interventional data from the SCM.

        If interventions are specified (e.g. {'X': 2.5}), the structural equation
        for that variable is replaced by a constant (Pearl's do-operator).
        """
        if seed is not None:
            np.random.seed(seed)

        interventions = interventions or {}
        ordered_vars = list(nx.topological_sort(self.graph))
        samples: Dict[str, np.ndarray] = {}

        for var in ordered_vars:
            if var in interventions:
                samples[var] = np.full(num_samples, interventions[var], dtype=float)
            else:
                eq = self.equations[var]
                parent_vals = {p: samples[p] for p in eq.parent_vars}
                samples[var] = eq.evaluate(parent_vals, num_samples)

        return samples

    def sample_matrix(
        self,
        num_samples: int = 1000,
        interventions: Optional[Dict[str, float]] = None,
        seed: Optional[int] = None,
        var_order: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """Sample observations as a 2D numpy array [num_samples, num_vars]."""
        samples = self.sample(num_samples=num_samples, interventions=interventions, seed=seed)
        order = var_order or sorted(list(self.graph.nodes()))
        matrix = np.column_stack([samples[v] for v in order])
        return matrix, order

    @property
    def adjacency_matrix(self) -> np.ndarray:
        """Adjacency matrix ordered by sorted variable names."""
        nodes = sorted(list(self.graph.nodes()))
        return nx.to_numpy_array(self.graph, nodelist=nodes, dtype=int)

    @property
    def edges(self) -> List[Tuple[str, str]]:
        return list(self.graph.edges())

    def get_markov_equivalence_class(self) -> nx.DiGraph:
        """Compute the CPDAG (Completed Partially Directed Acyclic Graph).

        Graphs in the same Markov Equivalence Class (MEC) share the same
        skeleton and the same v-structures (unshielded colliders).
        """
        cpdag = nx.DiGraph()
        skeleton = self.graph.to_undirected()
        for u, v in skeleton.edges():
            cpdag.add_edge(u, v)
            cpdag.add_edge(v, u)

        nodes = list(self.graph.nodes())
        for z in nodes:
            parents = list(self.graph.predecessors(z))
            for i in range(len(parents)):
                for j in range(i + 1, len(parents)):
                    x, y = parents[i], parents[j]
                    if not self.graph.has_edge(x, y) and not self.graph.has_edge(y, x):
                        if cpdag.has_edge(z, x):
                            cpdag.remove_edge(z, x)
                        if cpdag.has_edge(z, y):
                            cpdag.remove_edge(z, y)

        return cpdag
