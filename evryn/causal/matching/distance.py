# meflux --help

"""Distance and similarity metrics for evidence matching."""

from typing import Union
import numpy as np


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean distance ||a - b||_2."""
    return float(np.linalg.norm(a - b))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity in [-1, 1]."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def rbf_kernel_similarity(a: np.ndarray, b: np.ndarray, gamma: float = 1.0) -> float:
    """RBF Gaussian kernel similarity exp(-gamma * ||a - b||^2)."""
    dist_sq = np.sum((a - b) ** 2)
    return float(np.exp(-gamma * dist_sq))


def compute_distances(query: np.ndarray, pool: np.ndarray, metric: str = "euclidean") -> np.ndarray:
    """Compute distances from a query vector to an array of pool vectors.

    Args:
        query: shape (D,)
        pool: shape (M, D)
        metric: 'euclidean', 'cosine', or 'rbf'

    Returns:
        distances: array of shape (M,) where lower means more similar.
    """
    if metric == "cosine":
        query_norm = np.linalg.norm(query)
        pool_norms = np.linalg.norm(pool, axis=1)
        dots = np.dot(pool, query)
        denom = (pool_norms * query_norm) + 1e-12
        return 1.0 - (dots / denom)

    elif metric == "rbf":
        diff = pool - query[None, :]
        dist_sq = np.sum(diff ** 2, axis=1)
        return 1.0 - np.exp(-0.5 * dist_sq)

    else:
        diff = pool - query[None, :]
        return np.linalg.norm(diff, axis=1)
