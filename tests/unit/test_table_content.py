"""
Unit tests for TableContent model

Tests the TableContent class and related classes (CellReference, CellRelationship)
for proper functionality, validation, and edge cases.
"""

from datetime import UTC, datetime

import pytest

from src.models.base_models import ContentPosition
from src.models.content_elements import (
    ContentElement,
    ContentElementType,
    RelationshipType,
)
from src.models.table_content import (
    CellReference,
    CellRelationship,
    TableContent,
)


class TestCellReference:
    """Test cases for CellReference class."""

    def test_cell_reference_creation(self):
        """Test creating a basic cell reference."""
        cell_ref = CellReference(row=0, column=1, value="test")
        assert cell_ref.row == 0
        assert cell_ref.column == 1
        assert cell_ref.value == "test"
        assert cell_ref.is_header is False

    def test_cell_reference_with_header(self):
        """Test creating a header cell reference."""
        cell_ref = CellReference(row=0, column=0, value="Name", is_header=True)
        assert cell_ref.is_header is True

    def test_cell_reference_negative_row(self):
        """Test that negative row index raises ValueError."""
        with pytest.raises(ValueError, match=r"row index must be non-negative"):
            CellReference(row=-1, column=0)

    def test_cell_reference_negative_column(self):
        """Test that negative column index raises ValueError."""
        with pytest.raises(ValueError, match=r"column index must be non-negative"):
            CellReference(row=0, column=-1)

    def test_cell_reference_to_dict(self):
        """Test converting cell reference to dictionary."""
        cell_ref = CellReference(row=2, column=3, value=42, is_header=False)
        result = cell_ref.to_dict()

        assert result["row"] == 2
        assert result["column"] == 3
        assert result["value"] == 42
        assert result["is_header"] is False

    def test_cell_reference_none_value(self):
        """Test cell reference with None value."""
        cell_ref = CellReference(row=0, column=0, value=None)
        assert cell_ref.value is None

    def test_cell_reference_various_types(self):
        """Test cell reference with various value types."""
        # Integer
        ref1 = CellReference(row=0, column=0, value=123)
        assert ref1.value == 123

        # Float
        ref2 = CellReference(row=0, column=1, value=45.67)
        assert ref2.value == 45.67

        # String
        ref3 = CellReference(row=0, column=2, value="text")
        assert ref3.value == "text"

        # Boolean
        ref4 = CellReference(row=0, column=3, value=True)
        assert ref4.value is True


class TestCellRelationship:
    """Test cases for CellRelationship class."""

    def test_cell_relationship_creation(self):
        """Test creating a basic cell relationship."""
        source = CellReference(row=0, column=0, value="A1")
        target = CellReference(row=1, column=1, value="B2")

        rel = CellRelationship(source=source, target=target)
        assert rel.source == source
        assert rel.target == target
        assert rel.relationship_type == "reference"
        assert rel.confidence == 1.0
        assert rel.description is None

    def test_cell_relationship_with_type(self):
        """Test cell relationship with custom type."""
        source = CellReference(row=0, column=0)
        target = CellReference(row=0, column=1)

        rel = CellRelationship(
            source=source, target=target, relationship_type="formula"
        )
        assert rel.relationship_type == "formula"

    def test_cell_relationship_with_description(self):
        """Test cell relationship with description."""
        source = CellReference(row=0, column=0)
        target = CellReference(row=1, column=0)

        rel = CellRelationship(
            source=source, target=target, description="Sum formula dependency"
        )
        assert rel.description == "Sum formula dependency"

    def test_cell_relationship_confidence_validation(self):
        """Test that invalid confidence raises ValueError."""
        source = CellReference(row=0, column=0)
        target = CellReference(row=0, column=1)

        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            CellRelationship(source=source, target=target, confidence=1.5)

        with pytest.raises(
            ValueError, match=r"confidence must be between 0\.0 and 1\.0"
        ):
            CellRelationship(source=source, target=target, confidence=-0.1)

    def test_cell_relationship_to_dict(self):
        """Test converting cell relationship to dictionary."""
        source = CellReference(row=0, column=0, value=10)
        target = CellReference(row=1, column=0, value=20)

        rel = CellRelationship(
            source=source,
            target=target,
            relationship_type="arrow",
            description="Excel arrow indicator",
            confidence=0.95,
        )

        result = rel.to_dict()
        assert result["relationship_type"] == "arrow"
        assert result["description"] == "Excel arrow indicator"
        assert result["confidence"] == 0.95
        assert "source" in result
        assert "target" in result
        assert result["source"]["row"] == 0
        assert result["target"]["row"] == 1


