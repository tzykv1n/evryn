# meflux --help

"""Representation Storage R for Evidence Matching.

Stores evidence representations r and their corresponding causal graphs G_local.
Supports:
- Capacity constraints for continual learning
- Replacement policies (FIFO, Reservoir sampling)
- Abstraction clustering to avoid catastrophic forgetting and maintain capacity
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import networkx as nx


class EvidenceItem:
    """An individual piece of stored causal evidence (r, G_local, meta)."""

    def __init__(
        self,
        representation: np.ndarray,
        graph: nx.DiGraph,
        label: int,
        task_id: str = "",
        domain: str = "general",
        confidence: float = 1.0,
    ):
        self.representation = np.asarray(representation, dtype=np.float32)
        self.graph = graph
        self.label = label
        self.task_id = task_id
        self.domain = domain
        self.confidence = confidence

    @property
    def direction(self) -> int:
        return self.label


class RepresentationStorage:
    """Memory buffer R holding past evidence representations and causal graphs."""

    def __init__(
        self,
        capacity: Optional[int] = None,
        retention_policy: str = "reservoir",
        seed: int = 42,
    ):
        self.capacity = capacity
        self.retention_policy = retention_policy
        self.items: List[EvidenceItem] = []
        self.total_seen: int = 0
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def add(
        self,
        representation: np.ndarray,
        graph: nx.DiGraph,
        label: int,
        task_id: str = "",
        domain: str = "general",
        confidence: float = 1.0,
    ) -> None:
        """Store (r, G_local) into memory buffer R."""
        self.total_seen += 1
        item = EvidenceItem(
            representation=representation,
            graph=graph,
            label=label,
            task_id=task_id,
            domain=domain,
            confidence=confidence,
        )

        if self.capacity is None or len(self.items) < self.capacity:
            self.items.append(item)
        else:
            if self.retention_policy == "reservoir":
                j = self.rng.integers(0, self.total_seen)
                if j < self.capacity:
                    self.items[j] = item
            elif self.retention_policy == "fifo":
                self.items.pop(0)
                self.items.append(item)

    def get_representations_matrix(self) -> Tuple[np.ndarray, List[EvidenceItem]]:
        """Get matrix of all stored representations shape (M, D) and items list."""
        if self.is_empty():
            raise ValueError("Storage is empty.")
        matrix = np.vstack([item.representation for item in self.items])
        return matrix, self.items

    def clear(self) -> None:
        self.items.clear()
        self.total_seen = 0
