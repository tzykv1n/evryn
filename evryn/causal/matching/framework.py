# meflux --help

"""Algorithm 1: Evidence Matching Framework.

Complete implementation of Algorithm 1 from:
"Causality in Flux: Continual Adaptation of Causal Knowledge via Evidence Matching"
(Seng, Busch & Kersting, PMLR 2024/2025)

Workflow for each incoming observation dataset X_i:
1. r <- encode_observations(X_i)
2. If R is not empty:
     G_local <- match_and_infer(r, R)
     G_local <- refine_local_graph(G_local, X_i)
   Else:
     G_local <- identify_causal_graph(X_i)
3. store (r, G_local) in R
4. return G_local
"""

from typing import Tuple, Optional, Dict, Any, Union
import numpy as np
import networkx as nx

from ..features.meta_features import MetaFeatureExtractor
from ..features.deep_encoder import DeepSetDatasetEncoder
from ..discovery.anm import AdditiveNoiseModel
from ..discovery.lingam import LiNGAM
from ..discovery.refiner import LocalGraphRefiner
from .storage import RepresentationStorage
from .matcher import EvidenceMatcher


class EvidenceMatchingFramework:
    """Implements Algorithm 1 (Evidence Matching Framework) for continual causal discovery."""

    def __init__(
        self,
        encoder_type: str = "meta_features",
        k_neighbors: int = 3,
        metric: str = "euclidean",
        discovery_method: str = "anm",
        memory_capacity: Optional[int] = None,
        retention_policy: str = "reservoir",
        random_state: int = 42,
    ):
        self.encoder_type = encoder_type
        self.random_state = random_state

        self.meta_extractor = MetaFeatureExtractor(random_state=random_state)
        self.deep_encoder = DeepSetDatasetEncoder(seed=random_state)

        self.storage = RepresentationStorage(
            capacity=memory_capacity,
            retention_policy=retention_policy,
            seed=random_state,
        )

        self.matcher = EvidenceMatcher(
            k_neighbors=k_neighbors,
            metric=metric,
            distance_weighting=True,
        )

        if discovery_method == "lingam":
            self.discovery = LiNGAM(random_state=random_state)
        else:
            self.discovery = AdditiveNoiseModel(random_state=random_state)

        self.refiner = LocalGraphRefiner(
            discovery_method=discovery_method,
            random_state=random_state,
        )

    def encode_observations(self, X_i: np.ndarray) -> np.ndarray:
        """Step 1 of Algorithm 1: r <- encode_observations(X_i)."""
        if self.encoder_type == "deep":
            return self.deep_encoder.encode(X_i)
        return self.meta_extractor.extract(X_i)

    def identify_causal_graph(
        self,
        X_i: np.ndarray,
        var_names: Optional[list] = None,
    ) -> Tuple[nx.DiGraph, float]:
        """Discovery from scratch when R is empty: G_local <- identify_causal_graph(X_i)."""
        var_names = var_names or [f"X{j}" for j in range(X_i.shape[1])]
        direction, conf = self.discovery.predict_direction(X_i)

        g = nx.DiGraph()
        g.add_nodes_from(var_names)
        if direction == 0:
            g.add_edge(var_names[0], var_names[1])
        else:
            g.add_edge(var_names[1], var_names[0])

        return g, conf

    def process_observations(
        self,
        X_i: np.ndarray,
        task_id: str = "",
        domain: str = "general",
        var_names: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Execute Algorithm 1 on incoming observations X_i.

        Returns:
            Dictionary containing:
            - 'graph': G_local
            - 'direction': 0 or 1
            - 'confidence': confidence score
            - 'uncertainty': predictive uncertainty
            - 'source': 'matched_and_refined' or 'scratch_discovery'
            - 'representation': r
        """
        var_names = var_names or [f"X{j}" for j in range(X_i.shape[1])]

        r = self.encode_observations(X_i)

        if not self.storage.is_empty():
            matched_g, matched_label, matched_conf, uncertainty, top_matches = (
                self.matcher.match_and_infer(r, self.storage)
            )

            refined_g, updated_conf, was_modified = self.refiner.refine(
                candidate_graph=matched_g,
                observations=X_i,
                candidate_confidence=matched_conf,
                variable_names=var_names,
            )

            g_local = refined_g
            conf = updated_conf
            source = "matched_and_refined"
            meta_info = {
                "top_matches": top_matches,
                "was_modified_by_refiner": was_modified,
            }

        else:
            g_local, conf = self.identify_causal_graph(X_i, var_names=var_names)
            uncertainty = 1.0 - conf
            source = "scratch_discovery"
            meta_info = {"top_matches": []}

        v0, v1 = var_names[0], var_names[1]
        direction = 0 if g_local.has_edge(v0, v1) else 1

        self.storage.add(
            representation=r,
            graph=g_local,
            label=direction,
            task_id=task_id,
            domain=domain,
            confidence=conf,
        )

        return {
            "graph": g_local,
            "direction": direction,
            "confidence": conf,
            "uncertainty": uncertainty,
            "source": source,
            "representation": r,
            "meta_info": meta_info,
        }
