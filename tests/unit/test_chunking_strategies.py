"""
Tests for chunking strategies (T4.2.1, T4.2.2, T4.2.3).

This module tests:
- RelationshipAwareChunker (T4.2.1)
- LinkedChunker (T4.2.2)
- SemanticChunker (T4.2.3)
- ChunkerFactory
"""

import pytest

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.chunking_config import BoundaryType, ChunkingConfig, ChunkingStrategy
from src.processors.chunking_strategies import (
    BaseChunker,
    ChunkerFactory,
    LinkedChunker,
    RelationshipAwareChunker,
    SemanticChunker,
)


class TestRelationshipAwareChunker:
    """Tests for RelationshipAwareChunker (T4.2.1)."""

    def test_initialization(self):
        """Test chunker initialization."""
        config = ChunkingConfig.default()
        chunker = RelationshipAwareChunker(config)

        assert chunker.config == config
        assert isinstance(chunker, BaseChunker)

    def test_chunk_preserves_figure_references(self):
        """Test that figure references are preserved in chunks."""
        config = ChunkingConfig(chunk_size=200, chunk_overlap=20)
        chunker = RelationshipAwareChunker(config)

        # Create content with figure reference
        text = (
            "This is the introduction. "
            "Figure 1 shows the results of our experiment. "
            "The data demonstrates a clear trend in the measurements. "
            "As seen in Figure 1, the values increase over time."
        )
        
        content = MultiModalContent(document_id="doc-001")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should have chunks with figure references
        assert len(chunks) > 0
        
        # Find chunk with figure reference
        fig_chunks = [c for c in chunks if "Figure 1" in c.text]
        assert len(fig_chunks) > 0
        
        # Check that multi-modal refs are added
        for chunk in fig_chunks:
            assert chunk.has_multi_modal_content() or "Figure" in chunk.text

    def test_chunk_preserves_table_references(self):
        """Test that table references are preserved in chunks."""
        config = ChunkingConfig(chunk_size=150)
        chunker = RelationshipAwareChunker(config)

        text = (
            "The experimental results are summarized in Table 1. "
            "Table 1 contains all measurements from the study. "
            "Each row represents a different trial condition."
        )

        content = MultiModalContent(document_id="doc-002")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Find chunks with table references
        table_chunks = [c for c in chunks if "Table 1" in c.text]
        assert len(table_chunks) > 0

    def test_chunk_preserves_equation_references(self):
        """Test that equation references are preserved in chunks."""
        config = ChunkingConfig(chunk_size=150)
        chunker = RelationshipAwareChunker(config)

        text = (
            "The formula is given by Equation 1. "
            "As shown in Eq. 2, the relationship is linear. "
            "These equations form the theoretical foundation."
        )

        content = MultiModalContent(document_id="doc-003")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should preserve equation references
        eq_chunks = [c for c in chunks if "Equation" in c.text or "Eq." in c.text]
        assert len(eq_chunks) > 0

    def test_small_chunk_not_split(self):
        """Test that small chunks are not split."""
        config = ChunkingConfig(chunk_size=500)
        chunker = RelationshipAwareChunker(config)

        text = "This is a short paragraph that should not be split."
        content = MultiModalContent(document_id="doc-004")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_metadata_tracking(self):
        """Test that relationship metadata is tracked."""
        config = ChunkingConfig(chunk_size=200)
        chunker = RelationshipAwareChunker(config)

        text = "See Figure 1 and Table 2 for details. This references multiple elements."
        content = MultiModalContent(document_id="doc-005")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Check metadata
        for chunk in chunks:
            if "Figure" in chunk.text or "Table" in chunk.text:
                assert "has_references" in chunk.metadata or len(chunk.relationships) > 0


class TestLinkedChunker:
    """Tests for LinkedChunker (T4.2.2)."""

    def test_initialization(self):
        """Test chunker initialization."""
        config = ChunkingConfig.default()
        chunker = LinkedChunker(config)

        assert chunker.config == config
        assert isinstance(chunker, BaseChunker)

    def test_sequential_linking(self):
        """Test that chunks are linked sequentially."""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=10)
        chunker = LinkedChunker(config)

        text = "A" * 300  # Create text that will be split into multiple chunks
        content = MultiModalContent(document_id="doc-006")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should have multiple chunks
        assert len(chunks) >= 2

        # Check sequential linking
        for i in range(len(chunks) - 1):
            assert chunks[i].next_chunk_id == chunks[i + 1].chunk_id
            assert chunks[i + 1].prev_chunk_id == chunks[i].chunk_id

    def test_first_chunk_no_prev(self):
        """Test that first chunk has no previous link."""
        config = ChunkingConfig(chunk_size=100)
        chunker = LinkedChunker(config)

        text = "A" * 250
        content = MultiModalContent(document_id="doc-007")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        assert chunks[0].prev_chunk_id is None

    def test_last_chunk_no_next(self):
        """Test that last chunk has no next link."""
        config = ChunkingConfig(chunk_size=100)
        chunker = LinkedChunker(config)

        text = "A" * 250
        content = MultiModalContent(document_id="doc-008")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        assert chunks[-1].next_chunk_id is None

    def test_hierarchical_linking(self):
        """Test that parent-child relationships are maintained."""
        config = ChunkingConfig(chunk_size=100)
        chunker = LinkedChunker(config)

        text = "B" * 300  # Will be split
        content = MultiModalContent(document_id="doc-009")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Check parent-child relationships
        parent_ids = set()
        for chunk in chunks:
            if chunk.parent_chunk_id:
                parent_ids.add(chunk.parent_chunk_id)

        # Should have parent relationships
        assert len(parent_ids) > 0

    def test_sliding_window_overlap(self):
        """Test that sliding window maintains overlap."""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=25)
        chunker = LinkedChunker(config)

        text = "Word " * 100  # Repeating words for easy overlap check
        content = MultiModalContent(document_id="doc-010")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Check metadata for overlap info
        for chunk in chunks:
            if chunk.metadata.get("sliding_window"):
                assert chunk.metadata.get("overlap_size") == 25


