"""
Relationship Preservation Algorithms

This module provides algorithms for detecting and preserving relationships
between content elements in documents. It includes specialized logic for:
- Figure-caption linking
- Table-reference association
- Excel cell arrow relationship tracking
- Cross-reference detection
"""

import re
from dataclasses import dataclass, field
from typing import Any

from .content_elements import (
    ContentElement,
    ContentElementType,
    ContentRelationship,
    RelationshipType,
)


@dataclass
class RelationshipDetectionConfig:
    """
    Configuration for relationship detection algorithms.

    Attributes:
        proximity_threshold: Maximum distance (in document units) for proximity-based detection
        confidence_threshold: Minimum confidence score to consider a relationship valid
        caption_patterns: List of regex patterns for caption detection
        reference_patterns: List of regex patterns for reference detection
        max_caption_distance: Maximum distance between figure/table and its caption
        enable_fuzzy_matching: Whether to use fuzzy matching for text-based detection
        case_sensitive: Whether text matching should be case-sensitive
    """

    proximity_threshold: int = 500
    confidence_threshold: float = 0.5
    caption_patterns: list[str] = field(
        default_factory=lambda: [
            r"^Figure\s+\d+[:.]\s*",
            r"^Fig\.\s*\d+[:.]\s*",
            r"^Table\s+\d+[:.]\s*",
            r"^Equation\s+\d+[:.]\s*",
            r"^Eq\.\s*\d+[:.]\s*",
        ]
    )
    reference_patterns: list[str] = field(
        default_factory=lambda: [
            r"(?:see|as shown in|refer to)\s+(?:Figure|Fig\.|Table|Equation|Eq\.)\s+\d+",
            r"(?:Figure|Fig\.|Table|Equation|Eq\.)\s+\d+",
        ]
    )
    max_caption_distance: int = 200
    enable_fuzzy_matching: bool = False
    case_sensitive: bool = False


