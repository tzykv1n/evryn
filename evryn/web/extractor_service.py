import os
import re
import math
import uuid
from typing import List, Dict, Any, Optional, Tuple

from evryn.paper.types import (
    ScientificDocument,
    CausalAssertion,
    CrossPageLink,
    PaperCausalGraph,
)
from evryn.paper.normalizer import PaperEntityNormalizer, GLOBAL_SYNONYMS
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.graph_builder import PaperGraphBuilder
from evryn.web.db import SessionStore
from evryn.web.document_parser import DocumentParser


POSITIVE_STATE_PATTERNS = [
    (re.compile(r"^(?:an?\s+)?(?:(?:\+|-)?\d+(?:\.\d+)?(?:%|-?fold|x)?\s+)?(?:increase|rise|elevation|upregulation|activation|overexpression|induction|stimulation|hyperactivation|gain|accumulation|enhancement)\s+(?:in|of)\s+", re.IGNORECASE), "Increase"),
    (re.compile(r"^(?:(?:\+|-)?\d+(?:\.\d+)?(?:%|-?fold|x)?\s+)?(?:increased|elevated|higher|high|upregulated|activated|overexpressed|stimulated|enhanced)\s+", re.IGNORECASE), "Increase"),
    (re.compile(r"\s+(?:increase|rise|elevation|upregulation|activation|overexpression|induction|gain|accumulation|enhancement)$", re.IGNORECASE), "Increase"),
]

NEGATIVE_STATE_PATTERNS = [
    (re.compile(r"^(?:an?\s+)?(?:(?:\+|-)?\d+(?:\.\d+)?(?:%|-?fold|x)?\s+)?(?:decrease|reduction|loss|depletion|knockdown|knockout|inhibition|suppression|downregulation|deficiency|abrogation|degradation)\s+(?:in|of)\s+", re.IGNORECASE), "Decrease"),
    (re.compile(r"^(?:(?:\+|-)?\d+(?:\.\d+)?(?:%|-?fold|x)?\s+)?(?:decreased|reduced|lower|low|downregulated|inhibited|suppressed|deficient|depleted|ablated|silenced)\s+", re.IGNORECASE), "Decrease"),
    (re.compile(r"\s+(?:decrease|reduction|loss|depletion|knockdown|knockout|inhibition|suppression|downregulation|deficiency|abrogation|degradation)$", re.IGNORECASE), "Decrease"),
]

CATEGORY_PALETTE = {
    "Measured Outcome": {"fill": "#fef3c7", "stroke": "#d97706"},
    "Environmental Factor": {"fill": "#e0f2fe", "stroke": "#0284c7"},
    "Experimental Condition": {"fill": "#e0e7ff", "stroke": "#4f46e5"},
    "Gene/Protein": {"fill": "#fce7f3", "stroke": "#db2777"},
    "Chemical": {"fill": "#dcfce7", "stroke": "#16a34a"},
    "Biological Process": {"fill": "#f3e8ff", "stroke": "#9333ea"},
    "Phenotype": {"fill": "#ffedd5", "stroke": "#ea580c"},
    "Unclassified": {"fill": "#f1f5f9", "stroke": "#64748b"},
}

SENTENCE_PALETTE = [
    {"fill": "#eff6ff", "border": "#bfdbfe"},  # Blue
    {"fill": "#fef3c7", "border": "#fde68a"},  # Amber
    {"fill": "#ecfdf5", "border": "#a7f3d0"},  # Emerald
    {"fill": "#fdf4ff", "border": "#f5d0fe"},  # Fuchsia
    {"fill": "#fff1f2", "border": "#fecdd3"},  # Rose
    {"fill": "#f0fdf4", "border": "#bbf7d0"},  # Green
    {"fill": "#f5f3ff", "border": "#ddd6fe"},  # Violet
    {"fill": "#fefce8", "border": "#fef08a"},  # Yellow
]


