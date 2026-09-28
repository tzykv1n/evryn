# python cli.py baseline

import os
import pickle
import numpy as np
from typing import Any, Optional, Dict
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier

from .base import BaseCausalClassifier
from ..core.config import TFIDFConfig


class LogisticRegressionBaseline(BaseCausalClassifier):

    def __init__(self, config: Optional[TFIDFConfig] = None, seed: int = 42):
        self.config = config or TFIDFConfig()
        self.seed = seed
        self.model = LogisticRegression(
            C=self.config.c_reg,
            class_weight=self.config.class_weight,
            max_iter=1500,
            random_state=seed,
            solver="lbfgs",
        )

    def fit(self, X: Any, y: np.ndarray) -> "LogisticRegressionBaseline":
        self.model.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: Any) -> np.ndarray:
        return self.model.predict_proba(X)

    def save(self, file_path: str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump(self.model, f)

    def load(self, file_path: str) -> "LogisticRegressionBaseline":
        with open(file_path, "rb") as f:
            self.model = pickle.load(f)
        return self


class CalibratedSVMBaseline(BaseCausalClassifier):

    def __init__(self, c_reg: float = 1.0, seed: int = 42):
        self.c_reg = c_reg
        self.seed = seed
        base_svc = LinearSVC(C=c_reg, class_weight="balanced", random_state=seed, max_iter=2000)
        self.model = CalibratedClassifierCV(base_svc, cv=3)

    def fit(self, X: Any, y: np.ndarray) -> "CalibratedSVMBaseline":
        self.model.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: Any) -> np.ndarray:
        return self.model.predict_proba(X)
