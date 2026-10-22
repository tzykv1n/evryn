# evryn paper inspect <pdf_path>
# pytest tests/test_paper_pipeline.py

import re
from typing import List, Dict, Any, Optional, Tuple

from .types import (
    ScientificDocument,
    SectionSpan,
    ParagraphSpan,
    SentenceSpan,
    ScientificSectionType,
    PageBoundary,
)


SECTION_PATTERNS = [
    (r"^(?:(?:\d+\.?)?\s*)?abstract(?:\s+(?:and|&)\s+introduction)?\b", ScientificSectionType.ABSTRACT),
    (r"^(?:(?:\d+\.?)?\s*)?introduction\b", ScientificSectionType.INTRODUCTION),
    (r"^(?:(?:\d+\.?)?\s*)?background\b", ScientificSectionType.BACKGROUND),
    (r"^(?:(?:\d+\.?)?\s*)?(?:materials\s+and\s+methods|methods|experimental\s+procedures|assays|mechanisms?)\b", ScientificSectionType.METHODS),
    (r"^(?:(?:\d+\.?)?\s*)?results(?:\s+(?:and|&)\s+discussion|\s*:\s*[a-zA-Z\s]+)?\b", ScientificSectionType.RESULTS),
    (r"^(?:(?:\d+\.?)?\s*)?discussion(?:\s+(?:and|&)\s+conclusions?)?\b", ScientificSectionType.DISCUSSION),
    (r"^(?:(?:\d+\.?)?\s*)?(?:conclusions?|summary)\b", ScientificSectionType.CONCLUSION),
    (r"^(?:(?:\d+\.?)?\s*)?references\b", ScientificSectionType.REFERENCES),
]


PROTECTED_ABBREVIATIONS = [
    "fig.", "figs.", "e.g.", "i.e.", "et al.", "dr.", "prof.", "vs.", "ca.",
    "approx.", "wt.", "no.", "vol.", "pp.", "ed.", "eds.", "ref.", "refs.",
    "p.m.", "a.m.", "gen.", "sp.", "mol.", "wt.", "conc.", "temp.", "min.",
    "sec.", "hr.", "hrs.", "ave.", "std.", "dev.",
]