def get_deterministic_category_colors(category: str) -> Tuple[str, str]:
    if category in CATEGORY_PALETTE:
        p = CATEGORY_PALETTE[category]
        return p["fill"], p["stroke"]
    h = sum(ord(c) for c in category) % len(CATEGORY_PALETTE)
    keys = list(CATEGORY_PALETTE.keys())
    fallback = CATEGORY_PALETTE[keys[h]]
    return fallback["fill"], fallback["stroke"]


def segment_prompt_sentences(text: str) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    # Clean leading section labels before sentence segmentation
    text_clean = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary)[:\s]*\n+", "", text.strip(), flags=re.IGNORECASE)
    pattern = re.compile(r'[^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$')
    sentences = []
    idx = 1
    for match in pattern.finditer(text_clean.strip()):
        s_text = match.group().strip()
        if not s_text:
            continue
        pal = SENTENCE_PALETTE[(idx - 1) % len(SENTENCE_PALETTE)]
        sentences.append({
            "id": f"s{idx}",
            "text": s_text,
            "char_start": match.start(),
            "char_end": match.end(),
            "color_fill": pal["fill"],
            "color_border": pal["border"],
        })
        idx += 1
    return sentences


def infer_entity_category_and_confidence(concept: str, context_text: str = "") -> Tuple[str, float, str]:
    c_clean = concept.strip()
    c_lower = c_clean.lower()
    ctx_lower = context_text.lower().strip()

    # 1. Measured Outcome (performance, accuracy, latency, etc. - NEVER phenotype!)
    outcome_terms = {
        "performance", "accuracy", "latency", "throughput", "yield", "efficiency",
        "error rate", "runtime", "f1", "precision", "recall", "score", "loss",
        "performance decline", "performance variations", "performance variation"
    }
    if c_lower in outcome_terms or any(term in c_lower for term in ("performance", "accuracy", "latency", "throughput", "runtime", "efficiency")):
        return "Measured Outcome", 0.95, "Matched measured system or task-level outcome metric"

    # 2. Environmental Factor vs Experimental Condition
    env_terms = {
        "temperature", "heat", "cold", "hypoxia", "normoxia", "ph", "radiation",
        "salinity", "pressure", "humidity", "stress", "uv", "osmotic", "ambient",
        "climate", "weather", "temperature suppression"
    }
    if c_lower in env_terms or any(term in c_lower for term in ("temperature", "hypoxia", "normoxia", "humidity", "salinity", "ambient")):
        if any(w in ctx_lower for w in ("assay", "treatment", "protocol", "dose", "culture", "in vitro", "condition", "experimental")):
            return "Experimental Condition", 0.90, "Environmental factor applied as experimental condition"
        return "Environmental Factor", 0.92, "Physical or ambient environmental factor"

    # 3. Chemical / Compound (prioritize known chemical acronyms like LPS, ROS, NO, ATP)
    chem_terms = {
        "lipopolysaccharide", "lps", "ros", "no", "glucose", "lactate", "cation", "calcium",
        "magnesium", "atp", "oxygen", "drug", "inhibitor", "compound", "peptide", "peptides",
        "antibiotic", "polymyxin", "fe3+", "camps", "edna"
    }
    if c_lower in chem_terms:
        return "Chemical", 0.90, "Identified chemical, metabolite, or ion"

    # 4. Biological Process
    proc_terms = {
        "cell cycle progression", "cell cycle", "dna synthesis", "transcription", "translation",
        "autophagy", "signaling", "phosphorylation", "glycolysis", "differentiation", "cycle",
        "pathway", "cascade", "binding", "repair", "dna repair", "secretion", "alanylation", "chelation",
        "apoptosis", "cellular apoptosis", "programmed cell death"
    }
    if c_lower in proc_terms or any(p in c_lower for p in ("cell cycle", "dna synthesis", "dna repair", "autophagy", "apoptosis")):
        return "Biological Process", 0.88, "Identified biological pathway or cellular process"

    # 5. Phenotype (strictly biological cellular/organismal observable traits, NEVER general performance)
    pheno_terms = {
        "survival", "proliferation", "growth", "fibrosis",
        "viability", "motility", "migration", "invasion", "death", "necrosis", "virulence",
        "pathogenicity", "resistance", "immunity", "tumorigenesis", "senescence", "metastasis",
        "permeability", "cytotoxicity", "defect", "adherence", "fimbriae"
    }
    if c_lower in pheno_terms or any(t in c_lower for t in ("tumor", "growth", "survival", "proliferation", "viability", "motility", "migration", "invasion", "necrosis", "virulence", "pathogenicity", "resistance", "senescence", "metastasis", "cytotoxicity")):
        return "Phenotype", 0.90, "Identified cellular or organismal phenotype"

    # 6. Gene/Protein
    gene_terms = {
        "egfr", "stat3", "socs3", "tnf", "vegf", "hif1a", "hif-1alpha", "mapk", "erk", "akt",
        "mtor", "ampk", "nfkb", "nf-kb", "p53", "tp53", "p21", "tgfb", "caspase", "caspase-3", "caspase-9",
        "bax", "bcl2", "bcl-2", "grb2", "ras", "raf", "mek", "jak1", "jak2", "stat1", "pmra", "pmrb", "pmrd",
        "mlc", "hild", "hila", "invf", "fims", "fimr", "phop", "esat-6", "luxr", "salk", "salr", "grars", "dlta",
        "mprf", "csrs", "scpc", "phopq", "pmrab", "vicr", "vick", "slya", "ssrb", "hsp90", "cdk2", "atm", "chk2",
        "mdm2", "atr", "wee1", "cdc25"
    }
    if c_lower in gene_terms or any(c_lower.endswith(sfx) for sfx in ("ase", "kinase", "receptor", "protein", "factor", "synthase", "phosphatase", "cyclin")):
        return "Gene/Protein", 0.92, "Identified molecular entity, gene, or protein"
    if re.match(r"^[A-Z][A-Z0-9]{1,6}$", c_clean):
        return "Gene/Protein", 0.90, "Gene or protein symbol pattern"

    return "Unclassified", 0.50, "No domain ontology rule matched"


