# evryn datasets pmc_oa
# pytest tests/test_dataset_adapters.py

import os
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class PMCOASentence:
    id: str
    section_id: str
    text: str
    start_char: int
    end_char: int


@dataclass
class PMCOASection:
    id: str
    section_type: str
    title: str
    paragraphs: List[str]
    sentences: List[PMCOASentence] = field(default_factory=list)


@dataclass
class PMCOADocument:
    pmcid: str
    pmid: Optional[str]
    doi: Optional[str]
    title: str
    journal: str
    authors: List[str]
    license_type: str
    license_url: str
    source_url: str
    sections: List[PMCOASection] = field(default_factory=list)
    raw_xml: Optional[str] = None
    full_text: str = ""

    def get_section_by_type(self, section_type: str) -> List[PMCOASection]:
        target = section_type.upper()
        return [s for s in self.sections if s.section_type.upper() == target]


class PMCOAIngester:
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&retmode=xml&id="

    SECTION_MAP = {
        "intro": "INTRODUCTION",
        "introduction": "INTRODUCTION",
        "background": "BACKGROUND",
        "method": "METHODS",
        "methods": "METHODS",
        "material": "METHODS",
        "materials": "METHODS",
        "result": "RESULTS",
        "results": "RESULTS",
        "discuss": "DISCUSSION",
        "discussion": "DISCUSSION",
        "conclu": "CONCLUSION",
        "conclusions": "CONCLUSION",
        "abstract": "ABSTRACT",
    }

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "real_papers", "xml"
        )
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_xml(self, pmcid: str, force_refresh: bool = False) -> str:
        clean_id = pmcid.strip()
        numeric_id = clean_id.upper().replace("PMC", "")
        formatted_pmcid = f"PMC{numeric_id}"
        cache_path = os.path.join(self.cache_dir, f"{formatted_pmcid}.xml")

        if not force_refresh and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()

        url = f"{self.EFETCH_URL}{numeric_id}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EVRYN-Scientific-Causal-Discovery/2.0 (evryn-dev@users.noreply.github.com)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_bytes = resp.read()

        xml_str = xml_bytes.decode("utf-8", errors="replace")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        return xml_str

    def parse_xml(self, xml_content: str, pmcid_override: Optional[str] = None) -> PMCOADocument:
        root = ET.fromstring(xml_content)
        found_art = root.find(".//article")
        article = found_art if found_art is not None else root

        pmcid = pmcid_override or ""
        pmid = None
        doi = None

        for aid in article.findall(".//article-id"):
            id_type = aid.attrib.get("pub-id-type")
            text = (aid.text or "").strip()
            if id_type == "pmc":
                pmcid = f"PMC{text}" if not text.startswith("PMC") else text
            elif id_type == "pmid":
                pmid = text
            elif id_type == "doi":
                doi = text

        title_elem = article.find(".//article-title")
        title = "".join(title_elem.itertext()).strip() if title_elem is not None else "Untitled Article"

        j_title = article.find(".//journal-title")
        journal_elem = j_title if j_title is not None else article.find(".//journal-id")
        journal = "".join(journal_elem.itertext()).strip() if journal_elem is not None else "Unknown Journal"

        authors: List[str] = []
        for contrib in article.findall(".//contrib[@contrib-type='author']"):
            surname = contrib.findtext(".//surname") or ""
            given = contrib.findtext(".//given-names") or ""
            if surname or given:
                authors.append(f"{given} {surname}".strip())

        license_type = "Open Access"
        license_url = ""
        license_elem = article.find(".//license")
        if license_elem is not None:
            license_url = license_elem.attrib.get("{http://www.w3.org/1999/xlink}href", "")
            license_text = "".join(license_elem.itertext()).strip()
            if "Creative Commons" in license_text or "CC BY" in license_text:
                license_type = "CC BY"
                if "4.0" in license_text:
                    license_type = "CC BY 4.0"
                elif "3.0" in license_text:
                    license_type = "CC BY 3.0"

        source_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else ""

        sections: List[PMCOASection] = []
        sec_counter = 0

        abstract_elem = article.find(".//abstract")
        if abstract_elem is not None:
            abs_paras: List[str] = []
            for p in abstract_elem.findall(".//p"):
                ptxt = "".join(p.itertext()).strip()
                if ptxt:
                    abs_paras.append(ptxt)
            if abs_paras:
                sec_counter += 1
                sections.append(
                    PMCOASection(
                        id=f"sec_{sec_counter}",
                        section_type="ABSTRACT",
                        title="Abstract",
                        paragraphs=abs_paras,
                    )
                )

        body_elem = article.find(".//body")
        if body_elem is not None:
            for sec in body_elem.findall(".//sec"):
                title_node = sec.find("title")
                sec_title = "".join(title_node.itertext()).strip() if title_node is not None else ""
                sec_type = self._classify_section_type(sec_title)

                paras: List[str] = []
                for p in sec.findall("p"):
                    ptxt = "".join(p.itertext()).strip()
                    if ptxt:
                        paras.append(ptxt)

                if paras:
                    sec_counter += 1
                    sections.append(
                        PMCOASection(
                            id=f"sec_{sec_counter}",
                            section_type=sec_type,
                            title=sec_title or sec_type.title(),
                            paragraphs=paras,
                        )
                    )

        running_char = 0
        full_text_parts: List[str] = []
        for sec in sections:
            sec_sentences: List[PMCOASentence] = []
            for p in sec.paragraphs:
                full_text_parts.append(p)
                sentences = self._split_sentences(p)
                p_offset = 0
                for sent_idx, sent in enumerate(sentences):
                    s_pos = p.find(sent, p_offset)
                    if s_pos == -1:
                        s_pos = p_offset
                    e_pos = s_pos + len(sent)
                    p_offset = e_pos
                    sec_sentences.append(
                        PMCOASentence(
                            id=f"{sec.id}_s{len(sec_sentences)+1}",
                            section_id=sec.id,
                            text=sent,
                            start_char=running_char + s_pos,
                            end_char=running_char + e_pos,
                        )
                    )
                running_char += len(p) + 2
            sec.sentences = sec_sentences

        return PMCOADocument(
            pmcid=pmcid,
            pmid=pmid,
            doi=doi,
            title=title,
            journal=journal,
            authors=authors,
            license_type=license_type,
            license_url=license_url,
            source_url=source_url,
            sections=sections,
            raw_xml=xml_content,
            full_text="\n\n".join(full_text_parts),
        )

    def _classify_section_type(self, title: str) -> str:
        low = title.lower()
        for key, stype in self.SECTION_MAP.items():
            if key in low:
                return stype
        return "BODY"

    def _split_sentences(self, text: str) -> List[str]:
        pattern = re.compile(r"(?<=[.!?])\s+")
        splits = pattern.split(text)
        return [s.strip() for s in splits if s.strip()]

    def ingest_pmcid(self, pmcid: str) -> PMCOADocument:
        xml_str = self.fetch_xml(pmcid)
        return self.parse_xml(xml_str, pmcid_override=pmcid)


def load_pmc_oa_document(pmcid: str, cache_dir: Optional[str] = None) -> PMCOADocument:
    ingester = PMCOAIngester(cache_dir=cache_dir)
    return ingester.ingest_pmcid(pmcid)