class TestTableContentInitialization:
    """Test cases for TableContent initialization."""

    def test_basic_table_creation(self):
        """Test creating a basic table with headers and rows."""
        table = TableContent(headers=["Name", "Age"], rows=[["Alice", 30], ["Bob", 25]])

        assert table.element_type == ContentElementType.TABLE
        assert table.headers == ["Name", "Age"]
        assert len(table.rows) == 2
        assert table.num_rows == 2
        assert table.num_columns == 2
        assert table.has_headers is True

    def test_table_without_headers(self):
        """Test creating a table without headers."""
        table = TableContent(rows=[["A", "B"], ["C", "D"]])

        assert table.headers is None
        assert table.has_headers is False
        assert table.num_rows == 2
        assert table.num_columns == 2

    def test_table_with_caption(self):
        """Test creating a table with caption."""
        table = TableContent(
            headers=["Col1"], rows=[["data"]], caption="Table 1: Sample Data"
        )

        assert table.caption == "Table 1: Sample Data"
        assert table.has_caption() is True

    def test_table_with_notes(self):
        """Test creating a table with notes."""
        table = TableContent(rows=[["data"]], notes="* Some important note")

        assert table.notes == "* Some important note"
        assert table.has_notes() is True

    def test_empty_table(self):
        """Test creating an empty table."""
        table = TableContent()

        assert table.rows == []
        assert table.num_rows == 0
        assert table.num_columns == 0
        assert table.is_empty() is True

    def test_table_with_position(self):
        """Test creating a table with position information."""
        position = ContentPosition(page_number=5, bbox=(10, 20, 100, 200))
        table = TableContent(headers=["Col1"], rows=[["data"]], position=position)

        assert table.position == position
        assert table.position.page_number == 5

    def test_table_with_table_type(self):
        """Test creating a table with table_type."""
        table = TableContent(rows=[["data"]], table_type="financial")

        assert table.table_type == "financial"

    def test_empty_headers_validation(self):
        """Test that empty headers list raises ValueError."""
        with pytest.raises(ValueError, match=r"headers list cannot be empty"):
            TableContent(headers=[])

    def test_inconsistent_row_lengths(self):
        """Test that inconsistent row lengths raise ValueError."""
        with pytest.raises(ValueError, match=r"row 1 has 3 columns, expected 2"):
            TableContent(
                headers=["Col1", "Col2"],
                rows=[["A", "B"], ["C", "D", "E"]],  # Wrong number of columns
            )

    def test_table_auto_column_count(self):
        """Test that column count is auto-calculated from first row."""
        table = TableContent(rows=[["A", "B", "C"], ["D", "E", "F"]])

        assert table.num_columns == 3

    def test_table_with_metadata(self):
        """Test creating a table with metadata."""
        table = TableContent(
            rows=[["data"]], metadata={"source": "excel", "sheet": "Sheet1"}
        )

        assert table.metadata["source"] == "excel"
        assert table.metadata["sheet"] == "Sheet1"


