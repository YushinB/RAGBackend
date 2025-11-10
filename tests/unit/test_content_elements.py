"""
Unit Tests for Content Element Classes

Tests for:
- ContentElementType enum
- RelationshipType enum
- ContentRelationship class
- ContentElement base class
"""

from datetime import UTC, datetime

import pytest

from src.models.base_models import ContentPosition
from src.models.content_elements import (
    ContentElement,
    ContentElementType,
    ContentRelationship,
    RelationshipType,
)


class TestContentElementType:
    """Tests for ContentElementType enum."""

    def test_all_types_defined(self):
        """Test that all expected content types are defined."""
        expected_types = [
            "TEXT",
            "IMAGE",
            "TABLE",
            "EQUATION",
            "CODE",
            "CHART",
            "DIAGRAM",
            "HEADING",
            "LIST",
            "FOOTNOTE",
            "CAPTION",
            "REFERENCE",
            "LINK",
            "METADATA",
            "ANNOTATION",
            "UNKNOWN",
        ]
        actual_types = [t.name for t in ContentElementType]
        assert set(actual_types) == set(expected_types)

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert ContentElementType.TEXT.value == "text"
        assert ContentElementType.IMAGE.value == "image"
        assert ContentElementType.TABLE.value == "table"
        assert ContentElementType.UNKNOWN.value == "unknown"

    def test_enum_comparison(self):
        """Test enum comparison."""
        assert ContentElementType.TEXT == ContentElementType.TEXT
        assert ContentElementType.TEXT != ContentElementType.IMAGE


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_all_types_defined(self):
        """Test that all expected relationship types are defined."""
        expected_types = [
            "CAPTION",
            "REFERENCE",
            "PARENT_CHILD",
            "SIBLING",
            "SEQUENCE",
            "ANNOTATION",
            "DEPENDENCY",
            "CROSS_REFERENCE",
            "CONTAINS",
            "PART_OF",
            "RELATED",
            "FOOTNOTE",
            "CITATION",
            "UNKNOWN",
        ]
        actual_types = [t.name for t in RelationshipType]
        assert set(actual_types) == set(expected_types)

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert RelationshipType.CAPTION.value == "caption"
        assert RelationshipType.REFERENCE.value == "reference"
        assert RelationshipType.PARENT_CHILD.value == "parent_child"
        assert RelationshipType.UNKNOWN.value == "unknown"


class TestContentRelationship:
    """Tests for ContentRelationship class."""

    def test_basic_creation(self):
        """Test basic relationship creation."""
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.CAPTION,
        )
        assert rel.source_id == "source-123"
        assert rel.target_id == "target-456"
        assert rel.relationship_type == RelationshipType.CAPTION
        assert rel.confidence == 1.0
        assert not rel.bidirectional

    def test_with_confidence(self):
        """Test relationship with custom confidence."""
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.85,
        )
        assert rel.confidence == 0.85

    def test_with_metadata(self):
        """Test relationship with metadata."""
        metadata = {"context": "figure reference", "distance": 5}
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.REFERENCE,
            metadata=metadata,
        )
        assert rel.metadata == metadata

    def test_bidirectional_flag(self):
        """Test bidirectional relationship flag."""
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.SIBLING,
            bidirectional=True,
        )
        assert rel.bidirectional

    def test_empty_source_id_raises_error(self):
        """Test that empty source_id raises ValueError."""
        with pytest.raises(ValueError, match="source_id cannot be empty"):
            ContentRelationship(
                source_id="",
                target_id="target-456",
                relationship_type=RelationshipType.CAPTION,
            )

    def test_empty_target_id_raises_error(self):
        """Test that empty target_id raises ValueError."""
        with pytest.raises(ValueError, match="target_id cannot be empty"):
            ContentRelationship(
                source_id="source-123",
                target_id="",
                relationship_type=RelationshipType.CAPTION,
            )

    def test_same_source_target_raises_error(self):
        """Test that same source and target raises ValueError."""
        with pytest.raises(
            ValueError, match="source_id and target_id cannot be the same"
        ):
            ContentRelationship(
                source_id="same-id",
                target_id="same-id",
                relationship_type=RelationshipType.CAPTION,
            )

    def test_confidence_too_low_raises_error(self):
        """Test that confidence < 0 raises ValueError."""
        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            ContentRelationship(
                source_id="source-123",
                target_id="target-456",
                relationship_type=RelationshipType.CAPTION,
                confidence=-0.1,
            )

    def test_confidence_too_high_raises_error(self):
        """Test that confidence > 1 raises ValueError."""
        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            ContentRelationship(
                source_id="source-123",
                target_id="target-456",
                relationship_type=RelationshipType.CAPTION,
                confidence=1.1,
            )

    def test_is_high_confidence_default(self):
        """Test is_high_confidence with default threshold."""
        high_conf = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.CAPTION,
            confidence=0.85,
        )
        low_conf = ContentRelationship(
            source_id="source-123",
            target_id="target-789",
            relationship_type=RelationshipType.CAPTION,
            confidence=0.75,
        )
        assert high_conf.is_high_confidence()
        assert not low_conf.is_high_confidence()

    def test_is_high_confidence_custom_threshold(self):
        """Test is_high_confidence with custom threshold."""
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.CAPTION,
            confidence=0.75,
        )
        assert rel.is_high_confidence(threshold=0.7)
        assert not rel.is_high_confidence(threshold=0.8)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.CAPTION,
            confidence=0.9,
            metadata={"key": "value"},
        )
        result = rel.to_dict()
        assert result["source_id"] == "source-123"
        assert result["target_id"] == "target-456"
        assert result["relationship_type"] == "caption"
        assert result["confidence"] == 0.9
        assert result["metadata"] == {"key": "value"}
        assert "created_at" in result
        assert result["bidirectional"] is False

    def test_reverse(self):
        """Test creating reverse relationship."""
        original = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.8,
            metadata={"key": "value"},
            bidirectional=True,
        )
        reversed_rel = original.reverse()

        assert reversed_rel.source_id == "target-456"
        assert reversed_rel.target_id == "source-123"
        assert reversed_rel.relationship_type == original.relationship_type
        assert reversed_rel.confidence == original.confidence
        assert reversed_rel.metadata == original.metadata
        assert reversed_rel.bidirectional == original.bidirectional
        assert reversed_rel.created_at == original.created_at

    def test_reverse_metadata_is_copy(self):
        """Test that reverse creates a copy of metadata."""
        original = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.REFERENCE,
            metadata={"key": "value"},
        )
        reversed_rel = original.reverse()
        reversed_rel.metadata["key"] = "modified"

        assert original.metadata["key"] == "value"

    def test_created_at_timestamp(self):
        """Test that created_at is set correctly."""
        before = datetime.now(UTC)
        rel = ContentRelationship(
            source_id="source-123",
            target_id="target-456",
            relationship_type=RelationshipType.CAPTION,
        )
        after = datetime.now(UTC)

        assert before <= rel.created_at <= after


