"""Curriculum text chunking engine."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.ingestion.extractors import ExtractedSection


@dataclass
class ChunkPayload:
    """A single indexable chunk ready for embedding and lexical indexing."""

    chunk_index: int
    text_content: str
    page_number: int | None
    section_header: str | None
    token_count: int


class ContentChunker:
    """Splits structural sections into sliding-window chunks with metadata."""

    def __init__(
        self,
        target_chunk_chars: int = 1500,  # ~375 tokens
        overlap_chars: int = 200,  # ~50 tokens
    ) -> None:
        self.target_chunk_chars = target_chunk_chars
        self.overlap_chars = overlap_chars

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """Estimate token count: 1 token ~ 4 characters in English / code."""
        return max(1, len(text) // 4)

    def chunk_sections(self, sections: list[ExtractedSection]) -> list[ChunkPayload]:
        """Process sections into an ordered sequence of indexed chunks."""
        chunks: list[ChunkPayload] = []
        global_chunk_idx = 0

        for section in sections:
            text = section.text.strip()
            if not text:
                continue

            # If section text fits in a single chunk, preserve whole
            if len(text) <= self.target_chunk_chars:
                chunks.append(
                    ChunkPayload(
                        chunk_index=global_chunk_idx,
                        text_content=text,
                        page_number=section.page_number,
                        section_header=section.section_header,
                        token_count=self.estimate_token_count(text),
                    )
                )
                global_chunk_idx += 1
                continue

            # Split by paragraphs or sentences
            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + self.target_chunk_chars, text_len)

                # Try to break at paragraph or sentence boundary
                if end < text_len:
                    break_point = self._find_natural_break(text, start, end)
                    if break_point > start:
                        end = break_point

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(
                        ChunkPayload(
                            chunk_index=global_chunk_idx,
                            text_content=chunk_text,
                            page_number=section.page_number,
                            section_header=section.section_header,
                            token_count=self.estimate_token_count(chunk_text),
                        )
                    )
                    global_chunk_idx += 1

                if end >= text_len:
                    break

                # Advance window with overlap
                start = max(start + 1, end - self.overlap_chars)

        return chunks

    @staticmethod
    def _find_natural_break(text: str, start: int, target_end: int) -> int:
        """Find the nearest paragraph, period, or newline before target_end."""
        # Check for paragraph break \n\n
        p_idx = text.rfind("\n\n", start, target_end)
        if p_idx != -1 and p_idx > start + 300:
            return p_idx + 2

        # Check for sentence end (. or ? or !)
        match = None
        for m in re.finditer(r"[.?!]\s+", text[start:target_end]):
            match = m
        if match:
            return start + match.end()

        # Fallback to single newline or space
        space_idx = text.rfind(" ", start, target_end)
        if space_idx != -1 and space_idx > start + 100:
            return space_idx + 1

        return target_end
