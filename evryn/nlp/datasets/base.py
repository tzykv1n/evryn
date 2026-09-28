# python cli.py --help

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ..core.types import RelationExample


class BaseDataset(ABC):

    @abstractmethod
    def load(self) -> "BaseDataset":
        pass

    @abstractmethod
    def get_train_examples(self) -> List[RelationExample]:
        pass

    @abstractmethod
    def get_val_examples(self) -> List[RelationExample]:
        pass

    @abstractmethod
    def get_test_examples(self) -> List[RelationExample]:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass
