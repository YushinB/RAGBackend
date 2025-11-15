"""
Advanced chunking strategies for text processing.

This module implements multiple chunking strategies:
- T4.2.1: Relationship-aware chunking (preserve figure-caption, table-reference associations)
- T4.2.2: Linked chunking (generate cross-chunk references)
- T4.2.3: Semantic chunking (sentence/paragraph boundaries, hierarchical structure)

All strategies maintain context, relationships, and support multi-modal content.
"""

import re
from typing import Any

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.chunking_config import BoundaryType, ChunkingConfig, ChunkingStrategy


class BaseChunker:
    """Base class for all chunking strategies."""

    def __init__(self, config: ChunkingConfig):
        """
        Initialize the chunker with configuration.

        Args:
            config: Chunking configuration
        """
        self.config = config

    def chunk(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk the content according to the strategy.

        Args:
            content: Multi-modal content to chunk

        Returns:
            List of text chunks
        """
        raise NotImplementedError("Subclasses must implement chunk()")

    def _create_chunk(
        self,
        text: str,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
        position: ContentPosition | None = None,
        hierarchy: DocumentHierarchy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TextChunk:
        """
        Create a text chunk with strategy metadata.

        Args:
            text: Chunk text
            chunk_type: Type of chunk
            position: Position information
            hierarchy: Hierarchy information
            metadata: Additional metadata

        Returns:
            Configured TextChunk
        """
        chunk = TextChunk(
            text=text,
            chunk_type=chunk_type,
            position=position,
            hierarchy=hierarchy,
            metadata=metadata or {},
            chunking_strategy=self.config.strategy.value,
        )
        return chunk


class RelationshipAwareChunker(BaseChunker):
    """
    T4.2.1: Relationship-aware chunking strategy.

    Preserves associations between:
    - Figures and their captions
    - Tables and their references
    - Equations and their context
    - Cross-references within content
    """

    def chunk(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content while preserving multi-modal relationships.

        Args:
            content: Multi-modal content with relationships

        Returns:
            List of chunks with preserved relationships
        """
        chunks: list[TextChunk] = []

        # Process each existing text chunk
        for existing_chunk in content.text_chunks:
            # Split large chunks if needed
            if len(existing_chunk.text) > self.config.chunk_size:
                sub_chunks = self._split_with_relationships(
                    existing_chunk, content.relationships
                )
                chunks.extend(sub_chunks)
            else:
                # Keep chunk as-is but enhance with multi-modal refs
                enhanced_chunk = self._enhance_with_relationships(
                    existing_chunk, content.relationships
                )
                chunks.append(enhanced_chunk)

        return chunks

    def _split_with_relationships(
        self, chunk: TextChunk, relationships: dict[str, Any]
    ) -> list[TextChunk]:
        """
        Split a large chunk while preserving relationships.

        Args:
            chunk: Chunk to split
            relationships: Relationship map

        Returns:
            List of sub-chunks with preserved relationships
        """
        text = chunk.text
        sub_chunks: list[TextChunk] = []

        # Find relationship markers (figure references, table references, etc.)
        markers = self._find_relationship_markers(text)

        if not markers:
            # No relationships, do simple split
            return self._simple_split(chunk)

        # Split at relationship boundaries
        current_pos = 0
        for marker_start, marker_end, ref_type, ref_id in markers:
            # Get text before marker
            before_text = text[current_pos:marker_start].strip()

            if before_text and len(before_text) >= self.config.min_chunk_size:
                sub_chunk = self._create_chunk(
                    text=before_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    hierarchy=chunk.hierarchy,
                    metadata={
                        "parent_chunk_id": chunk.chunk_id,
                        "split_index": len(sub_chunks),
                    },
                )
                sub_chunks.append(sub_chunk)

            # Get text including marker and context
            context_end = min(marker_end + 200, len(text))
            context_text = text[marker_start:context_end].strip()

            if context_text:
                sub_chunk = self._create_chunk(
                    text=context_text,
                    chunk_type=ChunkType.MIXED,
                    position=chunk.position,
                    hierarchy=chunk.hierarchy,
                    metadata={
                        "parent_chunk_id": chunk.chunk_id,
                        "split_index": len(sub_chunks),
                        "has_reference": True,
                        "reference_type": ref_type,
                    },
                )
                sub_chunk.add_multi_modal_ref(ref_type, ref_id)
                sub_chunk.add_relationship(ref_id)
                sub_chunks.append(sub_chunk)

            current_pos = context_end

        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:].strip()
            if remaining_text and len(remaining_text) >= self.config.min_chunk_size:
                sub_chunk = self._create_chunk(
                    text=remaining_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    hierarchy=chunk.hierarchy,
                    metadata={
                        "parent_chunk_id": chunk.chunk_id,
                        "split_index": len(sub_chunks),
                    },
                )
                sub_chunks.append(sub_chunk)

        return sub_chunks if sub_chunks else [chunk]

    def _find_relationship_markers(self, text: str) -> list[tuple[int, int, str, str]]:
        """
        Find relationship markers in text (figure refs, table refs, etc.).

        Args:
            text: Text to search

        Returns:
            List of (start_pos, end_pos, ref_type, ref_id) tuples
        """
        markers: list[tuple[int, int, str, str]] = []

        # Pattern for common reference formats
        patterns = [
            (r"Figure\s+(\d+)", "image"),
            (r"Fig\.\s*(\d+)", "image"),
            (r"Table\s+(\d+)", "table"),
            (r"Equation\s+(\d+)", "equation"),
            (r"Eq\.\s*(\d+)", "equation"),
        ]

        for pattern, ref_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ref_id = f"{ref_type}-{match.group(1)}"
                markers.append((match.start(), match.end(), ref_type, ref_id))

        # Sort by position
        markers.sort(key=lambda x: x[0])
        return markers

    def _enhance_with_relationships(
        self, chunk: TextChunk, relationships: dict[str, Any]
    ) -> TextChunk:
        """
        Enhance chunk with relationship information.

        Args:
            chunk: Chunk to enhance
            relationships: Relationship map

        Returns:
            Enhanced chunk
        """
        # Find and add multi-modal references
        markers = self._find_relationship_markers(chunk.text)
        for _, _, ref_type, ref_id in markers:
            chunk.add_multi_modal_ref(ref_type, ref_id)
            chunk.add_relationship(ref_id)

        # Add metadata about relationships
        if markers:
            chunk.metadata["has_references"] = True
            chunk.metadata["reference_count"] = len(markers)
            chunk.metadata["reference_types"] = list(
                {ref_type for _, _, ref_type, _ in markers}
            )

        return chunk

    def _simple_split(self, chunk: TextChunk) -> list[TextChunk]:
        """
        Simple split without relationship preservation.

        Args:
            chunk: Chunk to split

        Returns:
            List of sub-chunks
        """
        text = chunk.text
        chunks: list[TextChunk] = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                sub_chunk = self._create_chunk(
                    text=chunk_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    hierarchy=chunk.hierarchy,
                    metadata={
                        "parent_chunk_id": chunk.chunk_id,
                        "split_index": len(chunks),
                    },
                )
                chunks.append(sub_chunk)

            start = end - overlap

        return chunks if chunks else [chunk]


