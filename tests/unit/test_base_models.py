"""
Unit Tests for Base Data Models

Tests for ContentPosition, DocumentHierarchy, ChunkType, TextChunk, and MultiModalContent.
"""

from datetime import datetime

import pytest

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)


class TestContentPosition:
    """Tests for ContentPosition class."""

    def test_basic_creation(self):
        """Test basic ContentPosition creation."""
        pos = ContentPosition(
            page_number=1,
            section_number="1.2.3",
            paragraph_index=0,
            char_start=100,
            char_end=250,
        )

        assert pos.page_number == 1
        assert pos.section_number == "1.2.3"
        assert pos.paragraph_index == 0
        assert pos.char_start == 100
        assert pos.char_end == 250

    def test_with_bbox(self):
        """Test ContentPosition with bounding box."""
        pos = ContentPosition(page_number=1, bbox=(10.0, 20.0, 100.0, 200.0))

        assert pos.bbox == (10.0, 20.0, 100.0, 200.0)

    def test_with_line_number(self):
        """Test ContentPosition with line number."""
        pos = ContentPosition(line_number=42)
        assert pos.line_number == 42

    def test_invalid_page_number(self):
        """Test that invalid page numbers raise ValueError."""
        with pytest.raises(ValueError, match="page_number must be >= 1"):
            ContentPosition(page_number=0)

    def test_invalid_paragraph_index(self):
        """Test that invalid paragraph indices raise ValueError."""
        with pytest.raises(ValueError, match="paragraph_index must be >= 0"):
            ContentPosition(paragraph_index=-1)

    def test_invalid_char_positions(self):
        """Test that invalid character positions raise ValueError."""
        with pytest.raises(ValueError, match="char_start and char_end must be >= 0"):
            ContentPosition(char_start=-1, char_end=10)

        with pytest.raises(ValueError, match="char_start must be <= char_end"):
            ContentPosition(char_start=100, char_end=50)

    def test_invalid_line_number(self):
        """Test that invalid line numbers raise ValueError."""
        with pytest.raises(ValueError, match="line_number must be >= 1"):
            ContentPosition(line_number=0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        pos = ContentPosition(
            page_number=2, section_number="3.1", char_start=500, char_end=750
        )

        result = pos.to_dict()

        assert result["page_number"] == 2
        assert result["section_number"] == "3.1"
        assert result["char_start"] == 500
        assert result["char_end"] == 750
        assert "paragraph_index" in result
        assert "bbox" in result

    def test_is_before_by_page(self):
        """Test position comparison by page number."""
        pos1 = ContentPosition(page_number=1, char_start=0)
        pos2 = ContentPosition(page_number=2, char_start=0)

        assert pos1.is_before(pos2)
        assert not pos2.is_before(pos1)

    def test_is_before_by_char_position(self):
        """Test position comparison by character position."""
        pos1 = ContentPosition(page_number=1, char_start=100, char_end=200)
        pos2 = ContentPosition(page_number=1, char_start=300, char_end=400)

        assert pos1.is_before(pos2)
        assert not pos2.is_before(pos1)

    def test_is_before_by_line_number(self):
        """Test position comparison by line number."""
        pos1 = ContentPosition(line_number=10)
        pos2 = ContentPosition(line_number=20)

        assert pos1.is_before(pos2)
        assert not pos2.is_before(pos1)


class TestDocumentHierarchy:
    """Tests for DocumentHierarchy class."""

    def test_basic_creation(self):
        """Test basic DocumentHierarchy creation."""
        hierarchy = DocumentHierarchy(level=1, title="Chapter 1", section_number="1")

        assert hierarchy.level == 1
        assert hierarchy.title == "Chapter 1"
        assert hierarchy.section_number == "1"
        assert isinstance(hierarchy.hierarchy_id, str)
        assert len(hierarchy.children_ids) == 0
        assert len(hierarchy.content_ids) == 0

    def test_invalid_level(self):
        """Test that invalid levels raise ValueError."""
        with pytest.raises(ValueError, match="level must be >= 0"):
            DocumentHierarchy(level=-1, title="Invalid")

    def test_empty_title(self):
        """Test that empty titles raise ValueError."""
        with pytest.raises(ValueError, match="title cannot be empty"):
            DocumentHierarchy(level=1, title="")

    def test_add_child(self):
        """Test adding child nodes."""
        parent = DocumentHierarchy(level=0, title="Root")
        child_id = "child-123"

        parent.add_child(child_id)

        assert child_id in parent.children_ids
        assert len(parent.children_ids) == 1

        # Adding same child again should not duplicate
        parent.add_child(child_id)
        assert len(parent.children_ids) == 1

    def test_add_content(self):
        """Test adding content elements."""
        hierarchy = DocumentHierarchy(level=1, title="Section")
        content_id = "content-456"

        hierarchy.add_content(content_id)

        assert content_id in hierarchy.content_ids
        assert len(hierarchy.content_ids) == 1

        # Adding same content again should not duplicate
        hierarchy.add_content(content_id)
        assert len(hierarchy.content_ids) == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        hierarchy = DocumentHierarchy(
            level=2,
            title="Subsection 1.2",
            section_number="1.2",
            parent_id="parent-123",
        )
        hierarchy.add_child("child-1")
        hierarchy.add_content("content-1")
        hierarchy.metadata["custom"] = "value"

        result = hierarchy.to_dict()

        assert result["level"] == 2
        assert result["title"] == "Subsection 1.2"
        assert result["section_number"] == "1.2"
        assert result["parent_id"] == "parent-123"
        assert "child-1" in result["children_ids"]
        assert "content-1" in result["content_ids"]
        assert result["metadata"]["custom"] == "value"

    def test_get_full_path(self):
        """Test getting full hierarchical path."""
        root = DocumentHierarchy(level=0, title="Document")
        chapter = DocumentHierarchy(
            level=1, title="Chapter 1", parent_id=root.hierarchy_id
        )
        section = DocumentHierarchy(
            level=2, title="Section 1.1", parent_id=chapter.hierarchy_id
        )

        hierarchy_map = {
            root.hierarchy_id: root,
            chapter.hierarchy_id: chapter,
            section.hierarchy_id: section,
        }

        path = section.get_full_path(hierarchy_map)

        assert path == ["Document", "Chapter 1", "Section 1.1"]

    def test_get_full_path_single_level(self):
        """Test getting path for root-level hierarchy."""
        root = DocumentHierarchy(level=0, title="Document")
        hierarchy_map = {root.hierarchy_id: root}

        path = root.get_full_path(hierarchy_map)

        assert path == ["Document"]


class TestChunkType:
    """Tests for ChunkType enum."""

    def test_enum_values(self):
        """Test that all expected chunk types exist."""
        assert ChunkType.TEXT.value == "text"
        assert ChunkType.HEADING.value == "heading"
        assert ChunkType.PARAGRAPH.value == "paragraph"
        assert ChunkType.LIST_ITEM.value == "list_item"
        assert ChunkType.CODE.value == "code"
        assert ChunkType.QUOTE.value == "quote"
        assert ChunkType.CAPTION.value == "caption"
        assert ChunkType.FOOTNOTE.value == "footnote"
        assert ChunkType.TABLE_CELL.value == "table_cell"
        assert ChunkType.EQUATION.value == "equation"
        assert ChunkType.METADATA.value == "metadata"
        assert ChunkType.MIXED.value == "mixed"

    def test_string_conversion(self):
        """Test string representation of enum."""
        assert str(ChunkType.PARAGRAPH) == "paragraph"
        assert str(ChunkType.HEADING) == "heading"


class TestTextChunk:
    """Tests for TextChunk class."""

    def test_basic_creation(self):
        """Test basic TextChunk creation."""
        chunk = TextChunk(text="This is a sample text chunk.")

        assert chunk.text == "This is a sample text chunk."
        assert chunk.chunk_type == ChunkType.PARAGRAPH
        assert isinstance(chunk.chunk_id, str)
        assert isinstance(chunk.created_at, datetime)
        assert chunk.confidence_score == 1.0
        assert "token_count" in chunk.metadata
        assert "char_count" in chunk.metadata

    def test_with_custom_type(self):
        """Test TextChunk with custom chunk type."""
        chunk = TextChunk(text="# Main Title", chunk_type=ChunkType.HEADING)

        assert chunk.chunk_type == ChunkType.HEADING

    def test_with_position(self):
        """Test TextChunk with position information."""
        position = ContentPosition(page_number=1, char_start=0, char_end=100)
        chunk = TextChunk(text="Text with position", position=position)

        assert chunk.position == position
        assert chunk.position.page_number == 1

    def test_with_hierarchy(self):
        """Test TextChunk with hierarchy information."""
        hierarchy = DocumentHierarchy(level=1, title="Chapter 1")
        chunk = TextChunk(text="Text in chapter", hierarchy=hierarchy)

        assert chunk.hierarchy == hierarchy
        assert chunk.hierarchy.title == "Chapter 1"

    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            TextChunk(text="")

    def test_invalid_confidence_score(self):
        """Test that invalid confidence scores raise ValueError."""
        with pytest.raises(
            ValueError, match=r"confidence_score must be between 0\.0 and 1\.0"
        ):
            TextChunk(text="Sample", confidence_score=1.5)

        with pytest.raises(
            ValueError, match=r"confidence_score must be between 0\.0 and 1\.0"
        ):
            TextChunk(text="Sample", confidence_score=-0.1)

    def test_metadata_token_count(self):
        """Test automatic token count estimation."""
        chunk = TextChunk(text="This is a test with five words.")

        assert "token_count" in chunk.metadata
        assert chunk.metadata["token_count"] > 0

    def test_metadata_char_count(self):
        """Test automatic character count."""
        text = "Sample text"
        chunk = TextChunk(text=text)

        assert chunk.metadata["char_count"] == len(text)

    def test_add_relationship(self):
        """Test adding relationships."""
        chunk = TextChunk(text="Text with relationships")

        chunk.add_relationship("image-123")
        chunk.add_relationship("table-456")

        assert "image-123" in chunk.relationships
        assert "table-456" in chunk.relationships
        assert len(chunk.relationships) == 2

        # Adding duplicate should not increase count
        chunk.add_relationship("image-123")
        assert len(chunk.relationships) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        position = ContentPosition(page_number=1)
        hierarchy = DocumentHierarchy(level=1, title="Section")

        chunk = TextChunk(
            text="Sample text",
            chunk_type=ChunkType.PARAGRAPH,
            position=position,
            hierarchy=hierarchy,
            confidence_score=0.95,
            source_document_id="doc-123",
        )
        chunk.add_relationship("related-1")

        result = chunk.to_dict()

        assert result["text"] == "Sample text"
        assert result["chunk_type"] == "paragraph"
        assert result["confidence_score"] == 0.95
        assert result["source_document_id"] == "doc-123"
        assert "related-1" in result["relationships"]
        assert result["position"] is not None
        assert result["hierarchy"] is not None

    def test_get_context_summary(self):
        """Test context summary generation."""
        position = ContentPosition(page_number=5)
        hierarchy = DocumentHierarchy(level=1, title="Introduction")

        chunk = TextChunk(
            text="Sample",
            chunk_type=ChunkType.PARAGRAPH,
            position=position,
            hierarchy=hierarchy,
        )

        summary = chunk.get_context_summary()

        assert "Introduction" in summary
        assert "Page 5" in summary
        assert "paragraph" in summary


class TestMultiModalContent:
    """Tests for MultiModalContent class."""

    def test_basic_creation(self):
        """Test basic MultiModalContent creation."""
        content = MultiModalContent(document_id="doc-123")

        assert content.document_id == "doc-123"
        assert len(content.text_chunks) == 0
        assert len(content.images) == 0
        assert len(content.tables) == 0
        assert len(content.equations) == 0
        assert isinstance(content.processing_timestamp, datetime)
        assert content.metadata["total_chunks"] == 0

    def test_empty_document_id_raises_error(self):
        """Test that empty document_id raises ValueError."""
        with pytest.raises(ValueError, match="document_id cannot be empty"):
            MultiModalContent(document_id="")

    def test_add_text_chunk(self):
        """Test adding text chunks."""
        content = MultiModalContent(document_id="doc-123")
        chunk = TextChunk(text="Sample chunk")

        content.add_text_chunk(chunk)

        assert len(content.text_chunks) == 1
        assert chunk.source_document_id == "doc-123"
        assert content.metadata["total_chunks"] == 1

    def test_add_image(self):
        """Test adding image references."""
        content = MultiModalContent(document_id="doc-123")

        content.add_image("image-1")
        content.add_image("image-2")

        assert len(content.images) == 2
        assert "image-1" in content.images
        assert content.metadata["total_images"] == 2

        # Duplicate should not be added
        content.add_image("image-1")
        assert len(content.images) == 2

    def test_add_table(self):
        """Test adding table references."""
        content = MultiModalContent(document_id="doc-123")

        content.add_table("table-1")

        assert len(content.tables) == 1
        assert content.metadata["total_tables"] == 1

    def test_add_equation(self):
        """Test adding equation references."""
        content = MultiModalContent(document_id="doc-123")

        content.add_equation("eq-1")

        assert len(content.equations) == 1
        assert content.metadata["total_equations"] == 1

    def test_add_relationship(self):
        """Test adding content relationships."""
        content = MultiModalContent(document_id="doc-123")

        content.add_relationship("chunk-1", "image-1")
        content.add_relationship("chunk-1", "table-1")
        content.add_relationship("chunk-2", "image-1")

        assert len(content.relationships["chunk-1"]) == 2
        assert "image-1" in content.relationships["chunk-1"]
        assert "table-1" in content.relationships["chunk-1"]
        assert len(content.relationships["chunk-2"]) == 1

        # Duplicate relationship should not be added
        content.add_relationship("chunk-1", "image-1")
        assert len(content.relationships["chunk-1"]) == 2

    def test_get_related_content(self):
        """Test retrieving related content."""
        content = MultiModalContent(document_id="doc-123")

        content.add_relationship("chunk-1", "image-1")
        content.add_relationship("chunk-1", "table-1")

        related = content.get_related_content("chunk-1")

        assert len(related) == 2
        assert "image-1" in related
        assert "table-1" in related

        # Non-existent content should return empty list
        assert content.get_related_content("nonexistent") == []

    def test_add_hierarchy(self):
        """Test adding hierarchy nodes."""
        content = MultiModalContent(document_id="doc-123")
        hierarchy = DocumentHierarchy(level=1, title="Chapter 1")

        content.add_hierarchy(hierarchy)

        assert len(content.hierarchy) == 1
        assert content.hierarchy[0].title == "Chapter 1"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        content = MultiModalContent(document_id="doc-123")
        chunk = TextChunk(text="Sample")
        hierarchy = DocumentHierarchy(level=1, title="Section")

        content.add_text_chunk(chunk)
        content.add_image("image-1")
        content.add_table("table-1")
        content.add_hierarchy(hierarchy)
        content.add_relationship("chunk-1", "image-1")

        result = content.to_dict()

        assert result["document_id"] == "doc-123"
        assert len(result["text_chunks"]) == 1
        assert "image-1" in result["images"]
        assert "table-1" in result["tables"]
        assert len(result["hierarchy"]) == 1
        assert "chunk-1" in result["relationships"]

    def test_get_chunks_by_type(self):
        """Test retrieving chunks by type."""
        content = MultiModalContent(document_id="doc-123")

        content.add_text_chunk(
            TextChunk(text="Paragraph 1", chunk_type=ChunkType.PARAGRAPH)
        )
        content.add_text_chunk(TextChunk(text="Heading", chunk_type=ChunkType.HEADING))
        content.add_text_chunk(
            TextChunk(text="Paragraph 2", chunk_type=ChunkType.PARAGRAPH)
        )

        paragraphs = content.get_chunks_by_type(ChunkType.PARAGRAPH)
        headings = content.get_chunks_by_type(ChunkType.HEADING)

        assert len(paragraphs) == 2
        assert len(headings) == 1
        assert all(c.chunk_type == ChunkType.PARAGRAPH for c in paragraphs)

    def test_get_chunks_in_range(self):
        """Test retrieving chunks in page range."""
        content = MultiModalContent(document_id="doc-123")

        content.add_text_chunk(
            TextChunk(text="Page 1", position=ContentPosition(page_number=1))
        )
        content.add_text_chunk(
            TextChunk(text="Page 2", position=ContentPosition(page_number=2))
        )
        content.add_text_chunk(
            TextChunk(text="Page 3", position=ContentPosition(page_number=3))
        )
        content.add_text_chunk(
            TextChunk(text="Page 5", position=ContentPosition(page_number=5))
        )

        # Test range
        chunks = content.get_chunks_in_range(start_page=2, end_page=3)
        assert len(chunks) == 2

        # Test start only
        chunks = content.get_chunks_in_range(start_page=3)
        assert len(chunks) == 2

        # Test end only
        chunks = content.get_chunks_in_range(end_page=2)
        assert len(chunks) == 2

        # Test no range (all chunks)
        chunks = content.get_chunks_in_range()
        assert len(chunks) == 4

    def test_summary_metadata_updates(self):
        """Test that summary metadata updates automatically."""
        content = MultiModalContent(document_id="doc-123")

        assert content.metadata["total_chunks"] == 0
        assert content.metadata["total_images"] == 0

        content.add_text_chunk(TextChunk(text="Chunk 1"))
        assert content.metadata["total_chunks"] == 1

        content.add_image("image-1")
        assert content.metadata["total_images"] == 1

        content.add_relationship("chunk-1", "image-1")
        assert content.metadata["total_relationships"] == 1
