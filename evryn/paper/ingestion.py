# evryn paper inspect <pdf_path>
# pytest tests/test_paper_pipeline.py

import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import pypdf

from .types import ScientificDocument, PageBoundary, PaperMetadata, ScientificSectionType
from .reliability import (
    DocumentValidator,
    ReliabilityConfig,
    CheckpointManager,
    StructuredExecutionLogger,
    PDFValidationError,
    PDFIngestionError,
)


class PaperIngestion:

    def __init__(
        self,
        remove_hyphenation: bool = True,
        clean_headers_footers: bool = True,
        config: Optional[ReliabilityConfig] = None,
        logger: Optional[StructuredExecutionLogger] = None,
    ):
        self.remove_hyphenation = remove_hyphenation
        self.clean_headers_footers = clean_headers_footers
        self.config = config or ReliabilityConfig()
        self.validator = DocumentValidator(self.config)
        self.logger = logger
        self.checkpoint_mgr = CheckpointManager(self.config.checkpoint_dir) if self.config.checkpoint_dir else None

    def ingest_pdf(self, file_path: str) -> ScientificDocument:
        doc_id = f"doc_{hashlib.sha256(os.path.basename(file_path).encode('utf-8')).hexdigest()[:12]}"
        
        if self.checkpoint_mgr:
            cached = self.checkpoint_mgr.load_checkpoint(doc_id, "ingestion")
            if cached:
                if self.logger:
                    self.logger.log_event(doc_id, "ingestion", "SUCCESS", message="Restored from checkpoint")
                return ScientificDocument.from_dict(cached)

        if self.config.strict_validation:
            self.validator.validate_pdf(file_path, doc_id=doc_id)

        try:
            reader = pypdf.PdfReader(file_path)
        except Exception as e:
            raise PDFIngestionError(f"Failed to read PDF {file_path}: {e}")

        raw_meta = reader.metadata or {}
        meta_title = str(raw_meta.get("/Title") or "").strip()
        meta_author = str(raw_meta.get("/Author") or "").strip()

        pages_boundaries: List[PageBoundary] = []
        full_text_parts: List[str] = []
        current_char_offset = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            cleaned_page = self._clean_page_text(page_text, page_num)
            
            start_char = current_char_offset
            full_text_parts.append(cleaned_page)
            end_char = start_char + len(cleaned_page)
            char_count = len(cleaned_page)

            pages_boundaries.append(
                PageBoundary(
                    page_number=page_num,
                    start_char=start_char,
                    end_char=end_char,
                    char_count=char_count,
                )
            )
            current_char_offset = end_char + 1

        full_text = "\n".join(full_text_parts)

        doi, pmid, pmcid = self._extract_identifiers(full_text)
        title = meta_title or self._heuristic_title(full_text)
        authors = [meta_author] if meta_author else self._heuristic_authors(full_text)

        paper_metadata = PaperMetadata(
            title=title,
            authors=authors,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            page_count=len(reader.pages),
        )

        doc = ScientificDocument(
            doc_id=doc_id,
            file_path=os.path.abspath(file_path),
            metadata=paper_metadata,
            full_text=full_text,
            pages=pages_boundaries,
            sections=[],
            paragraphs=[],
            sentences=[],
        )

        if self.checkpoint_mgr:
            self.checkpoint_mgr.save_checkpoint(doc_id, "ingestion", doc.to_dict())

        if self.logger:
            self.logger.log_event(doc_id, "ingestion", "SUCCESS", message=f"Ingested {len(reader.pages)} pages")

        return doc

    def _clean_page_text(self, text: str, page_num: int) -> str:
        lines = text.split("\n")
        filtered_lines: List[str] = []
        
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                filtered_lines.append("")
                continue

            if self.clean_headers_footers:
                if (idx < 3 or idx > len(lines) - 4) and (
                    stripped == str(page_num)
                    or re.match(r"^Page\s+\d+(\s+of\s+\d+)?$", stripped, re.IGNORECASE)
                    or re.match(r"^(\d+\s*\|\s*)?[A-Z\s]{4,}\b", stripped)
                ):
                    continue

            filtered_lines.append(line)

        cleaned = "\n".join(filtered_lines)

        if self.remove_hyphenation:
            cleaned = re.sub(r"(\b[a-zA-Z]{2,})-\n([a-zA-Z]{2,}\b)", r"\1\2", cleaned)

        return cleaned

    def _extract_identifiers(self, text: str) -> Tuple[str, str, str]:
        doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", text)
        doi = doi_match.group(0).rstrip(".") if doi_match else ""

        pmid_match = re.search(r"\bPMID[:\s]+(\d{6,9})\b", text, re.IGNORECASE)
        pmid = pmid_match.group(1) if pmid_match else ""

        pmcid_match = re.search(r"\b(PMC\d{6,8})\b", text, re.IGNORECASE)
        pmcid = pmcid_match.group(1).upper() if pmcid_match else ""

        return doi, pmid, pmcid

    def _heuristic_title(self, text: str) -> str:
        for line in text.split("\n")[:15]:
            stripped = line.strip()
            if len(stripped) > 15 and not stripped.startswith("http") and not stripped.startswith("doi:"):
                return stripped
        return "Untitled Scientific Paper"

    def _heuristic_authors(self, text: str) -> List[str]:
        lines = text.split("\n")[:25]
        for line in lines[1:]:
            stripped = line.strip()
            if re.search(r"\b(and|et al\.|Department|University|Laboratory|Institute)\b", stripped):
                tokens = re.split(r",|\sand\s", stripped)
                authors = [t.strip() for t in tokens if 2 < len(t.strip()) < 40 and not any(k in t.lower() for k in ["university", "department", "institute", "laboratory", "school"])]
                if authors:
                    return authors
        return []