def decompose_concept_and_state(
    phrase: str, context_text: str = "", return_metadata: bool = False
) -> Tuple[Any, ...]:
    """
    Decomposes a phrase (e.g. 'Increase in temperature', 'decrease in performance') into:
    (canonical_concept, state_label, delta, category) [if return_metadata is False]
    or
    (canonical_concept, state_label, delta, category, confidence, rationale, fill, stroke) [if return_metadata is True]
    """
    raw = phrase.strip()
    raw = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary)[:\s]+", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"[,;:\.]+$", "", raw).strip()
    state = None
    delta = None  # None unless an explicit numeric measurement is stated
    concept_candidate = raw

    # Check for explicit numeric measurements (e.g. "+10%", "2.5-fold", "increase of 5")
    m_num = re.search(r'(?:(?:by|of|\+|-)\s*(\d+(?:\.\d+)?)\s*(?:%|-?fold|x)?|\b(\d+(?:\.\d+)?)\s*(?:%|-?fold|x))', raw, re.IGNORECASE)

    # 1. Negative state patterns
    for pat, label in NEGATIVE_STATE_PATTERNS:
        m = pat.search(concept_candidate)
        if m:
            state = label
            if m_num:
                try:
                    num_val = float(m_num.group(1) or m_num.group(2))
                    delta = -num_val
                except (ValueError, TypeError):
                    delta = None
            if m.start() == 0:
                concept_candidate = concept_candidate[m.end():].strip()
            else:
                concept_candidate = concept_candidate[:m.start()].strip()
            break

    # 2. Positive state patterns
    if not state:
        for pat, label in POSITIVE_STATE_PATTERNS:
            m = pat.search(concept_candidate)
            if m:
                state = label
                if m_num:
                    try:
                        num_val = float(m_num.group(1) or m_num.group(2))
                        delta = num_val
                    except (ValueError, TypeError):
                        delta = None
                if m.start() == 0:
                    concept_candidate = concept_candidate[m.end():].strip()
                else:
                    concept_candidate = concept_candidate[:m.start()].strip()
                break

    # 3. Clean up articles, noise & whitespace
    concept_clean = re.sub(r"^(?:the|a|an|this|these|those|cellular|by|via|upon)\s+", "", concept_candidate, flags=re.IGNORECASE).strip()
    concept_clean = re.sub(r"\s+", " ", concept_clean).strip()
    if not concept_clean:
        concept_clean = raw.title()

    lower_concept = concept_clean.lower()
    if lower_concept in GLOBAL_SYNONYMS:
        canonical_concept = GLOBAL_SYNONYMS[lower_concept]
    elif any(c.isupper() for c in concept_clean[1:]) or any(c.isdigit() for c in concept_clean):
        canonical_concept = concept_clean
    else:
        canonical_concept = concept_clean.title()

    # 4. Context-aware category inference
    category, cat_conf, cat_rationale = infer_entity_category_and_confidence(canonical_concept, context_text)
    color_fill, color_stroke = get_deterministic_category_colors(category)

    if return_metadata:
        return canonical_concept, state, delta, category, cat_conf, cat_rationale, color_fill, color_stroke
    return canonical_concept, state, delta, category


