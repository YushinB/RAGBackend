"""
Base Data Models

This module contains fundamental data models used throughout the data processing module:
- ContentPosition: Tracks position of content elements in documents
- DocumentHierarchy: Represents document structure and hierarchy
- ChunkType: Enum for different types of text chunks
- TextChunk: Represents a chunk of text with metadata
- MultiModalContent: Container class for multi-modal content elements
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


@dataclass
class ContentPosition:
    """
    Tracks the position of content elements within a document.

    This class provides detailed positional information for content elements,
    enabling accurate relationship tracking and retrieval context.

    Attributes:
        page_number: Page number where content appears (1-indexed, None for non-paginated)
        section_number: Section number in document hierarchy (e.g., "1.2.3")
        paragraph_index: Index of paragraph within section (0-indexed)
        char_start: Starting character position in the entire document
        char_end: Ending character position in the entire document
        bbox: Bounding box coordinates for visual elements (x1, y1, x2, y2)
        line_number: Line number in the source (for plain text files)
    """

    page_number: int | None = None
    section_number: str | None = None
    paragraph_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    line_number: int | None = None

    def __post_init__(self) -> None:
        """Validate position data after initialization."""
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be >= 1")
        if self.paragraph_index is not None and self.paragraph_index < 0:
            raise ValueError("paragraph_index must be >= 0")
        if self.char_start is not None and self.char_end is not None:
            if self.char_start < 0 or self.char_end < 0:
                raise ValueError("char_start and char_end must be >= 0")
            if self.char_start > self.char_end:
                raise ValueError("char_start must be <= char_end")
        if self.line_number is not None and self.line_number < 1:
            raise ValueError("line_number must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "page_number": self.page_number,
            "section_number": self.section_number,
            "paragraph_index": self.paragraph_index,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "bbox": self.bbox,
            "line_number": self.line_number,
        }

    def is_before(self, other: "ContentPosition") -> bool:
        """
        Check if this position comes before another position.

        Args:
            other: Another ContentPosition to compare with

        Returns:
            True if this position comes before the other
        """
        # Compare by page first
        if (
            self.page_number is not None
            and other.page_number is not None
            and self.page_number != other.page_number
        ):
            return self.page_number < other.page_number

        # Then by character position
        if self.char_start is not None and other.char_start is not None:
            return self.char_start < other.char_start

        # Then by line number
        if self.line_number is not None and other.line_number is not None:
            return self.line_number < other.line_number

        return False


@dataclass
class DocumentHierarchy:
    """
    Represents the hierarchical structure of a document.

    This class maintains document organization including sections, headings,
    and nested structures to preserve logical document flow.

    Attributes:
        level: Hierarchy level (0=document root, 1=chapter, 2=section, etc.)
        title: Title or heading text at this level
        section_number: Numbering scheme (e.g., "1.2.3")
        parent_id: ID of parent hierarchy node
        children_ids: List of child hierarchy node IDs
        content_ids: IDs of content elements at this level
        metadata: Additional metadata (outline level, style, etc.)
    """

    level: int
    title: str
    section_number: str | None = None
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    content_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    hierarchy_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Validate hierarchy data after initialization."""
        if self.level < 0:
            raise ValueError("level must be >= 0")
        if not self.title:
            raise ValueError("title cannot be empty")

    def add_child(self, child_id: str) -> None:
        """Add a child node to this hierarchy level."""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)

    def add_content(self, content_id: str) -> None:
        """Add a content element to this hierarchy level."""
        if content_id not in self.content_ids:
            self.content_ids.append(content_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hierarchy_id": self.hierarchy_id,
            "level": self.level,
            "title": self.title,
            "section_number": self.section_number,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "content_ids": self.content_ids,
            "metadata": self.metadata,
        }

    def get_full_path(self, hierarchy_map: dict[str, "DocumentHierarchy"]) -> list[str]:
        """
        Get the full hierarchical path from root to this node.

        Args:
            hierarchy_map: Dictionary mapping hierarchy IDs to DocumentHierarchy objects

        Returns:
            List of titles from root to this node
        """
        path = [self.title]
        current_id = self.parent_id

        while current_id and current_id in hierarchy_map:
            parent = hierarchy_map[current_id]
            path.insert(0, parent.title)
            current_id = parent.parent_id

        return path


class ChunkType(Enum):
    """
    Enumeration of different types of text chunks.

    This enum classifies chunks based on their content characteristics,
    enabling type-specific processing and retrieval strategies.
    """

    TEXT = "text"  # Plain text content
    HEADING = "heading"  # Section or chapter heading
    PARAGRAPH = "paragraph"  # Regular paragraph
    LIST_ITEM = "list_item"  # Bullet or numbered list item
    CODE = "code"  # Code block or snippet
    QUOTE = "quote"  # Quoted text or blockquote
    CAPTION = "caption"  # Figure or table caption
    FOOTNOTE = "footnote"  # Footnote or endnote
    TABLE_CELL = "table_cell"  # Individual table cell content
    EQUATION = "equation"  # Mathematical equation or formula
    METADATA = "metadata"  # Document metadata (author, date, etc.)
    MIXED = "mixed"  # Chunk containing multiple content types

    def __str__(self) -> str:
        return self.value


