"""
Content Element Base Classes

This module defines the base classes for content elements that can appear in documents:
- ContentElementType: Enum defining all types of content elements
- RelationshipType: Enum defining types of relationships between elements
- ContentRelationship: Class representing a relationship between two elements
- ContentElement: Abstract base class for all content elements

These classes form the foundation for multi-modal content handling in the RAG system.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from .base_models import ContentPosition


class ContentElementType(Enum):
    """
    Enumeration of all content element types supported by the system.

    This enum defines the various types of content that can be extracted
    from documents and processed by the RAG system.
    """

    TEXT = "text"  # Plain text content
    IMAGE = "image"  # Images, figures, photos
    TABLE = "table"  # Tables and structured data
    EQUATION = "equation"  # Mathematical equations
    CODE = "code"  # Code blocks and snippets
    CHART = "chart"  # Charts and graphs
    DIAGRAM = "diagram"  # Diagrams and flowcharts
    HEADING = "heading"  # Section headings
    LIST = "list"  # Bulleted or numbered lists
    FOOTNOTE = "footnote"  # Footnotes and endnotes
    CAPTION = "caption"  # Captions for figures/tables
    REFERENCE = "reference"  # Citations and references
    LINK = "link"  # Hyperlinks
    METADATA = "metadata"  # Document metadata
    ANNOTATION = "annotation"  # Comments and annotations
    UNKNOWN = "unknown"  # Unknown or unclassified content


class RelationshipType(Enum):
    """
    Enumeration of relationship types between content elements.

    These relationships help preserve document structure and semantic
    connections between different content elements.
    """

    CAPTION = "caption"  # Element is a caption for another element
    REFERENCE = "reference"  # Element references another element
    PARENT_CHILD = "parent_child"  # Hierarchical parent-child relationship
    SIBLING = "sibling"  # Elements at the same hierarchical level
    SEQUENCE = "sequence"  # Elements in sequential order
    ANNOTATION = "annotation"  # Element annotates another element
    DEPENDENCY = "dependency"  # Element depends on another (e.g., formula cells)
    CROSS_REFERENCE = "cross_reference"  # Cross-reference in document
    CONTAINS = "contains"  # Element contains another element
    PART_OF = "part_of"  # Element is part of another element
    RELATED = "related"  # Generic related relationship
    FOOTNOTE = "footnote"  # Footnote relationship
    CITATION = "citation"  # Citation relationship
    UNKNOWN = "unknown"  # Unknown or unclassified relationship


@dataclass
class ContentRelationship:
    """
    Represents a relationship between two content elements.

    This class captures the connection between content elements, including
    the relationship type, confidence score, and additional metadata.

    Attributes:
        source_id: UUID of the source element
        target_id: UUID of the target element
        relationship_type: Type of relationship between elements
        confidence: Confidence score for this relationship (0.0 to 1.0)
        metadata: Additional metadata about the relationship
        created_at: Timestamp when relationship was created
        bidirectional: Whether the relationship is bidirectional

    Example:
        >>> rel = ContentRelationship(
        ...     source_id="figure-123",
        ...     target_id="caption-456",
        ...     relationship_type=RelationshipType.CAPTION,
        ...     confidence=0.95
        ... )
        >>> rel.is_high_confidence()
        True
    """

    source_id: str
    target_id: str
    relationship_type: RelationshipType
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    bidirectional: bool = False

    def __post_init__(self) -> None:
        """Validate relationship data after initialization."""
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id cannot be the same")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Check if the relationship has high confidence.

        Args:
            threshold: Minimum confidence score to be considered high (default: 0.8)

        Returns:
            True if confidence >= threshold, False otherwise
        """
        return self.confidence >= threshold

    def to_dict(self) -> dict[str, Any]:
        """
        Convert relationship to dictionary format.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "bidirectional": self.bidirectional,
        }

    def reverse(self) -> "ContentRelationship":
        """
        Create a reverse relationship (swap source and target).

        Returns:
            New ContentRelationship with source and target swapped
        """
        return ContentRelationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=self.relationship_type,
            confidence=self.confidence,
            metadata=self.metadata.copy(),
            created_at=self.created_at,
            bidirectional=self.bidirectional,
        )


@dataclass
class ContentElement:
    """
    Base class for all content elements in the system.

    This abstract base class provides common functionality for all types
    of content elements extracted from documents. Specific content types
    (images, tables, etc.) should inherit from this class.

    Attributes:
        id: Unique identifier for the element
        element_type: Type of content element
        position: Position information within the document
        metadata: Additional metadata about the element
        relationships: List of relationships to other elements
        confidence: Confidence score for element extraction (0.0 to 1.0)
        created_at: Timestamp when element was created
        source_document: Identifier of the source document

    Example:
        >>> element = ContentElement(
        ...     element_type=ContentElementType.TEXT,
        ...     position=ContentPosition(page_number=1),
        ...     metadata={"language": "en"}
        ... )
        >>> element.add_relationship("other-id", RelationshipType.REFERENCE)
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    element_type: ContentElementType = ContentElementType.UNKNOWN
    position: ContentPosition | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    relationships: list[ContentRelationship] = field(default_factory=list)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source_document: str | None = None

    def __post_init__(self) -> None:
        """Validate element data after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def add_relationship(
        self,
        target_id: str,
        relationship_type: RelationshipType,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
        bidirectional: bool = False,
    ) -> ContentRelationship:
        """
        Add a relationship to another content element.

        Args:
            target_id: UUID of the target element
            relationship_type: Type of relationship
            confidence: Confidence score for the relationship (0.0 to 1.0)
            metadata: Additional metadata about the relationship
            bidirectional: Whether the relationship is bidirectional

        Returns:
            The created ContentRelationship object

        Raises:
            ValueError: If target_id is the same as this element's id
        """
        if target_id == self.id:
            raise ValueError("Cannot create relationship to self")

        relationship = ContentRelationship(
            source_id=self.id,
            target_id=target_id,
            relationship_type=relationship_type,
            confidence=confidence,
            metadata=metadata or {},
            bidirectional=bidirectional,
        )
        self.relationships.append(relationship)
        return relationship

    def get_relationships(
        self, relationship_type: RelationshipType | None = None
    ) -> list[ContentRelationship]:
        """
        Get relationships, optionally filtered by type.

        Args:
            relationship_type: Filter by this relationship type (None for all)

        Returns:
            List of ContentRelationship objects
        """
        if relationship_type is None:
            return self.relationships.copy()
        return [
            r for r in self.relationships if r.relationship_type == relationship_type
        ]

    def has_relationship(
        self, target_id: str, relationship_type: RelationshipType | None = None
    ) -> bool:
        """
        Check if a relationship exists to a target element.

        Args:
            target_id: UUID of the target element
            relationship_type: Optional relationship type filter

        Returns:
            True if relationship exists, False otherwise
        """
        for rel in self.relationships:
            if rel.target_id == target_id and (
                relationship_type is None or rel.relationship_type == relationship_type
            ):
                return True
        return False

    def remove_relationship(self, target_id: str) -> bool:
        """
        Remove all relationships to a specific target element.

        Args:
            target_id: UUID of the target element

        Returns:
            True if any relationships were removed, False otherwise
        """
        original_count = len(self.relationships)
        self.relationships = [r for r in self.relationships if r.target_id != target_id]
        return len(self.relationships) < original_count

    def to_dict(self) -> dict[str, Any]:
        """
        Convert element to dictionary format.

        Returns:
            Dictionary representation of the element
        """
        return {
            "id": self.id,
            "element_type": self.element_type.value,
            "position": (
                {
                    "page_number": self.position.page_number,
                    "section_number": self.position.section_number,
                    "paragraph_index": self.position.paragraph_index,
                    "char_start": self.position.char_start,
                    "char_end": self.position.char_end,
                    "bbox": self.position.bbox,
                    "line_number": self.position.line_number,
                }
                if self.position
                else None
            ),
            "metadata": self.metadata,
            "relationships": [r.to_dict() for r in self.relationships],
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "source_document": self.source_document,
        }

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Check if the element has high confidence.

        Args:
            threshold: Minimum confidence score to be considered high (default: 0.8)

        Returns:
            True if confidence >= threshold, False otherwise
        """
        return self.confidence >= threshold
