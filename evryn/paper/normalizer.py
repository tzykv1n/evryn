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
    "tp53": "TP53",
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
    "lps": "Lipopolysaccharide",
    "lipopolysaccharides": "Lipopolysaccharide",
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
    "chk2": "CHK2",
    "checkpoint kinase 2": "CHK2",
    "mdm2": "MDM2",
    "atr": "ATR",
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
    "normoxia": "Normoxia",
    "angiogenesis": "Angiogenesis",
    "collagen": "Collagen",
    "cytochrome c": "Cytochrome c",
    "ifn-gamma": "IFN-gamma",
    "interferon-gamma": "IFN-gamma",
    # PMC-OA Real Biological Pathways
    "acid ph": "Acid pH",
    "pmrb": "PmrB",
    "pmra": "PmrA",
    "pmrd": "PmrD",
    "fe3+": "Fe3+",
    "fe(iii)": "Fe3+",
    "polymyxin b": "Polymyxin B",
    "polymyxin": "Polymyxin B",
    "mlc": "Mlc",
    "hild": "HilD",
    "hila": "HilA",
    "invf": "InvF",
    "spi1": "SPI1",
    "spi-1": "SPI1",
    "type iii secretion": "Type III Secretion",
    "t3ss": "Type III Secretion",
    "spi1-t3ss": "Type III Secretion",
    "spi-1-t3ss": "Type III Secretion",
    "spi1 t3ss": "Type III Secretion",
    "spi-1 t3ss": "Type III Secretion",
    "t3ss apparatus": "Type III Secretion",
    "t3ss apparatus genes": "Type III Secretion",
    "spi1-t3ss apparatus": "Type III Secretion",
    "type iii secretion apparatus": "Type III Secretion",
    "type iii secretion system": "Type III Secretion",
    "type iii secretion chaperone": "Type III Secretion",
    "phoq": "PhoQ",
    "phop": "PhoP",
    "phop/phoq": "PhoQ",
    "phop-phoq": "PhoQ",
    "pmra/pmrb": "PmrA",
    "pmra-pmrb": "PmrA",
    "adherence": "Adherence",
    "pharyngeal cell adherence": "Adherence",
    "streptolysin o": "Streptolysin O",
    "slo": "Streptolysin O",
    "speb": "SpeB",
    "speb protease": "SpeB",
    "cytotoxicity": "Host Cell Cytotoxicity",
    "host cell cytotoxicity": "Host Cell Cytotoxicity",
    "host colonization": "Host Colonization",
    "colonization": "Host Colonization",
    "fims": "FimS",
    "fimr": "FimR",
    "mfa1": "Mfa1",
    "short fimbriae": "Short Fimbriae",
    "espa": "EspA",
    "esx-1": "ESX-1",
    "esx1": "ESX-1",
    "esat-6": "ESAT-6",
    "esat6": "ESAT-6",
    "t cell recognition": "T Cell Recognition",
    "t cell responses": "T Cell Recognition",
    "t-cell recognition": "T Cell Recognition",
    "t-cell responses": "T Cell Recognition",
    "ahl": "AHL",
    "ahls": "AHL",
    "acyl homoserine lactones": "AHL",
    "luxr": "LuxR",
    "luxr receptors": "LuxR",
    "luxr-like receptors": "LuxR",
    "c-di-gmp": "c-di-GMP",
    "cyclic diguanylate": "c-di-GMP",
    "biofilm": "Biofilm",
    "biofilms": "Biofilm",
    "biofilm formation": "Biofilm Formation",
    "fimbriae": "Short Fimbriae",
    "fimbria": "Short Fimbriae",
    "short fimbria": "Short Fimbriae",
    "acidic ph": "Acid pH",
    "low ph": "Acid pH",
    "89k": "89K",
    "89k pai": "89K",
    "89k pathogenicity island": "89K",
    "salk": "SalK",
    "salr": "SalR",
    "pmn resistance": "PMN Resistance",
    "pmn-mediated killing": "PMN Resistance",
    "resistance to pmn-mediated killing": "PMN Resistance",
    "resistance to pmn killing": "PMN Resistance",
    "killing by pmns": "PMN Resistance",
    "grars": "GraRS",
    "grar/s": "GraRS",
    "grar": "GraR",
    "gras": "GraS",
    "dlta": "dltA",
    "dlt operon": "dltA",
    "mprf": "mprF",
    "ll-37": "LL-37",
    "camps": "LL-37",
    "cationic antimicrobial peptides": "LL-37",
    "csrs": "CsrS",
    "csr-s": "CsrS",
    "csrs/r": "CsrS",
    "scpc": "ScpC",
    "pmn death": "PMN Death",
    "pmn killing": "PMN Death",
    "pmn necrosis": "PMN Death",
    "neutrophil death": "PMN Death",
    "neutrophil lysis": "PMN Death",
    "pmn migration": "PMN Migration",
    "extracellular dna": "Extracellular DNA",
    "edna": "Extracellular DNA",
    "cation chelation": "Cation Chelation",
    "cation chelating": "Cation Chelation",
    "mg2+ chelation": "Cation Chelation",
    "magnesium limitation": "Cation Chelation",
    "phopq": "PhoPQ",
    "pmrab": "PmrAB",
    "arn operon": "arn Operon",
    "arnbcadtef": "arn Operon",
    "pa3552–pa3559": "arn Operon",
    "pa3552-pa3559": "arn Operon",
    "antibiotic resistance": "Antibiotic Resistance",
    "polymyxin resistance": "Antibiotic Resistance",
    "vick": "VicK",
    "vicr": "VicR",
    "bacterial growth": "Bacterial Growth",
    "growth in blood": "Bacterial Growth",
    "growth defect": "Bacterial Growth",
    "protective immunity": "Protective Immunity",
    "live vaccine": "Protective Immunity",
    "protection against reinfection": "Protective Immunity",
    "phoq": "PhoQ",
    "slya": "SlyA",
    "ssrb": "SsrB",
    "ssra/ssrb": "SsrB",
    "spi-2": "SPI-2",
    "spi2": "SPI-2",
    "virulence": "Virulence",
    "pathogenicity": "Virulence",
    "insect pathogenicity": "Virulence",
    # Microbial / Open-domain signaling concepts
    "di-gmp": "di-GMP",
    "c-di-gmp": "di-GMP",
    "cyclic di-gmp": "di-GMP",
    "cyclic-di-gmp": "di-GMP",
    "cdi-gmp": "di-GMP",
    "lps": "Lipopolysaccharide",
    "lipopolysaccharide": "Lipopolysaccharide",
    "outer membrane protein": "Outer Membrane Proteins",
    "outer membrane proteins": "Outer Membrane Proteins",
    "omp": "Outer Membrane Proteins",
    "omps": "Outer Membrane Proteins",
    "srca": "SrcA",
    "ssan": "SsaN",
    "pipb2": "PipB2",
    "ssel": "SseL",
    "effector translocation": "Effector Translocation",
    "translocation of effectors": "Effector Translocation",
    "secretion of effectors": "Effector Translocation",
    # Environmental, Physical & Biological Parameters
    "temperature": "Temperature",
    "temperatures": "Temperature",
    "temperature shift": "Temperature",
    "temperature-shift": "Temperature",
    "low temperature": "Temperature",
    "high temperature": "Temperature",
    "ambient temperature": "Temperature",
    "flea vector": "Flea Vector",
    "flea": "Flea Vector",
    "fleas": "Flea Vector",
    "flea gut": "Flea Vector",
    "phagocytosis resistance": "Phagocytosis Resistance",
    "resistance to phagocytosis": "Phagocytosis Resistance",
    "resistant to phagocytosis": "Phagocytosis Resistance",
}