@dataclass
class TextChunk:
    """
    Enhanced chunk of text with metadata and multi-modal relationships.

    This is the fundamental unit for text processing, embedding, and retrieval.
    Chunks preserve context, position, and relationships to multi-modal content.
    Supports relationship-aware chunking and semantic chunking strategies.

    Attributes:
        chunk_id: Unique identifier for the chunk
        text: The actual text content
        chunk_type: Type of chunk (from ChunkType enum)
        position: Position information in source document
        hierarchy: Document hierarchy context
        metadata: Additional metadata (token count, language, semantic info, etc.)
        relationships: IDs of related content elements
        confidence_score: Confidence in chunk quality (0.0 to 1.0)
        created_at: Timestamp when chunk was created
        source_document_id: ID of the source document
        parent_chunk_id: ID of parent chunk in hierarchical structure
        child_chunk_ids: IDs of child chunks in hierarchical structure
        prev_chunk_id: ID of previous chunk in sequence
        next_chunk_id: ID of next chunk in sequence
        multi_modal_refs: References to multi-modal elements (images, tables, equations)
        chunking_strategy: Strategy used to create this chunk
    """

    text: str
    chunk_type: ChunkType = ChunkType.PARAGRAPH
    position: ContentPosition | None = None
    hierarchy: DocumentHierarchy | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    relationships: list[str] = field(default_factory=list)
    confidence_score: float = 1.0
    chunk_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source_document_id: str | None = None
    # Enhanced fields for T4.1.2
    parent_chunk_id: str | None = None
    child_chunk_ids: list[str] = field(default_factory=list)
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None
    multi_modal_refs: dict[str, list[str]] = field(default_factory=dict)
    chunking_strategy: str | None = None

    def __post_init__(self) -> None:
        """Validate chunk data after initialization."""
        if not self.text:
            raise ValueError("text cannot be empty")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")

        # Add basic metadata if not present
        if "token_count" not in self.metadata:
            self.metadata["token_count"] = self._estimate_token_count()
        if "char_count" not in self.metadata:
            self.metadata["char_count"] = len(self.text)

    def _estimate_token_count(self) -> int:
        """Estimate token count (rough approximation: words * 1.3)."""
        word_count = len(self.text.split())
        return int(word_count * 1.3)

    def add_relationship(self, content_id: str) -> None:
        """Add a relationship to another content element."""
        if content_id not in self.relationships:
            self.relationships.append(content_id)

    def add_multi_modal_ref(self, ref_type: str, ref_id: str) -> None:
        """
        Add a reference to a multi-modal element.

        Args:
            ref_type: Type of reference (e.g., 'image', 'table', 'equation')
            ref_id: ID of the referenced element
        """
        if ref_type not in self.multi_modal_refs:
            self.multi_modal_refs[ref_type] = []
        if ref_id not in self.multi_modal_refs[ref_type]:
            self.multi_modal_refs[ref_type].append(ref_id)

    def add_child_chunk(self, child_id: str) -> None:
        """
        Add a child chunk ID to this chunk (for hierarchical chunking).

        Args:
            child_id: ID of the child chunk
        """
        if child_id not in self.child_chunk_ids:
            self.child_chunk_ids.append(child_id)

    def set_parent_chunk(self, parent_id: str) -> None:
        """
        Set the parent chunk ID (for hierarchical chunking).

        Args:
            parent_id: ID of the parent chunk
        """
        self.parent_chunk_id = parent_id

    def link_to_next(self, next_id: str) -> None:
        """
        Link this chunk to the next chunk in sequence.

        Args:
            next_id: ID of the next chunk
        """
        self.next_chunk_id = next_id

    def link_to_prev(self, prev_id: str) -> None:
        """
        Link this chunk to the previous chunk in sequence.

        Args:
            prev_id: ID of the previous chunk
        """
        self.prev_chunk_id = prev_id

    def get_multi_modal_refs_by_type(self, ref_type: str) -> list[str]:
        """
        Get all multi-modal references of a specific type.

        Args:
            ref_type: Type of reference to retrieve

        Returns:
            List of reference IDs for the specified type
        """
        return self.multi_modal_refs.get(ref_type, [])

    def has_multi_modal_content(self) -> bool:
        """
        Check if this chunk has any multi-modal references.

        Returns:
            True if chunk has multi-modal references, False otherwise
        """
        return len(self.multi_modal_refs) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "chunk_type": self.chunk_type.value,
            "position": self.position.to_dict() if self.position else None,
            "hierarchy": self.hierarchy.to_dict() if self.hierarchy else None,
            "metadata": self.metadata,
            "relationships": self.relationships,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
            "source_document_id": self.source_document_id,
            "parent_chunk_id": self.parent_chunk_id,
            "child_chunk_ids": self.child_chunk_ids,
            "prev_chunk_id": self.prev_chunk_id,
            "next_chunk_id": self.next_chunk_id,
            "multi_modal_refs": self.multi_modal_refs,
            "chunking_strategy": self.chunking_strategy,
        }

    def get_context_summary(self) -> str:
        """
        Generate a summary of the chunk's context.

        Returns:
            String describing the chunk's position and hierarchy
        """
        parts = []

        if self.hierarchy:
            parts.append(f"Section: {self.hierarchy.title}")

        if self.position and self.position.page_number:
            parts.append(f"Page {self.position.page_number}")

        parts.append(f"Type: {self.chunk_type.value}")

        return " | ".join(parts)


