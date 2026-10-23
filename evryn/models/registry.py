# evryn models registry
# pytest tests/test_model_registry.py

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable


@dataclass
class CalibrationMetrics:
    brier_score: float
    expected_calibration_error: float
    abstention_rate: float
    coverage_rate: float
    num_samples: int
    reliability_bins: List[Dict[str, float]] = field(default_factory=list)


class DenseEmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._loaded = False

    def load(self) -> "DenseEmbeddingModel":
        if self._loaded:
            return self
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            self._model.eval()
            self._loaded = True
        except Exception:
            self._loaded = False
        return self

    @property
    def is_available(self) -> bool:
        if not self._loaded:
            try:
                self.load()
            except Exception:
                return False
        return self._loaded

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        if not self.is_available:
            return self._fallback_encode(texts)
        import torch
        inputs = self._tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = self._model(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(outputs.last_hidden_state * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        mean_pooled = sum_embeddings / sum_mask
        normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
        return normalized.cpu().numpy()

    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        vecs = []
        for t in texts:
            h = hash(t)
            rng = np.random.RandomState(abs(h) % (2**31))
            v = rng.randn(384).astype(np.float32)
            v /= np.linalg.norm(v) + 1e-9
            vecs.append(v)
        return np.vstack(vecs)

    def similarity(self, text_a: str, text_b: str) -> float:
        embs = self.encode([text_a, text_b])
        dot = float(np.dot(embs[0], embs[1]))
        return max(0.0, min(1.0, dot))


class LexicalEmbeddingModel:
    def __init__(self, ngram_range: Tuple[int, int] = (1, 2)):
        self.ngram_range = ngram_range
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def _extract_ngrams(self, text: str) -> List[str]:
        words = [w.lower() for w in text.split() if w.isalnum()]
        ngrams: List[str] = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(words) - n + 1):
                ngrams.append(" ".join(words[i:i+n]))
        return ngrams

    def fit(self, corpus: List[str]) -> "LexicalEmbeddingModel":
        doc_counts: Dict[str, int] = {}
        n_docs = max(1, len(corpus))
        for doc in corpus:
            ngrams = set(self._extract_ngrams(doc))
            for ng in ngrams:
                doc_counts[ng] = doc_counts.get(ng, 0) + 1

        self.vocab = {ng: i for i, ng in enumerate(sorted(doc_counts.keys()))}
        self.idf = {ng: math.log((1.0 + n_docs) / (1.0 + count)) + 1.0 for ng, count in doc_counts.items()}
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        dim = max(1, len(self.vocab))
        mat = np.zeros((len(texts), dim), dtype=np.float32)
        for i, text in enumerate(texts):
            ngrams = self._extract_ngrams(text)
            for ng in ngrams:
                if ng in self.vocab:
                    col = self.vocab[ng]
                    mat[i, col] += self.idf.get(ng, 1.0)
            norm = np.linalg.norm(mat[i])
            if norm > 1e-9:
                mat[i] /= norm
        return mat

    def similarity(self, text_a: str, text_b: str) -> float:
        vecs = self.transform([text_a, text_b])
        return float(np.dot(vecs[0], vecs[1]))


class CalibratedVerifier:
    def __init__(self, abstention_threshold: float = 0.45):
        self.abstention_threshold = abstention_threshold
        self.weights = np.array([2.5, 1.8, -1.2, -0.8], dtype=np.float64)
        self.bias = -0.5
        self.temperature = 1.0

    def fit_calibration(self, feature_matrix: np.ndarray, labels: np.ndarray) -> "CalibratedVerifier":
        if len(feature_matrix) < 4:
            return self
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(max_iter=200, random_state=42)
        lr.fit(feature_matrix, labels)
        self.weights = lr.coef_[0]
        self.bias = float(lr.intercept_[0])
        return self

    def predict_probability(self, features: np.ndarray) -> np.ndarray:
        logits = (np.dot(features, self.weights) + self.bias) / self.temperature
        probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -20.0, 20.0)))
        return probs

    def verify_candidate(self, features: np.ndarray) -> Dict[str, Any]:
        p = float(self.predict_probability(features.reshape(1, -1))[0])
        abstain = p < self.abstention_threshold
        decision = (p >= 0.50) if not abstain else False
        confidence = abs(p - 0.50) * 2.0
        return {
            "calibrated_probability": round(p, 4),
            "confidence": round(confidence, 4),
            "decision": bool(decision),
            "is_abstained": bool(abstain),
            "threshold": self.abstention_threshold,
        }

    def evaluate_calibration(
        self, feature_matrix: np.ndarray, labels: np.ndarray, n_bins: int = 10
    ) -> CalibrationMetrics:
        probs = self.predict_probability(feature_matrix)
        brier = float(np.mean((probs - labels) ** 2))

        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        reliability_bins = []
        n_samples = len(labels)
        abstained_count = int(np.sum(probs < self.abstention_threshold))

        for i in range(n_bins):
            b_low = bin_boundaries[i]
            b_high = bin_boundaries[i + 1]
            in_bin = (probs >= b_low) & (probs < b_high if i < n_bins - 1 else probs <= b_high)
            bin_size = int(np.sum(in_bin))
            if bin_size > 0:
                bin_acc = float(np.mean(labels[in_bin]))
                bin_conf = float(np.mean(probs[in_bin]))
                ece += (bin_size / n_samples) * abs(bin_acc - bin_conf)
                reliability_bins.append({
                    "bin_lower": round(float(b_low), 2),
                    "bin_upper": round(float(b_high), 2),
                    "sample_count": bin_size,
                    "accuracy": round(bin_acc, 4),
                    "confidence": round(bin_conf, 4),
                })

        abstention_rate = abstained_count / max(1, n_samples)
        coverage_rate = 1.0 - abstention_rate

        return CalibrationMetrics(
            brier_score=round(brier, 4),
            expected_calibration_error=round(float(ece), 4),
            abstention_rate=round(abstention_rate, 4),
            coverage_rate=round(coverage_rate, 4),
            num_samples=n_samples,
            reliability_bins=reliability_bins,
        )


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._init_defaults()

    def _init_defaults(self):
        self._models["dense-minilm"] = DenseEmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        self._models["lexical-tfidf"] = LexicalEmbeddingModel()
        self._models["calibrated-verifier"] = CalibratedVerifier()

    def register(self, name: str, model_instance: Any):
        self._models[name] = model_instance

    def get(self, name: str) -> Any:
        if name not in self._models:
            raise KeyError(f"Model '{name}' not found in registry. Available: {list(self._models.keys())}")
        return self._models[name]

    def list_models(self) -> List[Dict[str, Any]]:
        result = []
        for name, mod in sorted(self._models.items()):
            mtype = type(mod).__name__
            status = "ready"
            if hasattr(mod, "is_available"):
                status = "ready" if mod.is_available else "fallback"
            result.append({
                "name": name,
                "type": mtype,
                "status": status,
            })
        return result


_REGISTRY_INSTANCE: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _REGISTRY_INSTANCE
    if _REGISTRY_INSTANCE is None:
        _REGISTRY_INSTANCE = ModelRegistry()
    return _REGISTRY_INSTANCE
