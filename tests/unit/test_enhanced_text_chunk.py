"""
Tests for enhanced TextChunk class (T4.1.2).

This module tests the enhanced TextChunk functionality including:
- Multi-modal element references
- Hierarchical chunk relationships
- Sequential chunk linking
- Chunking strategy tracking
"""

import pytest
from datetime import datetime, UTC

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    TextChunk,
)


class TestEnhancedTextChunkInitialization:
    """Tests for enhanced TextChunk initialization."""

    def test_basic_initialization(self):
        """Test creating a TextChunk with minimal parameters."""
        chunk = TextChunk(text="This is test content")

        assert chunk.text == "This is test content"
        assert chunk.chunk_type == ChunkType.PARAGRAPH
        assert chunk.confidence_score == 1.0
        assert chunk.parent_chunk_id is None
        assert chunk.child_chunk_ids == []
        assert chunk.prev_chunk_id is None
        assert chunk.next_chunk_id is None
        assert chunk.multi_modal_refs == {}
        assert chunk.chunking_strategy is None

    def test_initialization_with_chunking_strategy(self):
        """Test creating a TextChunk with chunking strategy."""
        chunk = TextChunk(
            text="Content with strategy",
            chunking_strategy="semantic",
        )

        assert chunk.chunking_strategy == "semantic"

    def test_initialization_with_hierarchy(self):
        """Test creating a TextChunk with hierarchical relationships."""
        parent_id = "parent-123"
        chunk = TextChunk(
            text="Child chunk content",
            parent_chunk_id=parent_id,
        )

        assert chunk.parent_chunk_id == parent_id
        assert chunk.child_chunk_ids == []

    def test_initialization_with_sequence_links(self):
        """Test creating a TextChunk with sequential links."""
        chunk = TextChunk(
            text="Middle chunk",
            prev_chunk_id="prev-123",
            next_chunk_id="next-456",
        )

        assert chunk.prev_chunk_id == "prev-123"
        assert chunk.next_chunk_id == "next-456"


class TestMultiModalReferences:
    """Tests for multi-modal element references."""

    def test_add_single_multi_modal_ref(self):
        """Test adding a single multi-modal reference."""
        chunk = TextChunk(text="Content with image")
        chunk.add_multi_modal_ref("image", "img-001")

        assert "image" in chunk.multi_modal_refs
        assert "img-001" in chunk.multi_modal_refs["image"]

    def test_add_multiple_refs_same_type(self):
        """Test adding multiple references of the same type."""
        chunk = TextChunk(text="Content with images")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("image", "img-002")
        chunk.add_multi_modal_ref("image", "img-003")

        assert len(chunk.multi_modal_refs["image"]) == 3
        assert "img-001" in chunk.multi_modal_refs["image"]
        assert "img-002" in chunk.multi_modal_refs["image"]
        assert "img-003" in chunk.multi_modal_refs["image"]

    def test_add_multiple_ref_types(self):
        """Test adding references of different types."""
        chunk = TextChunk(text="Content with multiple elements")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("table", "tbl-001")
        chunk.add_multi_modal_ref("equation", "eq-001")

        assert len(chunk.multi_modal_refs) == 3
        assert "image" in chunk.multi_modal_refs
        assert "table" in chunk.multi_modal_refs
        assert "equation" in chunk.multi_modal_refs

    def test_add_duplicate_ref_ignored(self):
        """Test that duplicate references are not added."""
        chunk = TextChunk(text="Content")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("image", "img-001")

        assert len(chunk.multi_modal_refs["image"]) == 1

    def test_get_multi_modal_refs_by_type(self):
        """Test retrieving references by type."""
        chunk = TextChunk(text="Content")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("image", "img-002")
        chunk.add_multi_modal_ref("table", "tbl-001")

        image_refs = chunk.get_multi_modal_refs_by_type("image")
        table_refs = chunk.get_multi_modal_refs_by_type("table")

        assert len(image_refs) == 2
        assert len(table_refs) == 1
        assert "img-001" in image_refs
        assert "tbl-001" in table_refs

    def test_get_nonexistent_ref_type(self):
        """Test retrieving references for type that doesn't exist."""
        chunk = TextChunk(text="Content")
        refs = chunk.get_multi_modal_refs_by_type("video")

        assert refs == []

    def test_has_multi_modal_content_true(self):
        """Test has_multi_modal_content when references exist."""
        chunk = TextChunk(text="Content")
        chunk.add_multi_modal_ref("image", "img-001")

        assert chunk.has_multi_modal_content() is True

    def test_has_multi_modal_content_false(self):
        """Test has_multi_modal_content when no references exist."""
        chunk = TextChunk(text="Content")

        assert chunk.has_multi_modal_content() is False


