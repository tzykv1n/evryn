# evryn datasets biocause
# pytest tests/test_dataset_adapters.py

import os
import re
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class BioCauseAnnotation:
    id: str
    label: str
    start: int
    end: int
    text: str


@dataclass
class BioCauseRelation:
    id: str
    doc_id: str
    rel_type: str
    cause_id: str
    cause_text: str
    cause_span: Tuple[int, int]
    effect_id: str
    effect_text: str
    effect_span: Tuple[int, int]
    trigger_id: Optional[str] = None
    trigger_text: Optional[str] = None
    trigger_span: Optional[Tuple[int, int]] = None
    evidence_id: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_span: Optional[Tuple[int, int]] = None
    is_cross_sentence: bool = False


@dataclass
class BioCauseDocument:
    doc_id: str
    pmcid: str
    section_name: str
    text: str
    annotations: Dict[str, BioCauseAnnotation] = field(default_factory=dict)
    relations: List[BioCauseRelation] = field(default_factory=list)
    license: str = "CC BY-NC-SA 3.0"


class BioCauseDataset:
    DEFAULT_ZIP_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "established", "biocause", "biocause.zip"
    )

    def __init__(self, zip_path: Optional[str] = None):
        self.zip_path = zip_path or self.DEFAULT_ZIP_PATH
        self.documents: Dict[str, BioCauseDocument] = {}
        self._loaded = False

    def load(self) -> "BioCauseDataset":
        if not os.path.exists(self.zip_path):
            raise FileNotFoundError(f"BioCause zip archive not found at {self.zip_path}")

        raw_files: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for name in zf.namelist():
                if not name.startswith("BioCause_corpus/"):
                    continue
                basename = os.path.basename(name)
                if not basename:
                    continue
                root, ext = os.path.splitext(basename)
                if ext not in (".ann", ".txt"):
                    continue
                content = zf.read(name).decode("utf-8", errors="replace")
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

    def _parse_document(self, doc_id: str, text: str, ann: str) -> BioCauseDocument:
        parts = doc_id.split("-")
        pmcid = parts[0] if parts else doc_id
        section_name = "-".join(parts[1:]) if len(parts) > 1 else "Unknown"

        annotations: Dict[str, BioCauseAnnotation] = {}
        events: List[Tuple[str, str, Dict[str, str]]] = []
        standoff_relations: List[Tuple[str, str, str, str]] = []

        for line in ann.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("T"):
                row = line.split("\t", 2)
                if len(row) >= 3:
                    tid = row[0]
                    type_spans = row[1].split()
                    label = type_spans[0]
                    try:
                        start = int(type_spans[1])
                        end = int(type_spans[-1])
                    except (ValueError, IndexError):
                        start, end = 0, 0
                    t_text = row[2]
                    annotations[tid] = BioCauseAnnotation(
                        id=tid, label=label, start=start, end=end, text=t_text
                    )
            elif line.startswith("E"):
                row = line.split("\t", 2)
                if len(row) >= 2:
                    eid = row[0]
                    tokens = row[1].split()
                    if not tokens:
                        continue
                    event_type, trigger_id = tokens[0].split(":", 1) if ":" in tokens[0] else (tokens[0], "")
                    args: Dict[str, str] = {}
                    for tok in tokens[1:]:
                        if ":" in tok:
                            arg_role, arg_tid = tok.split(":", 1)
                            args[arg_role] = arg_tid
                    events.append((eid, event_type, {"_trigger": trigger_id, **args}))
            elif line.startswith("R"):
                row = line.split("\t", 2)
                if len(row) >= 2:
                    rid = row[0]
                    tokens = row[1].split()
                    if len(tokens) >= 3:
                        rtype = tokens[0]
                        arg1 = tokens[1].split(":", 1)[1] if ":" in tokens[1] else tokens[1]
                        arg2 = tokens[2].split(":", 1)[1] if ":" in tokens[2] else tokens[2]
                        standoff_relations.append((rid, rtype, arg1, arg2))

        sentence_offsets = self._compute_sentence_offsets(text)
        relations: List[BioCauseRelation] = []

        for eid, etype, args in events:
            if "Causality" in etype or "regulation" in etype.lower():
                cause_id = args.get("Cause") or args.get("Theme")
                effect_id = args.get("Effect") or args.get("Cause")
                evidence_id = args.get("Evidence")
                trigger_id = args.get("_trigger")

                if cause_id and effect_id and cause_id in annotations and effect_id in annotations:
                    c_ann = annotations[cause_id]
                    e_ann = annotations[effect_id]
                    t_ann = annotations.get(trigger_id) if trigger_id else None
                    ev_ann = annotations.get(evidence_id) if evidence_id else None

                    is_cross = self._is_cross_sentence(c_ann.start, e_ann.start, sentence_offsets)
                    rel = BioCauseRelation(
                        id=eid,
                        doc_id=doc_id,
                        rel_type=etype,
                        cause_id=cause_id,
                        cause_text=c_ann.text,
                        cause_span=(c_ann.start, c_ann.end),
                        effect_id=effect_id,
                        effect_text=e_ann.text,
                        effect_span=(e_ann.start, e_ann.end),
                        trigger_id=trigger_id if t_ann else None,
                        trigger_text=t_ann.text if t_ann else None,
                        trigger_span=(t_ann.start, t_ann.end) if t_ann else None,
                        evidence_id=evidence_id if ev_ann else None,
                        evidence_text=ev_ann.text if ev_ann else None,
                        evidence_span=(ev_ann.start, ev_ann.end) if ev_ann else None,
                        is_cross_sentence=is_cross,
                    )
                    relations.append(rel)

        return BioCauseDocument(
            doc_id=doc_id,
            pmcid=pmcid,
            section_name=section_name,
            text=text,
            annotations=annotations,
            relations=relations,
        )

    def _compute_sentence_offsets(self, text: str) -> List[Tuple[int, int]]:
        offsets = []
        start = 0
        pattern = re.compile(r"(?<=[.!?])\s+|\n\n+")
        for match in pattern.finditer(text):
            end = match.start()
            if end > start:
                offsets.append((start, end))
            start = match.end()
        if start < len(text):
            offsets.append((start, len(text)))
        return offsets

    def _is_cross_sentence(self, pos_a: int, pos_b: int, sentence_offsets: List[Tuple[int, int]]) -> bool:
        idx_a = -1
        idx_b = -1
        for idx, (s, e) in enumerate(sentence_offsets):
            if s <= pos_a <= e:
                idx_a = idx
            if s <= pos_b <= e:
                idx_b = idx
        if idx_a != -1 and idx_b != -1:
            return idx_a != idx_b
        return False

    def get_splits(self, train_ratio: float = 0.70, dev_ratio: float = 0.15) -> Dict[str, List[BioCauseDocument]]:
        if not self._loaded:
            self.load()

        all_pmcids = sorted(list({doc.pmcid for doc in self.documents.values()}))
        n_total = len(all_pmcids)
        n_train = int(n_total * train_ratio)
        n_dev = int(n_total * dev_ratio)

        train_pmcs = set(all_pmcids[:n_train])
        dev_pmcs = set(all_pmcids[n_train:n_train + n_dev])
        test_pmcs = set(all_pmcids[n_train + n_dev:])

        splits: Dict[str, List[BioCauseDocument]] = {"train": [], "dev": [], "test": []}
        for doc in self.documents.values():
            if doc.pmcid in train_pmcs:
                splits["train"].append(doc)
            elif doc.pmcid in dev_pmcs:
                splits["dev"].append(doc)
            else:
                splits["test"].append(doc)

        return splits

    def summary_statistics(self) -> Dict[str, Any]:
        if not self._loaded:
            self.load()

        total_docs = len(self.documents)
        unique_pmcs = len({doc.pmcid for doc in self.documents.values()})
        total_annotations = sum(len(d.annotations) for d in self.documents.values())
        total_relations = sum(len(d.relations) for d in self.documents.values())
        causal_relations = sum(
            sum(1 for r in d.relations if "causality" in r.rel_type.lower())
            for d in self.documents.values()
        )
        cross_sentence = sum(
            sum(1 for r in d.relations if r.is_cross_sentence)
            for d in self.documents.values()
        )

        return {
            "total_documents": total_docs,
            "unique_pmc_articles": unique_pmcs,
            "total_annotations": total_annotations,
            "total_relations": total_relations,
            "causality_relations": causal_relations,
            "cross_sentence_relations": cross_sentence,
            "license": "CC BY-NC-SA 3.0",
            "provenance": "NaCTeM BioCause Corpus (Mihaila et al., BMC Bioinformatics 2013)",
        }


def load_biocause(zip_path: Optional[str] = None) -> BioCauseDataset:
    dataset = BioCauseDataset(zip_path=zip_path)
    return dataset.load()
