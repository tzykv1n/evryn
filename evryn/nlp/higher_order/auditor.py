# evryn higher-order
# evryn -s higher-order

from typing import List, Dict, Any
from collections import Counter
from .types import HigherOrderCandidate, HigherOrderCategory


class CandidateAuditor:

    def audit(self, candidates: List[HigherOrderCandidate]) -> Dict[str, Any]:
        semeval_cands = [c for c in candidates if c.source_dataset == "SemEval-2010_Task8"]

        unique_sents = set(c.sentence.strip() for c in semeval_cands)
        unique_tuples = set((c.entity1_text.strip().lower(), c.entity2_text.strip().lower()) for c in semeval_cands)

        cat_counts = Counter(c.category.value for c in semeval_cands)
        rule_counts = Counter(c.generation_rule for c in semeval_cands)

        explicit_causal = sum(1 for c in semeval_cands if any(
            t in c.sentence.lower() for t in ["cause", "caused", "induce", "lead to", "trigger", "produce", "generate", "result in"]
        ))
        implicit_causal = len(semeval_cands) - explicit_causal

        has_conjunction = sum(1 for c in semeval_cands if len(c.coordination_cues) > 0)
        has_temporal = sum(1 for c in semeval_cands if len(c.temporal_cues) > 0)

        coord_counter = Counter()
        for c in semeval_cands:
            for cue in c.coordination_cues:
                coord_counter[cue] += 1

        temp_counter = Counter()
        for c in semeval_cands:
            for t in c.temporal_cues:
                temp_counter[t] += 1

        return {
            "total_candidates": len(semeval_cands),
            "unique_sentences": len(unique_sents),
            "unique_entity_tuples": len(unique_tuples),
            "explicit_causal_count": explicit_causal,
            "implicit_causal_count": implicit_causal,
            "has_conjunction_count": has_conjunction,
            "has_temporal_count": has_temporal,
            "category_distribution": dict(cat_counts),
            "generation_rules": dict(rule_counts.most_common(6)),
            "top_coordination_cues": dict(coord_counter.most_common(5)),
            "top_temporal_cues": dict(temp_counter.most_common(5)),
            "control_count": len(candidates) - len(semeval_cands),
        }