class RelationshipManager:
    """
    Manages detection and preservation of relationships between content elements.

    This class provides algorithms for automatically detecting relationships
    between different types of content elements in documents.
    """

    def __init__(self, config: RelationshipDetectionConfig | None = None):
        """
        Initialize the relationship manager.

        Args:
            config: Configuration for relationship detection algorithms
        """
        self.config = config or RelationshipDetectionConfig()
        self._element_registry: dict[str, ContentElement] = {}

    def register_element(self, element: ContentElement) -> None:
        """
        Register a content element for relationship detection.

        Args:
            element: Content element to register
        """
        self._element_registry[element.id] = element

    def register_elements(self, elements: list[ContentElement]) -> None:
        """
        Register multiple content elements.

        Args:
            elements: List of content elements to register
        """
        for element in elements:
            self.register_element(element)

    def detect_all_relationships(self) -> list[ContentRelationship]:
        """
        Detect all relationships between registered elements.

        Returns:
            List of detected ContentRelationship objects
        """
        relationships: list[ContentRelationship] = []

        # Detect figure-caption relationships
        relationships.extend(self.detect_figure_caption_links())

        # Detect table-reference relationships
        relationships.extend(self.detect_table_reference_associations())

        # Detect proximity-based relationships
        relationships.extend(self.detect_proximity_relationships())

        # Detect hierarchical relationships
        relationships.extend(self.detect_hierarchical_relationships())

        return relationships

    def detect_figure_caption_links(self) -> list[ContentRelationship]:
        """
        Detect relationships between figures and their captions.

        This algorithm looks for caption-type elements near image elements
        and creates CAPTION relationships based on proximity and pattern matching.

        Returns:
            List of detected caption relationships
        """
        relationships: list[ContentRelationship] = []
        images = self._get_elements_by_type(ContentElementType.IMAGE)
        captions = self._get_elements_by_type(ContentElementType.CAPTION)
        text_elements = self._get_elements_by_type(ContentElementType.TEXT)

        # Process explicit caption elements
        for image in images:
            if image.position is None:
                continue

            # Find nearest caption
            nearest_caption = self._find_nearest_element(
                image, captions, max_distance=self.config.max_caption_distance
            )

            if nearest_caption:
                confidence = self._calculate_proximity_confidence(
                    image, nearest_caption, self.config.max_caption_distance
                )

                if confidence >= self.config.confidence_threshold:
                    rel = ContentRelationship(
                        source_id=nearest_caption.id,
                        target_id=image.id,
                        relationship_type=RelationshipType.CAPTION,
                        confidence=confidence,
                        metadata={
                            "detection_method": "proximity",
                            "distance": self._calculate_distance(
                                image, nearest_caption
                            ),
                        },
                    )
                    relationships.append(rel)
                    image.relationships.append(rel)

        # Also check text elements for caption patterns
        for image in images:
            if image.position is None:
                continue

            # Look for text elements matching caption patterns nearby
            for text_elem in text_elements:
                if text_elem.position is None:
                    continue

                if self._is_caption_text(text_elem):
                    distance = self._calculate_distance(image, text_elem)

                    if distance <= self.config.max_caption_distance:
                        confidence = self._calculate_proximity_confidence(
                            image, text_elem, self.config.max_caption_distance
                        )

                        if confidence >= self.config.confidence_threshold:
                            rel = ContentRelationship(
                                source_id=text_elem.id,
                                target_id=image.id,
                                relationship_type=RelationshipType.CAPTION,
                                confidence=confidence * 0.95,  # Slightly lower for text
                                metadata={
                                    "detection_method": "pattern_matching",
                                    "distance": distance,
                                },
                            )
                            relationships.append(rel)
                            image.relationships.append(rel)
                            break  # Only take the nearest caption-like text

        return relationships

    def detect_table_reference_associations(self) -> list[ContentRelationship]:
        """
        Detect relationships between tables and text that references them.

        This algorithm searches for text containing table references and
        creates REFERENCE relationships to the corresponding tables.

        Returns:
            List of detected reference relationships
        """
        relationships: list[ContentRelationship] = []
        tables = self._get_elements_by_type(ContentElementType.TABLE)
        text_elements = self._get_elements_by_type(ContentElementType.TEXT)

        for table in tables:
            # Extract table number/identifier from caption or metadata
            table_id = self._extract_table_identifier(table)
            if not table_id:
                continue

            # Search for references to this table in text elements
            for text_elem in text_elements:
                if self._contains_table_reference(text_elem, table_id):
                    confidence = 0.9  # High confidence for explicit references

                    # Adjust confidence based on proximity
                    if table.position and text_elem.position:
                        proximity_factor = self._calculate_proximity_confidence(
                            table, text_elem, self.config.proximity_threshold
                        )
                        confidence = min(
                            confidence, confidence * (0.8 + 0.2 * proximity_factor)
                        )

                    rel = ContentRelationship(
                        source_id=text_elem.id,
                        target_id=table.id,
                        relationship_type=RelationshipType.REFERENCE,
                        confidence=confidence,
                        metadata={
                            "detection_method": "reference_pattern",
                            "table_identifier": table_id,
                        },
                    )
                    relationships.append(rel)
                    text_elem.relationships.append(rel)

        return relationships

    def detect_excel_arrow_relationships(
        self, cell_elements: list[ContentElement]
    ) -> list[ContentRelationship]:
        """
        Detect relationships based on Excel cell arrows and dependencies.

        This algorithm analyzes cell metadata for arrow connections and
        formula dependencies to create DEPENDENCY relationships.

        Args:
            cell_elements: List of table cell content elements

        Returns:
            List of detected dependency relationships
        """
        relationships: list[ContentRelationship] = []

        for cell in cell_elements:
            # Check for arrow metadata (added by Excel processor)
            arrows = cell.metadata.get("arrows", [])
            for arrow_info in arrows:
                target_cell_id = arrow_info.get("target_cell_id")
                if target_cell_id:
                    rel = ContentRelationship(
                        source_id=cell.id,
                        target_id=target_cell_id,
                        relationship_type=RelationshipType.DEPENDENCY,
                        confidence=0.95,
                        metadata={
                            "detection_method": "excel_arrow",
                            "arrow_type": arrow_info.get("arrow_type", "unknown"),
                        },
                    )
                    relationships.append(rel)
                    cell.relationships.append(rel)

            # Check for formula dependencies
            formula_deps = cell.metadata.get("formula_dependencies", [])
            for dep_cell_id in formula_deps:
                rel = ContentRelationship(
                    source_id=cell.id,
                    target_id=dep_cell_id,
                    relationship_type=RelationshipType.DEPENDENCY,
                    confidence=1.0,  # Formula dependencies are explicit
                    metadata={
                        "detection_method": "formula_dependency",
                        "formula": cell.metadata.get("formula", ""),
                    },
                )
                relationships.append(rel)
                cell.relationships.append(rel)

        return relationships

    def detect_proximity_relationships(self) -> list[ContentRelationship]:
        """
        Detect relationships based on physical proximity in the document.

        Creates RELATED relationships between elements that are close together
        and likely semantically connected.

        Returns:
            List of detected proximity relationships
        """
        relationships: list[ContentRelationship] = []
        elements_with_position = [
            e for e in self._element_registry.values() if e.position is not None
        ]

        # Sort elements by position
        sorted_elements = sorted(
            elements_with_position,
            key=lambda e: (
                e.position.page_number or 0 if e.position else 0,
                e.position.paragraph_index or 0 if e.position else 0,
            ),
        )

        # Check consecutive elements for proximity relationships
        for i in range(len(sorted_elements) - 1):
            elem1 = sorted_elements[i]
            elem2 = sorted_elements[i + 1]

            distance = self._calculate_distance(elem1, elem2)

            if distance <= self.config.proximity_threshold:
                confidence = self._calculate_proximity_confidence(
                    elem1, elem2, self.config.proximity_threshold
                )

                if confidence >= self.config.confidence_threshold:
                    rel = ContentRelationship(
                        source_id=elem1.id,
                        target_id=elem2.id,
                        relationship_type=RelationshipType.RELATED,
                        confidence=confidence,
                        metadata={
                            "detection_method": "proximity",
                            "distance": distance,
                        },
                    )
                    relationships.append(rel)
                    elem1.relationships.append(rel)

        return relationships

    def detect_hierarchical_relationships(self) -> list[ContentRelationship]:
        """
        Detect parent-child and sibling relationships based on document hierarchy.

        Uses position information (section numbers, paragraph indices) to
        establish hierarchical relationships.

        Returns:
            List of detected hierarchical relationships
        """
        relationships: list[ContentRelationship] = []
        elements_with_position = [
            e for e in self._element_registry.values() if e.position is not None
        ]

        # Group elements by section
        sections: dict[str, list[ContentElement]] = {}
        for elem in elements_with_position:
            section = (
                elem.position.section_number or "root" if elem.position else "root"
            )
            if section not in sections:
                sections[section] = []
            sections[section].append(elem)

        # Detect parent-child relationships
        for section, elements in sections.items():
            if "." in str(section):  # Sub-section
                parent_section = str(section).rsplit(".", 1)[0]
                if parent_section in sections:
                    # Elements in sub-section are children of parent section elements
                    for child in elements:
                        for parent in sections[parent_section]:
                            if parent.element_type == ContentElementType.HEADING:
                                rel = ContentRelationship(
                                    source_id=parent.id,
                                    target_id=child.id,
                                    relationship_type=RelationshipType.PARENT_CHILD,
                                    confidence=0.9,
                                    metadata={
                                        "detection_method": "hierarchical",
                                        "parent_section": parent_section,
                                        "child_section": section,
                                    },
                                )
                                relationships.append(rel)
                                parent.relationships.append(rel)
                                break  # Only link to first heading in parent section

        # Detect sibling relationships
        for section, elements in sections.items():
            sorted_elems = sorted(
                elements,
                key=lambda e: e.position.paragraph_index or 0 if e.position else 0,
            )
            for i in range(len(sorted_elems) - 1):
                elem1 = sorted_elems[i]
                elem2 = sorted_elems[i + 1]

                if elem1.element_type == elem2.element_type:
                    rel = ContentRelationship(
                        source_id=elem1.id,
                        target_id=elem2.id,
                        relationship_type=RelationshipType.SIBLING,
                        confidence=0.85,
                        metadata={
                            "detection_method": "hierarchical",
                            "section": section,
                        },
                    )
                    relationships.append(rel)
                    elem1.relationships.append(rel)

        return relationships

    def _get_elements_by_type(
        self, element_type: ContentElementType
    ) -> list[ContentElement]:
        """Get all registered elements of a specific type."""
        return [
            e for e in self._element_registry.values() if e.element_type == element_type
        ]

    def _find_nearest_element(
        self,
        source: ContentElement,
        candidates: list[ContentElement],
        max_distance: int | None = None,
    ) -> ContentElement | None:
        """Find the nearest element from a list of candidates."""
        if not candidates or source.position is None:
            return None

        nearest = None
        min_distance = float("inf")

        for candidate in candidates:
            if candidate.position is None:
                continue

            distance = self._calculate_distance(source, candidate)
            if (
                max_distance is None or distance <= max_distance
            ) and distance < min_distance:
                min_distance = distance
                nearest = candidate

        return nearest

    def _calculate_distance(
        self, elem1: ContentElement, elem2: ContentElement
    ) -> float:
        """
        Calculate distance between two elements based on position.

        Uses page number, section, and paragraph indices to compute a distance metric.
        """
        if elem1.position is None or elem2.position is None:
            return float("inf")

        pos1 = elem1.position
        pos2 = elem2.position

        # Page distance (heavily weighted)
        page_diff = abs((pos1.page_number or 0) - (pos2.page_number or 0))
        page_distance = page_diff * 10000

        # Paragraph distance (moderately weighted)
        para_diff = abs((pos1.paragraph_index or 0) - (pos2.paragraph_index or 0))
        para_distance = para_diff * 100

        # Character distance (lightly weighted)
        char_distance = 0
        if pos1.char_start is not None and pos2.char_start is not None:
            char_distance = abs(pos1.char_start - pos2.char_start)

        return page_distance + para_distance + char_distance

    def _calculate_proximity_confidence(
        self, elem1: ContentElement, elem2: ContentElement, max_distance: int
    ) -> float:
        """
        Calculate confidence score based on proximity.

        Returns a value between 0.0 and 1.0, where closer elements have higher confidence.
        """
        distance = self._calculate_distance(elem1, elem2)

        if distance >= max_distance:
            return 0.0

        # Linear decay: confidence = 1.0 at distance 0, 0.0 at max_distance
        return 1.0 - (distance / max_distance)

    def _is_caption_text(self, element: ContentElement) -> bool:
        """Check if a text element matches caption patterns."""
        text = element.metadata.get("text", "")
        if not text:
            return False

        for pattern in self.config.caption_patterns:
            if re.match(
                pattern, text, re.IGNORECASE if not self.config.case_sensitive else 0
            ):
                return True

        return False

    def _extract_table_identifier(self, table: ContentElement) -> str | None:
        """Extract table identifier/number from table element."""
        # Check caption metadata
        caption = table.metadata.get("caption", "")
        if caption:
            match = re.search(r"Table\s+(\d+(?:\.\d+)?)", caption, re.IGNORECASE)
            if match:
                return match.group(1)

        # Check table_number metadata
        table_number = table.metadata.get("table_number")
        if table_number:
            return str(table_number)

        return None

    def _contains_table_reference(
        self, text_element: ContentElement, table_id: str
    ) -> bool:
        """Check if text element contains a reference to the specified table."""
        text = text_element.metadata.get("text", "")
        if not text:
            return False

        # Look for "Table X" patterns
        pattern = rf"Table\s+{re.escape(table_id)}\b"
        return bool(
            re.search(
                pattern, text, re.IGNORECASE if not self.config.case_sensitive else 0
            )
        )

    def get_relationship_statistics(self) -> dict[str, Any]:
        """
        Get statistics about detected relationships.

        Returns:
            Dictionary containing relationship counts and metrics
        """
        all_relationships: list[ContentRelationship] = []
        for element in self._element_registry.values():
            all_relationships.extend(element.relationships)

        # Count by type
        type_counts: dict[str, int] = {}
        for rel in all_relationships:
            rel_type = rel.relationship_type.value
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

        # Calculate average confidence
        avg_confidence = (
            sum(rel.confidence for rel in all_relationships) / len(all_relationships)
            if all_relationships
            else 0.0
        )

        # Count high-confidence relationships
        high_confidence_count = sum(
            1 for rel in all_relationships if rel.is_high_confidence()
        )

        return {
            "total_relationships": len(all_relationships),
            "total_elements": len(self._element_registry),
            "relationships_by_type": type_counts,
            "average_confidence": avg_confidence,
            "high_confidence_count": high_confidence_count,
            "high_confidence_percentage": (
                (high_confidence_count / len(all_relationships) * 100)
                if all_relationships
                else 0.0
            ),
        }

    def clear_registry(self) -> None:
        """Clear all registered elements."""
        self._element_registry.clear()
