# meflux --help

r"""Deep Dataset Representation Encoder (DeepSets Architecture).

Implements the neural dataset representation learning discussed in Section 4:
"An intriguing approach to leverage former evidence could involve learning
representations of entire datasets and making predictions based on these representations.
... In a sense, a full dataset is just a single variable for evidence matching."

Implements a permutation-invariant DeepSet encoder:
r = \rho( \sum_{i=1}^N \phi(x_i) )
where:
- \phi: element-wise feature projection network
- Aggregation: permutation-invariant pooling (mean, sum, max)
- \rho: dataset representation network
- Head: predicts causal direction / graph structure
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np


class DeepSetDatasetEncoder:
    r"""Numpy-based neural permutation-invariant dataset encoder.

    Provides end-to-end representation learning for sets of observations X \in R^{N x d}.
    Permutation invariance ensures that the order of samples in a dataset does not
    affect the learned representation r.
    """

    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 32,
        embedding_dim: int = 16,
        output_dim: int = 2,
        pooling: str = "mean",
        seed: int = 42,
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.embedding_dim = embedding_dim
        self.output_dim = output_dim
        self.pooling = pooling
        self.rng = np.random.default_rng(seed)

        scale_phi1 = np.sqrt(2.0 / input_dim)
        self.W_phi1 = self.rng.normal(0, scale_phi1, (input_dim, hidden_dim))
        self.b_phi1 = np.zeros(hidden_dim)

        scale_phi2 = np.sqrt(2.0 / hidden_dim)
        self.W_phi2 = self.rng.normal(0, scale_phi2, (hidden_dim, hidden_dim))
        self.b_phi2 = np.zeros(hidden_dim)

        scale_rho1 = np.sqrt(2.0 / (hidden_dim * (3 if pooling == "multi" else 1)))
        in_rho = hidden_dim * 3 if pooling == "multi" else hidden_dim
        self.W_rho1 = self.rng.normal(0, scale_rho1, (in_rho, embedding_dim))
        self.b_rho1 = np.zeros(embedding_dim)

        scale_head = np.sqrt(2.0 / embedding_dim)
        self.W_head = self.rng.normal(0, scale_head, (embedding_dim, output_dim))
        self.b_head = np.zeros(output_dim)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0.0, x)

    def encode(self, data: np.ndarray) -> np.ndarray:
        r"""Encode a dataset X \in R^{N x d} into a representation vector r \in R^{embedding_dim}.

        Args:
            data: observations of shape (N, d)
        Returns:
            r: representation vector of shape (embedding_dim,)
        """
        x = data.astype(np.float64)
        mu = np.mean(x, axis=0, keepdims=True)
        std = np.std(x, axis=0, keepdims=True) + 1e-8
        x_norm = (x - mu) / std

        h1 = self._relu(np.dot(x_norm, self.W_phi1) + self.b_phi1)
        h2 = self._relu(np.dot(h1, self.W_phi2) + self.b_phi2)

        if self.pooling == "mean":
            pooled = np.mean(h2, axis=0)
        elif self.pooling == "max":
            pooled = np.max(h2, axis=0)
        elif self.pooling == "multi":
            p_mean = np.mean(h2, axis=0)
            p_max = np.max(h2, axis=0)
            p_std = np.std(h2, axis=0)
            pooled = np.concatenate([p_mean, p_max, p_std])
        else:
            pooled = np.mean(h2, axis=0)

        r = self._relu(np.dot(pooled, self.W_rho1) + self.b_rho1)
        return r

    def forward(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute representation r and class probabilities."""
        r = self.encode(data)
        logits = np.dot(r, self.W_head) + self.b_head
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        return r, probs

    def predict(self, data: np.ndarray) -> int:
        _, probs = self.forward(data)
        return int(np.argmax(probs))

    def train_step(
        self,
        datasets: List[np.ndarray],
        labels: List[int],
        lr: float = 0.005,
    ) -> float:
        """Perform a single SGD training step over a batch of datasets."""
        total_loss = 0.0
        grad_W_head = np.zeros_like(self.W_head)
        grad_b_head = np.zeros_like(self.b_head)
        grad_W_rho1 = np.zeros_like(self.W_rho1)
        grad_b_rho1 = np.zeros_like(self.b_rho1)

        for data, y in zip(datasets, labels):
            r, probs = self.forward(data)
            loss = -np.log(max(probs[y], 1e-12))
            total_loss += loss

            d_logits = probs.copy()
            d_logits[y] -= 1.0

            grad_W_head += np.outer(r, d_logits)
            grad_b_head += d_logits

            d_r = np.dot(self.W_head, d_logits)
            d_r[r <= 0] = 0.0

            grad_b_rho1 += d_r

        n = len(datasets)
        self.W_head -= lr * (grad_W_head / n)
        self.b_head -= lr * (grad_b_head / n)
        self.b_rho1 -= lr * (grad_b_rho1 / n)

        return float(total_loss / max(1, n))
