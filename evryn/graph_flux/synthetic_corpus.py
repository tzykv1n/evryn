# evryn graph
# evryn -s graph

import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Any

from ..core.types import NormalizedEntity, ScientificDomain
from ..normalization.normalizer import RelationNormalizer
from ..nlp.higher_order.types import HigherOrderCategory
from .types import (
    CausalGraphEdge,
    MultiSentenceDocument,
    GraphHigherOrderCandidate,
    CandidatePattern,
)


class MultiSentenceBenchmarkGenerator:

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)
        self.normalizer = RelationNormalizer()

    def generate_corpus(self, n_documents: int = 60) -> List[MultiSentenceDocument]:
        docs: List[MultiSentenceDocument] = []
        mechanisms = [
            "independent_pairwise",
            "additive_pathway",
            "multiplicative_interaction",
            "nonlinear_interaction",
            "causal_cascade",
            "latent_confounding",
            "explicit_textual_synergy",
            "implicit_synergy",
            "cross_sentence_synergy",
            "irrelevant_cooccurrence",
            "temporal_mismatch",
        ]

        for i in range(n_documents):
            mech = mechanisms[i % len(mechanisms)]
            doc = self._create_document(doc_idx=i + 1, mechanism=mech)
            docs.append(doc)
        return docs

    def _create_document(self, doc_idx: int, mechanism: str) -> MultiSentenceDocument:
        doc_id = f"doc_synth_{doc_idx:03d}"
        e_names = [f"Gene_{chr(65 + j)}_{doc_idx}" for j in range(6)]
        pathway_name = f"Pathway_MAPK_{doc_idx}"
        phenotype_name = f"Phenotype_Apoptosis_{doc_idx}"
        confounder_name = f"Factor_Inflammation_{doc_idx}"

        sentences: List[str] = []
        edges: List[CausalGraphEdge] = []
        ground_truth: List[Dict[str, Any]] = []

        ent_a = self.normalizer.create_entity(e_names[0], domain=ScientificDomain.BIOMEDICINE)
        ent_b = self.normalizer.create_entity(e_names[1], domain=ScientificDomain.BIOMEDICINE)
        ent_c = self.normalizer.create_entity(phenotype_name, domain=ScientificDomain.BIOMEDICINE)
        ent_p = self.normalizer.create_entity(pathway_name, domain=ScientificDomain.BIOMEDICINE)
        ent_u = self.normalizer.create_entity(confounder_name, domain=ScientificDomain.BIOMEDICINE)
        entities = [ent_a, ent_b, ent_c, ent_p, ent_u]

        if mechanism == "independent_pairwise":
            s1 = f"{ent_a.canonical_name} induces {ent_c.canonical_name} under standard assays."
            s2 = f"Separately, {ent_b.canonical_name} stimulates {ent_c.canonical_name} through independent receptors."
            s3 = f"Both agents show additive effects on {ent_c.canonical_name} without cooperative enhancement."
            sentences = [s1, s2, s3]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.92,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(s1.find(ent_c.canonical_name), s1.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_b.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_b.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.89,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(s2.find(ent_b.canonical_name), s2.find(ent_b.canonical_name) + len(ent_b.canonical_name)),
                target_span=(s2.find(ent_c.canonical_name), s2.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=2,
            )
            edges = [e1, e2]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.PAIRWISE_DECOMPOSABLE.value,
            })

        elif mechanism == "additive_pathway":
            s1 = f"{ent_a.canonical_name} activates the downstream {ent_p.canonical_name} cascade."
            s2 = f"Concurrently, {ent_b.canonical_name} upregulates {ent_p.canonical_name} via parallel phosphorylation."
            s3 = f"Activation of {ent_p.canonical_name} subsequently triggers {ent_c.canonical_name}."
            sentences = [s1, s2, s3]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_p.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_p.canonical_name,
                relation_type="FORWARD",
                confidence=0.94,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(s1.find(ent_p.canonical_name), s1.find(ent_p.canonical_name) + len(ent_p.canonical_name)),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_b.entity_id,
                target_id=ent_p.entity_id,
                source_name=ent_b.canonical_name,
                target_name=ent_p.canonical_name,
                relation_type="FORWARD",
                confidence=0.91,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(s2.find(ent_b.canonical_name), s2.find(ent_b.canonical_name) + len(ent_b.canonical_name)),
                target_span=(s2.find(ent_p.canonical_name), s2.find(ent_p.canonical_name) + len(ent_p.canonical_name)),
                temporal_order=1,
            )
            e3 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_03",
                source_id=ent_p.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_p.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.95,
                sentence_id="s3",
                sentence_text=s3,
                document_id=doc_id,
                source_span=(s3.find(ent_p.canonical_name), s3.find(ent_p.canonical_name) + len(ent_p.canonical_name)),
                target_span=(s3.find(ent_c.canonical_name), s3.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=2,
            )
            edges = [e1, e2, e3]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.PAIRWISE_DECOMPOSABLE.value,
            })

        elif mechanism in ("multiplicative_interaction", "explicit_textual_synergy", "cross_sentence_synergy"):
            s1 = f"Exposure to {ent_a.canonical_name} sensitizes cells by modifying chromatin accessibility."
            s2 = f"Subsequent treatment with {ent_b.canonical_name} strongly engages transcriptional machinery."
            s3 = f"The combined co-administration of {ent_a.canonical_name} and {ent_b.canonical_name} produces synergistic elevation of {ent_c.canonical_name}."
            sentences = [s1, s2, s3]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.88,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(0, 0),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_b.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_b.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.87,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(0, len(ent_b.canonical_name)),
                target_span=(0, 0),
                temporal_order=2,
            )
            e3 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_03",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.96,
                sentence_id="s3",
                sentence_text=s3,
                document_id=doc_id,
                source_span=(s3.find(ent_a.canonical_name), s3.find(ent_a.canonical_name) + len(ent_a.canonical_name)),
                target_span=(s3.find(ent_c.canonical_name), s3.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=3,
            )
            edges = [e1, e2, e3]
            cat = HigherOrderCategory.HIGHER_ORDER_INTERACTION if mechanism == "multiplicative_interaction" else HigherOrderCategory.JOINT_CAUSE
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": cat.value,
            })

        elif mechanism in ("nonlinear_interaction", "implicit_synergy"):
            s1 = f"{ent_a.canonical_name} recruits regulatory complexes to the promoter."
            s2 = f"{ent_b.canonical_name} stabilizes the ternary elongation factor."
            s3 = f"When both {ent_a.canonical_name} and {ent_b.canonical_name} are co-present, {ent_c.canonical_name} expression increases exponentially."
            sentences = [s1, s2, s3]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.85,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(0, 0),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_b.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_b.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.86,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(0, len(ent_b.canonical_name)),
                target_span=(0, 0),
                temporal_order=1,
            )
            edges = [e1, e2]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.HIGHER_ORDER_INTERACTION.value,
            })

        elif mechanism == "causal_cascade":
            s1 = f"{ent_a.canonical_name} directly activates transcription of {ent_b.canonical_name}."
            s2 = f"Elevated {ent_b.canonical_name} then drives the downstream emergence of {ent_c.canonical_name}."
            sentences = [s1, s2]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_b.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_b.canonical_name,
                relation_type="FORWARD",
                confidence=0.95,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(s1.find(ent_b.canonical_name), s1.find(ent_b.canonical_name) + len(ent_b.canonical_name)),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_b.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_b.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.93,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(s2.find(ent_b.canonical_name), s2.find(ent_b.canonical_name) + len(ent_b.canonical_name)),
                target_span=(s2.find(ent_c.canonical_name), s2.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=2,
            )
            edges = [e1, e2]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.CAUSAL_CASCADE.value,
            })

        elif mechanism == "latent_confounding":
            s1 = f"Systemic {ent_u.canonical_name} stimulates expression of {ent_a.canonical_name}."
            s2 = f"Concurrently, {ent_u.canonical_name} triggers rapid progression of {ent_c.canonical_name}."
            s3 = f"Statistical correlation between {ent_a.canonical_name} and {ent_c.canonical_name} is mediated by {ent_u.canonical_name}."
            sentences = [s1, s2, s3]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_u.entity_id,
                target_id=ent_a.entity_id,
                source_name=ent_u.canonical_name,
                target_name=ent_a.canonical_name,
                relation_type="FORWARD",
                confidence=0.91,
                sentence_id="s1",
                sentence_text=s1,
                document_id=doc_id,
                source_span=(0, len(ent_u.canonical_name)),
                target_span=(s1.find(ent_a.canonical_name), s1.find(ent_a.canonical_name) + len(ent_a.canonical_name)),
                temporal_order=1,
            )
            e2 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_02",
                source_id=ent_u.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_u.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.92,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(s2.find(ent_u.canonical_name), s2.find(ent_u.canonical_name) + len(ent_u.canonical_name)),
                target_span=(s2.find(ent_c.canonical_name), s2.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=1,
            )
            e3 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_03",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="CONFOUNDED",
                confidence=0.84,
                sentence_id="s3",
                sentence_text=s3,
                document_id=doc_id,
                source_span=(s3.find(ent_a.canonical_name), s3.find(ent_a.canonical_name) + len(ent_a.canonical_name)),
                target_span=(s3.find(ent_c.canonical_name), s3.find(ent_c.canonical_name) + len(ent_c.canonical_name)),
                temporal_order=2,
            )
            edges = [e1, e2, e3]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.CONFOUNDED.value,
            })

        elif mechanism == "temporal_mismatch":
            s1 = f"{ent_c.canonical_name} manifested within the first 24 hours of observation."
            s2 = f"Administration of {ent_a.canonical_name} followed on day 3."
            sentences = [s1, s2]

            e1 = CausalGraphEdge(
                edge_id=f"e_{doc_id}_01",
                source_id=ent_a.entity_id,
                target_id=ent_c.entity_id,
                source_name=ent_a.canonical_name,
                target_name=ent_c.canonical_name,
                relation_type="FORWARD",
                confidence=0.72,
                sentence_id="s2",
                sentence_text=s2,
                document_id=doc_id,
                source_span=(0, len(ent_a.canonical_name)),
                target_span=(0, 0),
                temporal_order=-1,
            )
            edges = [e1]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.TEMPORAL_RELATION.value,
            })

        else:
            s1 = f"{ent_a.canonical_name} and {ent_b.canonical_name} are widely studied in cellular physiology."
            s2 = f"{ent_c.canonical_name} remains a prominent clinical marker."
            sentences = [s1, s2]
            ground_truth.append({
                "sources": [ent_a.entity_id, ent_b.entity_id],
                "target": ent_c.entity_id,
                "category": HigherOrderCategory.INSUFFICIENT_EVIDENCE.value,
            })

        return MultiSentenceDocument(
            doc_id=doc_id,
            title=f"Synthetic Study {doc_idx}: Investigation of {mechanism}",
            sentences=sentences,
            entities=entities,
            edges=edges,
            ground_truth_higher_order=ground_truth,
            mechanism_label=mechanism,
        )

    def inject_extraction_noise(
        self,
        docs: List[MultiSentenceDocument],
        noise_rate: float = 0.10,
    ) -> List[MultiSentenceDocument]:
        if noise_rate <= 0.0:
            return docs

        noisy_docs: List[MultiSentenceDocument] = []
        rng = random.Random(self.seed + int(noise_rate * 1000))

        for doc in docs:
            noisy_edges: List[CausalGraphEdge] = []
            for edge in doc.edges:
                u = rng.random()
                if u < noise_rate * 0.4:
                    continue
                elif u < noise_rate * 0.7:
                    rev_type = "BACKWARD" if edge.relation_type == "FORWARD" else "FORWARD"
                    noisy_e = CausalGraphEdge(
                        edge_id=edge.edge_id + "_rev",
                        source_id=edge.target_id,
                        target_id=edge.source_id,
                        source_name=edge.target_name,
                        target_name=edge.source_name,
                        relation_type=rev_type,
                        confidence=max(0.2, edge.confidence - 0.25),
                        sentence_id=edge.sentence_id,
                        sentence_text=edge.sentence_text,
                        document_id=edge.document_id,
                        source_span=edge.target_span,
                        target_span=edge.source_span,
                        temporal_order=edge.temporal_order,
                    )
                    noisy_edges.append(noisy_e)
                else:
                    noisy_edges.append(edge)

            if rng.random() < noise_rate and len(doc.entities) >= 2:
                src_ent, tgt_ent = rng.sample(doc.entities, 2)
                spurious_e = CausalGraphEdge(
                    edge_id=f"e_spurious_{doc.doc_id}_{len(noisy_edges)}",
                    source_id=src_ent.entity_id,
                    target_id=tgt_ent.entity_id,
                    source_name=src_ent.canonical_name,
                    target_name=tgt_ent.canonical_name,
                    relation_type="FORWARD",
                    confidence=0.45,
                    sentence_id="s_spurious",
                    sentence_text="Spurious co-occurrence in text.",
                    document_id=doc.doc_id,
                    source_span=(0, 5),
                    target_span=(6, 10),
                    temporal_order=1,
                )
                noisy_edges.append(spurious_e)

            noisy_doc = MultiSentenceDocument(
                doc_id=doc.doc_id,
                title=doc.title,
                sentences=doc.sentences,
                entities=doc.entities,
                edges=noisy_edges,
                ground_truth_higher_order=doc.ground_truth_higher_order,
                mechanism_label=doc.mechanism_label,
                metadata=doc.metadata,
            )
            noisy_docs.append(noisy_doc)

        return noisy_docs
