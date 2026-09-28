# python cli.py --help

from typing import List, Dict, Any, Optional
from ..core.types import RelationExample
from .base import BaseDataset


class MavenEreDataset(BaseDataset):
    SOURCE_URL = "https://github.com/THU-KEG/MAVEN-ERE"
    PAPER_CITATION = "Wang et al., EMNLP 2022: MAVEN-ERE: A Unified Large-scale Dataset for Event Coreference, Temporal, Causal, and Subevent Relation Extraction"

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.train_examples: List[RelationExample] = []
        self.val_examples: List[RelationExample] = []
        self.test_examples: List[RelationExample] = []

    def load(self) -> "MavenEreDataset":
        return self

    def get_train_examples(self) -> List[RelationExample]:
        return self.train_examples

    def get_val_examples(self) -> List[RelationExample]:
        return self.val_examples

    def get_test_examples(self) -> List[RelationExample]:
        return self.test_examples

    def get_stats(self) -> Dict[str, Any]:
        return {
            "source": self.SOURCE_URL,
            "citation": self.PAPER_CITATION,
            "status": "unreleased_test_keys_codalab",
            "relation_definitions": ["CAUSE", "PRECONDITION"],
            "document_count": 4480,
            "causal_relations_count": 57992,
            "limitation": "Test annotations are withheld on CodaLab server. Document-level graph formulation rather than isolated pairwise sentence extraction.",
        }