class LinkedChunker(BaseChunker):
    """
    T4.2.2: Linked chunking strategy.

    Creates chunks with explicit links to:
    - Previous and next chunks in sequence
    - Parent and child chunks in hierarchy
    - Related chunks across document sections
    """

    def chunk(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content with explicit linking between chunks.

        Args:
            content: Multi-modal content to chunk

        Returns:
            List of linked chunks
        """
        chunks: list[TextChunk] = []

        # First pass: Create chunks from content
        for existing_chunk in content.text_chunks:
            if len(existing_chunk.text) > self.config.chunk_size:
                sub_chunks = self._split_into_linked_chunks(existing_chunk)
                chunks.extend(sub_chunks)
            else:
                chunks.append(existing_chunk)

        # Second pass: Link chunks together
        self._link_sequential_chunks(chunks)
        self._link_hierarchical_chunks(chunks)

        return chunks

    def _split_into_linked_chunks(self, chunk: TextChunk) -> list[TextChunk]:
        """
        Split chunk into smaller linked chunks.

        Args:
            chunk: Chunk to split

        Returns:
            List of linked sub-chunks
        """
        text = chunk.text
        chunks: list[TextChunk] = []

        # Use sliding window for better context preservation
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Respect sentence boundaries if configured
            if self.config.respect_sentence_boundaries:
                end = self._find_sentence_boundary(text, end)

            chunk_text = text[start:end].strip()

            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                sub_chunk = self._create_chunk(
                    text=chunk_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    hierarchy=chunk.hierarchy,
                    metadata={
                        "parent_chunk_id": chunk.chunk_id,
                        "chunk_index": chunk_index,
                        "sliding_window": True,
                        "overlap_size": overlap,
                    },
                )
                sub_chunk.set_parent_chunk(chunk.chunk_id)
                chunks.append(sub_chunk)
                chunk_index += 1

            start = end - overlap

        return chunks

    def _find_sentence_boundary(self, text: str, target_pos: int) -> int:
        """
        Find nearest sentence boundary near target position.

        Args:
            text: Text to search
            target_pos: Target position

        Returns:
            Position of sentence boundary
        """
        if target_pos >= len(text):
            return len(text)

        # Look for sentence endings near target
        search_start = max(0, target_pos - 100)
        search_end = min(len(text), target_pos + 100)
        search_text = text[search_start:search_end]

        # Find sentence endings
        sentence_endings = [
            m.end() + search_start for m in re.finditer(r"[.!?]\s+", search_text)
        ]

        if not sentence_endings:
            return target_pos

        # Find closest to target
        closest = min(sentence_endings, key=lambda x: abs(x - target_pos))
        return closest

    def _link_sequential_chunks(self, chunks: list[TextChunk]) -> None:
        """
        Link chunks in sequential order (prev/next).

        Args:
            chunks: List of chunks to link
        """
        for i in range(len(chunks)):
            if i > 0:
                chunks[i].link_to_prev(chunks[i - 1].chunk_id)
            if i < len(chunks) - 1:
                chunks[i].link_to_next(chunks[i + 1].chunk_id)

    def _link_hierarchical_chunks(self, chunks: list[TextChunk]) -> None:
        """
        Link chunks hierarchically (parent/child).

        Args:
            chunks: List of chunks to link
        """
        # Group chunks by parent
        parent_map: dict[str, list[TextChunk]] = {}

        for chunk in chunks:
            parent_id = chunk.metadata.get("parent_chunk_id")
            if parent_id:
                if parent_id not in parent_map:
                    parent_map[parent_id] = []
                parent_map[parent_id].append(chunk)

        # Link parent-child relationships
        for parent_id, children in parent_map.items():
            # Find parent chunk
            parent = next((c for c in chunks if c.chunk_id == parent_id), None)
            if parent:
                for child in children:
                    parent.add_child_chunk(child.chunk_id)


class SemanticChunker(BaseChunker):
    """
    T4.2.3: Semantic chunking strategy.

    Creates chunks based on:
    - Sentence boundaries and semantic coherence
    - Paragraph structure and topic changes
    - Hierarchical document structure (sections, subsections)
    - Content type (code, prose, lists)
    """

    def chunk(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content based on semantic structure.

        Args:
            content: Multi-modal content to chunk

        Returns:
            List of semantically coherent chunks
        """
        chunks: list[TextChunk] = []

        # Process based on boundary type
        if self.config.boundary_type == BoundaryType.SENTENCE:
            chunks = self._chunk_by_sentences(content)
        elif self.config.boundary_type == BoundaryType.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(content)
        elif self.config.boundary_type == BoundaryType.SECTION:
            chunks = self._chunk_by_sections(content)
        else:
            # Default to paragraph-based
            chunks = self._chunk_by_paragraphs(content)

        return chunks

    def _chunk_by_sentences(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content by sentence boundaries.

        Args:
            content: Content to chunk

        Returns:
            List of sentence-based chunks
        """
        chunks: list[TextChunk] = []

        for text_chunk in content.text_chunks:
            sentences = self._split_into_sentences(text_chunk.text)

            current_chunk_sentences: list[str] = []
            current_length = 0

            for sentence in sentences:
                sentence_length = len(sentence)

                # Check if adding sentence exceeds chunk size
                if (
                    current_length + sentence_length > self.config.chunk_size
                    and current_chunk_sentences
                ):
                    # Create chunk from accumulated sentences
                    chunk_text = " ".join(current_chunk_sentences)
                    chunk = self._create_chunk(
                        text=chunk_text,
                        chunk_type=text_chunk.chunk_type,
                        position=text_chunk.position,
                        hierarchy=text_chunk.hierarchy,
                        metadata={
                            "sentence_count": len(current_chunk_sentences),
                            "boundary_type": "sentence",
                        },
                    )
                    chunks.append(chunk)

                    # Reset with overlap (keep last sentence)
                    if self.config.chunk_overlap > 0 and current_chunk_sentences:
                        current_chunk_sentences = [current_chunk_sentences[-1]]
                        current_length = len(current_chunk_sentences[0])
                    else:
                        current_chunk_sentences = []
                        current_length = 0

                current_chunk_sentences.append(sentence)
                current_length += sentence_length

            # Add remaining sentences
            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                if len(chunk_text) >= self.config.min_chunk_size:
                    chunk = self._create_chunk(
                        text=chunk_text,
                        chunk_type=text_chunk.chunk_type,
                        position=text_chunk.position,
                        hierarchy=text_chunk.hierarchy,
                        metadata={
                            "sentence_count": len(current_chunk_sentences),
                            "boundary_type": "sentence",
                        },
                    )
                    chunks.append(chunk)

        return chunks

    def _chunk_by_paragraphs(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content by paragraph boundaries.

        Args:
            content: Content to chunk

        Returns:
            List of paragraph-based chunks
        """
        chunks: list[TextChunk] = []

        for text_chunk in content.text_chunks:
            paragraphs = self._split_into_paragraphs(text_chunk.text)

            current_chunk_paragraphs: list[str] = []
            current_length = 0

            for paragraph in paragraphs:
                para_length = len(paragraph)

                # Check if adding paragraph exceeds chunk size
                if (
                    current_length + para_length > self.config.chunk_size
                    and current_chunk_paragraphs
                ):
                    # Create chunk from accumulated paragraphs
                    chunk_text = "\n\n".join(current_chunk_paragraphs)
                    chunk = self._create_chunk(
                        text=chunk_text,
                        chunk_type=ChunkType.PARAGRAPH,
                        position=text_chunk.position,
                        hierarchy=text_chunk.hierarchy,
                        metadata={
                            "paragraph_count": len(current_chunk_paragraphs),
                            "boundary_type": "paragraph",
                        },
                    )
                    chunks.append(chunk)

                    # Reset
                    current_chunk_paragraphs = []
                    current_length = 0

                current_chunk_paragraphs.append(paragraph)
                current_length += para_length

            # Add remaining paragraphs
            if current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                if len(chunk_text) >= self.config.min_chunk_size:
                    chunk = self._create_chunk(
                        text=chunk_text,
                        chunk_type=ChunkType.PARAGRAPH,
                        position=text_chunk.position,
                        hierarchy=text_chunk.hierarchy,
                        metadata={
                            "paragraph_count": len(current_chunk_paragraphs),
                            "boundary_type": "paragraph",
                        },
                    )
                    chunks.append(chunk)

        return chunks

    def _chunk_by_sections(self, content: MultiModalContent) -> list[TextChunk]:
        """
        Chunk content by section boundaries.

        Args:
            content: Content to chunk

        Returns:
            List of section-based chunks
        """
        chunks: list[TextChunk] = []

        # Group chunks by hierarchy
        sections: dict[str, list[TextChunk]] = {}

        for text_chunk in content.text_chunks:
            if text_chunk.hierarchy:
                section_key = f"{text_chunk.hierarchy.section_number or 'root'}"
                if section_key not in sections:
                    sections[section_key] = []
                sections[section_key].append(text_chunk)
            else:
                # No hierarchy, treat as separate chunk
                chunks.append(text_chunk)

        # Create chunks from sections
        for section_key, section_chunks in sections.items():
            # Combine section chunks
            combined_text = "\n\n".join(chunk.text for chunk in section_chunks)

            # Get hierarchy from first chunk
            hierarchy = section_chunks[0].hierarchy if section_chunks else None

            # Split if too large
            if len(combined_text) > self.config.chunk_size:
                sub_chunks = self._split_section(combined_text, hierarchy)
                chunks.extend(sub_chunks)
            else:
                chunk = self._create_chunk(
                    text=combined_text,
                    chunk_type=ChunkType.SECTION,
                    hierarchy=hierarchy,
                    metadata={
                        "section_key": section_key,
                        "boundary_type": "section",
                        "chunk_count": len(section_chunks),
                    },
                )
                chunks.append(chunk)

        return chunks

    def _split_section(
        self, text: str, hierarchy: DocumentHierarchy | None
    ) -> list[TextChunk]:
        """
        Split a large section into smaller chunks.

        Args:
            text: Section text
            hierarchy: Section hierarchy

        Returns:
            List of sub-chunks
        """
        chunks: list[TextChunk] = []
        paragraphs = self._split_into_paragraphs(text)

        current_chunk_paragraphs: list[str] = []
        current_length = 0

        for paragraph in paragraphs:
            para_length = len(paragraph)

            if (
                current_length + para_length > self.config.chunk_size
                and current_chunk_paragraphs
            ):
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunk = self._create_chunk(
                    text=chunk_text,
                    chunk_type=ChunkType.SECTION,
                    hierarchy=hierarchy,
                    metadata={
                        "paragraph_count": len(current_chunk_paragraphs),
                        "boundary_type": "section",
                        "split_section": True,
                    },
                )
                chunks.append(chunk)

                current_chunk_paragraphs = []
                current_length = 0

            current_chunk_paragraphs.append(paragraph)
            current_length += para_length

        # Add remaining
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunk = self._create_chunk(
                text=chunk_text,
                chunk_type=ChunkType.SECTION,
                hierarchy=hierarchy,
                metadata={
                    "paragraph_count": len(current_chunk_paragraphs),
                    "boundary_type": "section",
                    "split_section": True,
                },
            )
            chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be enhanced with NLP)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split on double newlines or multiple spaces
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]


