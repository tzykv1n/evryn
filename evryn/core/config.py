# evryn --help

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import hashlib
import json


@dataclass
class CacheConfig:
    cache_dir: str = "cache"
    enabled: bool = True
    force_rebuild: bool = False

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class NormalizationConfig:
    canonicalize_entities: bool = True
    similarity_threshold: float = 0.85
    min_confidence: float = 0.50
    domain: str = "general_science"

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class FamilyDiscoveryConfig:
    min_cluster_size: int = 2
    similarity_metric: str = "cosine"
    semantic_threshold: float = 0.72
    allow_cross_family_membership: bool = False

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class TemporalConfig:
    time_window_years: int = 5
    min_observations: int = 2
    decay_rate: float = 0.05
    forecast_horizon_years: int = 3

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class PredictionConfig:
    momentum_weight: float = 0.4
    transitivity_weight: float = 0.6
    min_path_confidence: float = 0.60
    top_k_forecasts: int = 10

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class TransferConfig:
    min_structural_isomorphism: float = 0.70
    min_mechanism_similarity: float = 0.65
    filter_pure_lexical_overlap: bool = True

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class HypothesisConfig:
    max_hypotheses: int = 20
    min_plausibility: float = 0.60
    require_provenance: bool = True
    include_higher_order: bool = True

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class VisualConfig:
    theme: str = "cyan_purple"
    render_terminal_graphics: bool = True
    color_depth: str = "truecolor"
    box_style: str = "rounded"

    def fingerprint(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass
class EvrynConfig:
    project_name: str = "EVRYN"
    output_dir: str = "outputs"
    seed: int = 42
    verbose: bool = False
    cache: CacheConfig = field(default_factory=CacheConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    families: FamilyDiscoveryConfig = field(default_factory=FamilyDiscoveryConfig)
    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    prediction: PredictionConfig = field(default_factory=PredictionConfig)
    transfer: TransferConfig = field(default_factory=TransferConfig)
    hypotheses: HypothesisConfig = field(default_factory=HypothesisConfig)
    visual: VisualConfig = field(default_factory=VisualConfig)

    def fingerprint(self) -> str:
        data = {
            "seed": self.seed,
            "cache": self.cache.fingerprint(),
            "normalization": self.normalization.fingerprint(),
            "families": self.families.fingerprint(),
            "temporal": self.temporal.fingerprint(),
            "prediction": self.prediction.fingerprint(),
            "transfer": self.transfer.fingerprint(),
            "hypotheses": self.hypotheses.fingerprint(),
            "visual": self.visual.fingerprint(),
        }
        s = json.dumps(data, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
