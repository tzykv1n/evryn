# python cli.py --help

import os
import re
import io
import json
import zipfile
import urllib.request
from typing import List, Dict, Any, Tuple, Optional
from sklearn.model_selection import train_test_split

from ..core.types import RelationExample, CausalRelationType
from ..core.config import DatasetConfig
from ..core.cache import ArtifactCache
from .base import BaseDataset


class SemEval2010Dataset(BaseDataset):
    DATA_URL = "https://github.com/JoelNiklaus/SemEval2010Task8/raw/main/SemEval2010_task8_all_data.zip"

    def __init__(self, config: Optional[DatasetConfig] = None, cache: Optional[ArtifactCache] = None):
        self.config = config or DatasetConfig()
        self.cache = cache or ArtifactCache()
        self.train_examples: List[RelationExample] = []
        self.val_examples: List[RelationExample] = []
        self.test_examples: List[RelationExample] = []

    def _download_and_extract(self) -> Tuple[str, str]:
        os.makedirs(self.config.data_dir, exist_ok=True)
        cands = [
            self.config.data_dir,
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "semeval2010"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "semeval2010"),
            "/home/tk/projects/evryn/data/semeval2010",
        ]
        for c in cands:
            c_train = os.path.join(c, "TRAIN_FILE.TXT")
            c_test = os.path.join(c, "TEST_FILE_FULL.TXT")
            if os.path.exists(c_train) and os.path.exists(c_test):
                return c_train, c_test

        req = urllib.request.Request(self.DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            zip_bytes = response.read()

        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        train_rel = "SemEval2010_task8_all_data/SemEval2010_task8_training/TRAIN_FILE.TXT"
        test_rel = "SemEval2010_task8_all_data/SemEval2010_task8_testing_keys/TEST_FILE_FULL.TXT"

        with open(train_path, "wb") as f:
            f.write(zf.read(train_rel))
        with open(test_path, "wb") as f:
            f.write(zf.read(test_rel))

        return train_path, test_path

    def _parse_file(self, file_path: str) -> List[RelationExample]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().replace("\r\n", "\n")

        blocks = content.strip().split("\n\n")
        examples = []
        for b in blocks:
            lines = [l.strip() for l in b.split("\n") if l.strip()]
            if len(lines) < 2:
                continue

            first_line = lines[0]
            parts = first_line.split("\t", 1)
            if len(parts) != 2:
                continue
            ex_id = parts[0].strip()
            raw_sent = parts[1].strip()
            if raw_sent.startswith('"') and raw_sent.endswith('"'):
                raw_sent = raw_sent[1:-1]

            rel_str = lines[1].strip()
            comment_str = lines[2].replace("Comment:", "").strip() if len(lines) >= 3 else ""

            m1 = re.search(r"<e1>(.*?)</e1>", raw_sent)
            m2 = re.search(r"<e2>(.*?)</e2>", raw_sent)
            if not m1 or not m2:
                continue

            clean_sent = re.sub(r"</?e[12]>", "", raw_sent)
            if m1.start() < m2.start():
                s1 = m1.start()
                e1 = s1 + len(m1.group(1))
                s2 = m2.start() - 9
                e2 = s2 + len(m2.group(1))
            else:
                s2 = m2.start()
                e2 = s2 + len(m2.group(1))
                s1 = m1.start() - 9
                e1 = s1 + len(m1.group(1))

            c_rel = CausalRelationType.from_str(rel_str)
            ex = RelationExample(
                example_id=ex_id,
                sentence=clean_sent,
                entity1_text=clean_sent[s1:e1],
                entity2_text=clean_sent[s2:e2],
                entity1_span=(s1, e1),
                entity2_span=(s2, e2),
                relation_type=c_rel,
                raw_label=rel_str,
                metadata={"comment": comment_str, "raw_sentence": raw_sent},
            )
            examples.append(ex)
        return examples

    def load(self) -> "SemEval2010Dataset":
        cache_key = f"semeval2010_{self.config.fingerprint()}"
        cached = self.cache.get("dataset", cache_key)
        if cached is not None:
            self.train_examples = cached["train"]
            self.val_examples = cached["val"]
            self.test_examples = cached["test"]
            return self

        train_path, test_path = self._download_and_extract()
        full_train = self._parse_file(train_path)
        self.test_examples = self._parse_file(test_path)

        train_labels = [int(ex.relation_type) for ex in full_train]
        tr_exs, val_exs = train_test_split(
            full_train,
            test_size=self.config.val_ratio,
            random_state=self.config.seed,
            stratify=train_labels,
        )
        self.train_examples = tr_exs
        self.val_examples = val_exs

        if self.config.max_samples is not None:
            self.train_examples = self.train_examples[: self.config.max_samples]

        self.cache.set(
            "dataset",
            cache_key,
            {"train": self.train_examples, "val": self.val_examples, "test": self.test_examples},
            {
                "num_train": len(self.train_examples),
                "num_val": len(self.val_examples),
                "num_test": len(self.test_examples),
            },
        )
        return self

    def get_train_examples(self) -> List[RelationExample]:
        return self.train_examples

    def get_val_examples(self) -> List[RelationExample]:
        return self.val_examples

    def get_test_examples(self) -> List[RelationExample]:
        return self.test_examples

    def get_stats(self) -> Dict[str, Any]:
        def _dist(exs: List[RelationExample]) -> Dict[str, int]:
            d = {"NO_RELATION": 0, "FORWARD": 0, "BACKWARD": 0}
            for e in exs:
                d[e.relation_type.name] += 1
            return d

        return {
            "train": {"total": len(self.train_examples), "distribution": _dist(self.train_examples)},
            "val": {"total": len(self.val_examples), "distribution": _dist(self.val_examples)},
            "test": {"total": len(self.test_examples), "distribution": _dist(self.test_examples)},
        }
