import re
from typing import List, Tuple
from dataclasses import dataclass
import spacy
import logging

from app.models import ChunkingStrategy

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    chunks: List[str]
    stratgey: ChunkingStrategy
    total_chunks: int
    chunk_lengths: List[int]


class ChunkingService:
    def __init__(self) -> None:
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm not found. Semantic chunking will use fallback method"
            )
            self.nlp = None

    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy,
        chunk_size: int = 800,
        overlap: int = 100,
    ) -> ChunkResult:
        """
        Chunk text based on selected strategy

        Args:
            text: Input text to chunk
            strategy: Chunking strategy to use
            chunk_size: Maximum size per chunk (characters)
            overlap: Overlap between chunks for fixed-size strategy

        Returns:
            ChunkResult with chunks and metadata
        """
        if strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._fixed_size_chunking(text, chunk_size, overlap)
        elif strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._spacy_semantic_chunking(text, chunk_size)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

        chunk_lengths = [len(chunk) for chunk in chunks]

        return ChunkResult(
            chunks=chunks,
            stratgey=strategy,
            total_chunks=len(chunks),
            chunk_lengths=chunk_lengths,
        )

    def _fixed_size_chunking(
        self, text: str, chunk_size: int, overlap: int
    ) -> List[str]:
        """Splitting text into fixed-size chunks with overlap"""
        if len(text) <= chunk_size:
            return [text.strip()]
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < len(text) else len(text)

            if start >= len(text):
                break

        logger.info(f"fixed-size chunking: {len(chunks)} chunks created")
        return chunks

    def _spacy_semantic_chunking(self, text: str, max_chunk_size: int) -> List[str]:
        if self.nlp is None:
            return self._regex_semantic_chunking(text, max_chunk_size)
        doc = self.nlp(text=text)
        sentences = [sent.text.strip() for sent in doc.sents]

        chunks = []

        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"spacy semantic chunking: {len(chunks)} chunks created")
        return chunks

    def _regex_semantic_chunking(self, text: str, max_chunk_size: int) -> List[str]:
        """Fallback regex-based semantic chunking"""

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(paragraph) <= max_chunk_size:
                if (
                    len(current_chunk) + len(paragraph) <= max_chunk_size
                    and current_chunk
                ):
                    current_chunk += "\n\n" + paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
            else:
                # paragraph too large, split by sentences
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                sentences = self._split_by_sentences(paragraph)
                for sentence in sentences:
                    if (
                        len(current_chunk) + len(sentence) > max_chunk_size
                        and current_chunk
                    ):
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Regex sematic chunking: {len(chunks)} chunks created")

        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        sentence_pattern: str = r"(?<=[.!?])\s+(?=[A-Z])"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
