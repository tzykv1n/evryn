"""
SemEval-2010 Task 8: Multi-Way Classification of Semantic Relations
Between Pairs of Nominals — Causal Benchmark Adapter (Phase 3).

Provides an independent, general-domain evaluation track for Cause-Effect relations
to measure out-of-domain causal generalization without leaking into PMC biological metrics.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set


@dataclass
class SemEvalSample:
    sample_id: str
    raw_line: str
    clean_text: str
    e1_text: str
    e2_text: str
    e1_span: Tuple[int, int]
    e2_span: Tuple[int, int]
    relation_label: str
    is_causal: bool = False
    cause_entity: Optional[str] = None
    effect_entity: Optional[str] = None
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "clean_text": self.clean_text,
            "e1_text": self.e1_text,
            "e2_text": self.e2_text,
            "relation_label": self.relation_label,
            "is_causal": self.is_causal,
            "cause_entity": self.cause_entity,
            "effect_entity": self.effect_entity,
            "comment": self.comment,
        }


class SemEval2010Dataset:
    DEFAULT_DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "semeval2010"
    )

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or self.DEFAULT_DATA_DIR
        self.train_samples: List[SemEvalSample] = []
        self.test_samples: List[SemEvalSample] = []
        self.load_dataset()

    def _parse_file(self, filepath: str) -> List[SemEvalSample]:
        if not os.path.exists(filepath):
            return []

        samples: List[SemEvalSample] = []
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Line 1: 8001\t"The most common <e1>audits</e1> were about <e2>waste</e2>..."
            m = re.match(r"^(\d+)\s+\"?(.*?)\"?$", line)
            if not m:
                i += 1
                continue

            sample_id = m.group(1)
            raw_text = m.group(2)

            # Line 2: Relation label
            rel_label = lines[i + 1].strip() if i + 1 < len(lines) else "Other"

            # Line 3: Comment
            comment = ""
            if i + 2 < len(lines) and lines[i + 2].strip().startswith("Comment:"):
                comment = lines[i + 2].strip()[len("Comment:"):].strip()
                i += 4  # skip empty line
            else:
                i += 3

            # Extract e1 and e2
            m1 = re.search(r"<e1>(.*?)</e1>", raw_text)
            m2 = re.search(r"<e2>(.*?)</e2>", raw_text)

            if not m1 or not m2:
                continue

            e1_text = m1.group(1)
            e2_text = m2.group(1)

            # Strip markup for clean text
            clean_text = raw_text.replace("<e1>", "").replace("</e1>", "").replace("<e2>", "").replace("</e2>", "")
            e1_start = clean_text.find(e1_text)
            e1_end = e1_start + len(e1_text) if e1_start != -1 else 0
            e2_start = clean_text.find(e2_text)
            e2_end = e2_start + len(e2_text) if e2_start != -1 else 0

            # Causal relation determination
            is_causal = rel_label.startswith("Cause-Effect")
            cause_ent = None
            effect_ent = None

            if is_causal:
                if "(e1,e2)" in rel_label:
                    cause_ent = e1_text
                    effect_ent = e2_text
                elif "(e2,e1)" in rel_label:
                    cause_ent = e2_text
                    effect_ent = e1_text

            sample = SemEvalSample(
                sample_id=sample_id,
                raw_line=raw_text,
                clean_text=clean_text,
                e1_text=e1_text,
                e2_text=e2_text,
                e1_span=(e1_start, e1_end),
                e2_span=(e2_start, e2_end),
                relation_label=rel_label,
                is_causal=is_causal,
                cause_entity=cause_ent,
                effect_entity=effect_ent,
                comment=comment,
            )
            samples.append(sample)

        return samples

    def load_dataset(self):
        train_path = os.path.join(self.data_dir, "TRAIN_FILE.TXT")
        test_path = os.path.join(self.data_dir, "TEST_FILE_FULL.TXT")

        if os.path.exists(train_path):
            self.train_samples = self._parse_file(train_path)
        if os.path.exists(test_path):
            self.test_samples = self._parse_file(test_path)

    def get_causal_test_samples(self) -> List[SemEvalSample]:
        return [s for s in self.test_samples if s.is_causal]

    def evaluate_causal_predictions(
        self,
        predicted_pairs: Dict[str, Tuple[str, str]],  # sample_id -> (predicted_cause, predicted_effect)
    ) -> Dict[str, float]:
        """
        Evaluates causal classification performance on SemEval-2010 Task 8 Cause-Effect subset.
        Computes Precision, Recall, and F1 with strict directionality.
        """
        tp = 0
        fp = 0
        fn = 0

        norm = lambda s: re.sub(r"[^a-zA-Z0-9]+", "", s).lower().strip()

        for sample in self.test_samples:
            gold_is_causal = sample.is_causal
            pred_pair = predicted_pairs.get(sample.sample_id)

            if gold_is_causal:
                if pred_pair is not None:
                    pred_c, pred_e = pred_pair
                    # Strict directional entity match
                    if (
                        norm(pred_c) == norm(sample.cause_entity or "")
                        and norm(pred_e) == norm(sample.effect_entity or "")
                    ):
                        tp += 1
                    else:
                        fp += 1
                else:
                    fn += 1
            else:
                if pred_pair is not None:
                    fp += 1

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        return {
            "total_test_samples": len(self.test_samples),
            "total_gold_causal": len(self.get_causal_test_samples()),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }
