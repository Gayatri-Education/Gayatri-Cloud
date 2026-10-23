"""Course-Scoped Hybrid Retrieval and Citation Engine."""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.course import ContentChunk, ContentSource

# --- Embedding Adapters ---


class EmbeddingService(ABC):
    """Abstract interface for dense semantic embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Convert single text into a normalized embedding vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch vectorize multiple texts."""
        pass


class MockEmbeddingAdapter(EmbeddingService):
    """Deterministic, zero-network embedding adapter for local development and offline testing."""

    VECTOR_DIM: ClassVar[int] = 64

    def embed_text(self, text: str) -> list[float]:
        cleaned = text.lower().strip()
        vec = [0.0] * self.VECTOR_DIM

        # Seed pseudo-random dimensions deterministically based on words and character n-grams
        words = re.findall(r"\w+", cleaned)
        if not words:
            return vec

        for word in words:
            # Hash word to dimension index
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            dim_idx = h % self.VECTOR_DIM
            vec[dim_idx] += 1.0

        # L2 Normalize vector
        magnitude = math.sqrt(sum(v * v for v in vec))
        if magnitude > 0:
            vec = [v / magnitude for v in vec]
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two normalized vectors."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    # Bound between 0.0 and 1.0 for non-negative embeddings
    return max(0.0, min(1.0, dot))


# --- Lexical BM25 Scoring ---


class LexicalMatcher:
    """Lightweight in-memory BM25 scorer for document chunks."""

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    @classmethod
    def score_chunks(cls, query: str, chunks: list[ContentChunk]) -> list[float]:
        query_terms = set(cls.tokenize(query))
        if not query_terms or not chunks:
            return [0.0] * len(chunks)

        n_docs = len(chunks)
        # Calculate term frequencies and document frequencies
        doc_tokens = [cls.tokenize(c.text_content) for c in chunks]
        doc_lengths = [len(dt) for dt in doc_tokens]
        avg_doc_len = sum(doc_lengths) / max(1, n_docs)

        # Document frequencies
        df: dict[str, int] = {}
        for q in query_terms:
            df[q] = sum(1 for dt in doc_tokens if q in dt)

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        scores: list[float] = []
        for dt, d_len in zip(doc_tokens, doc_lengths, strict=False):
            score = 0.0
            term_counts: dict[str, int] = {}
            for t in dt:
                term_counts[t] = term_counts.get(t, 0) + 1

            for q in query_terms:
                if q in term_counts:
                    tf = term_counts[q]
                    idf = math.log((n_docs - df[q] + 0.5) / (df[q] + 0.5) + 1.0)
                    denom = tf + k1 * (1.0 - b + b * (d_len / max(1.0, avg_doc_len)))
                    score += idf * ((tf * (k1 + 1.0)) / max(0.001, denom))
            scores.append(max(0.0, score))

        # Normalize lexical scores to [0.0, 1.0]
        max_score = max(scores) if scores else 0.0
        if max_score > 0:
            return [s / max_score for s in scores]
        return scores


# --- Retrieval Models & Engine ---


@dataclass
class RetrievedChunk:
    chunk_id: str
    source_id: str
    source_filename: str
    text_content: str
    page_number: int | None
    section_header: str | None
    relevance_score: float
    citation: str


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    alpha: float = 0.6  # 0.0 (pure lexical) to 1.0 (pure semantic)


class RAGQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str
    course_version_id: str
    retrieved_count: int
    results: list[dict]


class CourseRAGEngine:
    """Executes course-scoped hybrid search with strict multi-tenant boundary checks."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or MockEmbeddingAdapter()

    async def search(
        self,
        session: AsyncSession,
        organization_id: str | None,
        course_id: str,
        course_version_id: str,
        query: str,
        top_k: int = 5,
        alpha: float = 0.6,
    ) -> list[RetrievedChunk]:
        """Perform course-scoped hybrid retrieval ensuring cross-tenant isolation."""
        # 1. Mandatory hard query filter: restrict chunks strictly to target course_version_id
        # and match organization_id (or global)
        stmt = (
            select(ContentChunk, ContentSource)
            .join(ContentSource, ContentChunk.source_id == ContentSource.id)
            .where(
                ContentSource.course_version_id == course_version_id,
                (ContentSource.organization_id == organization_id)
                | (ContentSource.organization_id.is_(None)),
            )
        )
        res = await session.execute(stmt)
        rows = res.fetchall()

        if not rows:
            return []

        chunks = [row[0] for row in rows]
        sources = {row[1].id: row[1] for row in rows}

        # 2. Compute Lexical BM25 Scores
        lexical_scores = LexicalMatcher.score_chunks(query, chunks)

        # 3. Compute Semantic Dense Embedding Scores
        query_vec = self.embedding_service.embed_text(query)
        chunk_texts = [c.text_content for c in chunks]
        chunk_vecs = self.embedding_service.embed_batch(chunk_texts)
        semantic_scores = [cosine_similarity(query_vec, cv) for cv in chunk_vecs]

        # 4. Combine Hybrid Scores
        scored_results: list[RetrievedChunk] = []
        for i, chunk in enumerate(chunks):
            source = sources[chunk.source_id]
            h_score = (alpha * semantic_scores[i]) + ((1.0 - alpha) * lexical_scores[i])

            # Generate formal citation
            citation_parts = [source.filename]
            if chunk.page_number:
                citation_parts.append(f"p. {chunk.page_number}")
            if chunk.section_header:
                citation_parts.append(f'"{chunk.section_header}"')
            citation = f"[{', '.join(citation_parts)}]"

            scored_results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    source_id=source.id,
                    source_filename=source.filename,
                    text_content=chunk.text_content,
                    page_number=chunk.page_number,
                    section_header=chunk.section_header,
                    relevance_score=round(h_score, 4),
                    citation=citation,
                )
            )

        # 5. Sort by relevance descending and take top_k
        scored_results.sort(key=lambda r: r.relevance_score, reverse=True)
        return scored_results[:top_k]
