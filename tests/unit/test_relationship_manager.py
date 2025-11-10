"""
Unit tests for RelationshipManager and relationship detection algorithms

Tests the relationship preservation algorithms for:
- Figure-caption linking
- Table-reference associations
- Excel cell arrow relationships
- Proximity-based relationships
- Hierarchical relationships
"""

from src.models.base_models import ContentPosition
from src.models.content_elements import (
    ContentElement,
    ContentElementType,
    RelationshipType,
)
from src.models.relationship_manager import (
    RelationshipDetectionConfig,
    RelationshipManager,
)


class TestRelationshipDetectionConfig:
    """Test cases for RelationshipDetectionConfig."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = RelationshipDetectionConfig()

        assert config.proximity_threshold == 500
        assert config.confidence_threshold == 0.5
        assert config.max_caption_distance == 200
        assert config.enable_fuzzy_matching is False
        assert config.case_sensitive is False
        assert len(config.caption_patterns) > 0
        assert len(config.reference_patterns) > 0

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = RelationshipDetectionConfig(
            proximity_threshold=1000,
            confidence_threshold=0.8,
            max_caption_distance=300,
            enable_fuzzy_matching=True,
            case_sensitive=True,
        )

        assert config.proximity_threshold == 1000
        assert config.confidence_threshold == 0.8
        assert config.max_caption_distance == 300
        assert config.enable_fuzzy_matching is True
        assert config.case_sensitive is True

    def test_caption_patterns_included(self):
        """Test that caption patterns include common formats."""
        config = RelationshipDetectionConfig()

        assert any("Figure" in p for p in config.caption_patterns)
        assert any("Table" in p for p in config.caption_patterns)
        assert any("Equation" in p for p in config.caption_patterns)


class TestRelationshipManagerBasics:
    """Test cases for basic RelationshipManager functionality."""

    def test_initialization_with_default_config(self):
        """Test manager initialization with default configuration."""
        manager = RelationshipManager()

        assert manager.config is not None
        assert isinstance(manager.config, RelationshipDetectionConfig)
        assert len(manager._element_registry) == 0

    def test_initialization_with_custom_config(self):
        """Test manager initialization with custom configuration."""
        config = RelationshipDetectionConfig(proximity_threshold=1000)
        manager = RelationshipManager(config)

        assert manager.config.proximity_threshold == 1000

    def test_register_single_element(self):
        """Test registering a single element."""
        manager = RelationshipManager()
        element = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1),
        )

        manager.register_element(element)

        assert len(manager._element_registry) == 1
        assert element.id in manager._element_registry

    def test_register_multiple_elements(self):
        """Test registering multiple elements at once."""
        manager = RelationshipManager()
        elements = [
            ContentElement(element_type=ContentElementType.TEXT),
            ContentElement(element_type=ContentElementType.IMAGE),
            ContentElement(element_type=ContentElementType.TABLE),
        ]

        manager.register_elements(elements)

        assert len(manager._element_registry) == 3

    def test_clear_registry(self):
        """Test clearing the element registry."""
        manager = RelationshipManager()
        elements = [
            ContentElement(element_type=ContentElementType.TEXT),
            ContentElement(element_type=ContentElementType.IMAGE),
        ]
        manager.register_elements(elements)

        manager.clear_registry()

        assert len(manager._element_registry) == 0


class TestFigureCaptionDetection:
    """Test cases for figure-caption relationship detection."""

    def test_detect_caption_by_proximity(self):
        """Test detecting caption based on proximity to image."""
        manager = RelationshipManager()

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        caption = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(page_number=1, paragraph_index=6),
            metadata={"text": "Figure 1: Test image"},
        )

        manager.register_elements([image, caption])
        relationships = manager.detect_figure_caption_links()

        assert len(relationships) > 0
        assert relationships[0].target_id == image.id
        assert relationships[0].source_id == caption.id
        assert relationships[0].relationship_type == RelationshipType.CAPTION

    def test_detect_caption_from_text_element(self):
        """Test detecting caption from text element with caption pattern."""
        manager = RelationshipManager()

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        text_caption = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=6),
            metadata={"text": "Figure 1: This is a test figure"},
        )

        manager.register_elements([image, text_caption])
        relationships = manager.detect_figure_caption_links()

        assert len(relationships) > 0
        caption_rels = [
            r for r in relationships if r.relationship_type == RelationshipType.CAPTION
        ]
        assert len(caption_rels) > 0

    def test_no_caption_detected_when_too_far(self):
        """Test that captions are not detected when too far from image."""
        config = RelationshipDetectionConfig(max_caption_distance=100)
        manager = RelationshipManager(config)

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=1),
        )

        caption = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(page_number=1, paragraph_index=20),  # Far away
            metadata={"text": "Figure 1: Test"},
        )

        manager.register_elements([image, caption])
        relationships = manager.detect_figure_caption_links()

        # Should have low or no relationships due to distance
        high_conf_rels = [r for r in relationships if r.confidence > 0.5]
        assert len(high_conf_rels) == 0

    def test_multiple_images_with_captions(self):
        """Test detecting captions for multiple images."""
        manager = RelationshipManager()

        image1 = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        caption1 = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(page_number=1, paragraph_index=6),
            metadata={"text": "Figure 1: First image"},
        )

        image2 = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=10),
        )

        caption2 = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(page_number=1, paragraph_index=11),
            metadata={"text": "Figure 2: Second image"},
        )

        manager.register_elements([image1, caption1, image2, caption2])
        relationships = manager.detect_figure_caption_links()

        assert len(relationships) >= 2


class TestTableReferenceDetection:
    """Test cases for table-reference relationship detection."""

    def test_detect_table_reference_in_text(self):
        """Test detecting reference to table in text element."""
        manager = RelationshipManager()

        table = ContentElement(
            element_type=ContentElementType.TABLE,
            position=ContentPosition(page_number=2),
            metadata={"caption": "Table 1: Test data", "table_number": "1"},
        )

        text = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=2),
            metadata={"text": "As shown in Table 1, the results indicate..."},
        )

        manager.register_elements([table, text])
        relationships = manager.detect_table_reference_associations()

        assert len(relationships) > 0
        assert relationships[0].target_id == table.id
        assert relationships[0].source_id == text.id
        assert relationships[0].relationship_type == RelationshipType.REFERENCE

    def test_no_reference_without_table_number(self):
        """Test that no reference is detected without table identifier."""
        manager = RelationshipManager()

        table = ContentElement(
            element_type=ContentElementType.TABLE,
            position=ContentPosition(page_number=2),
            metadata={},  # No caption or table_number
        )

        text = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=2),
            metadata={"text": "As shown in Table 1, the results indicate..."},
        )

        manager.register_elements([table, text])
        relationships = manager.detect_table_reference_associations()

        assert len(relationships) == 0

    def test_multiple_references_to_same_table(self):
        """Test detecting multiple references to the same table."""
        manager = RelationshipManager()

        table = ContentElement(
            element_type=ContentElementType.TABLE,
            position=ContentPosition(page_number=2),
            metadata={"table_number": "3"},
        )

        text1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=2),
            metadata={"text": "Table 3 shows the data"},
        )

        text2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=3),
            metadata={"text": "Referring back to Table 3, we see..."},
        )

        manager.register_elements([table, text1, text2])
        relationships = manager.detect_table_reference_associations()

        assert len(relationships) >= 2

    def test_decimal_table_numbers(self):
        """Test detecting references with decimal table numbers."""
        manager = RelationshipManager()

        table = ContentElement(
            element_type=ContentElementType.TABLE,
            position=ContentPosition(page_number=2),
            metadata={"caption": "Table 2.3: Test data", "table_number": "2.3"},
        )

        text = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=2),
            metadata={"text": "See Table 2.3 for details"},
        )

        manager.register_elements([table, text])
        relationships = manager.detect_table_reference_associations()

        assert len(relationships) > 0


class TestExcelArrowRelationships:
    """Test cases for Excel cell arrow relationship detection."""

    def test_detect_excel_arrow_dependency(self):
        """Test detecting dependency from Excel arrow metadata."""
        manager = RelationshipManager()

        cell1 = ContentElement(
            element_type=ContentElementType.TABLE,
            metadata={
                "cell_type": "data",
                "arrows": [
                    {"target_cell_id": "cell-target-123", "arrow_type": "dependency"}
                ],
            },
        )

        cell2 = ContentElement(
            id="cell-target-123",
            element_type=ContentElementType.TABLE,
            metadata={"cell_type": "data"},
        )

        relationships = manager.detect_excel_arrow_relationships([cell1, cell2])

        assert len(relationships) > 0
        assert relationships[0].source_id == cell1.id
        assert relationships[0].target_id == "cell-target-123"
        assert relationships[0].relationship_type == RelationshipType.DEPENDENCY

    def test_detect_formula_dependencies(self):
        """Test detecting dependencies from formula metadata."""
        manager = RelationshipManager()

        cell1 = ContentElement(
            element_type=ContentElementType.TABLE,
            metadata={
                "formula": "=SUM(A1:A10)",
                "formula_dependencies": ["cell-a1", "cell-a2", "cell-a3"],
            },
        )

        relationships = manager.detect_excel_arrow_relationships([cell1])

        assert len(relationships) == 3
        assert all(
            r.relationship_type == RelationshipType.DEPENDENCY for r in relationships
        )
        assert all(r.confidence == 1.0 for r in relationships)

    def test_multiple_arrows_per_cell(self):
        """Test detecting multiple arrow dependencies from one cell."""
        manager = RelationshipManager()

        cell = ContentElement(
            element_type=ContentElementType.TABLE,
            metadata={
                "arrows": [
                    {"target_cell_id": "target-1", "arrow_type": "flow"},
                    {"target_cell_id": "target-2", "arrow_type": "dependency"},
                ],
            },
        )

        relationships = manager.detect_excel_arrow_relationships([cell])

        assert len(relationships) == 2

    def test_empty_arrow_metadata(self):
        """Test that cells without arrow metadata produce no relationships."""
        manager = RelationshipManager()

        cell = ContentElement(
            element_type=ContentElementType.TABLE,
            metadata={"cell_type": "data"},
        )

        relationships = manager.detect_excel_arrow_relationships([cell])

        assert len(relationships) == 0


class TestProximityRelationships:
    """Test cases for proximity-based relationship detection."""

    def test_detect_proximity_relationships(self):
        """Test detecting relationships based on element proximity."""
        manager = RelationshipManager()

        elem1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        elem2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=6),
        )

        manager.register_elements([elem1, elem2])
        relationships = manager.detect_proximity_relationships()

        assert len(relationships) > 0
        assert relationships[0].relationship_type == RelationshipType.RELATED

    def test_no_proximity_relationship_across_pages(self):
        """Test that proximity relationships don't span distant pages."""
        config = RelationshipDetectionConfig(proximity_threshold=500)
        manager = RelationshipManager(config)

        elem1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        elem2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=10, paragraph_index=5),
        )

        manager.register_elements([elem1, elem2])
        relationships = manager.detect_proximity_relationships()

        # Should not create relationship due to page distance
        assert len(relationships) == 0

    def test_proximity_confidence_decreases_with_distance(self):
        """Test that confidence decreases as distance increases."""
        manager = RelationshipManager()

        elem1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )

        elem2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=6),
        )

        elem3 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=10),
        )

        manager.register_elements([elem1, elem2, elem3])
        relationships = manager.detect_proximity_relationships()

        # Find relationships involving elem1
        rel_to_elem2 = next((r for r in relationships if r.target_id == elem2.id), None)
        rel_to_elem3 = next((r for r in relationships if r.target_id == elem3.id), None)

        if rel_to_elem2 and rel_to_elem3:
            assert rel_to_elem2.confidence > rel_to_elem3.confidence


