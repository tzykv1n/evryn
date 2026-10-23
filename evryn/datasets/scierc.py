# evryn datasets scierc
# pytest tests/test_dataset_adapters.py

import os
import tarfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class SciERCEntity:
    id: str
    label: str
    start: int
    end: int
    text: str


@dataclass
class SciERCRelation:
    id: str
    doc_id: str
    rel_type: str
    arg1_id: str
    arg1_text: str
    arg1_span: Tuple[int, int]
    arg2_id: str
    arg2_text: str
    arg2_span: Tuple[int, int]


@dataclass
class SciERCDocument:
    doc_id: str
    text: str
    entities: Dict[str, SciERCEntity] = field(default_factory=dict)
    relations: List[SciERCRelation] = field(default_factory=list)
    license: str = "CC BY-NC 4.0 / Research Use"
    schema_domain: str = "Scientific Entity and Relation Extraction"


class SciERCDataset:
    DEFAULT_TAR_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "established", "scierc", "sciERC_raw.tar.gz"
    )

    VALID_RELATION_TYPES = {
        "USED-FOR",
        "FEATURE-OF",
        "HYPONYM-OF",
        "PART-OF",
        "EVALUATE-FOR",
        "CONJUNCTION",
        "COMPARE",
    }

    def __init__(self, tar_path: Optional[str] = None):
        self.tar_path = tar_path or self.DEFAULT_TAR_PATH
        self.documents: Dict[str, SciERCDocument] = {}
        self._loaded = False

    def load(self) -> "SciERCDataset":
        if not os.path.exists(self.tar_path):
            raise FileNotFoundError(f"SciERC archive not found at {self.tar_path}")

        raw_files: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        with tarfile.open(self.tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                basename = os.path.basename(member.name)
                root, ext = os.path.splitext(basename)
                if ext not in (".ann", ".txt"):
                    continue
                f = tar.extractfile(member)
                if f is None:
                    continue
                content = f.read().decode("utf-8", errors="replace")
                if root not in raw_files:
                    raw_files[root] = (None, None)
                if ext == ".ann":
                    raw_files[root] = (content, raw_files[root][1])
                elif ext == ".txt":
                    raw_files[root] = (raw_files[root][0], content)

        for doc_id, (ann_content, txt_content) in sorted(raw_files.items()):
            if txt_content is None:
                continue
            ann_content = ann_content or ""
            doc = self._parse_document(doc_id, txt_content, ann_content)
            self.documents[doc_id] = doc

        self._loaded = True
        return self

    def _parse_document(self, doc_id: str, text: str, ann: str) -> SciERCDocument:
        entities: Dict[str, SciERCEntity] = {}
        relations: List[SciERCRelation] = []

        for line in ann.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("T"):
                parts = line.split("\t", 2)
                if len(parts) >= 3:
                    tid = parts[0]
                    type_span = parts[1].split()
                    label = type_span[0]
                    try:
                        start = int(type_span[1])
                        end = int(type_span[-1])
                    except (ValueError, IndexError):
                        start, end = 0, 0
                    ent_text = parts[2]
                    entities[tid] = SciERCEntity(
                        id=tid, label=label, start=start, end=end, text=ent_text
                    )
            elif line.startswith("R"):
                parts = line.split("\t", 2)
                if len(parts) >= 2:
                    rid = parts[0]
                    tokens = parts[1].split()
                    if len(tokens) >= 3:
                        rtype = tokens[0]
                        arg1_tok = tokens[1].split(":", 1)[1] if ":" in tokens[1] else tokens[1]
                        arg2_tok = tokens[2].split(":", 1)[1] if ":" in tokens[2] else tokens[2]
                        if arg1_tok in entities and arg2_tok in entities:
                            ent1 = entities[arg1_tok]
                            ent2 = entities[arg2_tok]
                            rel = SciERCRelation(
                                id=rid,
                                doc_id=doc_id,
                                rel_type=rtype,
                                arg1_id=arg1_tok,
                                arg1_text=ent1.text,
                                arg1_span=(ent1.start, ent1.end),
                                arg2_id=arg2_tok,
                                arg2_text=ent2.text,
                                arg2_span=(ent2.start, ent2.end),
                            )
                            relations.append(rel)

        return SciERCDocument(
            doc_id=doc_id,
            text=text,
            entities=entities,
            relations=relations,
        )

    def get_splits(self, train_ratio: float = 0.70, dev_ratio: float = 0.15) -> Dict[str, List[SciERCDocument]]:
        if not self._loaded:
            self.load()

        all_doc_ids = sorted(list(self.documents.keys()))
        n_total = len(all_doc_ids)
        n_train = int(n_total * train_ratio)
        n_dev = int(n_total * dev_ratio)

        train_ids = set(all_doc_ids[:n_train])
        dev_ids = set(all_doc_ids[n_train:n_train + n_dev])

        splits: Dict[str, List[SciERCDocument]] = {"train": [], "dev": [], "test": []}
        for doc_id, doc in self.documents.items():
            if doc_id in train_ids:
                splits["train"].append(doc)
            elif doc_id in dev_ids:
                splits["dev"].append(doc)
            else:
                splits["test"].append(doc)

        return splits

    def summary_statistics(self) -> Dict[str, Any]:
        if not self._loaded:
            self.load()

        total_docs = len(self.documents)
        total_entities = sum(len(d.entities) for d in self.documents.values())
        total_relations = sum(len(d.relations) for d in self.documents.values())

        relation_counts: Dict[str, int] = {}
        for d in self.documents.values():
            for r in d.relations:
                relation_counts[r.rel_type] = relation_counts.get(r.rel_type, 0) + 1

        entity_counts: Dict[str, int] = {}
        for d in self.documents.values():
            for e in d.entities.values():
                entity_counts[e.label] = entity_counts.get(e.label, 0) + 1

        return {
            "total_documents": total_docs,
            "total_entities": total_entities,
            "total_relations": total_relations,
            "entity_type_counts": entity_counts,
            "relation_type_counts": relation_counts,
            "license": "CC BY-NC 4.0 / Research Use",
            "provenance": "SciERC Corpus (Luan et al., EMNLP 2018)",
            "schema_fidelity": "Original relations preserved; no causal relabeling applied.",
        }


def load_scierc(tar_path: Optional[str] = None) -> SciERCDataset:
    dataset = SciERCDataset(tar_path=tar_path)
    return dataset.load()