class TestTableContentCellOperations:
    """Test cases for cell operations."""

    def test_get_cell(self):
        """Test getting a cell value."""
        table = TableContent(rows=[["A", "B"], ["C", "D"]])

        assert table.get_cell(0, 0) == "A"
        assert table.get_cell(0, 1) == "B"
        assert table.get_cell(1, 0) == "C"
        assert table.get_cell(1, 1) == "D"

    def test_get_cell_out_of_bounds_row(self):
        """Test that getting cell with invalid row raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError, match=r"row index 5 out of range"):
            table.get_cell(5, 0)

        with pytest.raises(IndexError, match=r"row index -1 out of range"):
            table.get_cell(-1, 0)

    def test_get_cell_out_of_bounds_column(self):
        """Test that getting cell with invalid column raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError, match=r"column index 5 out of range"):
            table.get_cell(0, 5)

        with pytest.raises(IndexError, match=r"column index -1 out of range"):
            table.get_cell(0, -1)

    def test_set_cell(self):
        """Test setting a cell value."""
        table = TableContent(rows=[["A", "B"]])

        table.set_cell(0, 0, "X")
        assert table.get_cell(0, 0) == "X"

        table.set_cell(0, 1, 99)
        assert table.get_cell(0, 1) == 99

    def test_set_cell_out_of_bounds(self):
        """Test that setting cell with invalid indices raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError, match=r"row index 5 out of range"):
            table.set_cell(5, 0, "X")

        with pytest.raises(IndexError, match=r"column index 5 out of range"):
            table.set_cell(0, 5, "X")

    def test_get_header(self):
        """Test getting header values."""
        table = TableContent(
            headers=["Name", "Age", "City"], rows=[["Alice", 30, "NYC"]]
        )

        assert table.get_header(0) == "Name"
        assert table.get_header(1) == "Age"
        assert table.get_header(2) == "City"

    def test_get_header_no_headers(self):
        """Test getting header when table has no headers."""
        table = TableContent(rows=[["A", "B"]])

        assert table.get_header(0) is None
        assert table.get_header(1) is None

    def test_get_header_out_of_bounds(self):
        """Test that getting header with invalid index raises IndexError."""
        table = TableContent(headers=["Col1", "Col2"], rows=[])

        with pytest.raises(IndexError, match=r"column index 5 out of range"):
            table.get_header(5)

    def test_get_row(self):
        """Test getting row values."""
        table = TableContent(rows=[["A", "B", "C"], ["D", "E", "F"]])

        row0 = table.get_row(0)
        assert row0 == ["A", "B", "C"]

        row1 = table.get_row(1)
        assert row1 == ["D", "E", "F"]

        # Verify returned list is a copy
        row0[0] = "X"
        assert table.get_cell(0, 0) == "A"

    def test_get_row_out_of_bounds(self):
        """Test that getting row with invalid index raises IndexError."""
        table = TableContent(rows=[["A"]])

        with pytest.raises(IndexError, match=r"row index 5 out of range"):
            table.get_row(5)

    def test_get_column(self):
        """Test getting column values."""
        table = TableContent(rows=[["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]])

        col0 = table.get_column(0)
        assert col0 == ["A", "D", "G"]

        col1 = table.get_column(1)
        assert col1 == ["B", "E", "H"]

        col2 = table.get_column(2)
        assert col2 == ["C", "F", "I"]

    def test_get_column_empty_table(self):
        """Test that getting column from empty table raises IndexError."""
        table = TableContent()

        with pytest.raises(IndexError, match=r"table has no rows"):
            table.get_column(0)

    def test_get_column_out_of_bounds(self):
        """Test that getting column with invalid index raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError, match=r"column index 5 out of range"):
            table.get_column(5)

    def test_add_row(self):
        """Test adding a row to the table."""
        table = TableContent(headers=["Col1", "Col2"], rows=[["A", "B"]])

        table.add_row(["C", "D"])
        assert len(table.rows) == 2
        assert table.num_rows == 2
        assert table.get_row(1) == ["C", "D"]

    def test_add_row_to_empty_table(self):
        """Test adding first row to empty table."""
        table = TableContent()

        table.add_row(["A", "B", "C"])
        assert len(table.rows) == 1
        assert table.num_rows == 1
        assert table.num_columns == 3

    def test_add_row_wrong_length(self):
        """Test that adding row with wrong length raises ValueError."""
        table = TableContent(headers=["Col1", "Col2"], rows=[["A", "B"]])

        with pytest.raises(ValueError, match=r"row has 3 columns, expected 2"):
            table.add_row(["C", "D", "E"])