class TestContentElement:
    """Tests for ContentElement base class."""

    def test_basic_creation(self):
        """Test basic element creation."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        assert element.element_type == ContentElementType.TEXT
        assert element.id is not None
        assert element.confidence == 1.0
        assert element.position is None
        assert len(element.relationships) == 0
        assert element.source_document is None

    def test_with_position(self):
        """Test element with position."""
        position = ContentPosition(page_number=1, paragraph_index=0)
        element = ContentElement(
            element_type=ContentElementType.IMAGE, position=position
        )
        assert element.position == position

    def test_with_metadata(self):
        """Test element with metadata."""
        metadata = {"language": "en", "author": "test"}
        element = ContentElement(
            element_type=ContentElementType.TEXT, metadata=metadata
        )
        assert element.metadata == metadata

    def test_with_custom_id(self):
        """Test element with custom ID."""
        custom_id = "custom-element-123"
        element = ContentElement(id=custom_id, element_type=ContentElementType.TABLE)
        assert element.id == custom_id

    def test_with_confidence(self):
        """Test element with custom confidence."""
        element = ContentElement(element_type=ContentElementType.TEXT, confidence=0.75)
        assert element.confidence == 0.75

    def test_with_source_document(self):
        """Test element with source document."""
        element = ContentElement(
            element_type=ContentElementType.TEXT, source_document="doc-123"
        )
        assert element.source_document == "doc-123"

    def test_confidence_too_low_raises_error(self):
        """Test that confidence < 0 raises ValueError."""
        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            ContentElement(element_type=ContentElementType.TEXT, confidence=-0.1)

    def test_confidence_too_high_raises_error(self):
        """Test that confidence > 1 raises ValueError."""
        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            ContentElement(element_type=ContentElementType.TEXT, confidence=1.1)

    def test_add_relationship(self):
        """Test adding a relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        rel = element.add_relationship("target-123", RelationshipType.REFERENCE)

        assert len(element.relationships) == 1
        assert rel.source_id == element.id
        assert rel.target_id == "target-123"
        assert rel.relationship_type == RelationshipType.REFERENCE

    def test_add_relationship_with_confidence(self):
        """Test adding relationship with custom confidence."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        rel = element.add_relationship(
            "target-123", RelationshipType.REFERENCE, confidence=0.85
        )

        assert rel.confidence == 0.85

    def test_add_relationship_with_metadata(self):
        """Test adding relationship with metadata."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        metadata = {"context": "nearby"}
        rel = element.add_relationship(
            "target-123", RelationshipType.REFERENCE, metadata=metadata
        )

        assert rel.metadata == metadata

    def test_add_relationship_bidirectional(self):
        """Test adding bidirectional relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        rel = element.add_relationship(
            "target-123", RelationshipType.SIBLING, bidirectional=True
        )

        assert rel.bidirectional

    def test_add_relationship_to_self_raises_error(self):
        """Test that adding relationship to self raises ValueError."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        with pytest.raises(ValueError, match="Cannot create relationship to self"):
            element.add_relationship(element.id, RelationshipType.REFERENCE)

    def test_get_relationships_all(self):
        """Test getting all relationships."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-1", RelationshipType.REFERENCE)
        element.add_relationship("target-2", RelationshipType.CAPTION)

        rels = element.get_relationships()
        assert len(rels) == 2

    def test_get_relationships_filtered(self):
        """Test getting filtered relationships."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-1", RelationshipType.REFERENCE)
        element.add_relationship("target-2", RelationshipType.CAPTION)
        element.add_relationship("target-3", RelationshipType.REFERENCE)

        ref_rels = element.get_relationships(RelationshipType.REFERENCE)
        assert len(ref_rels) == 2
        assert all(r.relationship_type == RelationshipType.REFERENCE for r in ref_rels)

    def test_get_relationships_returns_copy(self):
        """Test that get_relationships returns a copy."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-1", RelationshipType.REFERENCE)

        rels1 = element.get_relationships()
        rels2 = element.get_relationships()

        assert rels1 is not rels2

    def test_has_relationship_exists(self):
        """Test checking for existing relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)

        assert element.has_relationship("target-123")

    def test_has_relationship_not_exists(self):
        """Test checking for non-existing relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        assert not element.has_relationship("nonexistent-id")

    def test_has_relationship_with_type_filter(self):
        """Test checking for relationship with type filter."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)

        assert element.has_relationship("target-123", RelationshipType.REFERENCE)
        assert not element.has_relationship("target-123", RelationshipType.CAPTION)

    def test_remove_relationship(self):
        """Test removing a relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)
        element.add_relationship("target-456", RelationshipType.CAPTION)

        result = element.remove_relationship("target-123")

        assert result is True
        assert len(element.relationships) == 1
        assert not element.has_relationship("target-123")

    def test_remove_nonexistent_relationship(self):
        """Test removing non-existent relationship."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        result = element.remove_relationship("nonexistent-id")

        assert result is False

    def test_remove_all_relationships_to_target(self):
        """Test removing all relationships to a target."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)
        element.add_relationship("target-123", RelationshipType.CAPTION)
        element.add_relationship("target-456", RelationshipType.REFERENCE)

        result = element.remove_relationship("target-123")

        assert result is True
        assert len(element.relationships) == 1
        assert element.relationships[0].target_id == "target-456"

    def test_to_dict_minimal(self):
        """Test conversion to dictionary with minimal data."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        result = element.to_dict()

        assert result["id"] == element.id
        assert result["element_type"] == "text"
        assert result["position"] is None
        assert result["metadata"] == {}
        assert result["relationships"] == []
        assert result["confidence"] == 1.0
        assert "created_at" in result
        assert result["source_document"] is None

    def test_to_dict_with_position(self):
        """Test conversion to dictionary with position."""
        position = ContentPosition(page_number=1, char_start=0, char_end=100)
        element = ContentElement(
            element_type=ContentElementType.IMAGE, position=position
        )
        result = element.to_dict()

        assert result["position"]["page_number"] == 1
        assert result["position"]["char_start"] == 0
        assert result["position"]["char_end"] == 100

    def test_to_dict_with_relationships(self):
        """Test conversion to dictionary with relationships."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)
        result = element.to_dict()

        assert len(result["relationships"]) == 1
        assert result["relationships"][0]["target_id"] == "target-123"
        assert result["relationships"][0]["relationship_type"] == "reference"

    def test_to_dict_with_metadata(self):
        """Test conversion to dictionary with metadata."""
        metadata = {"language": "en", "source": "test"}
        element = ContentElement(
            element_type=ContentElementType.TEXT, metadata=metadata
        )
        result = element.to_dict()

        assert result["metadata"] == metadata

    def test_is_high_confidence_default(self):
        """Test is_high_confidence with default threshold."""
        high_conf = ContentElement(
            element_type=ContentElementType.TEXT, confidence=0.85
        )
        low_conf = ContentElement(element_type=ContentElementType.TEXT, confidence=0.75)

        assert high_conf.is_high_confidence()
        assert not low_conf.is_high_confidence()

    def test_is_high_confidence_custom_threshold(self):
        """Test is_high_confidence with custom threshold."""
        element = ContentElement(element_type=ContentElementType.TEXT, confidence=0.75)

        assert element.is_high_confidence(threshold=0.7)
        assert not element.is_high_confidence(threshold=0.8)

    def test_created_at_timestamp(self):
        """Test that created_at is set correctly."""
        before = datetime.now(UTC)
        element = ContentElement(element_type=ContentElementType.TEXT)
        after = datetime.now(UTC)

        assert before <= element.created_at <= after

    def test_default_element_type(self):
        """Test that default element type is UNKNOWN."""
        element = ContentElement()
        assert element.element_type == ContentElementType.UNKNOWN

    def test_multiple_relationships_same_target_different_types(self):
        """Test adding multiple relationships to same target with different types."""
        element = ContentElement(element_type=ContentElementType.TEXT)
        element.add_relationship("target-123", RelationshipType.REFERENCE)
        element.add_relationship("target-123", RelationshipType.CAPTION)

        assert len(element.relationships) == 2
        assert element.has_relationship("target-123", RelationshipType.REFERENCE)
        assert element.has_relationship("target-123", RelationshipType.CAPTION)