def compute_edge_polarity_and_style(
    rel_type: str,
    cause_delta: Any = None,
    effect_delta: Any = None,
    is_negated: bool = False,
    is_transitive: bool = False,
    context_sentence: str = "",
    return_full: bool = False,
    cause_state: Optional[str] = None,
    effect_state: Optional[str] = None,
) -> Tuple[Any, ...]:
    """
    Returns (effect_polarity, edge_color, edge_style) by default, or
    (effect_polarity, edge_color, edge_style, is_suppressed, assertion_status, directional_trend) if return_full=True
    """
    rel_upper = rel_type.upper()

    # Backward compatibility: handle cause_state and effect_state passed or derived from delta
    if cause_state is None:
        if isinstance(cause_delta, str):
            cause_state = cause_delta
        elif cause_delta == -1:
            cause_state = "Decrease"
        elif cause_delta == 1:
            cause_state = "Increase"

    if effect_state is None:
        if isinstance(effect_delta, str):
            effect_state = effect_delta
        elif effect_delta == -1:
            effect_state = "Decrease"
        elif effect_delta == 1:
            effect_state = "Increase"

    # Speculative modal check
    is_speculative = bool(re.search(r"\b(?:might|may|suggests?|hypothesiz(?:e|ed|es)|possibly|perhaps|could)\b", context_sentence, re.IGNORECASE))
    if is_negated:
        assertion_status = "negated"
    elif is_speculative:
        assertion_status = "speculative"
    else:
        assertion_status = "affirmed"

    is_suppressed = bool(is_negated)

    if is_negated:
        # Negation does NOT invert polarity (does not decrease != increase)
        if return_full:
            return "unknown", "#94a3b8", "dashed", is_suppressed, assertion_status, "neutral"
        return "unknown", "#94a3b8", "dashed"

    if "ASSOCIAT" in rel_upper or "CORRELAT" in rel_upper:
        if return_full:
            return "association", "#64748b", "dotted", is_suppressed, assertion_status, "correlated"
        return "association", "#64748b", "dotted"

    # Explicitly inhibitory or preventive predicates represent an opposing / inhibitory relation
    if rel_upper in ["DOWNREGULATES", "INHIBITS", "PREVENTS", "SUPPRESSES", "REDUCES", "BLOCKS"]:
        if return_full:
            return "negative", "#dc2626", "dashed" if is_transitive else "solid", is_suppressed, assertion_status, "opposing"
        return "negative", "#dc2626", "dashed" if is_transitive else "solid"

    # For causal influence or activating relations (DIRECT_CAUSE, UPREGULATES, etc.):
    c_sign = -1 if cause_state in ["Decrease", "Inhibited", "Reduced", "Down", "Loss"] else 1
    e_sign = -1 if effect_state in ["Decrease", "Inhibited", "Reduced", "Down", "Loss", "Prevented"] else 1
    net_sign = c_sign * e_sign

    if net_sign < 0:
        if return_full:
            return "negative", "#dc2626", "dashed" if is_transitive else "solid", is_suppressed, assertion_status, "opposing"
        return "negative", "#dc2626", "dashed" if is_transitive else "solid"
    else:
        if return_full:
            return "positive", "#0f172a", "dashed" if is_transitive else "solid", is_suppressed, assertion_status, "reinforcing"
        return "positive", "#0f172a", "dashed" if is_transitive else "solid"


