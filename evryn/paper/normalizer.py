# evryn paper extract <pdf_path>
# pytest tests/test_paper_pipeline.py

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set

from .types import ScientificDocument, SentenceSpan


GLOBAL_SYNONYMS = {
    "interleukin-6": "IL-6",
    "interleukin 6": "IL-6",
    "il6": "IL-6",
    "il-6": "IL-6",
    "signal transducer and activator of transcription 3": "STAT3",
    "stat-3": "STAT3",
    "stat3": "STAT3",
    "suppressor of cytokine signaling 3": "SOCS3",
    "socs-3": "SOCS3",
    "socs3": "SOCS3",
    "tumor necrosis factor alpha": "TNF-alpha",
    "tumor necrosis factor-alpha": "TNF-alpha",
    "tnf-a": "TNF-alpha",
    "tnfa": "TNF-alpha",
    "tnf-alpha": "TNF-alpha",
    "vascular endothelial growth factor": "VEGF",
    "vegf-a": "VEGF",
    "vegf": "VEGF",
    "hypoxia-inducible factor 1-alpha": "HIF-1alpha",
    "hypoxia-inducible factor 1 alpha": "HIF-1alpha",
    "hif-1a": "HIF-1alpha",
    "hif1a": "HIF-1alpha",
    "hif-1alpha": "HIF-1alpha",
    "epidermal growth factor receptor": "EGFR",
    "egf receptor": "EGFR",
    "egfr": "EGFR",
    "mitogen-activated protein kinase": "MAPK",
    "map kinase": "MAPK",
    "mapk": "MAPK",
    "extracellular signal-regulated kinase": "ERK",
    "erk1/2": "ERK",
    "erk": "ERK",
    "protein kinase b": "AKT",
    "akt1": "AKT",
    "akt": "AKT",
    "mammalian target of rapamycin": "mTOR",
    "mtor": "mTOR",
    "mtorc1": "mTORC1",
    "mtorc2": "mTORC2",
    "amp-activated protein kinase": "AMPK",
    "ampk": "AMPK",
    "nuclear factor kappa b": "NF-kB",
    "nuclear factor-kappa b": "NF-kB",
    "nf-kappab": "NF-kB",
    "nf-kb": "NF-kB",
    "nfkb": "NF-kB",
    "cellular tumor antigen p53": "p53",
    "tumor protein p53": "p53",
    "tp53": "p53",
    "p53": "p53",
    "cyclin-dependent kinase inhibitor 1a": "p21",
    "cdkn1a": "p21",
    "p21": "p21",
    "transforming growth factor beta": "TGF-beta",
    "tgf-b": "TGF-beta",
    "tgf-beta": "TGF-beta",
    "tgfb": "TGF-beta",
    "reactive oxygen species": "ROS",
    "ros": "ROS",
    "nitric oxide": "NO",
    "caspase-3": "Caspase-3",
    "casp3": "Caspase-3",
    "caspase-9": "Caspase-9",
    "casp9": "Caspase-9",
    "bcl-2-associated x protein": "BAX",
    "bax": "BAX",
    "b-cell lymphoma 2": "Bcl-2",
    "bcl2": "Bcl-2",
    "bcl-2": "Bcl-2",
    "grb2": "GRB2",
    "sos1": "SOS1",
    "ras": "RAS",
    "raf": "RAF",
    "mek": "MEK",
    "jak1": "JAK1",
    "jak2": "JAK2",
    "stat1": "STAT1",
    "irf1": "IRF1",
    "atm": "ATM",
    "cdk2": "CDK2",
    "tsc2": "TSC2",
    "ulk1": "ULK1",
    "ikk": "IKK",
    "tgfbr1": "TGFBR1",
    "smad3": "SMAD3",
    "wnt3a": "Wnt3a",
    "dishevelled": "Dishevelled",
    "gsk3-beta": "GSK3-beta",
    "gsk-3b": "GSK3-beta",
    "beta-catenin": "beta-catenin",
    "b-catenin": "beta-catenin",
    "dll4": "DLL4",
    "notch1": "Notch1",
    "nicd": "NICD",
    "hes1": "HES1",
    "pi3k": "PI3K",
    "igf-1": "IGF-1",
    "bad": "BAD",
    "hypoxia": "Hypoxia",
    "angiogenesis": "Angiogenesis",
    "collagen": "Collagen",
    "cytochrome c": "Cytochrome c",
    "ifn-gamma": "IFN-gamma",
    "interferon-gamma": "IFN-gamma",
}


class PaperEntityNormalizer:

    def __init__(self):
        self.abbreviation_pattern = re.compile(
            r"\b([A-Za-z][A-Za-z0-9\s-]{2,45})\s*\(([A-Za-z0-9\u0370-\u03ff-]{2,15})\)"
        )

    def extract_document_abbreviations(self, full_text: str) -> Dict[str, str]:
        abbr_map: Dict[str, str] = {}
        for match in self.abbreviation_pattern.finditer(full_text):
            long_form = match.group(1).strip()
            short_form = match.group(2).strip()
            
            if len(short_form) < 2 or len(short_form) > 12:
                continue
            if len(long_form) < len(short_form):
                continue
            if any(w in long_form.lower() for w in ["figure", "table", "ref", "page", "et al", "see"]):
                continue

            canon = self.canonicalize(short_form)
            if canon == short_form and (short_form.isupper() or any(c.isupper() for c in short_form)):
                canon = short_form
            elif canon == short_form:
                canon = self.canonicalize(long_form)

            abbr_map[short_form.lower()] = canon
            abbr_map[long_form.lower()] = canon

        return abbr_map

    def canonicalize(self, raw_name: str, local_abbr_map: Optional[Dict[str, str]] = None) -> str:
        cleaned = raw_name.strip()
        cleaned = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusion|page\s+\d+)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^the\s+|^a\s+|^an\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:phosphorylated|activated|active|nuclear|cytosolic|membrane-anchored|elevated|stabilized|secreted|soluble|dimerized|pro-apoptotic)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        key = cleaned.lower()

        if local_abbr_map and key in local_abbr_map:
            return local_abbr_map[key]

        if key in GLOBAL_SYNONYMS:
            return GLOBAL_SYNONYMS[key]

        for syn_k, syn_v in GLOBAL_SYNONYMS.items():
            if key == syn_k or key == syn_k.replace("-", " ") or key.replace("-", " ") == syn_k:
                return syn_v

        return cleaned

    def detect_entities_in_sentence(
        self,
        sentence: str,
        local_abbr_map: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[str, str, int, int]]:
        mentions: List[Tuple[str, str, int, int]] = []
        known_vocab = set(GLOBAL_SYNONYMS.keys())
        if local_abbr_map:
            known_vocab.update(local_abbr_map.keys())

        for term in sorted(known_vocab, key=len, reverse=True):
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for m in pattern.finditer(sentence):
                raw = m.group(0)
                canon = self.canonicalize(raw, local_abbr_map)
                mentions.append((raw, canon, m.start(), m.end()))

        mentions.sort(key=lambda x: x[2])
        filtered_mentions: List[Tuple[str, str, int, int]] = []
        last_end = -1
        for m in mentions:
            if m[2] >= last_end:
                filtered_mentions.append(m)
                last_end = m[3]

        return filtered_mentions
