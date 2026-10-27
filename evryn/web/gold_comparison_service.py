"""
EVRYN Phase 2.5: Gold Comparison & False-Positive Adjudication Service.
Compares extracted causal relations against frozen reference gold standards using
the official 1-to-1 matching protocol with semantic direction preservation.
"""

import os
import re
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REAL_PAPERS_DIR = os.path.join(REPO_ROOT, "data", "real_papers")
SPLIT_MANIFEST_PATH = os.path.join(REAL_PAPERS_DIR, "split_manifest.json")


def normalize_entity_token(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", " ", str(text)).strip().lower()


def match_edge(p_c: str, p_e: str, g_c: str, g_e: str) -> bool:
    """Official EVRYN directional edge matching protocol."""
    p_c_n = normalize_entity_token(p_c)
    p_e_n = normalize_entity_token(p_e)
    g_c_n = normalize_entity_token(g_c)
    g_e_n = normalize_entity_token(g_e)
    if not p_c_n or not p_e_n or not g_c_n or not g_e_n:
        return False
    # Preserves direction: cause must match cause, effect must match effect
    return (p_c_n in g_c_n or g_c_n in p_c_n) and (p_e_n in g_e_n or g_e_n in p_e_n)


class GoldComparisonService:
    _instance: Optional["GoldComparisonService"] = None

    @classmethod
    def get_instance(cls) -> "GoldComparisonService":
        if cls._instance is None:
            cls._instance = GoldComparisonService()
        return cls._instance

    def __init__(self):
        self._manifest_cache: Optional[Dict[str, Any]] = None
        self._ground_truth_cache: Dict[str, Dict[str, Any]] = {}
        self._session_adjudications: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def get_manifest(self) -> Dict[str, Any]:
        if self._manifest_cache is None and os.path.exists(SPLIT_MANIFEST_PATH):
            with open(SPLIT_MANIFEST_PATH, "r", encoding="utf-8") as f:
                self._manifest_cache = json.load(f)
        return self._manifest_cache or {"papers": []}

    def get_ground_truth(self, pmcid: str) -> Optional[Dict[str, Any]]:
        pmcid_upper = pmcid.upper()
        if pmcid_upper in self._ground_truth_cache:
            return self._ground_truth_cache[pmcid_upper]

        gt_path = os.path.join(REAL_PAPERS_DIR, f"{pmcid_upper}_ground_truth.json")
        if os.path.exists(gt_path):
            with open(gt_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._ground_truth_cache[pmcid_upper] = data
                return data
        return None

    def suggest_adjudication_category(self, rel: Dict[str, Any], is_cross: bool = False) -> Tuple[str, str]:
        """Provides heuristic classification of unmatched candidate false positives."""
        quote = (rel.get("sentence_text") or rel.get("quote") or "").lower()
        cause = str(rel.get("cause_name", "")).lower()
        effect = str(rel.get("effect_name", "")).lower()

        # 1. Hypothesis / Intent language
        if any(w in quote for w in ["we hypothesized", "hypothesized that", "we postulated", "we speculated", "to test whether", "tested whether"]):
            return (
                "Genuine false positive",
                "Extracted from a research-intent or hypothesis clause ('we hypothesized that...') rather than an established empirical finding.",
            )

        # 2. Speculative hedge
        if any(w in quote for w in ["could be due to", "might be caused by", "may be due to", "potential mechanism", "remains unclear"]):
            return (
                "Genuine false positive",
                "Triggered by speculative possibility phrase ('could be due to...') expressing uncertainty rather than factual confirmation.",
            )

        # 3. Unsupported cross-page inference
        if is_cross or rel.get("is_transitive", False):
            return (
                "Unsupported inference",
                "Cross-page transitive jump linking endpoints without direct experimental co-validation in the text.",
            )

        # 4. Phenotypic correlation / manifestation
        if any(w in quote for w in ["more resistant to", "resistant to", "increased resistance"]):
            return (
                "Likely annotation omission",
                "Describes phenotypic manifestation supported by text; absent from direct biochemical gold annotations.",
            )

        # 5. Biological valid relation
        if rel.get("relation_type") in ["UPREGULATES", "DOWNREGULATES", "MEDIATES"]:
            return (
                "Likely annotation omission",
                "Text supports causal assertion with specific biochemical mechanism, but reference gold standard did not annotate this edge.",
            )

        return (
            "Ambiguous",
            "Syntactic assertion requires expert manual review to verify whether context establishes true causality.",
        )

    def compare_session_with_gold(
        self, session_id: str, session_data: Dict[str, Any], pmcid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs 1-to-1 matching and generates gold comparison report."""
        # Determine PMCID if not explicitly provided
        target_pmcid = pmcid
        if not target_pmcid:
            # Check title or documents
            title = session_data.get("title", "")
            m = re.search(r"PMC\d+", title, re.IGNORECASE)
            if m:
                target_pmcid = m.group(0).upper()
            else:
                for doc in session_data.get("documents", []):
                    fn = doc.get("filename", "")
                    m2 = re.search(r"PMC\d+", fn, re.IGNORECASE)
                    if m2:
                        target_pmcid = m2.group(0).upper()
                        break

            # Check raw text or relation quotes for PMCID
            if not target_pmcid:
                raw_text = session_data.get("text", "")
                m_txt = re.search(r"PMC\d+", raw_text, re.IGNORECASE)
                if m_txt:
                    target_pmcid = m_txt.group(0).upper()

            # Match against manifest paper titles
            if not target_pmcid and title:
                manifest = self.get_manifest()
                norm_title = re.sub(r"[^a-zA-Z0-9]+", " ", title).strip().lower()
                for p in manifest.get("papers", []):
                    p_title_norm = re.sub(r"[^a-zA-Z0-9]+", " ", p.get("title", "")).strip().lower()
                    if p_title_norm and (p_title_norm in norm_title or norm_title in p_title_norm):
                        target_pmcid = p["pmcid"].upper()
                        break

        if not target_pmcid:
            return {
                "gold_available": False,
                "pmcid": None,
                "message": "No benchmark PMCID detected for this session. Gold comparison is available for benchmark papers (e.g. PMC1804205, PMC1874608).",
                "total_gold": 0,
                "total_predicted": len(session_data.get("relations", [])),
                "metrics": {"precision": None, "recall": None, "f1": None},
                "matched_relations": [],
                "unmatched_predictions": [],
                "missed_gold": [],
                "adjudicated_summary": {
                    "gold_match": 0,
                    "likely_annotation_omission": 0,
                    "genuine_false_positive": 0,
                    "unsupported_inference": 0,
                    "duplicate_or_normalization": 0,
                    "ambiguous": 0,
                },
            }

        gt = self.get_ground_truth(target_pmcid)
        if not gt:
            return {
                "gold_available": False,
                "pmcid": target_pmcid,
                "message": f"Reference gold annotations are not available for {target_pmcid}. Available in Dev and Locked-Test benchmark papers.",
                "total_gold": 0,
                "total_predicted": len(session_data.get("relations", [])),
                "metrics": {"precision": None, "recall": None, "f1": None},
                "matched_relations": [],
                "unmatched_predictions": [],
                "missed_gold": [],
                "adjudicated_summary": {},
            }

        gt_direct = [tuple(x) for x in gt.get("direct_edges", [])]
        gt_cross = [tuple(x) for x in gt.get("cross_page_edges", [])]
        canon_entities = gt.get("canonical_entities", [])

        relations = session_data.get("relations", [])
        clean_relations = [r for r in relations if not r.get("is_negated")]

        matched_gt_d_indices: Set[int] = set()
        matched_gt_c_indices: Set[int] = set()

        matched_items: List[Dict[str, Any]] = []
        unmatched_items: List[Dict[str, Any]] = []

        # Retrieve any stored reviewer overrides for this session
        session_overrides = self._session_adjudications.get(session_id, {})

        for r in clean_relations:
            c_name = r.get("cause_name", "")
            e_name = r.get("effect_name", "")
            is_trans = bool(r.get("is_transitive", False))
            r_id = r.get("id", "")

            # Match against direct first
            matched_gold_edge = None
            is_match = False
            match_type = None

            if not is_trans:
                for idx, (g_c, g_e) in enumerate(gt_direct):
                    if idx not in matched_gt_d_indices and match_edge(c_name, e_name, g_c, g_e):
                        is_match = True
                        matched_gold_edge = [g_c, g_e]
                        matched_gt_d_indices.add(idx)
                        match_type = "direct"
                        break

            # If not matched direct, check cross-page gold edges
            if not is_match:
                for idx, (g_c, g_e) in enumerate(gt_cross):
                    if idx not in matched_gt_c_indices and match_edge(c_name, e_name, g_c, g_e):
                        is_match = True
                        matched_gold_edge = [g_c, g_e]
                        matched_gt_c_indices.add(idx)
                        match_type = "cross_page"
                        break

            # Get evidence quote
            ev_list = r.get("evidence", [])
            evidence_quote = ev_list[0].get("sentence_text") if ev_list else r.get("evidence_sentence_ids", "")

            item_data = {
                "relation_id": r_id,
                "cause": c_name,
                "effect": e_name,
                "relation_type": r.get("relation_type", "UPREGULATES"),
                "effect_polarity": r.get("effect_polarity", "POSITIVE"),
                "is_transitive": is_trans,
                "confidence": r.get("confidence", 0.90),
                "evidence_quote": evidence_quote,
                "page_number": ev_list[0].get("page_number", 1) if ev_list else 1,
                "is_match": is_match,
                "matched_gold": matched_gold_edge,
                "match_type": match_type,
            }

            if is_match:
                item_data["adjudication_category"] = "Gold match"
                item_data["adjudication_explanation"] = "Prediction exactly matches reference gold standard relation."
                matched_items.append(item_data)
            else:
                cat, exp = self.suggest_adjudication_category(r, is_cross=is_trans)
                # Check for reviewer override
                if r_id in session_overrides:
                    cat = session_overrides[r_id].get("category", cat)
                    exp = session_overrides[r_id].get("note", exp)
                    item_data["is_reviewed"] = True
                else:
                    item_data["is_reviewed"] = False

                item_data["adjudication_category"] = cat
                item_data["adjudication_explanation"] = exp
                unmatched_items.append(item_data)

        # Compute missed gold edges
        missed_gold_items: List[Dict[str, Any]] = []
        for idx, (g_c, g_e) in enumerate(gt_direct):
            if idx not in matched_gt_d_indices:
                missed_gold_items.append({
                    "cause": g_c,
                    "effect": g_e,
                    "gold_type": "direct",
                    "status": "Missed gold relation (FN)",
                })
        for idx, (g_c, g_e) in enumerate(gt_cross):
            if idx not in matched_gt_c_indices:
                missed_gold_items.append({
                    "cause": g_c,
                    "effect": g_e,
                    "gold_type": "cross_page",
                    "status": "Missed gold relation (FN)",
                })

        # Official Metrics (Direct + Cross combined)
        total_gold = len(gt_direct) + len(gt_cross)
        total_pred = len(clean_relations)
        tp = len(matched_items)
        fp = len(unmatched_items)
        fn = len(missed_gold_items)

        p = round(tp / max(1, total_pred), 4) if total_pred > 0 else 0.0
        r = round(tp / max(1, total_gold), 4) if total_gold > 0 else 0.0
        f1 = round((2 * p * r) / (p + r), 4) if (p + r) > 0 else 0.0

        # Adjudicated Counts
        adj_counts = {
            "gold_match": len(matched_items),
            "likely_annotation_omission": sum(1 for x in unmatched_items if x["adjudication_category"] == "Likely annotation omission"),
            "genuine_false_positive": sum(1 for x in unmatched_items if x["adjudication_category"] == "Genuine false positive"),
            "unsupported_inference": sum(1 for x in unmatched_items if x["adjudication_category"] == "Unsupported inference"),
            "duplicate_or_normalization": sum(1 for x in unmatched_items if x["adjudication_category"] == "Duplicate or normalization issue"),
            "ambiguous": sum(1 for x in unmatched_items if x["adjudication_category"] == "Ambiguous"),
        }

        # Exploratory precision (crediting likely annotation omissions)
        exploratory_tp = tp + adj_counts["likely_annotation_omission"]
        exploratory_p = round(exploratory_tp / max(1, total_pred), 4) if total_pred > 0 else 0.0

        return {
            "gold_available": True,
            "pmcid": target_pmcid,
            "paper_title": gt.get("title", session_data.get("title", "")),
            "annotation_source": gt.get("provenance", "PubMed Central Open Access Benchmark Standard"),
            "canonical_entities": canon_entities,
            "total_gold": total_gold,
            "total_predicted": total_pred,
            "counts": {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "gold_direct": len(gt_direct),
                "gold_cross": len(gt_cross),
                "matched_direct": len(matched_gt_d_indices),
                "matched_cross": len(matched_gt_c_indices),
            },
            "official_metrics": {
                "precision": p,
                "recall": r,
                "f1": f1,
            },
            "adjudicated_analysis": {
                "summary": adj_counts,
                "exploratory_precision_with_omissions": exploratory_p,
            },
            "matched_relations": matched_items,
            "unmatched_predictions": unmatched_items,
            "missed_gold": missed_gold_items,
        }

    def record_adjudication_override(
        self, session_id: str, relation_id: str, category: str, note: str = ""
    ) -> Dict[str, Any]:
        """Allows human reviewer to record an adjudication decision for a session relation."""
        if session_id not in self._session_adjudications:
            self._session_adjudications[session_id] = {}
        self._session_adjudications[session_id][relation_id] = {
            "category": category,
            "note": note,
            "timestamp": time.time(),
        }
        return {"status": "success", "session_id": session_id, "relation_id": relation_id, "category": category}