class TestTableContentRelationships:
    """Test cases for cell relationships."""

    def test_add_cell_relationship(self):
        """Test adding a cell relationship."""
        table = TableContent(rows=[["A", "B"], ["C", "D"]])

        table.add_cell_relationship(
            source_row=0,
            source_col=0,
            target_row=1,
            target_col=1,
            relationship_type="formula",
        )

        assert len(table.cell_relationships) == 1
        rel = table.cell_relationships[0]
        assert rel.source.row == 0
        assert rel.source.column == 0
        assert rel.target.row == 1
        assert rel.target.column == 1
        assert rel.relationship_type == "formula"

    def test_add_cell_relationship_with_description(self):
        """Test adding cell relationship with description."""
        table = TableContent(rows=[["10", "20"], ["=A1+B1", ""]])

        table.add_cell_relationship(
            source_row=1,
            source_col=0,
            target_row=0,
            target_col=0,
            relationship_type="formula",
            description="Cell A2 references A1",
            confidence=0.98,
        )

        rel = table.cell_relationships[0]
        assert rel.description == "Cell A2 references A1"
        assert rel.confidence == 0.98

    def test_add_cell_relationship_invalid_source(self):
        """Test that invalid source cell raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError):
            table.add_cell_relationship(
                source_row=5, source_col=0, target_row=0, target_col=0
            )

    def test_add_cell_relationship_invalid_target(self):
        """Test that invalid target cell raises IndexError."""
        table = TableContent(rows=[["A", "B"]])

        with pytest.raises(IndexError):
            table.add_cell_relationship(
                source_row=0, source_col=0, target_row=0, target_col=5
            )

    def test_get_cell_relationships(self):
        """Test getting relationships for a specific cell."""
        table = TableContent(rows=[["A", "B"], ["C", "D"], ["E", "F"]])

        # Add multiple relationships
        table.add_cell_relationship(0, 0, 1, 0, "arrow")
        table.add_cell_relationship(0, 0, 0, 1, "reference")
        table.add_cell_relationship(2, 0, 1, 0, "formula")

        # Cell (0,0) is involved in 2 relationships
        rels_00 = table.get_cell_relationships(0, 0)
        assert len(rels_00) == 2

        # Cell (1,0) is involved in 2 relationships (as target and source)
        rels_10 = table.get_cell_relationships(1, 0)
        assert len(rels_10) == 2

        # Cell (2,1) has no relationships
        rels_21 = table.get_cell_relationships(2, 1)
        assert len(rels_21) == 0

    def test_cell_relationship_stores_values(self):
        """Test that cell relationships store cell values."""
        table = TableContent(rows=[["100", "200"], ["=A1+B1", "300"]])

        table.add_cell_relationship(1, 0, 0, 0, "formula")

        rel = table.cell_relationships[0]
        assert rel.source.value == "=A1+B1"
        assert rel.target.value == "100"


class TestTableContentMethods:
    """Test cases for table content methods."""

    def test_has_caption(self):
        """Test has_caption method."""
        table1 = TableContent(rows=[["A"]], caption="Table 1")
        assert table1.has_caption() is True

        table2 = TableContent(rows=[["A"]], caption="")
        assert table2.has_caption() is False

        table3 = TableContent(rows=[["A"]], caption="   ")
        assert table3.has_caption() is False

        table4 = TableContent(rows=[["A"]])
        assert table4.has_caption() is False

    def test_has_notes(self):
        """Test has_notes method."""
        table1 = TableContent(rows=[["A"]], notes="Important note")
        assert table1.has_notes() is True

        table2 = TableContent(rows=[["A"]], notes="")
        assert table2.has_notes() is False

        table3 = TableContent(rows=[["A"]], notes="   ")
        assert table3.has_notes() is False

        table4 = TableContent(rows=[["A"]])
        assert table4.has_notes() is False

    def test_is_empty(self):
        """Test is_empty method."""
        table1 = TableContent()
        assert table1.is_empty() is True

        table2 = TableContent(rows=[])
        assert table2.is_empty() is True

        table3 = TableContent(rows=[["A"]])
        assert table3.is_empty() is False

    def test_get_dimensions(self):
        """Test get_dimensions method."""
        table1 = TableContent(rows=[["A", "B"], ["C", "D"], ["E", "F"]])
        assert table1.get_dimensions() == (3, 2)

        table2 = TableContent()
        assert table2.get_dimensions() == (0, 0)


class TestTableContentSerialization:
    """Test cases for table serialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        table = TableContent(
            headers=["Name", "Age"], rows=[["Alice", 30]], caption="User Data"
        )

        result = table.to_dict()

        assert result["element_type"] == "table"  # ContentElementType enum value
        assert result["headers"] == ["Name", "Age"]
        assert result["rows"] == [["Alice", 30]]
        assert result["caption"] == "User Data"
        assert result["num_rows"] == 1
        assert result["num_columns"] == 2
        assert result["has_headers"] is True

    def test_to_dict_with_relationships(self):
        """Test to_dict with cell relationships."""
        table = TableContent(rows=[["A", "B"], ["C", "D"]])
        table.add_cell_relationship(0, 0, 1, 1, "arrow")

        result = table.to_dict()

        assert len(result["cell_relationships"]) == 1
        rel = result["cell_relationships"][0]
        assert rel["relationship_type"] == "arrow"
        assert "source" in rel
        assert "target" in rel

    def test_to_dict_empty_table(self):
        """Test to_dict for empty table."""
        table = TableContent()
        result = table.to_dict()

        assert result["rows"] == []
        assert result["num_rows"] == 0
        assert result["num_columns"] == 0
        assert result["cell_relationships"] == []

    def test_repr_basic(self):
        """Test __repr__ for basic table."""
        table = TableContent(
            headers=["Col1", "Col2"],
            rows=[["A", "B"], ["C", "D"]],
            caption="Sample Table",
        )

        repr_str = repr(table)
        assert "TableContent" in repr_str
        assert "2x2" in repr_str
        assert "headers=True" in repr_str
        assert "Sample Table" in repr_str

    def test_repr_long_caption(self):
        """Test __repr__ with long caption."""
        long_caption = "This is a very long caption that should be truncated"
        table = TableContent(rows=[["A"]], caption=long_caption)

        repr_str = repr(table)
        assert "..." in repr_str  # Caption should be truncated
        assert len(long_caption) > 30  # Ensure caption was actually long

    def test_repr_no_caption(self):
        """Test __repr__ without caption."""
        table = TableContent(rows=[["A", "B"]])
        repr_str = repr(table)

        assert "caption=None" in repr_str

    def test_repr_with_relationships(self):
        """Test __repr__ showing relationship count."""
        table = TableContent(rows=[["A", "B"], ["C", "D"]])
        table.add_cell_relationship(0, 0, 1, 1)
        table.add_cell_relationship(0, 1, 1, 0)

        repr_str = repr(table)
        assert "relationships=2" in repr_str