class TestHierarchicalRelationships:
    """Test cases for hierarchical relationship detection."""

    def test_detect_parent_child_relationships(self):
        """Test detecting parent-child relationships from section hierarchy."""
        manager = RelationshipManager()

        heading = ContentElement(
            element_type=ContentElementType.HEADING,
            position=ContentPosition(page_number=1, section_number="2"),
        )

        text = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, section_number="2.1"),
        )

        manager.register_elements([heading, text])
        relationships = manager.detect_hierarchical_relationships()

        parent_child_rels = [
            r
            for r in relationships
            if r.relationship_type == RelationshipType.PARENT_CHILD
        ]
        assert len(parent_child_rels) > 0

    def test_detect_sibling_relationships(self):
        """Test detecting sibling relationships in same section."""
        manager = RelationshipManager()

        text1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(
                page_number=1, section_number="2.1", paragraph_index=5
            ),
        )

        text2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(
                page_number=1, section_number="2.1", paragraph_index=6
            ),
        )

        manager.register_elements([text1, text2])
        relationships = manager.detect_hierarchical_relationships()

        sibling_rels = [
            r for r in relationships if r.relationship_type == RelationshipType.SIBLING
        ]
        assert len(sibling_rels) > 0

    def test_no_sibling_relationship_for_different_types(self):
        """Test that sibling relationships require same element type."""
        manager = RelationshipManager()

        text = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(
                page_number=1, section_number="2.1", paragraph_index=5
            ),
        )

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(
                page_number=1, section_number="2.1", paragraph_index=6
            ),
        )

        manager.register_elements([text, image])
        relationships = manager.detect_hierarchical_relationships()

        sibling_rels = [
            r for r in relationships if r.relationship_type == RelationshipType.SIBLING
        ]
        # Should not create sibling relationship between different types
        assert len(sibling_rels) == 0


