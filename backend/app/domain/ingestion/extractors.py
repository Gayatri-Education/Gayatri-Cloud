"""Multi-format curriculum document extractors."""

from __future__ import annotations

import io
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import pypdf

from app.domain.ingestion.sanitizer import sanitize_document_text


@dataclass
class ExtractedSection:
    """A distinct structural section or page extracted from a document."""

    text: str
    page_number: int | None = None
    section_header: str | None = None
    confidence: float = 1.0  # 0.0 to 1.0


class BaseExtractor(ABC):
    """Abstract interface for format-specific extractors."""

    @abstractmethod
    def extract(self, content: bytes) -> list[ExtractedSection]:
        """Parse raw document bytes into a sequence of structural sections."""
        pass


class TextAndMarkdownExtractor(BaseExtractor):
    """Extracts plain text and markdown documents preserving heading structure."""

    HEADER_REGEX: ClassVar[re.Pattern] = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def extract(self, content: bytes) -> list[ExtractedSection]:
        decoded = content.decode("utf-8", errors="replace")
        sanitized = sanitize_document_text(decoded)

        # Break text by top-level headers (# or ##) if markdown, otherwise paragraphs
        lines = sanitized.splitlines()
        sections: list[ExtractedSection] = []
        current_header: str | None = None
        current_lines: list[str] = []

        for line in lines:
            header_match = self.HEADER_REGEX.match(line)
            if header_match:
                if current_lines:
                    text_block = "\n".join(current_lines).strip()
                    if text_block:
                        sections.append(
                            ExtractedSection(
                                text=text_block,
                                section_header=current_header,
                                confidence=1.0,
                            )
                        )
                    current_lines = []
                current_header = header_match.group(2).strip()
            current_lines.append(line)

        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                sections.append(
                    ExtractedSection(
                        text=text_block,
                        section_header=current_header,
                        confidence=1.0,
                    )
                )

        if not sections and sanitized.strip():
            sections.append(ExtractedSection(text=sanitized.strip(), confidence=1.0))

        return sections


class PDFExtractor(BaseExtractor):
    """Extracts digital PDF files page-by-page using pypdf."""

    def extract(self, content: bytes) -> list[ExtractedSection]:
        sections: list[ExtractedSection] = []
        stream = io.BytesIO(content)

        try:
            reader = pypdf.PdfReader(stream)
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                sanitized_text = sanitize_document_text(page_text)
                if sanitized_text:
                    sections.append(
                        ExtractedSection(
                            text=sanitized_text,
                            page_number=page_idx + 1,
                            confidence=1.0,
                        )
                    )
        except Exception as err:
            raise ValueError(f"Failed to parse PDF document: {err}") from err

        if not sections:
            # Document may be scanned or empty
            sections.append(
                ExtractedSection(
                    text="[Scanned or empty PDF content - text extraction unavailable]",
                    page_number=1,
                    confidence=0.1,
                )
            )

        return sections


class VTTTranscriptExtractor(BaseExtractor):
    """Extracts video/audio lecture transcripts in WebVTT or SRT format."""

    TIMESTAMP_REGEX: ClassVar[re.Pattern] = re.compile(
        r"(\d{2}:)?\d{2}:\d{2}\.\d{3}\s+-->\s+(\d{2}:)?\d{2}:\d{2}\.\d{3}"
    )

    def extract(self, content: bytes) -> list[ExtractedSection]:
        text = content.decode("utf-8", errors="replace")
        lines = text.splitlines()
        clean_lines: list[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("WEBVTT") or line_str.isdigit():
                continue
            if self.TIMESTAMP_REGEX.search(line_str):
                continue
            clean_lines.append(line_str)

        full_transcript = sanitize_document_text("\n".join(clean_lines))
        return [
            ExtractedSection(
                text=full_transcript,
                section_header="Lecture Transcript",
                confidence=1.0,
            )
        ]


class PluggableOCRExtractor(BaseExtractor):
    """OCR fallback extractor for scanned PDFs and image materials with confidence thresholding."""

    def __init__(self, confidence_threshold: float = 0.60) -> None:
        self.confidence_threshold = confidence_threshold

    def extract(self, content: bytes) -> list[ExtractedSection]:
        # Local deterministic mock OCR for development and tests
        # Real Tesseract or Textract integration plugged here
        text = content.decode("utf-8", errors="ignore")
        sanitized = sanitize_document_text(text)
        confidence = 0.85 if len(sanitized) > 20 else 0.40

        return [
            ExtractedSection(
                text=sanitized,
                section_header="OCR Scanned Text",
                confidence=confidence,
            )
        ]


def get_extractor_for_mime(mime_type: str) -> BaseExtractor:
    """Factory resolving appropriate extractor for a declared MIME type."""
    if mime_type == "application/pdf":
        return PDFExtractor()
    if mime_type in {"text/plain", "text/markdown"}:
        return TextAndMarkdownExtractor()
    if mime_type == "text/vtt":
        return VTTTranscriptExtractor()
    if mime_type.startswith("image/"):
        return PluggableOCRExtractor()

    # Default fallback
    return TextAndMarkdownExtractor()