class ChunkerFactory:
    """Factory for creating chunking strategies."""

    @staticmethod
    def create_chunker(config: ChunkingConfig) -> BaseChunker:
        """
        Create a chunker based on configuration strategy.

        Args:
            config: Chunking configuration

        Returns:
            Appropriate chunker instance

        Raises:
            ValueError: If strategy is not supported
        """
        if config.strategy == ChunkingStrategy.FIXED_SIZE:
            return LinkedChunker(config)  # Use linked for fixed size
        elif config.strategy in {
            ChunkingStrategy.SENTENCE,
            ChunkingStrategy.PARAGRAPH,
            ChunkingStrategy.SEMANTIC,
            ChunkingStrategy.HIERARCHICAL,
        }:
            return SemanticChunker(config)
        elif config.strategy == ChunkingStrategy.SLIDING_WINDOW:
            return LinkedChunker(config)
        else:
            raise ValueError(f"Unsupported chunking strategy: {config.strategy}")

    @staticmethod
    def create_relationship_aware_chunker(
        config: ChunkingConfig,
    ) -> RelationshipAwareChunker:
        """
        Create a relationship-aware chunker.

        Args:
            config: Chunking configuration

        Returns:
            RelationshipAwareChunker instance
        """
        return RelationshipAwareChunker(config)

    @staticmethod
    def create_linked_chunker(config: ChunkingConfig) -> LinkedChunker:
        """
        Create a linked chunker.

        Args:
            config: Chunking configuration

        Returns:
            LinkedChunker instance
        """
        return LinkedChunker(config)

    @staticmethod
    def create_semantic_chunker(config: ChunkingConfig) -> SemanticChunker:
        """
        Create a semantic chunker.

        Args:
            config: Chunking configuration

        Returns:
            SemanticChunker instance
        """
        return SemanticChunker(config)
