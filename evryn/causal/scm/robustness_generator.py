# meflux robustness
# python -m causality_in_flux.experiments.run_robustness_benchmark

"""Controlled Robustness Benchmark Task Generator for Higher-Order FLUX.

Generates systematic synthetic benchmark tasks for evaluating higher-order causal discovery
under controlled degradation:
1. Sample-size sweeps: N in {50, 100, 200, 500, 1000, 2000}
2. Noise-level sweeps: sigma in {0.05, 0.10, 0.25, 0.50, 1.00, 2.00}
3. Interaction-strength sweeps: alpha in {0.1, 0.25, 0.5, 1.0, 2.0, 4.0} (multiplicative and continuous XOR)
4. Mechanism diversity:
   - Additive: C = A + B + eps
   - Multiplicative: C = A * B + eps
   - Nonlinear additive: C = sin(A) + tanh(B) + eps
   - Nonlinear interaction: C = sin(A * B) + eps
   - Continuous XOR: C = alpha * sign(A) * sign(B) + eps
   - Three-way interaction: D = A * B * C + eps
5. Matched-marginal negative controls:
   - Dataset A (Additive) vs Dataset B (Joint Multiplicative) with matched marginal variances and SNR
6. Noise distributions: Gaussian, Laplace, Student-t (df=3), and Heteroscedastic Gaussian
7. Irrelevant distractor variables: D in {5, 10, 20, 50, 100} for candidate screening validation

Follows Sections 2 through 10 of experimental requirements.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from .mixed_graph import MixedCausalGraph, RelationType, HyperCausalRelation
from .semi_markovian_generator import MultivariateCausalTask


class RobustnessTaskGenerator:
    """Generates synthetic tasks across degradation sweeps and realistic regimes."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _get_rng(self, seed: Optional[int] = None) -> np.random.Generator:
        if seed is None:
            return self.rng
        return np.random.default_rng(seed)

    def generate_sample_size_task(
        self,
        num_samples: int,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate a controlled task for sample-size evaluation: N in {50, 100, 200, 500, 1000, 2000}.
        
        Graph:
        - Higher-order joint hyperedge: {A, B} -> C
        - Directed pairwise edge: C -> D
        - Independent distractor: E
        """
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C", "D", "E"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")
        graph.add_directed_edge("C", "D")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps_c = rng.normal(0, 0.4, size=num_samples)
        c = 1.8 * (a * b) + eps_c

        eps_d = rng.normal(0, 0.4, size=num_samples)
        d = 1.2 * c + eps_d

        e = rng.normal(0, 1.0, size=num_samples)

        X = np.column_stack([a, b, c, d, e])
        return MultivariateCausalTask(
            task_id=f"sample_size_N{num_samples}",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="sample_size_sweep",
            meta_info={"num_samples": num_samples, "structure": "{A,B}->C, C->D, E"},
        )

    def generate_noise_sweep_task(
        self,
        sigma: float,
        num_samples: int = 800,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate a controlled task for noise-level evaluation: sigma in {0.05, 0.10, 0.25, 0.50, 1.00, 2.00}."""
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C", "D"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")
        graph.add_directed_edge("C", "D")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps_c = rng.normal(0, sigma, size=num_samples)
        c = 2.0 * (a * b) + eps_c

        eps_d = rng.normal(0, sigma, size=num_samples)
        d = 1.2 * c + eps_d

        X = np.column_stack([a, b, c, d])
        return MultivariateCausalTask(
            task_id=f"noise_sigma_{sigma:.2f}",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="noise_sweep",
            meta_info={"sigma": sigma, "structure": "{A,B}->C, C->D"},
        )

    def generate_interaction_sweep_task(
        self,
        alpha: float,
        interaction_type: str = "multiplicative",
        num_samples: int = 800,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate a controlled task for interaction-strength evaluation:
        C = alpha * A * B + eps  or  C = alpha * XOR(A, B) + eps.
        """
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism=interaction_type)

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps_c = rng.normal(0, 0.4, size=num_samples)

        if interaction_type == "multiplicative":
            c = alpha * (a * b) + eps_c
        elif interaction_type == "xor":
            c = alpha * np.sign(a) * np.sign(b) + eps_c
        else:
            raise ValueError(f"Unknown interaction_type: {interaction_type}")

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id=f"interaction_{interaction_type}_alpha_{alpha:.2f}",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="interaction_sweep",
            meta_info={"alpha": alpha, "interaction_type": interaction_type, "structure": "{A,B}->C"},
        )

    def generate_mechanism_task(
        self,
        mechanism: str,
        num_samples: int = 800,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate tasks across diverse mechanism families:
        1. 'additive': C = A + B + eps -> Ground truth: A -> C and B -> C (No joint hyperedge)
        2. 'multiplicative': C = A * B + eps -> Ground truth: {A, B} -> C
        3. 'nonlinear_additive': C = sin(A) + tanh(B) + eps -> Ground truth: A -> C and B -> C
        4. 'nonlinear_interaction': C = sin(A * B) + eps -> Ground truth: {A, B} -> C
        5. 'xor': C = 2.0 * sign(A) * sign(B) + eps -> Ground truth: {A, B} -> C
        6. 'threeway_interaction': D = A * B * C + eps -> Ground truth: {A, B, C} -> D
        """
        rng = self._get_rng(seed)

        if mechanism == "additive":
            nodes = ["A", "B", "C"]
            graph = MixedCausalGraph(nodes)
            graph.add_directed_edge("A", "C")
            graph.add_directed_edge("B", "C")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = 1.1 * a + 1.1 * b + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c])

        elif mechanism == "multiplicative":
            nodes = ["A", "B", "C"]
            graph = MixedCausalGraph(nodes)
            graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = 1.8 * (a * b) + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c])

        elif mechanism == "nonlinear_additive":
            nodes = ["A", "B", "C"]
            graph = MixedCausalGraph(nodes)
            graph.add_directed_edge("A", "C")
            graph.add_directed_edge("B", "C")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = 1.2 * np.sin(a) + 1.2 * np.tanh(b) + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c])

        elif mechanism == "nonlinear_interaction":
            nodes = ["A", "B", "C"]
            graph = MixedCausalGraph(nodes)
            graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="nonlinear_interaction")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = 1.8 * np.sin(1.5 * a * b) + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c])

        elif mechanism == "xor":
            nodes = ["A", "B", "C"]
            graph = MixedCausalGraph(nodes)
            graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="continuous_xor")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = 2.0 * np.sign(a) * np.sign(b) + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c])

        elif mechanism == "threeway_interaction":
            nodes = ["A", "B", "C", "D"]
            graph = MixedCausalGraph(nodes)
            graph.add_hyperedge(["A", "B", "C"], "D", relation_type=RelationType.JOINT_CAUSAL, mechanism="3way_product")
            a = rng.normal(0, 1.0, size=num_samples)
            b = rng.normal(0, 1.0, size=num_samples)
            c = rng.normal(0, 1.0, size=num_samples)
            d = 2.2 * (a * b * c) + rng.normal(0, 0.4, size=num_samples)
            X = np.column_stack([a, b, c, d])

        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        return MultivariateCausalTask(
            task_id=f"mech_{mechanism}",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="mechanism_diversity",
            meta_info={"mechanism": mechanism},
        )

    def generate_matched_marginal_pair(
        self,
        num_samples: int = 1000,
        seed: Optional[int] = None,
    ) -> Tuple[MultivariateCausalTask, MultivariateCausalTask, Dict[str, float]]:
        """Construct matched negative control datasets:
        Dataset A (Additive): C = A + B + eps (Ground truth: A -> C, B -> C, NO joint hyperedge)
        Dataset B (Multiplicative): C = gamma * (A * B) + eps (Ground truth: {A, B} -> C)
        
        Matches marginal means, marginal variances, pairwise correlations, and SNR as closely as practical.
        """
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]

        g_add = MixedCausalGraph(nodes)
        g_add.add_directed_edge("A", "C")
        g_add.add_directed_edge("B", "C")
        a_add = rng.normal(0, 1.0, size=num_samples)
        b_add = rng.normal(0, 1.0, size=num_samples)
        eps_add = rng.normal(0, 0.5, size=num_samples)
        c_add = 1.0 * a_add + 1.0 * b_add + eps_add
        X_add = np.column_stack([a_add, b_add, c_add])
        task_add = MultivariateCausalTask(
            task_id="matched_control_additive",
            observations=X_add,
            graph=g_add,
            variable_names=nodes,
            domain="matched_marginal",
            meta_info={"is_joint": False, "mechanism": "additive"},
        )

        g_mult = MixedCausalGraph(nodes)
        g_mult.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")
        a_mult = rng.normal(0, 1.0, size=num_samples)
        b_mult = rng.normal(0, 1.0, size=num_samples)
        eps_mult = rng.normal(0, 0.5, size=num_samples)
        gamma = np.sqrt(2.0)
        c_mult = gamma * (a_mult * b_mult) + eps_mult
        X_mult = np.column_stack([a_mult, b_mult, c_mult])
        task_mult = MultivariateCausalTask(
            task_id="matched_joint_multiplicative",
            observations=X_mult,
            graph=g_mult,
            variable_names=nodes,
            domain="matched_marginal",
            meta_info={"is_joint": True, "mechanism": "multiplicative"},
        )

        stats_dict = {
            "mean_C_additive": float(np.mean(c_add)),
            "mean_C_multiplicative": float(np.mean(c_mult)),
            "mean_diff_C": float(abs(np.mean(c_add) - np.mean(c_mult))),
            "var_C_additive": float(np.var(c_add)),
            "var_C_multiplicative": float(np.var(c_mult)),
            "var_ratio_C": float(np.var(c_add) / (np.var(c_mult) + 1e-9)),
            "corr_AC_additive": float(np.corrcoef(a_add, c_add)[0, 1]),
            "corr_AC_multiplicative": float(np.corrcoef(a_mult, c_mult)[0, 1]),
            "corr_BC_additive": float(np.corrcoef(b_add, c_add)[0, 1]),
            "corr_BC_multiplicative": float(np.corrcoef(b_mult, c_mult)[0, 1]),
        }

        return task_add, task_mult, stats_dict

    def generate_noise_distribution_task(
        self,
        noise_dist: str,
        num_samples: int = 800,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate tasks across non-Gaussian and heteroscedastic noise distributions:
        - 'gaussian': Standard normal noise N(0, 0.4^2)
        - 'laplace': Double exponential Laplace(0, b) with matched variance
        - 'student_t': Heavy-tailed Student-t with df=3
        - 'heteroscedastic': Noise variance depends on parent inputs: Var(eps | A, B) ~ (1 + 0.5*tanh(A+B))^2
        """
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)

        if noise_dist == "gaussian":
            eps = rng.normal(0, 0.4, size=num_samples)
        elif noise_dist == "laplace":
            scale = 0.4 / np.sqrt(2.0)
            eps = rng.laplace(0, scale, size=num_samples)
        elif noise_dist == "student_t":
            eps = rng.standard_t(df=3, size=num_samples) * (0.4 / np.sqrt(3.0))
        elif noise_dist == "heteroscedastic":
            local_scale = 0.35 * (1.0 + 0.6 * np.tanh(a + b))
            eps = local_scale * rng.normal(0, 1.0, size=num_samples)
        else:
            raise ValueError(f"Unknown noise_dist: {noise_dist}")

        c = 1.8 * (a * b) + eps
        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id=f"noise_dist_{noise_dist}",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="noise_distribution",
            meta_info={"noise_dist": noise_dist, "structure": "{A,B}->C"},
        )

    def generate_irrelevant_vars_task(
        self,
        num_total_vars: int,
        num_samples: int = 800,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        """Generate task with D total variables where only {X0, X1} -> X2 is the true causal hyperedge,
        and X3 ... X_{D-1} are independent distractor variables.
        Validates candidate-screening mechanism against O(N^3) explosion.
        """
        rng = self._get_rng(seed)
        var_names = [f"X{i}" for i in range(num_total_vars)]
        graph = MixedCausalGraph(var_names)
        graph.add_hyperedge([var_names[0], var_names[1]], var_names[2], relation_type=RelationType.JOINT_CAUSAL)

        X = np.zeros((num_samples, num_total_vars))
        X[:, 0] = rng.normal(0, 1.0, size=num_samples)
        X[:, 1] = rng.normal(0, 1.0, size=num_samples)
        eps_2 = rng.normal(0, 0.4, size=num_samples)
        X[:, 2] = 1.8 * (X[:, 0] * X[:, 1]) + 0.25 * X[:, 0] + 0.25 * X[:, 1] + eps_2

        for j in range(3, num_total_vars):
            X[:, j] = rng.normal(0, 1.0, size=num_samples)

        return MultivariateCausalTask(
            task_id=f"distractors_D{num_total_vars}",
            observations=X,
            graph=graph,
            variable_names=var_names,
            domain="candidate_screening",
            meta_info={"num_vars": num_total_vars, "true_hyperedge": "{X0, X1} -> X2"},
        )
