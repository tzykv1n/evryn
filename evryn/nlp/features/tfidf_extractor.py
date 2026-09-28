# python cli.py baseline

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Tuple, Dict, Any, Optional

from ..core.types import RelationExample
from ..core.config import TFIDFConfig
from ..core.cache import ArtifactCache


FORWARD_CONNECTIVES = [
    "causes", "caused", "causing", "results in", "resulted in",
    "leads to", "lead to", "leading to", "produces", "produced",
    "induces", "induced", "triggers", "triggered", "creates",
    "created", "generates", "brings about", "gives rise to"
]

BACKWARD_CONNECTIVES = [
    "caused by", "results from", "resulted from", "due to",
    "because of", "stems from", "stemmed from", "induced by",
    "triggered by", "provoked by", "arises from", "produced by",
    "originated from", "owing to", "consequence of"
]


class TFIDFExtractor:

    def __init__(self, config: Optional[TFIDFConfig] = None, cache: Optional[ArtifactCache] = None):
        self.config = config or TFIDFConfig()
        self.cache = cache or ArtifactCache()
        self.sent_vectorizer = TfidfVectorizer(
            ngram_range=self.config.ngram_range,
            max_features=self.config.max_features,
            sublinear_tf=True,
        )
        self.mid_vectorizer = TfidfVectorizer(
            ngram_range=self.config.ngram_range,
            max_features=self.config.max_features // 2,
            sublinear_tf=True,
        )
        self.is_fitted = False

    def _extract_heuristic_features(self, examples: List[RelationExample]) -> np.ndarray:
        feats = []
        for ex in examples:
            s1, e1 = ex.entity1_span
            s2, e2 = ex.entity2_span
            e1_first = 1.0 if s1 < s2 else -1.0
            char_dist = float(abs(s2 - e1) if s1 < s2 else abs(s1 - e2))
            mid = ex.middle_context.lower()

            fwd_hits = sum(1.0 for pat in FORWARD_CONNECTIVES if pat in mid)
            bwd_hits = sum(1.0 for pat in BACKWARD_CONNECTIVES if pat in mid)

            e1_len = float(len(ex.entity1_text))
            e2_len = float(len(ex.entity2_text))

            row = [
                e1_first,
                char_dist,
                np.log1p(char_dist),
                fwd_hits,
                bwd_hits,
                fwd_hits - bwd_hits,
                e1_len,
                e2_len,
            ]
            feats.append(row)
        return np.array(feats, dtype=np.float32)

    def fit_transform(
        self,
        train_examples: List[RelationExample],
        dataset_hash: str = "default",
    ) -> sp.csr_matrix:
        cache_key = f"tfidf_train_{dataset_hash}_{self.config.fingerprint()}"
        cached = self.cache.get("features", cache_key)
        if cached is not None:
            self.sent_vectorizer = cached["sent_vectorizer"]
            self.mid_vectorizer = cached["mid_vectorizer"]
            self.is_fitted = True
            return cached["matrix"]

        sents = [ex.marked_sentence for ex in train_examples]
        mids = [ex.middle_context for ex in train_examples]

        X_sent = self.sent_vectorizer.fit_transform(sents)
        X_mid = self.mid_vectorizer.fit_transform(mids)
        X_heur = sp.csr_matrix(self._extract_heuristic_features(train_examples))

        X_comb = sp.hstack([X_sent, X_mid, X_heur], format="csr")
        self.is_fitted = True

        self.cache.set(
            "features",
            cache_key,
            {
                "matrix": X_comb,
                "sent_vectorizer": self.sent_vectorizer,
                "mid_vectorizer": self.mid_vectorizer,
            },
            {"shape": list(X_comb.shape), "nnz": X_comb.nnz},
        )
        return X_comb

    def transform(
        self,
        examples: List[RelationExample],
        split_name: str = "test",
        dataset_hash: str = "default",
    ) -> sp.csr_matrix:
        if not self.is_fitted:
            raise RuntimeError("TFIDFExtractor must be fitted before calling transform.")

        cache_key = f"tfidf_{split_name}_{dataset_hash}_{self.config.fingerprint()}"
        cached = self.cache.get("features", cache_key)
        if cached is not None:
            return cached

        sents = [ex.marked_sentence for ex in examples]
        mids = [ex.middle_context for ex in examples]

        X_sent = self.sent_vectorizer.transform(sents)
        X_mid = self.mid_vectorizer.transform(mids)
        X_heur = sp.csr_matrix(self._extract_heuristic_features(examples))

        X_comb = sp.hstack([X_sent, X_mid, X_heur], format="csr")

        self.cache.set(
            "features",
            cache_key,
            X_comb,
            {"shape": list(X_comb.shape), "nnz": X_comb.nnz, "split": split_name},
        )
        return X_comb
