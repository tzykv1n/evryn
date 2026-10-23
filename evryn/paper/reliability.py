# evryn paper reliability
# pytest tests/test_paper_reliability.py

import os
import sys
import time
import json
import logging
import tempfile
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Callable
import pypdf

from .types import ScientificDocument


class PDFValidationStatus(str, Enum):
    VALID = "VALID"
    NOT_FOUND = "NOT_FOUND"
    EMPTY_FILE = "EMPTY_FILE"
    NOT_A_PDF = "NOT_A_PDF"
    ENCRYPTED = "ENCRYPTED"
    CORRUPT = "CORRUPT"
    IMAGE_ONLY = "IMAGE_ONLY"
    PAGE_LIMIT_EXCEEDED = "PAGE_LIMIT_EXCEEDED"
    SIZE_LIMIT_EXCEEDED = "SIZE_LIMIT_EXCEEDED"


class PipelineFailureCategory(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    TRANSIENT_SERVICE_ERROR = "TRANSIENT_SERVICE_ERROR"


class PaperReliabilityError(Exception):
    def __init__(self, message: str, category: PipelineFailureCategory, doc_id: str = ""):
        super().__init__(message)
        self.message = message
        self.category = category
        self.doc_id = doc_id


class PDFIngestionError(PaperReliabilityError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PipelineFailureCategory.PARSING_ERROR, doc_id)


class PDFValidationError(PaperReliabilityError):
    def __init__(self, message: str, status: PDFValidationStatus, doc_id: str = ""):
        super().__init__(message, PipelineFailureCategory.VALIDATION_ERROR, doc_id)
        self.status = status


class EncryptedPDFError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.ENCRYPTED, doc_id)


class CorruptPDFError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.CORRUPT, doc_id)


class EmptyPDFError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.EMPTY_FILE, doc_id)


class ImageOnlyPDFError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.IMAGE_ONLY, doc_id)


class PageLimitExceededError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.PAGE_LIMIT_EXCEEDED, doc_id)


class FileSizeLimitExceededError(PDFValidationError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PDFValidationStatus.SIZE_LIMIT_EXCEEDED, doc_id)


class PipelineTimeoutError(PaperReliabilityError):
    def __init__(self, message: str, doc_id: str = ""):
        super().__init__(message, PipelineFailureCategory.TIMEOUT_ERROR, doc_id)


@dataclass
class ReliabilityConfig:
    max_file_size_mb: float = 50.0
    max_pages: int = 150
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    checkpoint_dir: Optional[str] = None
    atomic_writes: bool = True
    strict_validation: bool = True
    clean_temp_files: bool = True


@dataclass
class StructuredLogRecord:
    timestamp: float
    doc_id: str
    page_number: Optional[int]
    stage: str
    duration_ms: float
    retry_count: int
    failure_category: Optional[str]
    message: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StructuredExecutionLogger:
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.records: List[StructuredLogRecord] = []
        self._sanitized_keys = {"token", "key", "secret", "password", "auth", "bearer"}

    def log_event(
        self,
        doc_id: str,
        stage: str,
        status: str,
        page_number: Optional[int] = None,
        duration_ms: float = 0.0,
        retry_count: int = 0,
        failure_category: Optional[PipelineFailureCategory] = None,
        message: str = "",
    ) -> StructuredLogRecord:
        clean_msg = self._sanitize(message)
        rec = StructuredLogRecord(
            timestamp=time.time(),
            doc_id=doc_id,
            page_number=page_number,
            stage=stage,
            duration_ms=round(duration_ms, 2),
            retry_count=retry_count,
            failure_category=failure_category.value if failure_category else None,
            message=clean_msg,
            status=status,
        )
        self.records.append(rec)
        if self.log_file:
            self._write_log(rec)
        return rec

    def _sanitize(self, msg: str) -> str:
        for secret_token in ["sk-", "ghp_", "Bearer ", "AIza"]:
            if secret_token in msg:
                msg = msg.replace(secret_token, "[REDACTED]")
        return msg

    def _write_log(self, record: StructuredLogRecord) -> None:
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except Exception:
            pass

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.records)
        successes = sum(1 for r in self.records if r.status == "SUCCESS")
        failures = sum(1 for r in self.records if r.status == "FAILED")
        by_cat: Dict[str, int] = {}
        for r in self.records:
            if r.failure_category:
                by_cat[r.failure_category] = by_cat.get(r.failure_category, 0) + 1
        return {
            "total_events": total,
            "success_count": successes,
            "failure_count": failures,
            "failures_by_category": by_cat,
        }