@dataclass
class MultiModalContent:
    """
    Container class for multi-modal content elements.

    This class aggregates different types of content (text, images, tables, equations)
    and maintains relationships between them. It serves as the primary data structure
    for processed documents.

    Attributes:
        document_id: Unique identifier for the document
        text_chunks: List of TextChunk objects
        images: List of image content elements (IDs or objects)
        tables: List of table content elements (IDs or objects)
        equations: List of equation content elements (IDs or objects)
        relationships: Map of content relationships
        hierarchy: Document hierarchy structure
        metadata: Document-level metadata
        processing_timestamp: When content was processed
    """

    document_id: str
    text_chunks: list[TextChunk] = field(default_factory=list)
    images: list[str] = field(default_factory=list)  # Image content IDs
    tables: list[str] = field(default_factory=list)  # Table content IDs
    equations: list[str] = field(default_factory=list)  # Equation content IDs
    relationships: dict[str, list[str]] = field(default_factory=dict)
    hierarchy: list[DocumentHierarchy] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Initialize and validate multi-modal content."""
        if not self.document_id:
            raise ValueError("document_id cannot be empty")

        # Add summary metadata
        self._update_summary_metadata()

    def _update_summary_metadata(self) -> None:
        """Update summary statistics in metadata."""
        self.metadata.update(
            {
                "total_chunks": len(self.text_chunks),
                "total_images": len(self.images),
                "total_tables": len(self.tables),
                "total_equations": len(self.equations),
                "total_relationships": sum(
                    len(rels) for rels in self.relationships.values()
                ),
            }
        )

    def add_text_chunk(self, chunk: TextChunk) -> None:
        """Add a text chunk to the collection."""
        chunk.source_document_id = self.document_id
        self.text_chunks.append(chunk)
        self._update_summary_metadata()

    def add_image(self, image_id: str) -> None:
        """Add an image reference to the collection."""
        if image_id not in self.images:
            self.images.append(image_id)
            self._update_summary_metadata()

    def add_table(self, table_id: str) -> None:
        """Add a table reference to the collection."""
        if table_id not in self.tables:
            self.tables.append(table_id)
            self._update_summary_metadata()

    def add_equation(self, equation_id: str) -> None:
        """Add an equation reference to the collection."""
        if equation_id not in self.equations:
            self.equations.append(equation_id)
            self._update_summary_metadata()

    def add_relationship(self, source_id: str, target_id: str) -> None:
        """
        Add a relationship between two content elements.

        Args:
            source_id: ID of the source content element
            target_id: ID of the target content element
        """
        if source_id not in self.relationships:
            self.relationships[source_id] = []

        if target_id not in self.relationships[source_id]:
            self.relationships[source_id].append(target_id)
            self._update_summary_metadata()

    def get_related_content(self, content_id: str) -> list[str]:
        """
        Get all content IDs related to a given content element.

        Args:
            content_id: ID of the content element

        Returns:
            List of related content IDs
        """
        return self.relationships.get(content_id, [])

    def add_hierarchy(self, hierarchy: DocumentHierarchy) -> None:
        """Add a hierarchy node to the document structure."""
        self.hierarchy.append(hierarchy)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "text_chunks": [chunk.to_dict() for chunk in self.text_chunks],
            "images": self.images,
            "tables": self.tables,
            "equations": self.equations,
            "relationships": self.relationships,
            "hierarchy": [h.to_dict() for h in self.hierarchy],
            "metadata": self.metadata,
            "processing_timestamp": self.processing_timestamp.isoformat(),
        }

    def get_chunks_by_type(self, chunk_type: ChunkType) -> list[TextChunk]:
        """
        Get all chunks of a specific type.

        Args:
            chunk_type: The type of chunks to retrieve

        Returns:
            List of TextChunk objects of the specified type
        """
        return [chunk for chunk in self.text_chunks if chunk.chunk_type == chunk_type]

    def get_chunks_in_range(
        self, start_page: int | None = None, end_page: int | None = None
    ) -> list[TextChunk]:
        """
        Get all chunks within a page range.

        Args:
            start_page: Starting page number (inclusive)
            end_page: Ending page number (inclusive)

        Returns:
            List of TextChunk objects in the page range
        """
        if start_page is None and end_page is None:
            return self.text_chunks

        filtered_chunks = []
        for chunk in self.text_chunks:
            if chunk.position and chunk.position.page_number:
                page = chunk.position.page_number
                if start_page and page < start_page:
                    continue
                if end_page and page > end_page:
                    continue
                filtered_chunks.append(chunk)

        return filtered_chunks