class TestRelationshipStatistics:
    """Test cases for relationship statistics."""

    def test_statistics_with_no_relationships(self):
        """Test statistics when no relationships exist."""
        manager = RelationshipManager()

        elem = ContentElement(element_type=ContentElementType.TEXT)
        manager.register_element(elem)

        stats = manager.get_relationship_statistics()

        assert stats["total_relationships"] == 0
        assert stats["total_elements"] == 1
        assert stats["average_confidence"] == 0.0

    def test_statistics_with_relationships(self):
        """Test statistics calculation with relationships."""
        manager = RelationshipManager()

        elem1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )
        elem2 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(page_number=1, paragraph_index=6),
        )

        manager.register_elements([elem1, elem2])
        manager.detect_proximity_relationships()

        stats = manager.get_relationship_statistics()

        assert stats["total_relationships"] > 0
        assert stats["total_elements"] == 2
        assert 0.0 <= stats["average_confidence"] <= 1.0

    def test_statistics_relationship_type_counts(self):
        """Test that statistics include counts by relationship type."""
        manager = RelationshipManager()

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(page_number=1, paragraph_index=5),
        )
        caption = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(page_number=1, paragraph_index=6),
            metadata={"text": "Figure 1: Test"},
        )

        manager.register_elements([image, caption])
        manager.detect_figure_caption_links()

        stats = manager.get_relationship_statistics()

        assert "relationships_by_type" in stats
        assert isinstance(stats["relationships_by_type"], dict)

    def test_statistics_high_confidence_percentage(self):
        """Test high confidence percentage calculation."""
        manager = RelationshipManager()

        elem = ContentElement(element_type=ContentElementType.TEXT)
        elem.add_relationship(
            target_id="target-1",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.95,
        )
        elem.add_relationship(
            target_id="target-2",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.5,
        )

        manager.register_element(elem)
        stats = manager.get_relationship_statistics()

        assert stats["high_confidence_count"] == 1
        assert 0.0 <= stats["high_confidence_percentage"] <= 100.0