class DocumentValidator:
    def __init__(self, config: Optional[ReliabilityConfig] = None):
        self.config = config or ReliabilityConfig()

    def validate_pdf(self, file_path: str, doc_id: str = "") -> PDFValidationStatus:
        if not os.path.exists(file_path):
            raise PDFValidationError(f"File does not exist: {file_path}", PDFValidationStatus.NOT_FOUND, doc_id)

        if not os.path.isfile(file_path):
            raise PDFValidationError(f"Path is not a file: {file_path}", PDFValidationStatus.NOT_FOUND, doc_id)

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise EmptyPDFError(f"PDF file is completely empty (0 bytes): {file_path}", doc_id)

        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise FileSizeLimitExceededError(
                f"File size ({file_size / (1024*1024):.1f}MB) exceeds limit of {self.config.max_file_size_mb}MB",
                doc_id,
            )

        with open(file_path, "rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                raise CorruptPDFError(f"File lacks valid %PDF header: {file_path}", doc_id)

        try:
            reader = pypdf.PdfReader(file_path)
        except Exception as e:
            raise CorruptPDFError(f"Malformed or corrupt PDF: {e}", doc_id)

        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    raise EncryptedPDFError(f"PDF is encrypted with an unknown password: {file_path}", doc_id)
            except Exception:
                raise EncryptedPDFError(f"PDF is encrypted and password-protected: {file_path}", doc_id)

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise EmptyPDFError(f"PDF contains 0 pages: {file_path}", doc_id)

        if num_pages > self.config.max_pages:
            raise PageLimitExceededError(
                f"PDF has {num_pages} pages, which exceeds maximum allowable limit of {self.config.max_pages}",
                doc_id,
            )

        text_found = False
        sample_pages = min(num_pages, 5)
        for i in range(sample_pages):
            try:
                t = reader.pages[i].extract_text()
                if t and len(t.strip()) > 20:
                    text_found = True
                    break
            except Exception:
                continue

        if not text_found and num_pages <= 3:
            total_text_chars = 0
            for page in reader.pages:
                try:
                    txt = page.extract_text() or ""
                    total_text_chars += len(txt.strip())
                except Exception:
                    pass
            if total_text_chars < 30:
                raise ImageOnlyPDFError(
                    f"PDF appears to be an image-only scan with no extractable text layer: {file_path}",
                    doc_id,
                )

        return PDFValidationStatus.VALID


class CheckpointManager:
    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = checkpoint_dir or os.path.join(tempfile.gettempdir(), "evryn_checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _get_checkpoint_path(self, doc_id: str, stage: str) -> str:
        safe_id = "".join(c for c in doc_id if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.checkpoint_dir, f"{safe_id}_{stage}.checkpoint.json")

    def save_checkpoint(self, doc_id: str, stage: str, data: Dict[str, Any]) -> None:
        path = self._get_checkpoint_path(doc_id, stage)
        tmp_path = path + f".tmp_{os.getpid()}_{time.time()}"
        payload = {
            "doc_id": doc_id,
            "stage": stage,
            "saved_at": time.time(),
            "data": data,
        }
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, path)

    def load_checkpoint(self, doc_id: str, stage: str) -> Optional[Dict[str, Any]]:
        path = self._get_checkpoint_path(doc_id, stage)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("data")
        except Exception:
            return None

    def clear_checkpoint(self, doc_id: str, stage: Optional[str] = None) -> None:
        if stage:
            path = self._get_checkpoint_path(doc_id, stage)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        else:
            safe_id = "".join(c for c in doc_id if c.isalnum() or c in ("-", "_"))
            for fname in os.listdir(self.checkpoint_dir):
                if fname.startswith(safe_id) and fname.endswith(".checkpoint.json"):
                    try:
                        os.remove(os.path.join(self.checkpoint_dir, fname))
                    except OSError:
                        pass


def atomic_write_json(file_path: str, data: Any, indent: int = 2) -> None:
    directory = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(directory, exist_ok=True)
    tmp_path = file_path + f".tmp_{os.getpid()}_{time.time()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
    os.replace(tmp_path, file_path)


def execute_with_retry(
    action: Callable[[], Any],
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    transient_exceptions: Tuple[type, ...] = (TimeoutError, ConnectionError, OSError),
    logger: Optional[StructuredExecutionLogger] = None,
    doc_id: str = "",
    stage: str = "execution",
) -> Any:
    attempt = 0
    while attempt <= max_retries:
        t0 = time.time()
        try:
            result = action()
            duration_ms = (time.time() - t0) * 1000
            if logger:
                logger.log_event(
                    doc_id=doc_id,
                    stage=stage,
                    status="SUCCESS",
                    duration_ms=duration_ms,
                    retry_count=attempt,
                )
            return result
        except transient_exceptions as exc:
            duration_ms = (time.time() - t0) * 1000
            attempt += 1
            if logger:
                logger.log_event(
                    doc_id=doc_id,
                    stage=stage,
                    status="RETRYING",
                    duration_ms=duration_ms,
                    retry_count=attempt,
                    failure_category=PipelineFailureCategory.TRANSIENT_SERVICE_ERROR,
                    message=f"Transient failure (attempt {attempt}/{max_retries}): {exc}",
                )
            if attempt > max_retries:
                raise PaperReliabilityError(
                    f"Action failed after {max_retries} retries: {exc}",
                    PipelineFailureCategory.TRANSIENT_SERVICE_ERROR,
                    doc_id,
                )
            sleep_time = backoff_factor ** attempt
            time.sleep(sleep_time)
        except PaperReliabilityError:
            raise
        except Exception as permanent_exc:
            duration_ms = (time.time() - t0) * 1000
            if logger:
                logger.log_event(
                    doc_id=doc_id,
                    stage=stage,
                    status="FAILED",
                    duration_ms=duration_ms,
                    retry_count=attempt,
                    failure_category=PipelineFailureCategory.PARSING_ERROR,
                    message=f"Permanent failure: {permanent_exc}",
                )
            raise
