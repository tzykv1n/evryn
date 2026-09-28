# python cli.py contextual

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
from typing import Any, Optional, Dict
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from .base import BaseCausalClassifier
from ..core.config import ContextualConfig


class ContextualMLPClassifier(BaseCausalClassifier):

    def __init__(self, config: Optional[ContextualConfig] = None, seed: int = 42):
        self.config = config or ContextualConfig()
        self.seed = seed
        self.pipeline = make_pipeline(
            StandardScaler(),
            MLPClassifier(
                hidden_layer_sizes=(self.config.hidden_dim, 64),
                activation="relu",
                alpha=1e-4,
                batch_size=64,
                learning_rate_init=1e-3,
                max_iter=150,
                random_state=seed,
                early_stopping=True,
                validation_fraction=0.1,
                n_iter_no_change=10,
            ),
        )

    def fit(self, X: Any, y: np.ndarray) -> "ContextualMLPClassifier":
        self.pipeline.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return self.pipeline.predict(X)

    def predict_proba(self, X: Any) -> np.ndarray:
        return self.pipeline.predict_proba(X)
