# meflux figure2
# python -m causality_in_flux.experiments.reproduce_figure2

"""Reproduction of Figure 2 from Seng, Busch & Kersting (2024/2025).

Figure 2: Dimensionality Reduction of Meta Features (t-SNE).
Extracts the meta-features on the Tübingen Cause-Effect-Pairs benchmark,
applies t-SNE to project them onto 2 dimensions, and visualizes the
resulting clusters of X->Y vs Y->X.
"""

import os
from typing import Optional, Tuple
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from ..datasets.tuebingen_loader import TuebingenPairLoader
from ..features.meta_features import MetaFeatureExtractor


def run_figure2_tsne(
    data_dir: Optional[str] = None,
    output_path: str = "figure2_tsne.png",
    perplexity: float = 30.0,
    random_state: int = 42,
    include_expanded: bool = False,
) -> Tuple[np.ndarray, np.ndarray, str]:
    """Compute t-SNE embeddings and save Figure 2 visualization."""
    loader = TuebingenPairLoader(data_dir=data_dir)
    tasks = loader.load_clean_pairs(augment_swapped=True)

    extractor = MetaFeatureExtractor(include_expanded=include_expanded, random_state=random_state)
    features_list = []
    labels_list = []

    for task in tasks:
        feats = extractor.extract(task.observations)
        features_list.append(feats)
        labels_list.append(task.label)

    X = np.vstack(features_list)
    y = np.array(labels_list, dtype=int)

    mu = np.mean(X, axis=0, keepdims=True)
    sigma = np.std(X, axis=0, keepdims=True) + 1e-8
    X_std = (X - mu) / sigma

    print(f"Applying t-SNE on {len(X)} meta-feature vectors...")
    tsne = TSNE(
        n_components=2,
        perplexity=min(perplexity, len(X) - 1),
        random_state=random_state,
        max_iter=1000,
        init="pca",
    )
    embeddings = tsne.fit_transform(X_std)

    plt.figure(figsize=(7, 6), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    idx_forward = (y == 0)
    idx_backward = (y == 1)

    plt.scatter(
        embeddings[idx_forward, 0],
        embeddings[idx_forward, 1],
        c="#1f77b4",
        label="True Model: X->Y",
        alpha=0.85,
        edgecolors="none",
        s=35,
    )
    plt.scatter(
        embeddings[idx_backward, 0],
        embeddings[idx_backward, 1],
        c="#ff7f0e",
        label="True Model: Y->X",
        alpha=0.85,
        edgecolors="none",
        s=35,
    )

    plt.xlabel("t-SNE component 1", fontsize=12)
    plt.ylabel("t-SNE component 2", fontsize=12)
    plt.title("Figure 2: Dimensionality Reduction of Meta Features (t-SNE)", fontsize=13, pad=12)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, loc="upper right")
    plt.tight_layout()

    out_abs = os.path.abspath(output_path)
    plt.savefig(out_abs, dpi=300)
    plt.close()

    print(f"Figure 2 saved successfully to: {out_abs}")
    return embeddings, y, out_abs


if __name__ == "__main__":
    run_figure2_tsne()
