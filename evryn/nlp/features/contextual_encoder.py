# python cli.py contextual

import os
import torch
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel

from ..core.types import RelationExample
from ..core.config import ContextualConfig
from ..core.cache import ArtifactCache


class ContextualEncoder:

    def __init__(self, config: Optional[ContextualConfig] = None, cache: Optional[ArtifactCache] = None):
        self.config = config or ContextualConfig()
        self.cache = cache or ArtifactCache()
        self.device = torch.device("cpu")
        self.tokenizer = None
        self.model = None

    def _init_model(self):
        if self.tokenizer is None or self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            self.model = AutoModel.from_pretrained(self.config.model_name)
            self.model.to(self.device)
            self.model.eval()

    def encode_examples(
        self,
        examples: List[RelationExample],
        split_name: str = "train",
        dataset_hash: str = "default",
    ) -> np.ndarray:
        cache_key = f"ctx_{split_name}_{dataset_hash}_{self.config.fingerprint()}"
        cached = self.cache.get("contextual_embeddings", cache_key)
        if cached is not None:
            return cached

        self._init_model()

        texts = []
        for ex in examples:
            s1, e1 = ex.entity1_span
            s2, e2 = ex.entity2_span
            if s1 < s2:
                t = f"{ex.sentence[:s1]} [E1] {ex.sentence[s1:e1]} [/E1] {ex.sentence[e1:s2]} [E2] {ex.sentence[s2:e2]} [/E2] {ex.sentence[e2:]}"
            else:
                t = f"{ex.sentence[:s2]} [E2] {ex.sentence[s2:e2]} [/E2] {ex.sentence[e2:s1]} [E1] {ex.sentence[s1:e1]} [/E1] {ex.sentence[e1:]}"
            texts.append(t)

        all_embs = []
        batch_size = self.config.batch_size

        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                b_texts = texts[i : i + batch_size]
                b_exs = examples[i : i + batch_size]

                inputs = self.tokenizer(
                    b_texts,
                    padding=True,
                    truncation=True,
                    max_length=self.config.max_length,
                    return_tensors="pt",
                ).to(self.device)

                outputs = self.model(**inputs)
                last_hidden = outputs.last_hidden_state
                cls_rep = last_hidden[:, 0, :]

                input_ids = inputs["input_ids"]
                e1_open_id = self.tokenizer.encode("[E1]", add_special_tokens=False)
                e1_close_id = self.tokenizer.encode("[/E1]", add_special_tokens=False)
                e2_open_id = self.tokenizer.encode("[E2]", add_special_tokens=False)
                e2_close_id = self.tokenizer.encode("[/E2]", add_special_tokens=False)

                b_features = []
                for b_idx in range(len(b_texts)):
                    toks = input_ids[b_idx].tolist()
                    h = last_hidden[b_idx]

                    def _get_span_rep(tok_seq, open_toks, close_toks, fallback_vec):
                        try:
                            start_idx = -1
                            end_idx = -1
                            for pos in range(len(tok_seq) - len(open_toks) + 1):
                                if tok_seq[pos : pos + len(open_toks)] == open_toks:
                                    start_idx = pos + len(open_toks)
                                    break
                            if start_idx != -1:
                                for pos in range(start_idx, len(tok_seq) - len(close_toks) + 1):
                                    if tok_seq[pos : pos + len(close_toks)] == close_toks:
                                        end_idx = pos
                                        break
                            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                                return h[start_idx:end_idx].mean(dim=0)
                            return fallback_vec
                        except Exception:
                            return fallback_vec

                    cls_vec = cls_rep[b_idx]
                    e1_vec = _get_span_rep(toks, e1_open_id, e1_close_id, cls_vec)
                    e2_vec = _get_span_rep(toks, e2_open_id, e2_close_id, cls_vec)

                    diff_vec = e1_vec - e2_vec
                    prod_vec = e1_vec * e2_vec

                    if self.config.include_interactions:
                        feat = torch.cat([cls_vec, e1_vec, e2_vec, diff_vec, prod_vec], dim=-1)
                    else:
                        feat = torch.cat([cls_vec, e1_vec, e2_vec], dim=-1)
                    b_features.append(feat.cpu().numpy())

                all_embs.append(np.array(b_features, dtype=np.float32))

        X_mat = np.vstack(all_embs)
        self.cache.set(
            "contextual_embeddings",
            cache_key,
            X_mat,
            {
                "shape": list(X_mat.shape),
                "model_name": self.config.model_name,
                "split": split_name,
            },
        )
        return X_mat
