# python cli.py --help

from dataclasses import dataclass, field, asdict
from typing import Tuple, Optional, Dict, Any
import hashlib
import json


@dataclass
class DatasetConfig:
    dataset_name: str = "semeval2010_task8"
    data_dir: str = "data/semeval2010"
    val_ratio: float = 0.15
    seed: int = 42
    max_samples: Optional[int] = None

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class TFIDFConfig:
    max_features: int = 20000
    ngram_range: Tuple[int, int] = (1, 3)
    include_middle_context: bool = True
    include_entity_ngrams: bool = True
    include_directional_indicators: bool = True
    c_reg: float = 2.0
    class_weight: str = "balanced"

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class ContextualConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_length: int = 128
    batch_size: int = 64
    pooling: str = "span_mean"
    include_interactions: bool = True
    classifier_type: str = "mlp"
    hidden_dim: int = 128
    dropout: float = 0.2
    c_reg: float = 1.0

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class CacheConfig:
    cache_dir: str = "cache"
    enabled: bool = True
    force_rebuild: bool = False


@dataclass
class ExperimentConfig:
    experiment_name: str = "pairwise_causal_baseline"
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    tfidf: TFIDFConfig = field(default_factory=TFIDFConfig)
    contextual: ContextualConfig = field(default_factory=ContextualConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    seed: int = 42
    output_dir: str = "outputs"

    def get_hash(self, stage: str) -> str:
        d: Dict[str, Any] = {
            "stage": stage,
            "seed": self.seed,
            "dataset": asdict(self.dataset),
        }
        if stage == "tfidf":
            d["tfidf"] = asdict(self.tfidf)
        elif stage == "contextual":
            d["contextual"] = asdict(self.contextual)
        s = json.dumps(d, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:20]