class TestHierarchicalRelationships:
    """Tests for hierarchical chunk relationships."""

    def test_set_parent_chunk(self):
        """Test setting parent chunk ID."""
        chunk = TextChunk(text="Child chunk")
        chunk.set_parent_chunk("parent-123")

        assert chunk.parent_chunk_id == "parent-123"

    def test_add_single_child_chunk(self):
        """Test adding a single child chunk."""
        chunk = TextChunk(text="Parent chunk")
        chunk.add_child_chunk("child-001")

        assert len(chunk.child_chunk_ids) == 1
        assert "child-001" in chunk.child_chunk_ids

    def test_add_multiple_child_chunks(self):
        """Test adding multiple child chunks."""
        chunk = TextChunk(text="Parent chunk")
        chunk.add_child_chunk("child-001")
        chunk.add_child_chunk("child-002")
        chunk.add_child_chunk("child-003")

        assert len(chunk.child_chunk_ids) == 3
        assert all(
            cid in chunk.child_chunk_ids
            for cid in ["child-001", "child-002", "child-003"]
        )

    def test_add_duplicate_child_ignored(self):
        """Test that duplicate child IDs are not added."""
        chunk = TextChunk(text="Parent chunk")
        chunk.add_child_chunk("child-001")
        chunk.add_child_chunk("child-001")

        assert len(chunk.child_chunk_ids) == 1

    def test_parent_child_relationship(self):
        """Test complete parent-child relationship."""
        parent = TextChunk(text="Parent content")
        child1 = TextChunk(text="Child 1")
        child2 = TextChunk(text="Child 2")

        # Set up relationships
        parent.add_child_chunk(child1.chunk_id)
        parent.add_child_chunk(child2.chunk_id)
        child1.set_parent_chunk(parent.chunk_id)
        child2.set_parent_chunk(parent.chunk_id)

        assert len(parent.child_chunk_ids) == 2
        assert child1.parent_chunk_id == parent.chunk_id
        assert child2.parent_chunk_id == parent.chunk_id


class TestSequentialLinking:
    """Tests for sequential chunk linking."""

    def test_link_to_next(self):
        """Test linking to next chunk."""
        chunk = TextChunk(text="Current chunk")
        chunk.link_to_next("next-123")

        assert chunk.next_chunk_id == "next-123"

    def test_link_to_prev(self):
        """Test linking to previous chunk."""
        chunk = TextChunk(text="Current chunk")
        chunk.link_to_prev("prev-123")

        assert chunk.prev_chunk_id == "prev-123"

    def test_bidirectional_linking(self):
        """Test bidirectional linking between chunks."""
        chunk1 = TextChunk(text="First chunk")
        chunk2 = TextChunk(text="Second chunk")
        chunk3 = TextChunk(text="Third chunk")

        # Link chunks in sequence
        chunk1.link_to_next(chunk2.chunk_id)
        chunk2.link_to_prev(chunk1.chunk_id)
        chunk2.link_to_next(chunk3.chunk_id)
        chunk3.link_to_prev(chunk2.chunk_id)

        assert chunk1.next_chunk_id == chunk2.chunk_id
        assert chunk2.prev_chunk_id == chunk1.chunk_id
        assert chunk2.next_chunk_id == chunk3.chunk_id
        assert chunk3.prev_chunk_id == chunk2.chunk_id

    def test_update_links(self):
        """Test updating existing links."""
        chunk = TextChunk(text="Chunk")
        chunk.link_to_next("next-old")
        chunk.link_to_next("next-new")

        assert chunk.next_chunk_id == "next-new"


class TestEnhancedSerialization:
    """Tests for serialization with enhanced fields."""

    def test_to_dict_with_all_fields(self):
        """Test converting chunk with all fields to dict."""
        chunk = TextChunk(
            text="Complete chunk",
            chunk_type=ChunkType.PARAGRAPH,
            chunking_strategy="semantic",
            parent_chunk_id="parent-123",
            prev_chunk_id="prev-456",
            next_chunk_id="next-789",
        )
        chunk.add_child_chunk("child-001")
        chunk.add_child_chunk("child-002")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("table", "tbl-001")

        data = chunk.to_dict()

        assert data["text"] == "Complete chunk"
        assert data["chunk_type"] == "paragraph"
        assert data["chunking_strategy"] == "semantic"
        assert data["parent_chunk_id"] == "parent-123"
        assert data["prev_chunk_id"] == "prev-456"
        assert data["next_chunk_id"] == "next-789"
        assert len(data["child_chunk_ids"]) == 2
        assert "image" in data["multi_modal_refs"]
        assert "table" in data["multi_modal_refs"]

    def test_to_dict_with_minimal_fields(self):
        """Test converting chunk with minimal fields to dict."""
        chunk = TextChunk(text="Simple chunk")
        data = chunk.to_dict()

        assert data["text"] == "Simple chunk"
        assert data["parent_chunk_id"] is None
        assert data["child_chunk_ids"] == []
        assert data["prev_chunk_id"] is None
        assert data["next_chunk_id"] is None
        assert data["multi_modal_refs"] == {}
        assert data["chunking_strategy"] is None