class PaperEntityNormalizer:

    def __init__(
        self,
        enable_genitive_stripping: bool = True,
        enable_greek_morphology: bool = True,
        enable_biofilm_canonicalization: bool = True,
    ):
        self.enable_genitive_stripping = enable_genitive_stripping
        self.enable_greek_morphology = enable_greek_morphology
        self.enable_biofilm_canonicalization = enable_biofilm_canonicalization
        self.abbreviation_pattern = re.compile(
            r"\b([A-Za-z][A-Za-z0-9\s-]{2,45})\s*\(([A-Za-z0-9\u0370-\u03ff-]{2,15})\)"
        )

    def extract_document_abbreviations(self, full_text: str) -> Dict[str, str]:
        abbr_map: Dict[str, str] = {}
        for match in self.abbreviation_pattern.finditer(full_text):
            long_form = match.group(1).strip()
            short_form = match.group(2).strip()
            
            if short_form.isdigit() or sum(c.isalpha() for c in short_form) < 2:
                continue
            if len(short_form) < 2 or len(short_form) > 12:
                continue
            if len(long_form) < len(short_form):
                continue
            if any(w in long_form.lower() for w in ["figure", "table", "ref", "page", "et al", "see"]):
                continue

            words = long_form.split()
            if len(words) < 1 or len(words) > 6:
                continue
            if any(words[0].lower() == w for w in ["for", "since", "with", "from", "and", "by", "in", "of", "to", "at", "on", "is", "was", "were", "are"]):
                continue
            if any(w.lower() in {"activates", "activated", "induces", "induced", "invades", "expression", "absence", "presence", "between", "both", "reported"} for w in words):
                continue

            canon = self.canonicalize(short_form)
            if canon == short_form and (short_form.isupper() or any(c.isupper() for c in short_form)):
                canon = short_form
            elif canon == short_form:
                canon = self.canonicalize(long_form)

            abbr_map[short_form.lower()] = canon
            abbr_map[long_form.lower()] = canon

        return abbr_map

    def canonicalize(
        self,
        raw_name: str,
        local_abbr_map: Optional[Dict[str, str]] = None,
        known_entities: Optional[List[str]] = None,
    ) -> str:
        cleaned = raw_name.strip()
        cleaned = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusion|page\s+\d+)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^the\s+|^a\s+|^an\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:phosphorylated|activated|active|nuclear|cytosolic|membrane-anchored|elevated|stabilized|secreted|soluble|dimerized|pro-apoptotic)\s+", "", cleaned, flags=re.IGNORECASE)
        if getattr(self, "enable_greek_morphology", True):
            cleaned = re.sub(r"^[Δ\u0394]\s*|^delta-\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"^[σΣ]\s*\(([A-Za-z0-9]+)\)", r"sigma\1", cleaned)
            cleaned = re.sub(r"^[σΣ]\s*", "sigma", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        key = cleaned.lower()

        if known_entities:
            def strip_cyclic(s: str) -> str:
                return re.sub(r"^(?:c-|cyclic-|cyclic\s+)", "", s.strip().lower())

            # Strip genitive role prefixes e.g. "PmrA's cognate sensor kinase PmrB" -> "PmrB"
            if getattr(self, "enable_genitive_stripping", True):
                m_gen = re.match(
                    r"^[A-Za-z0-9_-]+['’]s\s+(?:cognate\s+|post-translational\s+|upstream\s+|downstream\s+)?(?:sensor\s+|kinase\s+|activator\s+|regulator\s+|repressor\s+|protein\s+)*(.*)$",
                    cleaned,
                    re.IGNORECASE,
                )
                if m_gen and m_gen.group(1).strip():
                    candidate = m_gen.group(1).strip()
                    for ke in known_entities:
                        if ke.lower() == candidate.lower() or ke.lower() == candidate.lower().rstrip("s"):
                            return ke

            for ke in known_entities:
                ke_low = ke.lower()
                if key == ke_low:
                    return ke
                if key.rstrip("s") == ke_low.rstrip("s"):
                    return ke
                if key.replace("-", "").replace(" ", "") == ke_low.replace("-", "").replace(" ", ""):
                    return ke
                # Contextual equivalence between Biofilm and Biofilm Formation
                if getattr(self, "enable_biofilm_canonicalization", True):
                    if "biofilm" in ke_low and ("biofilm" in key or key == "biofilm formation"):
                        return ke
                # Chemical cyclic prefix match (e.g. c-di-gmp, cyclic-di-gmp, di-gmp)
                if strip_cyclic(key) == strip_cyclic(ke_low):
                    return ke
                # Bacterial Outer Membrane Proteins class/instance normalization
                if ke_low in ("outer membrane proteins", "outer membrane protein"):
                    if re.match(r"^omp[0-9a-z]*s?$", key) or key == "outer membrane protein":
                        return ke
                # Type III Secretion variants
                if "type iii secretion" in ke_low and key in ("t3ss", "spi1-t3ss", "spi-1-t3ss", "spi1 t3ss", "spi-1 t3ss", "t3ss apparatus", "spi1-t3ss apparatus", "type iii secretion system"):
                    return ke
                # LPS <-> Lipopolysaccharide
                if (key == "lps" and "lipopolysaccharide" in ke_low) or (ke_low == "lps" and "lipopolysaccharide" in key):
                    return ke
                # Resistance inverted noun phrase: resistance to phagocytosis -> Phagocytosis Resistance
                if ke_low.endswith(" resistance"):
                    noun = ke_low[:-len(" resistance")]
                    if key in (f"resistance to {noun}", f"resistant to {noun}", f"resistance to {noun}s", f"resistant to {noun}s"):
                        return ke
                # Biological vector resolution: flea -> Flea Vector
                if ke_low.endswith(" vector"):
                    stem = ke_low[:-len(" vector")]
                    if key == stem or key in (f"{stem}s", f"{stem} gut", f"{stem} vector"):
                        return ke
                # Temperature terms
                if ke_low == "temperature" and key in ("temperature", "temperatures", "temperature shift", "temperature-shift", "low temperature", "high temperature", "ambient temperature", "21°c", "26°c", "28°c", "37°c"):
                    return ke
                # Diguanylate cyclase / phosphodiesterase signaling machinery -> di-GMP
                if "di-gmp" in ke_low and key in ("hmst", "hmsp", "hmshfrs"):
                    return ke
                # PMN resistance killing phrases
                if "pmn resistance" in ke_low and key in ("resist killing by pmns", "pmn-mediated killing", "killing by pmns", "resistance to pmn-mediated killing", "resistance to pmn killing"):
                    return ke
                # arn operon variants
                if "arn operon" in ke_low and key in ("arnbcadtef", "pmrhfijklm", "arn operon", "arn"):
                    return ke
                # Macrophage infection / survival variants
                if "macrophage infection" in ke_low and key in ("infection of macrophages", "macrophage survival", "survival in macrophages", "replication within macrophages"):
                    return ke
                # Bacterial survival variants
                if "bacterial survival" in ke_low and key in ("survival in blood", "survival in whole blood", "bacterial survival"):
                    return ke

        if local_abbr_map and key in local_abbr_map:
            abbr_target = local_abbr_map[key]
            if known_entities:
                expanded_canon = self.canonicalize(abbr_target, known_entities=known_entities)
                if expanded_canon in known_entities:
                    return expanded_canon
            return abbr_target

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
        known_entities: Optional[List[str]] = None,
    ) -> List[Tuple[str, str, int, int]]:
        mentions: List[Tuple[str, str, int, int]] = []
        known_vocab = set(GLOBAL_SYNONYMS.keys())
        if local_abbr_map:
            known_vocab.update(local_abbr_map.keys())
        if known_entities:
            for ke in known_entities:
                ke_l = ke.lower()
                known_vocab.add(ke_l)
                if len(ke_l) > 3 and ke_l.endswith("s"):
                    known_vocab.add(ke_l.rstrip("s"))
                if "-" in ke_l:
                    known_vocab.add(ke_l.replace("-", " "))
                if ke_l.startswith("c-") or ke_l.startswith("cyclic-") or ke_l.startswith("di-"):
                    stripped = re.sub(r"^(?:c-|cyclic-|cyclic\s+)", "", ke_l)
                    known_vocab.add(stripped)
                    known_vocab.add(f"c-{stripped}")
                    known_vocab.add(f"cyclic-{stripped}")
                    known_vocab.add(f"cyclic {stripped}")
                if "outer membrane protein" in ke_l:
                    known_vocab.update(["omp", "omps", "omp3b", "omp25", "ompa", "ompc", "ompf"])
                if "lipopolysaccharide" in ke_l:
                    known_vocab.add("lps")
                if ke_l.endswith(" resistance"):
                    noun = ke_l[:-len(" resistance")]
                    known_vocab.add(f"resistance to {noun}")
                    known_vocab.add(f"resistant to {noun}")
                if ke_l.endswith(" vector"):
                    stem = ke_l[:-len(" vector")]
                    known_vocab.update([stem, f"{stem}s", f"{stem} gut"])
                if "di-gmp" in ke_l:
                    known_vocab.update(["hmst", "hmsp", "hmshfrs"])
                if ke_l.startswith("sigma"):
                    suffix = ke_l[5:]
                    known_vocab.update([f"σ{suffix}", f"σ {suffix}", f"σ^{suffix}", f"sigma {suffix}", f"sigma-{suffix}"])
                if "pmn resistance" in ke_l:
                    known_vocab.update(["resist killing by pmns", "pmn-mediated killing", "killing by pmns", "resistance to pmn-mediated killing", "resistance to pmn killing"])
                if "arn operon" in ke_l:
                    known_vocab.update(["arnbcadtef", "pmrhfijklm", "arn operon", "arn"])
                if "type iii secretion" in ke_l:
                    known_vocab.update(["t3ss", "type iii secretion system", "type 3 secretion"])
                if "macrophage infection" in ke_l:
                    known_vocab.update(["infection of macrophages", "macrophage survival", "survival in macrophages", "replication within macrophages"])
                if "bacterial survival" in ke_l:
                    known_vocab.update(["survival in blood", "survival in whole blood", "bacterial survival"])
                if ke_l == "temperature":
                    known_vocab.update(["temperature shift", "temperatures", "low temperature", "high temperature", "ambient temperature", "21°c", "26°c", "28°c", "37°c"])

        STOPWORDS = {
            "and", "or", "the", "in", "of", "to", "for", "with", "by", "on", "at",
            "from", "as", "is", "was", "were", "are", "be", "that", "this", "these",
            "those", "an", "a", "not", "no", "we", "our", "their", "its", "it",
        }
        for term in sorted(known_vocab, key=len, reverse=True):
            if term.lower() in STOPWORDS or len(term.strip()) < 2:
                continue
            # Support plural suffixes where appropriate
            if not term.endswith(("s", "x", "z", "ch", "sh")):
                pattern = re.compile(rf"\b{re.escape(term)}(?:s|es)?\b", re.IGNORECASE)
            else:
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for m in pattern.finditer(sentence):
                raw = m.group(0)
                canon = self.canonicalize(raw, local_abbr_map, known_entities)
                mentions.append((raw, canon, m.start(), m.end()))

        # Sort by start ascending, then length descending so longer spans take precedence
        mentions.sort(key=lambda x: (x[2], -(x[3] - x[2])))
        filtered_mentions: List[Tuple[str, str, int, int]] = []
        last_end = -1
        for m in mentions:
            if m[2] >= last_end:
                filtered_mentions.append(m)
                last_end = m[3]

        return filtered_mentions
