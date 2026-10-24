"""
Phase 1.6 Regression Test Suite.
Validates:
1. Passive genetic complementation / rescue triggers ('was restored by/upon/in', 'was rescued by').
2. Terminal disease phenotype direction invariant (rejecting Virulence/Host Survival as causes of genes).
3. Greek morphology normalization (Δ mutant prefix stripping, σ alternative sigma factor mapping).
4. Biofilm contextual canonicalization.
5. Negation and speculative evidence classification.
6. BioCause standoff recursive Theme dereferencing.
7. V1 vs V2 benchmark split isolation and immutability.
"""

import pytest
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.types import (
    ScientificDocument,
    PageBoundary,
    PaperMetadata,
    ParagraphSpan,
    SentenceSpan,
    CausalRelationType,
    EvidenceStatus,
)
from evryn.paper.real_benchmark import (
    CURATED_REAL_PAPERS_V1,
    CURATED_REAL_PAPERS_V2,
    get_curated_papers,
)
from evryn.datasets.biocause import BioCauseDataset


def _make_doc(text: str) -> ScientificDocument:
    return ScientificDocument(
        doc_id="test_doc",
        file_path="test.pdf",
        metadata=PaperMetadata(title="Test Document"),
        full_text=text,
        pages=[PageBoundary(page_number=1, start_char=0, end_char=len(text), char_count=len(text))],
        sections=[],
        paragraphs=[ParagraphSpan(paragraph_id="p1", section_title="Results", page_number=1, start_char=0, end_char=len(text), text=text)],
        sentences=[SentenceSpan(sentence_id="s1", paragraph_id="p1", section_title="Results", page_number=1, start_char=0, end_char=len(text), text=text)],
    )


class TestPhase16Regressions:

    def test_passive_genetic_complementation_restored(self):
        """Virulence restored upon complementation with cheB2 must extract cheB2 -> Virulence."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "As shown in Figure 3B the virulence was restored in the complemented cheB2 mutant."
        doc = _make_doc(sent)
        known = ["cheB2", "Virulence"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        edges = [(a.cause_canonical, a.effect_canonical) for a in res]
        assert ("cheB2", "Virulence") in edges
        assert ("Virulence", "cheB2") not in edges

    def test_passive_genetic_complementation_rescued(self):
        """Growth defect was rescued by salR must extract salR -> Growth."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "The defective virulence phenotype was mostly rescued upon reintroduction of salR."
        doc = _make_doc(sent)
        known = ["salR", "Virulence"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        edges = [(a.cause_canonical, a.effect_canonical) for a in res]
        assert ("salR", "Virulence") in edges
        assert ("Virulence", "salR") not in edges

    def test_terminal_phenotype_invariant_blocks_gene_cause(self):
        """Terminal phenotype (Virulence) cannot be extracted as causing a molecular gene (SalK)."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "High virulence induces transcription of salK and salR in pathogenic strains."
        doc = _make_doc(sent)
        known = ["salK", "salR", "Virulence"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        for a in res:
            assert a.cause_canonical != "Virulence", "Virulence must not be extracted as the cause of a gene."

    def test_terminal_phenotype_phenotype_interaction_preserved(self):
        """Interactions between two phenotypes (e.g. Bacterial Survival -> Virulence) must be preserved."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "Enhanced bacterial survival in the bloodstream promotes virulence in animal hosts."
        doc = _make_doc(sent)
        known = ["Bacterial Survival", "Virulence"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        edges = [(a.cause_canonical, a.effect_canonical) for a in res]
        assert ("Bacterial Survival", "Virulence") in edges

    def test_greek_delta_mutant_normalization(self):
        """Greek delta mutant prefix (ΔvicK) must normalize to VicK."""
        norm = PaperEntityNormalizer()
        known = ["VicK", "Virulence"]
        assert norm.canonicalize("ΔvicK", known_entities=known) == "VicK"
        assert norm.canonicalize("delta-vicK", known_entities=known) == "VicK"

    def test_greek_sigma_normalization(self):
        """Greek sigma (σE, σ(E)) must normalize to sigmaE."""
        norm = PaperEntityNormalizer()
        known = ["sigmaE", "RseA", "RpoE"]
        assert norm.canonicalize("σE", known_entities=known) == "sigmaE"
        assert norm.canonicalize("σ(E)", known_entities=known) == "sigmaE"

    def test_biofilm_contextual_canonicalization(self):
        """biofilm formation must canonicalize to Biofilm when Biofilm is known."""
        norm = PaperEntityNormalizer()
        known_biofilm = ["cyclic-di-GMP", "Biofilm", "Virulence"]
        assert norm.canonicalize("biofilm formation", known_entities=known_biofilm) == "Biofilm"
        assert norm.canonicalize("biofilm", known_entities=known_biofilm) == "Biofilm"

        # And vice-versa when Biofilm Formation is canonical
        known_formation = ["LuxR", "Biofilm Formation"]
        assert norm.canonicalize("biofilm", known_entities=known_formation) == "Biofilm Formation"

    def test_negation_flagging(self):
        """Statements with 'does not inhibit' must be flagged as is_negated=True."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "SeMac does not inhibit opsonophagocytosis of Streptococcus equi subsp. equi."
        doc = _make_doc(sent)
        known = ["SeMac", "Opsonophagocytosis"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        # When negated, assertion must have is_negated=True or REFUTED_NEGATION status
        for a in res:
            assert a.is_negated is True
            assert a.evidence_status == EvidenceStatus.REFUTED_NEGATION

    def test_speculation_uncertainty_score(self):
        """Speculative claims must have high uncertainty score >= 0.5."""
        norm = PaperEntityNormalizer()
        ext = PaperCausalExtractor(norm)
        sent = "We hypothesize that protein X might possibly activate gene Y."
        doc = _make_doc(sent)
        known = ["Protein X", "Gene Y"]
        res = ext.extract_assertions(doc, known_entities=known)
        
        for a in res:
            assert a.uncertainty_score >= 0.5
            assert a.evidence_status == EvidenceStatus.HYPOTHESIS_CLAIM

    def test_biocause_recursive_theme_dereferencing(self):
        """BioCause parser must not produce artificial self-referential relations (e.g. PhoQ -> PhoQ)."""
        dataset = BioCauseDataset().load()
        self_loops = 0
        total_rels = 0
        for doc in dataset.documents.values():
            for rel in doc.relations:
                total_rels += 1
                if rel.cause_text.strip().lower() == rel.effect_text.strip().lower():
                    self_loops += 1
        
        # In corrupted standoff it was 366/417 (87.8%). It must now be < 5% (only true feedback loops).
        assert (self_loops / total_rels) < 0.05, f"Spurious self-loops too high: {self_loops}/{total_rels}"

    def test_benchmark_v1_and_v2_isolation(self):
        """Benchmark V1 must retain historical papers; V2 must contain authenticated PMC2816692."""
        v1_papers = {p["pmcid"]: p for p in get_curated_papers("v1")}
        v2_papers = {p["pmcid"]: p for p in get_curated_papers("v2")}
        
        assert len(v1_papers) == 20
        assert len(v2_papers) == 20
        
        # PMC2816692 in V2 must be SrcA (Salmonella enterica)
        srca_v2 = v2_papers["PMC2816692"]
        assert "SrcA" in srca_v2["canonical_entities"]
        assert "SseL" in srca_v2["canonical_entities"]
        
        # V1 must remain immutable
        assert len(CURATED_REAL_PAPERS_V1) == 20
        assert len(CURATED_REAL_PAPERS_V2) == 20
