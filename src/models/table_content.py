"""
Table Content Model

This module defines the TableContent class for handling tabular data extracted from documents.
TableContent inherits from ContentElement and adds table-specific attributes and functionality.
"""

from dataclasses import dataclass, field
from typing import Any

from .content_elements import ContentElement, ContentElementType


@dataclass
class CellReference:
    """
    Represents a reference to a specific cell in a table.

    Attributes:
        row: Row index (0-based)
        column: Column index (0-based)
        value: Cell value
        is_header: Whether this cell is part of the header row
    """

    row: int
    column: int
    value: Any = None
    is_header: bool = False

    def __post_init__(self) -> None:
        """Validate cell reference after creation."""
        if self.row < 0:
            raise ValueError("row index must be non-negative")
        if self.column < 0:
            raise ValueError("column index must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert cell reference to dictionary format."""
        return {
            "row": self.row,
            "column": self.column,
            "value": self.value,
            "is_header": self.is_header,
        }


@dataclass
class CellRelationship:
    """
    Represents a relationship between cells (e.g., Excel arrow connections).

    This captures dependencies like formulas, references, or visual indicators
    showing how cells relate to each other.

    Attributes:
        source: Source cell reference
        target: Target cell reference
        relationship_type: Type of relationship (e.g., 'formula', 'reference', 'arrow')
        description: Optional description of the relationship
        confidence: Confidence score for the relationship detection (0.0-1.0)
    """

    source: CellReference
    target: CellReference
    relationship_type: str = "reference"
    description: str | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Validate cell relationship after creation."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        """Convert cell relationship to dictionary format."""
        return {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "relationship_type": self.relationship_type,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class TableContent(ContentElement):
    """
    Represents a table content element extracted from a document.

    This class extends ContentElement to handle table-specific data including
    headers, rows, cells, captions, notes, and cell relationships.

    Attributes:
        headers: List of header values (None if no headers)
        rows: List of rows, where each row is a list of cell values
        caption: Caption or title associated with the table
        notes: Additional notes or footnotes for the table
        num_columns: Number of columns in the table
        num_rows: Number of data rows (excluding headers)
        cell_relationships: List of relationships between cells
        has_headers: Whether the table has a header row
        table_type: Type of table (e.g., 'data', 'layout', 'financial')

    Inherits from ContentElement:
        id: Unique identifier
        element_type: Automatically set to ContentElementType.TABLE
        position: Position in the document
        metadata: Additional metadata
        relationships: Relationships to other elements
        confidence: Extraction confidence score
        created_at: Creation timestamp
        source_document: Source document identifier

    Example:
        >>> table = TableContent(
        ...     headers=["Name", "Age", "City"],
        ...     rows=[
        ...         ["Alice", 30, "New York"],
        ...         ["Bob", 25, "London"]
        ...     ],
        ...     caption="Table 1: User Information",
        ...     position=ContentPosition(page_number=3)
        ... )
        >>> table.get_cell(0, 1)  # Get cell at row 0, column 1
        30
    """

    # Table-specific attributes
    headers: list[str] | None = None
    rows: list[list[Any]] = field(default_factory=list)
    caption: str | None = None
    notes: str | None = None
    num_columns: int | None = None
    num_rows: int | None = None
    cell_relationships: list[CellRelationship] = field(default_factory=list)
    has_headers: bool = False
    table_type: str | None = None

    def __post_init__(self) -> None:
        """Initialize and validate table content after creation."""
        # Set element type to TABLE
        self.element_type = ContentElementType.TABLE

        # Call parent validation
        super().__post_init__()

        # Validate table structure
        if self.headers is not None:
            self.has_headers = True
            if not self.headers:
                raise ValueError("headers list cannot be empty if provided")

        # Calculate dimensions if not provided
        if self.num_rows is None:
            self.num_rows = len(self.rows)

        if self.num_columns is None:
            if self.headers:
                self.num_columns = len(self.headers)
            elif self.rows:
                # Use the first row to determine column count
                self.num_columns = len(self.rows[0]) if self.rows[0] else 0
            else:
                self.num_columns = 0

        # Validate row consistency
        if self.headers and self.rows:
            expected_cols = len(self.headers)
            for i, row in enumerate(self.rows):
                if len(row) != expected_cols:
                    raise ValueError(
                        f"row {i} has {len(row)} columns, expected {expected_cols}"
                    )

    def get_cell(self, row: int, column: int) -> Any:
        """
        Get the value of a specific cell.

        Args:
            row: Row index (0-based)
            column: Column index (0-based)

        Returns:
            Cell value

        Raises:
            IndexError: If row or column index is out of bounds
        """
        if row < 0 or row >= len(self.rows):
            raise IndexError(f"row index {row} out of range (0-{len(self.rows) - 1})")

        if column < 0 or column >= len(self.rows[row]):
            raise IndexError(
                f"column index {column} out of range (0-{len(self.rows[row]) - 1})"
            )

        return self.rows[row][column]

    def set_cell(self, row: int, column: int, value: Any) -> None:
        """
        Set the value of a specific cell.

        Args:
            row: Row index (0-based)
            column: Column index (0-based)
            value: New cell value

        Raises:
            IndexError: If row or column index is out of bounds
        """
        if row < 0 or row >= len(self.rows):
            raise IndexError(f"row index {row} out of range (0-{len(self.rows) - 1})")

        if column < 0 or column >= len(self.rows[row]):
            raise IndexError(
                f"column index {column} out of range (0-{len(self.rows[row]) - 1})"
            )

        self.rows[row][column] = value

    def get_header(self, column: int) -> str | None:
        """
        Get the header value for a specific column.

        Args:
            column: Column index (0-based)

        Returns:
            Header value or None if no headers

        Raises:
            IndexError: If column index is out of bounds
        """
        if self.headers is None:
            return None

        if column < 0 or column >= len(self.headers):
            raise IndexError(
                f"column index {column} out of range (0-{len(self.headers) - 1})"
            )

        return self.headers[column]

    def get_row(self, row: int) -> list[Any]:
        """
        Get all values in a specific row.

        Args:
            row: Row index (0-based)

        Returns:
            List of cell values in the row

        Raises:
            IndexError: If row index is out of bounds
        """
        if row < 0 or row >= len(self.rows):
            raise IndexError(f"row index {row} out of range (0-{len(self.rows) - 1})")

        return self.rows[row].copy()

    def get_column(self, column: int) -> list[Any]:
        """
        Get all values in a specific column.

        Args:
            column: Column index (0-based)

        Returns:
            List of cell values in the column

        Raises:
            IndexError: If column index is out of bounds
        """
        if not self.rows:
            raise IndexError("table has no rows")

        if column < 0 or column >= len(self.rows[0]):
            raise IndexError(
                f"column index {column} out of range (0-{len(self.rows[0]) - 1})"
            )

        return [row[column] for row in self.rows if column < len(row)]

    def add_row(self, row: list[Any]) -> None:
        """
        Add a new row to the table.

        Args:
            row: List of cell values

        Raises:
            ValueError: If row length doesn't match table column count
        """
        expected_cols = self.num_columns or 0
        if expected_cols > 0 and len(row) != expected_cols:
            raise ValueError(f"row has {len(row)} columns, expected {expected_cols}")

        self.rows.append(row)
        self.num_rows = len(self.rows)

        # Update column count if this is the first row
        if self.num_columns == 0:
            self.num_columns = len(row)

    def add_cell_relationship(
        self,
        source_row: int,
        source_col: int,
        target_row: int,
        target_col: int,
        relationship_type: str = "reference",
        description: str | None = None,
        confidence: float = 1.0,
    ) -> None:
        """
        Add a relationship between two cells.

        This is useful for tracking dependencies like formulas, references,
        or visual indicators (e.g., Excel arrows).

        Args:
            source_row: Source cell row index
            source_col: Source cell column index
            target_row: Target cell row index
            target_col: Target cell column index
            relationship_type: Type of relationship
            description: Optional description
            confidence: Confidence score (0.0-1.0)

        Raises:
            IndexError: If cell indices are out of bounds
            ValueError: If confidence is not between 0.0 and 1.0
        """
        # Validate indices
        self.get_cell(source_row, source_col)  # Will raise IndexError if invalid
        self.get_cell(target_row, target_col)  # Will raise IndexError if invalid

        source_ref = CellReference(
            row=source_row,
            column=source_col,
            value=self.get_cell(source_row, source_col),
            is_header=False,
        )

        target_ref = CellReference(
            row=target_row,
            column=target_col,
            value=self.get_cell(target_row, target_col),
            is_header=False,
        )

        relationship = CellRelationship(
            source=source_ref,
            target=target_ref,
            relationship_type=relationship_type,
            description=description,
            confidence=confidence,
        )

        self.cell_relationships.append(relationship)

    def get_cell_relationships(self, row: int, column: int) -> list[CellRelationship]:
        """
        Get all relationships involving a specific cell.

        Args:
            row: Cell row index
            column: Cell column index

        Returns:
            List of cell relationships where the cell is source or target
        """
        relationships = []
        for rel in self.cell_relationships:
            if (rel.source.row == row and rel.source.column == column) or (
                rel.target.row == row and rel.target.column == column
            ):
                relationships.append(rel)
        return relationships

    def has_caption(self) -> bool:
        """
        Check if the table has a caption.

        Returns:
            True if caption exists and is non-empty, False otherwise
        """
        return bool(self.caption and self.caption.strip())

    def has_notes(self) -> bool:
        """
        Check if the table has notes.

        Returns:
            True if notes exist and are non-empty, False otherwise
        """
        return bool(self.notes and self.notes.strip())

    def is_empty(self) -> bool:
        """
        Check if the table is empty (no rows).

        Returns:
            True if table has no rows, False otherwise
        """
        return len(self.rows) == 0

    def get_dimensions(self) -> tuple[int, int]:
        """
        Get table dimensions.

        Returns:
            Tuple of (num_rows, num_columns)
        """
        return (self.num_rows or 0, self.num_columns or 0)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert table content to dictionary format.

        Returns:
            Dictionary representation of the table content
        """
        base_dict = super().to_dict()

        # Add table-specific fields
        table_dict = {
            "headers": self.headers,
            "rows": self.rows,
            "caption": self.caption,
            "notes": self.notes,
            "num_columns": self.num_columns,
            "num_rows": self.num_rows,
            "has_headers": self.has_headers,
            "table_type": self.table_type,
            "cell_relationships": [rel.to_dict() for rel in self.cell_relationships],
        }

        # Merge with base dictionary
        base_dict.update(table_dict)
        return base_dict

    def __repr__(self) -> str:
        """
        Return a string representation of the TableContent.

        Returns:
            String representation with key attributes
        """
        caption_preview = (
            f'"{self.caption[:30]}..."'
            if self.caption and len(self.caption) > 30
            else f'"{self.caption}"'
            if self.caption
            else "None"
        )
        return (
            f"TableContent(id={self.id[:8]}..., dims={self.num_rows}x{self.num_columns}, "
            f"headers={self.has_headers}, caption={caption_preview}, "
            f"relationships={len(self.cell_relationships)})"
        )