class TestEnhancedMetadata:
    """Tests for enhanced metadata handling."""

    def test_metadata_with_chunking_info(self):
        """Test adding chunking-specific metadata."""
        chunk = TextChunk(text="Content")
        chunk.metadata["semantic_score"] = 0.95
        chunk.metadata["boundary_type"] = "sentence"
        chunk.metadata["chunk_method"] = "sliding_window"

        assert chunk.metadata["semantic_score"] == 0.95
        assert chunk.metadata["boundary_type"] == "sentence"
        assert chunk.metadata["chunk_method"] == "sliding_window"

    def test_metadata_with_relationship_info(self):
        """Test adding relationship metadata."""
        chunk = TextChunk(text="Content")
        chunk.metadata["has_caption"] = True
        chunk.metadata["caption_position"] = "below"
        chunk.metadata["table_ref_count"] = 3

        assert chunk.metadata["has_caption"] is True
        assert chunk.metadata["table_ref_count"] == 3


class TestComplexScenarios:
    """Tests for complex chunking scenarios."""

    def test_hierarchical_semantic_chunk(self):
        """Test chunk with both hierarchical and semantic properties."""
        chunk = TextChunk(
            text="Complex semantic chunk",
            chunk_type=ChunkType.MIXED,
            chunking_strategy="hierarchical_semantic",
            confidence_score=0.92,
            parent_chunk_id="parent-001",
        )
        chunk.add_child_chunk("child-001")
        chunk.add_multi_modal_ref("image", "img-001")
        chunk.add_multi_modal_ref("equation", "eq-001")
        chunk.metadata["semantic_similarity"] = 0.88
        chunk.metadata["hierarchy_level"] = 2

        assert chunk.chunking_strategy == "hierarchical_semantic"
        assert chunk.parent_chunk_id == "parent-001"
        assert len(chunk.child_chunk_ids) == 1
        assert chunk.has_multi_modal_content()
        assert len(chunk.multi_modal_refs) == 2

    def test_sliding_window_chunk_sequence(self):
        """Test chunks created with sliding window strategy."""
        chunks = []
        for i in range(5):
            chunk = TextChunk(
                text=f"Window chunk {i}",
                chunking_strategy="sliding_window",
            )
            chunk.metadata["window_index"] = i
            chunk.metadata["overlap_start"] = i * 400
            chunk.metadata["overlap_end"] = (i + 1) * 400 + 50
            chunks.append(chunk)

        # Link chunks in sequence
        for i in range(len(chunks) - 1):
            chunks[i].link_to_next(chunks[i + 1].chunk_id)
            chunks[i + 1].link_to_prev(chunks[i].chunk_id)

        # Verify sequence
        assert chunks[0].next_chunk_id == chunks[1].chunk_id
        assert chunks[2].prev_chunk_id == chunks[1].chunk_id
        assert chunks[4].prev_chunk_id == chunks[3].chunk_id
        assert chunks[4].next_chunk_id is None

    def test_mixed_content_chunk_with_all_features(self):
        """Test chunk with all enhanced features combined."""
        chunk = TextChunk(
            text="This chunk references Figure 1 and Table 2 in section 3.1",
            chunk_type=ChunkType.MIXED,
            chunking_strategy="relationship_aware",
            confidence_score=0.95,
            position=ContentPosition(
                page_number=5,
                paragraph_index=2,
                char_start=1200,
            ),
            hierarchy=DocumentHierarchy(
                level=2,
                title="Results",
                section_number="3.1",
            ),
        )

        # Add relationships
        chunk.add_relationship("ref-fig-1")
        chunk.add_relationship("ref-tbl-2")

        # Add multi-modal references
        chunk.add_multi_modal_ref("image", "fig-001")
        chunk.add_multi_modal_ref("table", "tbl-002")

        # Set hierarchical context
        chunk.set_parent_chunk("section-3")
        chunk.add_child_chunk("subsection-3.1.1")

        # Set sequential context
        chunk.link_to_prev("chunk-012")
        chunk.link_to_next("chunk-014")

        # Add metadata
        chunk.metadata["preserves_figure_caption"] = True
        chunk.metadata["preserves_table_reference"] = True

        # Verify all features
        assert chunk.chunk_type == ChunkType.MIXED
        assert chunk.chunking_strategy == "relationship_aware"
        assert len(chunk.relationships) == 2
        assert len(chunk.multi_modal_refs) == 2
        assert chunk.parent_chunk_id == "section-3"
        assert len(chunk.child_chunk_ids) == 1
        assert chunk.prev_chunk_id == "chunk-012"
        assert chunk.next_chunk_id == "chunk-014"
        assert chunk.has_multi_modal_content()
        assert chunk.metadata["preserves_figure_caption"]