class TestTableContentEdgeCases:
    """Test cases for edge cases and special scenarios."""

    def test_table_with_none_values(self):
        """Test table with None cell values."""
        table = TableContent(headers=["Col1", "Col2"], rows=[["A", None], [None, "B"]])

        assert table.get_cell(0, 1) is None
        assert table.get_cell(1, 0) is None

    def test_table_with_mixed_types(self):
        """Test table with mixed value types."""
        table = TableContent(
            rows=[["text", 123, 45.67, True, None], [False, "more", 0, -1.5, "end"]]
        )

        assert table.get_cell(0, 0) == "text"
        assert table.get_cell(0, 1) == 123
        assert table.get_cell(0, 2) == 45.67
        assert table.get_cell(0, 3) is True
        assert table.get_cell(0, 4) is None

    def test_table_with_unicode(self):
        """Test table with unicode characters."""
        table = TableContent(
            headers=["名前", "年齢"],
            rows=[["太郎", "25"], ["花子", "30"]],
            caption="日本語テーブル",
        )

        assert table.get_header(0) == "名前"
        assert table.caption == "日本語テーブル"

    def test_table_with_large_data(self):
        """Test table with large number of rows."""
        rows = [[f"R{i}C{j}" for j in range(10)] for i in range(100)]
        table = TableContent(rows=rows)

        assert table.num_rows == 100
        assert table.num_columns == 10
        assert table.get_cell(99, 9) == "R99C9"

    def test_table_with_empty_strings(self):
        """Test table with empty string values."""
        table = TableContent(headers=["Col1", "Col2"], rows=[["", ""], ["A", ""]])

        assert table.get_cell(0, 0) == ""
        assert table.get_cell(0, 1) == ""
        assert table.get_cell(1, 1) == ""

    def test_table_relationship_confidence_boundaries(self):
        """Test cell relationships with boundary confidence values."""
        table = TableContent(rows=[["A", "B"]])

        # Minimum confidence
        table.add_cell_relationship(0, 0, 0, 1, confidence=0.0)
        assert table.cell_relationships[0].confidence == 0.0

        # Maximum confidence
        table.add_cell_relationship(0, 1, 0, 0, confidence=1.0)
        assert table.cell_relationships[1].confidence == 1.0

    def test_table_single_cell(self):
        """Test table with single cell."""
        table = TableContent(rows=[["single"]])

        assert table.num_rows == 1
        assert table.num_columns == 1
        assert table.get_cell(0, 0) == "single"
        assert table.get_row(0) == ["single"]
        assert table.get_column(0) == ["single"]


