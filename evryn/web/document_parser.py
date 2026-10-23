import os
import re
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple

import pypdf

from evryn.paper.types import (
    ScientificDocument,
    PageBoundary,
    PaperMetadata,
    SectionSpan,
    ScientificSectionType,
    ParagraphSpan,
    SentenceSpan,
)
from evryn.paper.ingestion import PaperIngestion
from evryn.paper.segmentation import PaperSegmenter


class DocumentParsingError(Exception):
    pass


class DocumentParser:
    def __init__(self):
        self.ingestion = PaperIngestion()
        self.segmenter = PaperSegmenter()

    def parse_file(self, file_path: str, original_filename: Optional[str] = None) -> ScientificDocument:
        name = original_filename or os.path.basename(file_path)
        ext = os.path.splitext(name)[1].lower()

        if ext == ".pdf":
            return self._parse_pdf(file_path, name)
        elif ext in [".txt", ".text", ".md"]:
            return self._parse_txt(file_path, name)
        elif ext == ".docx":
            return self._parse_docx(file_path, name)
        else:
            # Fallback to plain text read
            return self._parse_txt(file_path, name)

    def _parse_pdf(self, file_path: str, filename: str) -> ScientificDocument:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise DocumentParsingError(f"PDF file '{filename}' is empty or does not exist.")

        try:
            doc = self.ingestion.ingest_pdf(file_path)
            doc = self.segmenter.segment_document(doc)
            return doc
        except Exception as e:
            raise DocumentParsingError(f"Failed to parse PDF '{filename}': {str(e)}")

    def _parse_txt(self, file_path: str, filename: str) -> ScientificDocument:
        if not os.path.exists(file_path):
            raise DocumentParsingError(f"File '{filename}' does not exist.")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise DocumentParsingError(f"Failed to read file '{filename}': {str(e)}")

        if not content.strip():
            raise DocumentParsingError(f"Text file '{filename}' contains no readable text.")

        return self.parse_raw_text(content, filename)

    def parse_raw_text(self, text: str, filename: str = "raw_input.txt") -> ScientificDocument:
        doc_id = f"doc_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"
        full_text = text.strip()

        # Check for explicit page markers e.g. "Page 1", "[Page 2]"
        page_splits = re.split(r"\n+(?:---\s*Page\s+\d+\s*---|\[Page\s+\d+\]|Page\s+\d+\s*[-—:])\n*", full_text, flags=re.IGNORECASE)
        pages_boundaries: List[PageBoundary] = []
        sentences: List[SentenceSpan] = []
        paragraphs: List[ParagraphSpan] = []
        sections: List[SectionSpan] = []

        if len(page_splits) > 1 and page_splits[0].strip() == "":
            page_splits = page_splits[1:]

        offset = 0
        if len(page_splits) > 1:
            for p_idx, p_text in enumerate(page_splits):
                p_num = p_idx + 1
                p_len = len(p_text)
                pages_boundaries.append(
                    PageBoundary(page_number=p_num, start_char=offset, end_char=offset + p_len, char_count=p_len)
                )
                self._extract_paras_and_sentences(p_text, p_num, offset, paragraphs, sentences, sections)
                offset += p_len + 1
        else:
            pages_boundaries.append(
                PageBoundary(page_number=1, start_char=0, end_char=len(full_text), char_count=len(full_text))
            )
            self._extract_paras_and_sentences(full_text, 1, 0, paragraphs, sentences, sections)

        meta = PaperMetadata(
            title=filename.replace("_", " ").replace(".txt", "").title(),
            authors=["Direct Input"],
            doi=None,
            pmid=None,
            pmcid=None,
            page_count=len(pages_boundaries),
        )

        return ScientificDocument(
            doc_id=doc_id,
            file_path=filename,
            metadata=meta,
            full_text=full_text,
            pages=pages_boundaries,
            sections=sections,
            paragraphs=paragraphs,
            sentences=sentences,
        )

    def _extract_paras_and_sentences(
        self,
        text: str,
        page_num: int,
        base_offset: int,
        paragraphs: List[ParagraphSpan],
        sentences: List[SentenceSpan],
        sections: List[SectionSpan],
    ):
        raw_paras = re.split(r"\n\s*\n+", text)
        curr_offset = base_offset
        current_section = "Results & Discussion"

        for para_idx, para in enumerate(raw_paras):
            para_clean = para.strip()
            if not para_clean:
                continue

            # Check if paragraph is a section header
            sec_m = re.match(r"^\[?(?:Section|Part)?\s*([A-Za-z0-9\s&/-]{3,40})\]?:?$", para_clean, re.IGNORECASE)
            if sec_m and len(para_clean.split()) <= 4:
                current_section = sec_m.group(1).strip()
                sections.append(
                    SectionSpan(
                        section_title=current_section,
                        section_type=ScientificSectionType.RESULTS,
                        start_char=curr_offset,
                        end_char=curr_offset + len(para_clean),
                        page_number=page_num,
                    )
                )
                curr_offset += len(para) + 1
                continue

            p_id = f"para_p{page_num}_{len(paragraphs) + 1}"
            para_start = curr_offset
            para_end = curr_offset + len(para_clean)

            paragraphs.append(
                ParagraphSpan(
                    paragraph_id=p_id,
                    page_number=page_num,
                    section_title=current_section,
                    start_char=para_start,
                    end_char=para_end,
                    text=para_clean,
                )
            )

            # Sentence splitting
            raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", para_clean)
            s_offset = para_start
            for s_idx, sent_str in enumerate(raw_sents):
                s_str = sent_str.strip()
                if not s_str:
                    continue
                s_id = f"sent_p{page_num}_{len(sentences) + 1}"
                s_len = len(s_str)
                sentences.append(
                    SentenceSpan(
                        sentence_id=s_id,
                        page_number=page_num,
                        section_title=current_section,
                        paragraph_id=p_id,
                        start_char=s_offset,
                        end_char=s_offset + s_len,
                        text=s_str,
                    )
                )
                s_offset += len(sent_str) + 1

            curr_offset += len(para) + 1

    def _parse_docx(self, file_path: str, filename: str) -> ScientificDocument:
        if not os.path.exists(file_path):
            raise DocumentParsingError(f"DOCX file '{filename}' does not exist.")

        try:
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            paragraphs = []
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for p in tree.iter(f"{{{ns['w']}}}p"):
                texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            full_text = "\n\n".join(paragraphs)
            return self.parse_raw_text(full_text, filename)
        except Exception as e:
            raise DocumentParsingError(f"Failed to parse DOCX '{filename}': {str(e)}")
