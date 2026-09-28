# meflux higher_order
# python -m causality_in_flux.experiments.run_higher_order_benchmark

"""Controlled Higher-Order Synthetic Task and Stream Generator.

Generates benchmarks and continual learning streams supporting:
1. Canonical higher-order structures:
   - Case A: Independent pairwise causes (A -> C and B -> C)
   - Case B: Joint synergistic causal mechanism ({A, B} -> C)
   - Case C: Three-way mechanism ({A, B, C} -> D)
   - Case D: Mediation (A -> B -> C)
   - Case E: Collider (A -> C <- B)
   - Case F: Common cause (A <- C -> B)
   - Case G: Latent confounding (A <-> B)
   - Case H: True independence (A _|_ B)
2. Matched Negative Control:
   - Pairwise additive vs Joint interaction with matched marginal variances
3. Non-stationary continual learning stream with higher-order mechanisms across domains:
   linear, nonlinear, confounded, heavy-tail, interaction-dominant.

Follows Section 2, 9, and 10 of experimental requirements.
"""

from typing import List, Tuple, Dict, Optional, Any
import numpy as np
from .mixed_graph import MixedCausalGraph, RelationType, HyperCausalRelation
from .semi_markovian_generator import MultivariateCausalTask


class HigherOrderTaskGenerator:
    """Generates synthetic tasks and lifelong streams featuring higher-order causal mechanisms."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_case_a_independent_causes(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case A: Independent pairwise causes A -> C and B -> C (strictly additive, no interaction)."""
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "C")
        graph.add_directed_edge("B", "C")

        a = self.rng.normal(0, 1.0, size=num_samples)
        b = self.rng.laplace(0, 1.0, size=num_samples)
        noise = self.rng.normal(0, 0.4, size=num_samples)
        c = 1.1 * a + 1.2 * b + noise

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="case_A_independent",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_causes",
            meta_info={"structure": "A->C, B->C", "is_joint": False},
        )

    def generate_case_b_joint_mechanism(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case B: Joint synergistic causal mechanism {A, B} -> C (non-separable interaction)."""
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")

        a = self.rng.normal(0, 1.0, size=num_samples)
        b = self.rng.normal(0, 1.0, size=num_samples)
        noise = self.rng.normal(0, 0.4, size=num_samples)
        c = 2.0 * (a * b) + noise

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="case_B_joint",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="joint_mechanism",
            meta_info={"structure": "{A,B}->C", "is_joint": True},
        )

    def generate_case_c_three_way(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case C: Three-way mechanism {A, B, C} -> D."""
        nodes = ["A", "B", "C", "D"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B", "C"], "D", relation_type=RelationType.JOINT_CAUSAL, mechanism="3way_product")

        a = self.rng.normal(0, 1.0, size=num_samples)
        b = self.rng.normal(0, 1.0, size=num_samples)
        c = self.rng.normal(0, 1.0, size=num_samples)
        noise = self.rng.normal(0, 0.4, size=num_samples)
        d = 2.2 * (a * b * c) + noise

        X = np.column_stack([a, b, c, d])
        return MultivariateCausalTask(
            task_id="case_C_threeway",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="three_way_mechanism",
            meta_info={"structure": "{A,B,C}->D", "is_joint": True},
        )

    def generate_case_d_mediation(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case D: Mediation A -> B -> C."""
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "B")
        graph.add_directed_edge("B", "C")

        a = self.rng.normal(0, 1.0, size=num_samples)
        e_b = self.rng.laplace(0, 0.5, size=num_samples)
        b = 1.3 * a + e_b
        e_c = self.rng.normal(0, 0.5, size=num_samples)
        c = 1.2 * b + e_c

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="case_D_mediation",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="mediation",
            meta_info={"structure": "A->B->C", "is_joint": False},
        )

    def generate_case_e_collider(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case E: Collider A -> C <- B."""
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "C")
        graph.add_directed_edge("B", "C")

        a = self.rng.normal(0, 1.0, size=num_samples)
        b = self.rng.normal(0, 1.0, size=num_samples)
        noise = self.rng.normal(0, 0.5, size=num_samples)
        c = 1.1 * a + 1.1 * b + noise

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="case_E_collider",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="collider",
            meta_info={"structure": "A->C<-B", "is_joint": False},
        )

    def generate_case_f_common_cause(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case F: Common cause A <- C -> B."""
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("C", "A")
        graph.add_directed_edge("C", "B")

        c = self.rng.normal(0, 1.0, size=num_samples)
        e_a = self.rng.normal(0, 0.5, size=num_samples)
        e_b = self.rng.normal(0, 0.5, size=num_samples)
        a = 1.2 * c + e_a
        b = 1.2 * c + e_b

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="case_F_common_cause",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="common_cause",
            meta_info={"structure": "A<-C->B", "is_joint": False},
        )

    def generate_case_g_latent_confounding(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case G: Latent confounding A <-> B."""
        nodes = ["A", "B"]
        graph = MixedCausalGraph(nodes)
        graph.add_bidirected_edge("A", "B")

        L = self.rng.laplace(0, 1.2, size=num_samples)
        e_a = self.rng.normal(0, 0.5, size=num_samples)
        e_b = self.rng.normal(0, 0.5, size=num_samples)
        a = 1.0 * L + e_a
        b = 1.0 * L + e_b

        X = np.column_stack([a, b])
        return MultivariateCausalTask(
            task_id="case_G_latent_confounding",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="latent_confounding",
            meta_info={"structure": "A<->B", "is_joint": False},
        )

    def generate_case_h_true_independence(self, num_samples: int = 1000) -> MultivariateCausalTask:
        """Case H: True independence A _|_ B."""
        nodes = ["A", "B"]
        graph = MixedCausalGraph(nodes)

        a = self.rng.normal(0, 1.0, size=num_samples)
        b = self.rng.laplace(0, 1.0, size=num_samples)

        X = np.column_stack([a, b])
        return MultivariateCausalTask(
            task_id="case_H_independence",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independence",
            meta_info={"structure": "A _|_ B", "is_joint": False},
        )

    def generate_canonical_benchmark(self, num_samples: int = 1000) -> Dict[str, MultivariateCausalTask]:
        """Generate full suite of Cases A through H."""
        return {
            "case_A": self.generate_case_a_independent_causes(num_samples),
            "case_B": self.generate_case_b_joint_mechanism(num_samples),
            "case_C": self.generate_case_c_three_way(num_samples),
            "case_D": self.generate_case_d_mediation(num_samples),
            "case_E": self.generate_case_e_collider(num_samples),
            "case_F": self.generate_case_f_common_cause(num_samples),
            "case_G": self.generate_case_g_latent_confounding(num_samples),
            "case_H": self.generate_case_h_true_independence(num_samples),
        }

    def generate_negative_control_pair(
        self,
        num_samples: int = 1000,
    ) -> Tuple[MultivariateCausalTask, MultivariateCausalTask]:
        """Generate matched negative control pair:
        Task 1: A -> C and B -> C (additive, NO joint interaction)
        Task 2: {A, B} -> C (synergistic interaction with matched marginal dependencies)
        """
        nodes = ["A", "B", "C"]

        g1 = MixedCausalGraph(nodes)
        g1.add_directed_edge("A", "C")
        g1.add_directed_edge("B", "C")
        a1 = self.rng.normal(0, 1.0, size=num_samples)
        b1 = self.rng.normal(0, 1.0, size=num_samples)
        c1 = 1.0 * a1 + 1.0 * b1 + self.rng.normal(0, 0.4, size=num_samples)
        X1 = np.column_stack([a1, b1, c1])
        t1 = MultivariateCausalTask(
            task_id="neg_control_additive",
            observations=X1,
            graph=g1,
            variable_names=nodes,
            domain="additive_control",
            meta_info={"is_joint": False},
        )

        g2 = MixedCausalGraph(nodes)
        g2.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL)
        a2 = self.rng.normal(0, 1.0, size=num_samples)
        b2 = self.rng.normal(0, 1.0, size=num_samples)
        c2 = 1.8 * (a2 * b2) + self.rng.normal(0, 0.4, size=num_samples)
        X2 = np.column_stack([a2, b2, c2])
        t2 = MultivariateCausalTask(
            task_id="joint_synergistic_target",
            observations=X2,
            graph=g2,
            variable_names=nodes,
            domain="synergistic_target",
            meta_info={"is_joint": True},
        )

        return t1, t2

    def generate_higher_order_continual_stream(
        self,
        num_tasks: int = 16,
        num_variables: int = 6,
        samples_per_task: int = 800,
        regimes: Optional[List[str]] = None,
    ) -> List[MultivariateCausalTask]:
        """Generate a lifelong continual learning stream with non-stationary regimes and higher-order mechanisms."""
        regimes = regimes or ["linear", "nonlinear", "confounded", "heavy_tail", "interaction_dominant"]
        tasks = []
        d = num_variables
        var_names = [f"X{i}" for i in range(d)]

        for idx in range(num_tasks):
            regime = regimes[idx % len(regimes)]
            task_id = f"ho_stream_{idx+1:02d}_{regime}"

            graph = MixedCausalGraph(var_names)
            X = np.zeros((samples_per_task, d))

            if regime == "heavy_tail":
                E = self.rng.standard_t(df=3, size=(samples_per_task, d)) * 0.7
            elif regime == "confounded":
                E = self.rng.laplace(0, 0.8, size=(samples_per_task, d))
            else:
                E = self.rng.normal(0, 0.8, size=(samples_per_task, d))

            X[:, 0] = E[:, 0]
            X[:, 1] = E[:, 1]

            if regime == "interaction_dominant" or idx % 3 == 1:
                graph.add_hyperedge([var_names[0], var_names[1]], var_names[2], relation_type=RelationType.JOINT_CAUSAL)
                X[:, 2] = 2.0 * (X[:, 0] * X[:, 1]) + E[:, 2]

                graph.add_directed_edge(var_names[2], var_names[3])
                X[:, 3] = 1.2 * X[:, 2] + E[:, 3]

                if d >= 5:
                    graph.add_hyperedge([var_names[0], var_names[1], var_names[3]], var_names[4], relation_type=RelationType.JOINT_CAUSAL)
                    X[:, 4] = 1.5 * (X[:, 0] * X[:, 1] * np.tanh(X[:, 3])) + E[:, 4]

                if d >= 6:
                    graph.add_bidirected_edge(var_names[4], var_names[5])
                    L = self.rng.normal(0, 1.2, size=samples_per_task)
                    X[:, 4] += 0.8 * L
                    X[:, 5] = 1.0 * L + E[:, 5]

            elif regime == "confounded":
                graph.add_directed_edge(var_names[0], var_names[1])
                X[:, 1] = 1.2 * X[:, 0] + E[:, 1]
                graph.add_bidirected_edge(var_names[1], var_names[2])
                L = self.rng.laplace(0, 1.2, size=samples_per_task)
                X[:, 1] += 0.9 * L
                X[:, 2] = 1.0 * L + E[:, 2]

                graph.add_directed_edge(var_names[2], var_names[3])
                X[:, 3] = 1.1 * X[:, 2] + E[:, 3]

                if d >= 5:
                    graph.add_directed_edge(var_names[3], var_names[4])
                    X[:, 4] = 1.2 * np.tanh(X[:, 3]) + E[:, 4]
                if d >= 6:
                    X[:, 5] = E[:, 5]

            elif regime == "nonlinear":
                graph.add_directed_edge(var_names[0], var_names[2])
                graph.add_directed_edge(var_names[1], var_names[2])
                X[:, 2] = 1.2 * np.tanh(X[:, 0]) + 0.8 * (X[:, 1] ** 2) + E[:, 2]

                graph.add_directed_edge(var_names[2], var_names[3])
                X[:, 3] = 1.3 * np.tanh(X[:, 2]) + E[:, 3]

                if d >= 5:
                    graph.add_directed_edge(var_names[3], var_names[4])
                    X[:, 4] = 1.1 * X[:, 3] + E[:, 4]
                if d >= 6:
                    X[:, 5] = E[:, 5]

            else:
                graph.add_directed_edge(var_names[0], var_names[2])
                graph.add_directed_edge(var_names[1], var_names[2])
                X[:, 2] = 1.1 * X[:, 0] + 1.1 * X[:, 1] + E[:, 2]

                graph.add_directed_edge(var_names[2], var_names[3])
                X[:, 3] = 1.2 * X[:, 2] + E[:, 3]

                if d >= 5:
                    graph.add_directed_edge(var_names[3], var_names[4])
                    X[:, 4] = 1.0 * X[:, 3] + E[:, 4]
                if d >= 6:
                    X[:, 5] = E[:, 5]

            tasks.append(
                MultivariateCausalTask(
                    task_id=task_id,
                    observations=X,
                    graph=graph,
                    variable_names=var_names,
                    domain=regime,
                    meta_info={"regime": regime, "task_index": idx},
                )
            )

        return tasks