class TestTableContentInheritance:
    """Test cases verifying ContentElement inheritance."""

    def test_table_inherits_from_content_element(self):
        """Test that TableContent inherits ContentElement features."""
        table = TableContent(rows=[["A"]])
        assert isinstance(table, ContentElement)

    def test_table_has_content_element_attributes(self):
        """Test that table has all ContentElement attributes."""
        table = TableContent(rows=[["A"]], confidence=0.95, metadata={"key": "value"})

        # ContentElement attributes
        assert hasattr(table, "id")
        assert hasattr(table, "element_type")
        assert hasattr(table, "position")
        assert hasattr(table, "metadata")
        assert hasattr(table, "confidence")
        assert hasattr(table, "created_at")

        # Check values
        assert table.element_type == ContentElementType.TABLE
        assert table.confidence == 0.95
        assert table.metadata["key"] == "value"

    def test_table_relationships_from_base(self):
        """Test that table can use ContentElement relationship methods."""
        table = TableContent(rows=[["A"]])

        # Add a relationship using ContentElement method
        table.add_relationship(
            target_id="img_123",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.9,
        )

        assert len(table.relationships) == 1
        assert table.has_relationship("img_123")

    def test_table_created_at_timestamp(self):
        """Test that table has creation timestamp."""
        table = TableContent(rows=[["A"]])

        assert table.created_at is not None
        assert isinstance(table.created_at, datetime)
        assert table.created_at.tzinfo == UTC

    def test_table_to_dict_includes_base_fields(self):
        """Test that to_dict includes ContentElement fields."""
        table = TableContent(rows=[["A"]], metadata={"source": "pdf"})

        result = table.to_dict()

        # Base fields from ContentElement
        assert "id" in result
        assert "element_type" in result
        assert "confidence" in result
        assert "created_at" in result
        assert "metadata" in result

        # Table-specific fields
        assert "rows" in result
        assert "headers" in result