class TestIntegrationScenarios:
    """Test cases for complete relationship detection scenarios."""

    def test_document_with_multiple_relationship_types(self):
        """Test detecting all relationship types in a complex document."""
        manager = RelationshipManager()

        # Create a mini document structure
        heading = ContentElement(
            element_type=ContentElementType.HEADING,
            position=ContentPosition(page_number=1, section_number="1"),
        )

        text1 = ContentElement(
            element_type=ContentElementType.TEXT,
            position=ContentPosition(
                page_number=1, section_number="1.1", paragraph_index=2
            ),
            metadata={"text": "As shown in Table 1, the results are clear."},
        )

        table = ContentElement(
            element_type=ContentElementType.TABLE,
            position=ContentPosition(
                page_number=1, section_number="1.1", paragraph_index=3
            ),
            metadata={"table_number": "1", "caption": "Table 1: Results"},
        )

        image = ContentElement(
            element_type=ContentElementType.IMAGE,
            position=ContentPosition(
                page_number=2, section_number="1.2", paragraph_index=5
            ),
        )

        caption = ContentElement(
            element_type=ContentElementType.CAPTION,
            position=ContentPosition(
                page_number=2, section_number="1.2", paragraph_index=6
            ),
            metadata={"text": "Figure 1: Test image"},
        )

        manager.register_elements([heading, text1, table, image, caption])

        # Detect all relationships
        all_rels = manager.detect_all_relationships()

        # Should have multiple types of relationships
        rel_types = {r.relationship_type for r in all_rels}
        assert len(rel_types) > 1

        # Should have caption relationship
        caption_rels = [
            r for r in all_rels if r.relationship_type == RelationshipType.CAPTION
        ]
        assert len(caption_rels) > 0

        # Should have reference relationship
        ref_rels = [
            r for r in all_rels if r.relationship_type == RelationshipType.REFERENCE
        ]
        assert len(ref_rels) > 0

    def test_clearing_and_reusing_manager(self):
        """Test that manager can be cleared and reused."""
        manager = RelationshipManager()

        # First batch
        elem1 = ContentElement(element_type=ContentElementType.TEXT)
        manager.register_element(elem1)
        assert len(manager._element_registry) == 1

        # Clear and reuse
        manager.clear_registry()
        assert len(manager._element_registry) == 0

        # Second batch
        elem2 = ContentElement(element_type=ContentElementType.IMAGE)
        manager.register_element(elem2)
        assert len(manager._element_registry) == 1
        assert elem2.id in manager._element_registry
        assert elem1.id not in manager._element_registry
