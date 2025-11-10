"""
Chunking Configuration

This module provides configuration classes for text chunking strategies,
including size limits, overlap settings, and boundary detection options.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChunkingStrategy(Enum):
    """Enumeration of chunking strategies."""

    FIXED_SIZE = "fixed_size"  # Fixed character/token count
    SENTENCE = "sentence"  # Sentence boundary-aware
    PARAGRAPH = "paragraph"  # Paragraph boundary-aware
    SEMANTIC = "semantic"  # Semantic similarity-based
    HIERARCHICAL = "hierarchical"  # Document structure-aware
    SLIDING_WINDOW = "sliding_window"  # Sliding window with overlap


class BoundaryType(Enum):
    """Enumeration of boundary detection types."""

    CHARACTER = "character"  # Character count
    TOKEN = "token"  # Token count (word-based)    
    SENTENCE = "sentence"  # Sentence boundaries
    PARAGRAPH = "paragraph"  # Paragraph boundaries
    SECTION = "section"  # Section/heading boundaries


@dataclass
class ChunkingConfig:
    """
    Configuration for text chunking operations.

    This class defines parameters for chunking strategies, including size limits,
    overlap settings, and boundary detection options. It provides validation
    and default configuration profiles.

    Attributes:
        strategy: The chunking strategy to use
        chunk_size: Target size for each chunk (meaning depends on boundary_type)
        chunk_overlap: Number of units to overlap between chunks
        boundary_type: Type of boundary to respect (character, token, sentence, etc.)
        min_chunk_size: Minimum acceptable chunk size
        max_chunk_size: Maximum acceptable chunk size
        respect_sentence_boundaries: Whether to avoid splitting sentences
        respect_paragraph_boundaries: Whether to avoid splitting paragraphs
        respect_section_boundaries: Whether to avoid splitting sections
        preserve_formatting: Whether to preserve text formatting
        include_metadata: Whether to include chunk metadata
        metadata_fields: Specific metadata fields to include
    """

    strategy: ChunkingStrategy = ChunkingStrategy.PARAGRAPH
    chunk_size: int = 512
    chunk_overlap: int = 50
    boundary_type: BoundaryType = BoundaryType.CHARACTER
    min_chunk_size: int = 100
    max_chunk_size: int = 2048
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = True
    respect_section_boundaries: bool = False
    preserve_formatting: bool = False
    include_metadata: bool = True
    metadata_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_sizes()
        self._validate_overlap()
        self._validate_strategy_compatibility()

    def _validate_sizes(self) -> None:
        """Validate chunk size constraints."""
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        if self.min_chunk_size < 1:
            raise ValueError("min_chunk_size must be positive")
        if self.max_chunk_size < self.min_chunk_size:
            raise ValueError("max_chunk_size must be >= min_chunk_size")
        if self.chunk_size < self.min_chunk_size:
            raise ValueError("chunk_size must be >= min_chunk_size")
        if self.chunk_size > self.max_chunk_size:
            raise ValueError("chunk_size must be <= max_chunk_size")

    def _validate_overlap(self) -> None:
        """Validate overlap constraints."""
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")

    def _validate_strategy_compatibility(self) -> None:
        """Validate strategy and boundary type compatibility."""
        # Semantic strategy requires sentence boundaries
        if self.strategy == ChunkingStrategy.SEMANTIC:
            if not self.respect_sentence_boundaries:
                raise ValueError(
                    "Semantic strategy requires respect_sentence_boundaries=True"
                )

        # Hierarchical strategy requires section boundaries
        if self.strategy == ChunkingStrategy.HIERARCHICAL:
            if not self.respect_section_boundaries:
                raise ValueError(
                    "Hierarchical strategy requires respect_section_boundaries=True"
                )

    @classmethod
    def default(cls) -> "ChunkingConfig":
        """
        Create a default chunking configuration.

        Returns:
            ChunkingConfig with balanced settings for general use
        """
        return cls(
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=512,
            chunk_overlap=50,
            boundary_type=BoundaryType.CHARACTER,
            min_chunk_size=100,
            max_chunk_size=2048,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=True,
        )

    @classmethod
    def small_chunks(cls) -> "ChunkingConfig":
        """
        Create configuration for small, focused chunks.

        Suitable for precise retrieval and detailed analysis.

        Returns:
            ChunkingConfig optimized for small chunks
        """
        return cls(
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=256,
            chunk_overlap=25,
            boundary_type=BoundaryType.CHARACTER,
            min_chunk_size=50,
            max_chunk_size=512,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=False,
        )

    @classmethod
    def large_chunks(cls) -> "ChunkingConfig":
        """
        Create configuration for large, context-rich chunks.

        Suitable for broader context and summarization tasks.

        Returns:
            ChunkingConfig optimized for large chunks
        """
        return cls(
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=1024,
            chunk_overlap=100,
            boundary_type=BoundaryType.CHARACTER,
            min_chunk_size=200,
            max_chunk_size=4096,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=True,
        )

    @classmethod
    def semantic_chunks(cls) -> "ChunkingConfig":
        """
        Create configuration for semantic similarity-based chunking.

        Groups content by semantic coherence rather than fixed size.

        Returns:
            ChunkingConfig optimized for semantic chunking
        """
        return cls(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=512,
            chunk_overlap=50,
            boundary_type=BoundaryType.SENTENCE,
            min_chunk_size=100,
            max_chunk_size=1024,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=True,
        )

    @classmethod
    def hierarchical_chunks(cls) -> "ChunkingConfig":
        """
        Create configuration for document structure-aware chunking.

        Respects document hierarchy (sections, subsections, etc.).

        Returns:
            ChunkingConfig optimized for hierarchical chunking
        """
        return cls(
            strategy=ChunkingStrategy.HIERARCHICAL,
            chunk_size=768,
            chunk_overlap=75,
            boundary_type=BoundaryType.SECTION,
            min_chunk_size=150,
            max_chunk_size=2048,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=True,
            respect_section_boundaries=True,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "strategy": self.strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "boundary_type": self.boundary_type.value,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "respect_sentence_boundaries": self.respect_sentence_boundaries,
            "respect_paragraph_boundaries": self.respect_paragraph_boundaries,
            "respect_section_boundaries": self.respect_section_boundaries,
            "preserve_formatting": self.preserve_formatting,
            "include_metadata": self.include_metadata,
            "metadata_fields": self.metadata_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkingConfig":
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration parameters

        Returns:
            ChunkingConfig instance
        """
        return cls(
            strategy=ChunkingStrategy(data.get("strategy", "paragraph")),
            chunk_size=data.get("chunk_size", 512),
            chunk_overlap=data.get("chunk_overlap", 50),
            boundary_type=BoundaryType(data.get("boundary_type", "character")),
            min_chunk_size=data.get("min_chunk_size", 100),
            max_chunk_size=data.get("max_chunk_size", 2048),
            respect_sentence_boundaries=data.get("respect_sentence_boundaries", True),
            respect_paragraph_boundaries=data.get("respect_paragraph_boundaries", True),
            respect_section_boundaries=data.get("respect_section_boundaries", False),
            preserve_formatting=data.get("preserve_formatting", False),
            include_metadata=data.get("include_metadata", True),
            metadata_fields=data.get("metadata_fields", []),
        )

    def validate_chunk_size(self, size: int) -> bool:
        """
        Check if a chunk size is within acceptable bounds.

        Args:
            size: The size to validate

        Returns:
            True if size is valid, False otherwise
        """
        return self.min_chunk_size <= size <= self.max_chunk_size

    def adjust_for_content_type(self, content_type: str) -> "ChunkingConfig":
        """
        Adjust configuration based on content type.

        Args:
            content_type: Type of content (code, markdown, latex, etc.)

        Returns:
            New ChunkingConfig adjusted for the content type
        """
        if content_type == "code":
            # For code, respect block boundaries more strictly
            return ChunkingConfig(
                strategy=self.strategy,
                chunk_size=self.chunk_size,
                chunk_overlap=max(10, self.chunk_overlap // 2),  # Less overlap for code
                boundary_type=self.boundary_type,
                min_chunk_size=self.min_chunk_size,
                max_chunk_size=self.max_chunk_size,
                respect_sentence_boundaries=False,
                respect_paragraph_boundaries=True,
                respect_section_boundaries=True,
                preserve_formatting=True,
            )
        elif content_type == "markdown":
            # For markdown, respect heading boundaries
            return ChunkingConfig(
                strategy=ChunkingStrategy.HIERARCHICAL,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                boundary_type=BoundaryType.SECTION,
                min_chunk_size=self.min_chunk_size,
                max_chunk_size=self.max_chunk_size,
                respect_sentence_boundaries=True,
                respect_paragraph_boundaries=True,
                respect_section_boundaries=True,
            )
        elif content_type == "latex":
            # For LaTeX, preserve equation boundaries
            return ChunkingConfig(
                strategy=self.strategy,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                boundary_type=self.boundary_type,
                min_chunk_size=self.min_chunk_size,
                max_chunk_size=self.max_chunk_size,
                respect_sentence_boundaries=True,
                respect_paragraph_boundaries=True,
                preserve_formatting=True,
            )
        else:
            # Return a copy for other types
            return ChunkingConfig(
                strategy=self.strategy,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                boundary_type=self.boundary_type,
                min_chunk_size=self.min_chunk_size,
                max_chunk_size=self.max_chunk_size,
                respect_sentence_boundaries=self.respect_sentence_boundaries,
                respect_paragraph_boundaries=self.respect_paragraph_boundaries,
                respect_section_boundaries=self.respect_section_boundaries,
                preserve_formatting=self.preserve_formatting,
                include_metadata=self.include_metadata,
                metadata_fields=self.metadata_fields.copy(),
            )