class PaperSegmenter:

    def __init__(self):
        pass

    def segment_document(self, doc: ScientificDocument) -> ScientificDocument:
        full_text = doc.full_text
        pages = doc.pages

        sections: List[SectionSpan] = []
        paragraphs: List[ParagraphSpan] = []
        sentences: List[SentenceSpan] = []

        lines = full_text.split("\n")
        current_offset = 0
        current_section_title = "Title & Abstract"
        current_section_type = ScientificSectionType.ABSTRACT
        current_section_start = 0

        raw_paras: List[Tuple[int, int, str, str, ScientificSectionType]] = []
        curr_para_lines: List[str] = []
        curr_para_start = 0

        for line in lines:
            line_len = len(line)
            line_start = current_offset
            line_end = current_offset + line_len
            stripped = line.strip()

            detected_sec = self._detect_section_heading(stripped)
            if detected_sec:
                if curr_para_lines:
                    para_text = "\n".join(curr_para_lines).strip()
                    if para_text:
                        raw_paras.append((curr_para_start, line_start, para_text, current_section_title, current_section_type))
                    curr_para_lines = []

                if sections:
                    sections[-1].end_char = line_start

                sec_page = self._find_page_number(line_start, pages)
                sec_span = SectionSpan(
                    section_title=stripped,
                    section_type=detected_sec,
                    page_number=sec_page,
                    start_char=line_start,
                    end_char=line_end,
                )
                sections.append(sec_span)
                current_section_title = stripped
                current_section_type = detected_sec
                current_offset = line_end + 1
                curr_para_start = current_offset
                continue

            if not stripped:
                if curr_para_lines:
                    para_text = "\n".join(curr_para_lines).strip()
                    if para_text:
                        raw_paras.append((curr_para_start, line_start, para_text, current_section_title, current_section_type))
                    curr_para_lines = []
                current_offset = line_end + 1
                curr_para_start = current_offset
                continue

            if not curr_para_lines:
                curr_para_start = line_start
            curr_para_lines.append(line)
            current_offset = line_end + 1

        if curr_para_lines:
            para_text = "\n".join(curr_para_lines).strip()
            if para_text:
                raw_paras.append((curr_para_start, current_offset - 1, para_text, current_section_title, current_section_type))

        if sections:
            sections[-1].end_char = len(full_text)
        else:
            sections.append(
                SectionSpan(
                    section_title="Full Document",
                    section_type=ScientificSectionType.RESULTS,
                    page_number=1,
                    start_char=0,
                    end_char=len(full_text),
                )
            )

        para_counter = 1
        sent_counter = 1

        for p_start, p_end, p_text, sec_title, sec_type in raw_paras:
            if not p_text.strip():
                continue
            p_page = self._find_page_number(p_start, pages)
            p_id = f"para_{p_page}_{para_counter:04d}"
            para_counter += 1

            paragraphs.append(
                ParagraphSpan(
                    paragraph_id=p_id,
                    page_number=p_page,
                    section_title=sec_title,
                    start_char=p_start,
                    end_char=p_end,
                    text=p_text,
                )
            )

            split_sents = self._split_sentences_with_offsets(p_text, p_start)
            for s_start, s_end, s_text in split_sents:
                s_page = self._find_page_number(s_start, pages)
                s_id = f"sent_{s_page}_{sent_counter:04d}"
                sent_counter += 1

                sentences.append(
                    SentenceSpan(
                        sentence_id=s_id,
                        page_number=s_page,
                        section_title=sec_title,
                        paragraph_id=p_id,
                        start_char=s_start,
                        end_char=s_end,
                        text=s_text,
                    )
                )

        doc.sections = sections
        doc.paragraphs = paragraphs
        doc.sentences = sentences
        return doc

    def _detect_section_heading(self, line: str) -> Optional[ScientificSectionType]:
        if len(line) < 3 or len(line) > 80:
            return None
        cleaned = re.sub(r"^(?:page\s+\d+\s*[—\-:]\s*|\d+[\.\)]\s*)", "", line.strip(), flags=re.IGNORECASE).strip().lower()
        for pattern, sec_type in SECTION_PATTERNS:
            if re.match(pattern, cleaned):
                return sec_type
        return None

    def _find_page_number(self, char_offset: int, pages: List[PageBoundary]) -> int:
        if not pages:
            return 1
        for p in pages:
            if p.start_char <= char_offset <= p.end_char:
                return p.page_number
        if char_offset < pages[0].start_char:
            return pages[0].page_number
        return pages[-1].page_number

    def _split_sentences_with_offsets(self, text: str, base_offset: int) -> List[Tuple[int, int, str]]:
        if not text.strip():
            return []

        clean_text = text
        token_map: Dict[str, str] = {}
        for idx, abbr in enumerate(PROTECTED_ABBREVIATIONS):
            pattern = re.compile(re.escape(abbr), re.IGNORECASE)
            matches = list(pattern.finditer(clean_text))
            for m in reversed(matches):
                tok = f"__ABBR_{idx}_{m.start()}__"
                token_map[tok] = m.group(0)
                clean_text = clean_text[:m.start()] + tok + clean_text[m.end():]

        num_pattern = re.compile(r"(\d+)\.(\d+)")
        matches = list(num_pattern.finditer(clean_text))
        for m in reversed(matches):
            tok = f"__NUM_{m.start()}__"
            token_map[tok] = m.group(0)
            clean_text = clean_text[:m.start()] + tok + clean_text[m.end():]

        results: List[Tuple[int, int, str]] = []
        raw_splits = list(re.finditer(r"([^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$)", clean_text))

        for m in raw_splits:
            sent_str = m.group(0)
            s_start = base_offset + m.start()
            s_end = base_offset + m.end()

            for tok, orig in token_map.items():
                sent_str = sent_str.replace(tok, orig)

            cleaned_sent = sent_str.strip()
            if len(cleaned_sent) >= 8:
                results.append((s_start, s_end, cleaned_sent))

        return results
