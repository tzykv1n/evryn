# python cli.py --help

from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Dict, Optional


class BaseCausalClassifier(ABC):

    @abstractmethod
    def fit(self, X: Any, y: np.ndarray) -> "BaseCausalClassifier":
        pass

    @abstractmethod
    def predict(self, X: Any) -> np.ndarray:
        pass

    @abstractmethod
    def predict_proba(self, X: Any) -> np.ndarray:
        pass