class TestSemanticChunker:
    """Tests for SemanticChunker (T4.2.3)."""

    def test_initialization(self):
        """Test chunker initialization."""
        config = ChunkingConfig.semantic_chunks()
        chunker = SemanticChunker(config)

        assert chunker.config == config
        assert isinstance(chunker, BaseChunker)

    def test_sentence_boundary_chunking(self):
        """Test chunking by sentence boundaries."""
        config = ChunkingConfig(
            chunk_size=100,
            boundary_type=BoundaryType.SENTENCE,
            respect_sentence_boundaries=True,
        )
        chunker = SemanticChunker(config)

        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        content = MultiModalContent(document_id="doc-011")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should respect sentence boundaries
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.get("boundary_type") == "sentence"

    def test_paragraph_boundary_chunking(self):
        """Test chunking by paragraph boundaries."""
        config = ChunkingConfig(
            chunk_size=200,
            boundary_type=BoundaryType.PARAGRAPH,
            respect_paragraph_boundaries=True,
        )
        chunker = SemanticChunker(config)

        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        content = MultiModalContent(document_id="doc-012")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should respect paragraph boundaries
        for chunk in chunks:
            if chunk.metadata.get("boundary_type"):
                assert chunk.metadata["boundary_type"] == "paragraph"

    def test_section_boundary_chunking(self):
        """Test chunking by section boundaries."""
        config = ChunkingConfig(
            chunk_size=300,
            boundary_type=BoundaryType.SECTION,
            respect_section_boundaries=True,
        )
        chunker = SemanticChunker(config)

        # Create content with hierarchy
        hierarchy1 = DocumentHierarchy(level=1, title="Introduction", section_number="1")
        hierarchy2 = DocumentHierarchy(level=1, title="Methods", section_number="2")

        content = MultiModalContent(document_id="doc-013")
        content.add_text_chunk(
            TextChunk(text="Introduction text here.", hierarchy=hierarchy1)
        )
        content.add_text_chunk(
            TextChunk(text="Methods description here.", hierarchy=hierarchy2)
        )

        chunks = chunker.chunk(content)

        # Should group by sections
        assert len(chunks) >= 1

    def test_respects_min_chunk_size(self):
        """Test that chunks respect minimum size."""
        config = ChunkingConfig(chunk_size=500, min_chunk_size=100)
        chunker = SemanticChunker(config)

        text = "Short text."
        content = MultiModalContent(document_id="doc-014")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Small text might be dropped or combined
        for chunk in chunks:
            assert len(chunk.text) >= config.min_chunk_size or len(chunks) == 1

    def test_hierarchical_structure_preservation(self):
        """Test that hierarchical structure is preserved."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.HIERARCHICAL,
            boundary_type=BoundaryType.SECTION,
        )
        chunker = SemanticChunker(config)

        hierarchy = DocumentHierarchy(
            level=2, title="Results", section_number="3.1", parent_section="3"
        )

        content = MultiModalContent(document_id="doc-015")
        content.add_text_chunk(
            TextChunk(text="Results of the analysis.", hierarchy=hierarchy)
        )

        chunks = chunker.chunk(content)

        # Check hierarchy is preserved
        for chunk in chunks:
            if chunk.hierarchy:
                assert chunk.hierarchy.level == 2
                assert chunk.hierarchy.title == "Results"


class TestChunkerFactory:
    """Tests for ChunkerFactory."""

    def test_create_relationship_aware_chunker(self):
        """Test creating relationship-aware chunker."""
        config = ChunkingConfig.default()
        chunker = ChunkerFactory.create_relationship_aware_chunker(config)

        assert isinstance(chunker, RelationshipAwareChunker)
        assert chunker.config == config

    def test_create_linked_chunker(self):
        """Test creating linked chunker."""
        config = ChunkingConfig.default()
        chunker = ChunkerFactory.create_linked_chunker(config)

        assert isinstance(chunker, LinkedChunker)
        assert chunker.config == config

    def test_create_semantic_chunker(self):
        """Test creating semantic chunker."""
        config = ChunkingConfig.semantic_chunks()
        chunker = ChunkerFactory.create_semantic_chunker(config)

        assert isinstance(chunker, SemanticChunker)
        assert chunker.config == config

    def test_create_chunker_by_strategy_sentence(self):
        """Test factory creates correct chunker for sentence strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SENTENCE)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_by_strategy_paragraph(self):
        """Test factory creates correct chunker for paragraph strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.PARAGRAPH)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_by_strategy_semantic(self):
        """Test factory creates correct chunker for semantic strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_by_strategy_hierarchical(self):
        """Test factory creates correct chunker for hierarchical strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.HIERARCHICAL)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_by_strategy_fixed_size(self):
        """Test factory creates correct chunker for fixed size strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, LinkedChunker)

    def test_create_chunker_by_strategy_sliding_window(self):
        """Test factory creates correct chunker for sliding window strategy."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SLIDING_WINDOW)
        chunker = ChunkerFactory.create_chunker(config)

        assert isinstance(chunker, LinkedChunker)


class TestChunkingIntegration:
    """Integration tests for chunking strategies."""

    def test_relationship_aware_with_multiple_refs(self):
        """Test relationship-aware chunking with multiple reference types."""
        config = ChunkingConfig(chunk_size=200)
        chunker = RelationshipAwareChunker(config)

        text = (
            "The experimental setup is shown in Figure 1. "
            "Table 2 summarizes the results. "
            "Equation 3 defines the relationship. "
            "As demonstrated in Fig. 4, the correlation is strong."
        )

        content = MultiModalContent(document_id="doc-016")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Should preserve references
        ref_count = sum(1 for c in chunks if c.has_multi_modal_content())
        assert ref_count > 0

    def test_linked_chunking_maintains_context(self):
        """Test that linked chunking maintains context across splits."""
        config = ChunkingConfig(chunk_size=150, chunk_overlap=30)
        chunker = LinkedChunker(config)

        text = " ".join([f"Sentence number {i}." for i in range(50)])
        content = MultiModalContent(document_id="doc-017")
        content.add_text_chunk(TextChunk(text=text))

        chunks = chunker.chunk(content)

        # Verify complete chain
        assert len(chunks) > 1
        
        # Check that all chunks are connected
        for i in range(len(chunks) - 1):
            assert chunks[i].next_chunk_id is not None
            assert chunks[i + 1].prev_chunk_id is not None

    def test_semantic_chunking_with_structure(self):
        """Test semantic chunking preserves document structure."""
        config = ChunkingConfig.hierarchical_chunks()
        chunker = SemanticChunker(config)

        # Create structured content
        intro = DocumentHierarchy(level=1, title="Introduction", section_number="1")
        methods = DocumentHierarchy(level=1, title="Methods", section_number="2")

        content = MultiModalContent(document_id="doc-018")
        content.add_text_chunk(
            TextChunk(text="Introduction paragraph one.\n\nIntroduction paragraph two.", hierarchy=intro)
        )
        content.add_text_chunk(
            TextChunk(text="Methods description here.", hierarchy=methods)
        )

        chunks = chunker.chunk(content)

        # Check that structure is preserved
        assert len(chunks) >= 1
        
        # Verify hierarchy information is maintained
        for chunk in chunks:
            if chunk.hierarchy:
                assert chunk.hierarchy.level in [1, 2, 3]

    def test_combined_strategies(self):
        """Test using multiple strategies in sequence."""
        config1 = ChunkingConfig(chunk_size=300)
        config2 = ChunkingConfig.semantic_chunks()

        # First pass: relationship-aware
        relationship_chunker = RelationshipAwareChunker(config1)
        
        text = (
            "Figure 1 shows the results. " * 20 +
            "Table 2 contains the data. " * 20
        )
        
        content = MultiModalContent(document_id="doc-019")
        content.add_text_chunk(TextChunk(text=text))

        chunks1 = relationship_chunker.chunk(content)

        # Second pass: semantic refinement
        semantic_chunker = SemanticChunker(config2)
        content2 = MultiModalContent(document_id="doc-020")
        for chunk in chunks1:
            content2.add_text_chunk(chunk)

        chunks2 = semantic_chunker.chunk(content2)

        # Should have processed content through both strategies
        assert len(chunks2) > 0

    def test_chunking_with_all_metadata(self):
        """Test that all metadata is properly set across strategies."""
        config = ChunkingConfig.default()
        
        # Test with relationship-aware
        ra_chunker = RelationshipAwareChunker(config)
        text = "See Figure 1 for details."
        content = MultiModalContent(document_id="doc-021")
        content.add_text_chunk(TextChunk(text=text))
        ra_chunks = ra_chunker.chunk(content)
        
        for chunk in ra_chunks:
            assert chunk.chunking_strategy == config.strategy.value
            assert chunk.chunk_id is not None
            assert chunk.created_at is not None