class ExtractionService:
    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or SessionStore()
        self.normalizer = PaperEntityNormalizer()
        self.extractor = PaperCausalExtractor(self.normalizer)
        self.linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.65)
        self.builder = PaperGraphBuilder(include_inferred_cross_page_edges=True)
        self.parser = DocumentParser()

    def process_text_input(
        self, text: str, session_id: Optional[str] = None, title_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        doc = self.parser.parse_raw_text(text, filename="Specification")
        if not session_id:
            first_line = text.strip().split("\n")[0][:45]
            title = title_hint or (first_line if len(first_line) > 3 else "Causal Analysis")
            s = self.store.create_session(title=title)
            session_id = s["id"]
            self.store.add_input(session_id, input_type="text", content=text)
            return self.replace_graph_from_prompt(text, session_id, title_hint=title_hint)

        self.store.add_input(session_id, input_type="text", content=text)
        return self._extract_and_accumulate(doc, session_id, filename="Query Input", title_hint=title_hint)

    def replace_graph_from_prompt(
        self, text: str, session_id: str, title_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        sentences = segment_prompt_sentences(text)
        doc = self.parser.parse_raw_text(text, filename="Specification")
        assertions = self.extractor.extract_assertions(doc)
        cross_links: List[CrossPageLink] = []
        if len(doc.pages) > 1:
            cross_links = self.linker.link_cross_page_relations(doc, assertions)

        graph = self.builder.build_graph(doc.doc_id, doc.metadata.title, assertions, cross_links)
        nodes, relations, evidence = self._format_graph_data(
            graph, filename="Specification", doc_id=doc.doc_id, sentences=sentences
        )

        # Initialize layout positions if needed
        self._initialize_radial_layout(nodes)

        updated_session = self.store.replace_session_graph(
            session_id=session_id,
            new_nodes=nodes,
            new_relations=relations,
            new_evidence=evidence,
            primary_prompt=text,
            title_hint=title_hint,
        )
        updated_session["sentences"] = sentences
        return updated_session

    def process_file_upload(
        self, file_path: str, original_filename: str, session_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        doc = self.parser.parse_file(file_path, original_filename)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else len(doc.full_text)
        ext = os.path.splitext(original_filename)[1].lower()

        if not session_id:
            title = original_filename.replace("_", " ").rsplit(".", 1)[0][:45]
            s = self.store.create_session(title=title)
            session_id = s["id"]

        self.store.add_input(session_id, input_type="file", content=f"Uploaded {original_filename}")
        self.store.add_document(
            session_id=session_id,
            doc_id=doc.doc_id,
            filename=original_filename,
            file_type=ext.lstrip("."),
            file_size=file_size,
            page_count=len(doc.pages),
            status="completed",
        )

        assertions = self.extractor.extract_assertions(doc)
        cross_links: List[CrossPageLink] = []
        if len(doc.pages) > 1:
            cross_links = self.linker.link_cross_page_relations(doc, assertions)

        graph = self.builder.build_graph(doc.doc_id, doc.metadata.title, assertions, cross_links)
        nodes, relations, evidence = self._format_graph_data(graph, filename=original_filename, doc_id=doc.doc_id)

        in_degree = {}
        out_degree = {}
        for r in relations:
            c = r["cause_name"]
            e = r["effect_name"]
            out_degree[c] = out_degree.get(c, 0) + 1
            in_degree[e] = in_degree.get(e, 0) + 1

        for n in nodes:
            n["in_degree"] = in_degree.get(n["canonical_name"], 0)
            n["out_degree"] = out_degree.get(n["canonical_name"], 0)

        # Attach evidence to relation
        rel_map = {r["id"]: r for r in relations}
        for ev in evidence:
            r_id = ev["relation_id"]
            if r_id in rel_map:
                rel_map[r_id]["evidence"].append(ev)

        doc_result = {
            "doc_id": doc.doc_id,
            "filename": original_filename,
            "file_type": ext.lstrip("."),
            "file_size": file_size,
            "page_count": len(doc.pages),
            "status": "completed",
            "nodes": nodes,
            "relations": relations,
            "relation_count": len(relations),
        }

        # Layout initialization for any new nodes
        self._initialize_radial_layout(nodes)

        updated_session = self.store.accumulate_evidence(
            session_id=session_id,
            new_nodes=nodes,
            new_relations=relations,
            new_evidence=evidence,
            title_hint=original_filename,
        )
        return doc_result, updated_session

    def _extract_doc_level(self, doc: ScientificDocument, filename: str) -> Dict[str, Any]:
        assertions = self.extractor.extract_assertions(doc)
        cross_links: List[CrossPageLink] = []
        if len(doc.pages) > 1:
            cross_links = self.linker.link_cross_page_relations(doc, assertions)

        graph = self.builder.build_graph(doc.doc_id, doc.metadata.title, assertions, cross_links)
        nodes, relations, evidence = self._format_graph_data(graph, filename=filename, doc_id=doc.doc_id)

        in_degree = {}
        out_degree = {}
        for r in relations:
            c = r["cause_name"]
            e = r["effect_name"]
            out_degree[c] = out_degree.get(c, 0) + 1
            in_degree[e] = in_degree.get(e, 0) + 1

        for n in nodes:
            n["in_degree"] = in_degree.get(n["canonical_name"], 0)
            n["out_degree"] = out_degree.get(n["canonical_name"], 0)

        # Attach evidence to relation
        rel_map = {r["id"]: r for r in relations}
        for ev in evidence:
            r_id = ev["relation_id"]
            if r_id in rel_map:
                rel_map[r_id]["evidence"].append(ev)

        return {
            "doc_id": doc.doc_id,
            "filename": filename,
            "file_type": filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt",
            "file_size": len(doc.full_text),
            "page_count": len(doc.pages),
            "status": "completed",
            "nodes": nodes,
            "relations": relations,
            "relation_count": len(relations),
        }

    def _extract_and_accumulate(
        self,
        doc: ScientificDocument,
        session_id: str,
        filename: str,
        doc_id: Optional[str] = None,
        title_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        assertions = self.extractor.extract_assertions(doc)
        cross_links: List[CrossPageLink] = []
        if len(doc.pages) > 1:
            cross_links = self.linker.link_cross_page_relations(doc, assertions)

        graph = self.builder.build_graph(doc.doc_id, doc.metadata.title, assertions, cross_links)
        nodes, relations, evidence = self._format_graph_data(
            graph, filename=filename, doc_id=doc_id or doc.doc_id
        )

        # Layout initialization for any new nodes
        self._initialize_radial_layout(nodes)

        updated_session = self.store.accumulate_evidence(
            session_id=session_id,
            new_nodes=nodes,
            new_relations=relations,
            new_evidence=evidence,
            title_hint=title_hint or filename,
        )
        return updated_session

    def _format_graph_data(
        self,
        graph: PaperCausalGraph,
        filename: str,
        doc_id: str,
        sentences: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        node_map: Dict[str, Dict[str, Any]] = {}
        relations: List[Dict[str, Any]] = []
        evidence_list: List[Dict[str, Any]] = []
        node_sentence_ids: Dict[str, set] = {}

        for edge in graph.edges:
            rel_id = f"rel_{uuid.uuid4().hex[:8]}"
            if isinstance(edge, dict):
                raw_cause = edge.get("source", "")
                raw_effect = edge.get("target", "")
                rel_type = edge.get("relation_type", "UPREGULATES")
                is_neg = bool(edge.get("is_negated", False))
                status = edge.get("evidence_status", "MEASURED_FACT")
                is_trans = not bool(edge.get("is_direct", True))
                conf = float(edge.get("confidence", 0.90))
                quotes = edge.get("quotes", [])
                pages = edge.get("pages", [1])
            else:
                raw_cause = edge.source
                raw_effect = edge.target
                rel_type = edge.relation_type.value if hasattr(edge.relation_type, "value") else str(edge.relation_type)
                is_neg = bool(edge.is_negated)
                status = edge.evidence_status.value if hasattr(edge.evidence_status, "value") else str(edge.evidence_status)
                is_trans = bool(getattr(edge, "is_cross_page", False))
                conf = float(edge.confidence)
                quotes = [quote for _, quote, _, _, _ in getattr(edge, "supporting_evidence", [])]
                pages = [p for _, _, p, _, _ in getattr(edge, "supporting_evidence", [])] or [1]

            ctx_text = " ".join(quotes) if quotes else f"{raw_cause} {rel_type} {raw_effect}"

            # Decompose concepts and states with context awareness
            (
                src_canon, src_state, src_delta, src_cat,
                src_conf, src_rat, src_fill, src_stroke
            ) = decompose_concept_and_state(raw_cause, context_text=ctx_text, return_metadata=True)

            (
                tgt_canon, tgt_state, tgt_delta, tgt_cat,
                tgt_conf, tgt_rat, tgt_fill, tgt_stroke
            ) = decompose_concept_and_state(raw_effect, context_text=ctx_text, return_metadata=True)

            # Match sentence provenance IDs
            rel_sentence_ids = []
            if sentences:
                for s in sentences:
                    s_clean = s["text"].strip().lower()
                    if any(s_clean in q.lower() or q.lower() in s_clean for q in quotes):
                        rel_sentence_ids.append(s["id"])
                    elif (src_canon.lower() in s_clean and tgt_canon.lower() in s_clean):
                        rel_sentence_ids.append(s["id"])
                if not rel_sentence_ids and sentences:
                    rel_sentence_ids.append(sentences[0]["id"])

            node_sentence_ids.setdefault(src_canon, set()).update(rel_sentence_ids)
            node_sentence_ids.setdefault(tgt_canon, set()).update(rel_sentence_ids)

            if src_canon not in node_map:
                node_map[src_canon] = {
                    "id": f"n_{uuid.uuid4().hex[:8]}",
                    "canonical_name": src_canon,
                    "display_name": src_canon,
                    "category": src_cat,
                    "category_confidence": src_conf,
                    "category_rationale": src_rat,
                    "user_override_category": None,
                    "color_fill": src_fill,
                    "color_stroke": src_stroke,
                    "state": src_state,
                    "state_delta": src_delta,
                    "x": None,
                    "y": None,
                    "fixed": False,
                    "evidence_sentence_ids": list(node_sentence_ids[src_canon]),
                }
            else:
                if src_state and not node_map[src_canon].get("state"):
                    node_map[src_canon]["state"] = src_state
                    node_map[src_canon]["state_delta"] = src_delta
                node_map[src_canon]["evidence_sentence_ids"] = list(node_sentence_ids[src_canon])

            if tgt_canon not in node_map:
                node_map[tgt_canon] = {
                    "id": f"n_{uuid.uuid4().hex[:8]}",
                    "canonical_name": tgt_canon,
                    "display_name": tgt_canon,
                    "category": tgt_cat,
                    "category_confidence": tgt_conf,
                    "category_rationale": tgt_rat,
                    "user_override_category": None,
                    "color_fill": tgt_fill,
                    "color_stroke": tgt_stroke,
                    "state": tgt_state,
                    "state_delta": tgt_delta,
                    "x": None,
                    "y": None,
                    "fixed": False,
                    "evidence_sentence_ids": list(node_sentence_ids[tgt_canon]),
                }
            else:
                if tgt_state and not node_map[tgt_canon].get("state"):
                    node_map[tgt_canon]["state"] = tgt_state
                    node_map[tgt_canon]["state_delta"] = tgt_delta
                node_map[tgt_canon]["evidence_sentence_ids"] = list(node_sentence_ids[tgt_canon])

            polarity, edge_col, edge_sty, is_supp, a_status, dir_trend = compute_edge_polarity_and_style(
                rel_type=rel_type,
                cause_delta=src_delta,
                effect_delta=tgt_delta,
                is_negated=is_neg,
                is_transitive=is_trans,
                context_sentence=ctx_text,
                return_full=True,
                cause_state=src_state,
                effect_state=tgt_state,
            )

            rel_dict = {
                "id": rel_id,
                "doc_id": doc_id,
                "cause_name": src_canon,
                "effect_name": tgt_canon,
                "relation_type": rel_type,
                "direction": "FORWARD",
                "is_negated": is_neg,
                "is_suppressed": is_supp,
                "assertion_status": a_status,
                "uncertainty_score": 0.05 if not is_neg else 0.0,
                "confidence": round(conf, 3),
                "is_transitive": is_trans,
                "status": status,
                "has_contradiction": False,
                "effect_polarity": polarity,
                "directional_trend": dir_trend,
                "edge_color": edge_col,
                "edge_style": edge_sty,
                "tension_level": 1,
                "source_state": src_state,
                "source_delta": src_delta,
                "target_state": tgt_state,
                "target_delta": tgt_delta,
                "evidence_sentence_ids": rel_sentence_ids,
                "evidence": [],
            }
            relations.append(rel_dict)

            # Supporting evidence
            if quotes:
                for q_idx, quote in enumerate(quotes):
                    p_num = pages[q_idx] if q_idx < len(pages) else (pages[0] if pages else 1)
                    ev_dict = {
                        "id": f"ev_{uuid.uuid4().hex[:8]}",
                        "relation_id": rel_id,
                        "doc_id": doc_id,
                        "filename": filename,
                        "page_number": p_num,
                        "section_title": "Results",
                        "sentence_text": quote,
                        "quote": quote,
                        "char_start": 0,
                        "char_end": len(quote),
                        "evidence_status": status,
                    }
                    evidence_list.append(ev_dict)
            else:
                ev_dict = {
                    "id": f"ev_{uuid.uuid4().hex[:8]}",
                    "relation_id": rel_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_number": 1,
                    "section_title": "Results",
                    "sentence_text": f"{src_canon} {rel_type} {tgt_canon}",
                    "quote": f"{src_canon} {rel_type} {tgt_canon}",
                    "char_start": 0,
                    "char_end": len(src_canon) + len(tgt_canon) + 10,
                    "evidence_status": status,
                }
                evidence_list.append(ev_dict)

        # Include any remaining isolated graph nodes
        for n in graph.nodes:
            raw_n = n["name"] if isinstance(n, dict) else getattr(n, "canonical_name", str(n))
            canon, state, delta, cat, conf, rat, fill, stroke = decompose_concept_and_state(
                raw_n, return_metadata=True
            )
            if canon not in node_map:
                node_map[canon] = {
                    "id": f"n_{uuid.uuid4().hex[:8]}",
                    "canonical_name": canon,
                    "display_name": canon,
                    "category": cat,
                    "category_confidence": conf,
                    "category_rationale": rat,
                    "user_override_category": None,
                    "color_fill": fill,
                    "color_stroke": stroke,
                    "state": state,
                    "state_delta": delta,
                    "x": None,
                    "y": None,
                    "fixed": False,
                    "evidence_sentence_ids": [],
                }

        nodes = list(node_map.values())
        return nodes, relations, evidence_list

        nodes = list(node_map.values())
        return nodes, relations, evidence_list

    def _initialize_radial_layout(self, nodes: List[Dict[str, Any]], radius: float = 240.0) -> None:
        n = len(nodes)
        if n == 0:
            return
        center_x = 450.0
        center_y = 300.0
        angle_step = 2 * math.pi / n
        for idx, node in enumerate(nodes):
            angle = idx * angle_step
            node["x"] = round(center_x + radius * math.cos(angle), 1)
            node["y"] = round(center_y + radius * math.sin(angle), 1)
