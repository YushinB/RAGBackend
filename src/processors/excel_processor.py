"""
Excel Document Processor

This module implements a processor for Microsoft Excel files (.xlsx),
handling cell data, formulas, relationships, arrows, notes, and cross-worksheet references.
"""

import re
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.core.debug_logger import (
    PDFDebugLogger,
    get_production_safe_debug_logger,
)
from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.content_elements import ContentElementType
from src.models.relationship_manager import RelationshipManager
from src.models.table_content import TableContent

from .base import DataProcessor


class ExcelProcessor(DataProcessor):
    """
    Processor for Microsoft Excel documents (.xlsx).

    Handles extraction of cell data, tables, formulas, relationships,
    arrows/connections, notes, and cross-worksheet references.

    Attributes:
        supported_extensions: Set of file extensions ('.xlsx', '.xlsm')
        processor_name: Human-readable name ('Excel Processor')
    """

    supported_extensions: ClassVar[set[str]] = {"xlsx", "xlsm"}
    processor_name = "Excel Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the Excel processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - extract_formulas: Whether to extract formulas (default: True)
                - extract_comments: Whether to extract comments (default: True)
                - extract_named_ranges: Whether to extract named ranges (default: True)
                - include_hidden_sheets: Whether to process hidden sheets (default: False)
                - debug: Enable debug logging (default: False)
                - debug_level: Debug logging level (default: "DEBUG")
        """
        super().__init__(**config)
        self.extract_formulas = config.get("extract_formulas", True)
        self.extract_comments = config.get("extract_comments", True)
        self.extract_named_ranges = config.get("extract_named_ranges", True)
        self.include_hidden_sheets = config.get("include_hidden_sheets", False)

        # Initialize debug logging
        debug_enabled = config.get("debug", False)
        debug_level = config.get("debug_level", "DEBUG")
        if debug_enabled:
            self.debug_logger = PDFDebugLogger(
                level=debug_level, auto_detect_production=True
            )
            self.debug_logger.logger.info(
                "Excel Processor initialized with debug logging enabled"
            )
        else:
            self.debug_logger = get_production_safe_debug_logger()

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks file extension (.xlsx, .xlsm) and attempts to open as Excel workbook.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a valid Excel workbook, False otherwise
        """
        path = Path(file_path)

        # Check extension first
        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            return False

        # If file doesn't exist, rely on extension check only
        if not path.exists():
            return True

        # Try to open as Excel workbook
        try:
            load_workbook(str(path), read_only=True, data_only=False)
            return True
        except Exception:
            return False

    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the Excel workbook.

        Extracts cell values, sheet names, and notes as plain text.

        Args:
            file_path: Path to the Excel file

        Returns:
            Extracted text content with sheet and cell structure

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the workbook is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            wb = load_workbook(str(file_path), read_only=True, data_only=True)
            text_parts = []

            for sheet in wb.worksheets:
                # Skip hidden sheets if configured
                if sheet.sheet_state == "hidden" and not self.include_hidden_sheets:
                    continue

                text_parts.append(f"=== Sheet: {sheet.title} ===\n")

                # Extract cell values
                for row in sheet.iter_rows():
                    row_values = []
                    for cell in row:
                        if cell.value is not None:
                            row_values.append(str(cell.value))

                    if row_values:
                        text_parts.append(" | ".join(row_values))

                text_parts.append("\n")

            return "\n".join(text_parts)

        except Exception as e:
            raise ValueError(f"Failed to extract text from Excel workbook: {e}") from e

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including tables, formulas, relationships, and notes.

        This method performs comprehensive extraction including:
        - Cell data and tables
        - Formula dependencies
        - Cell notes and comments
        - Cross-worksheet references
        - Named ranges

        Args:
            file_path: Path to the Excel file
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with all extracted content and relationships

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the workbook is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            # Load workbook with formulas
            wb = load_workbook(str(file_path), data_only=False)
            relationship_manager = RelationshipManager()

            # Initialize content containers
            tables: list[TableContent] = []
            text_chunks: list[TextChunk] = []

            # Build document hierarchy
            hierarchy = self._extract_hierarchy(wb, document_id)

            # Process each worksheet
            for sheet_index, sheet in enumerate(wb.worksheets):
                # Skip hidden sheets if configured
                if sheet.sheet_state == "hidden" and not self.include_hidden_sheets:
                    continue

                # Extract tables from sheet
                sheet_tables = self._extract_tables_from_sheet(
                    sheet, sheet_index, document_id, wb
                )
                tables.extend(sheet_tables)
                for table in sheet_tables:
                    relationship_manager.register_element(table)

                # Extract text chunks for sheet
                sheet_text = self._extract_sheet_text(sheet)
                if sheet_text:
                    chunks = self.chunk_text(
                        sheet_text, chunk_size=512, chunk_overlap=50
                    )
                    # Add sheet metadata to chunks
                    for chunk in chunks:
                        chunk.metadata["sheet_name"] = sheet.title
                        chunk.metadata["sheet_index"] = sheet_index
                    text_chunks.extend(chunks)

            # Detect relationships (formula dependencies, etc.)
            relationships = relationship_manager.detect_all_relationships()

            # Create and return MultiModalContent
            return MultiModalContent(
                document_id=document_id,
                text_chunks=text_chunks,
                images=[],  # Excel images would require additional libraries
                tables=[table.id for table in tables],
                equations=[],  # Excel doesn't typically have equations like Word/PDF
                relationships={rel.source_id: [rel.target_id] for rel in relationships},
                hierarchy=[hierarchy],
                metadata={
                    "processor": self.processor_name,
                    "sheet_count": len(wb.worksheets),
                    "file_path": str(file_path),
                },
            )

        except Exception as e:
            raise ValueError(
                f"Failed to extract content from Excel workbook: {e}"
            ) from e

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.TABLE_CELL,
    ) -> list[TextChunk]:
        """
        Split text into chunks suitable for embedding and retrieval.

        For Excel, chunks typically represent table sections or sheet content.

        Args:
            text: The text content to chunk
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
            chunk_type: Type classification for the chunks (default: TABLE)

        Returns:
            List of TextChunk objects with appropriate metadata

        Raises:
            ValueError: If chunk_size <= chunk_overlap
        """
        if chunk_size <= chunk_overlap:
            raise ValueError("chunk_size must be greater than chunk_overlap")

        if not text or not text.strip():
            return []

        chunks: list[TextChunk] = []
        text = text.strip()

        # Split by double newlines (table sections)
        sections = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for section_text in sections:
            section = section_text.strip()
            if not section:
                continue

            # Check if adding this section exceeds chunk size
            if len(current_chunk) + len(section) > chunk_size and current_chunk:
                # Create chunk
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    chunk_type=chunk_type,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=chunk_index,
                        char_start=0,
                    ),
                    metadata={"source": "excel_processor", "chunk_index": chunk_index},
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + section
                else:
                    current_chunk = section
            # Add to current chunk
            elif current_chunk:
                current_chunk += "\n\n" + section
            else:
                current_chunk = section

        # Add final chunk
        if current_chunk:
            chunk = TextChunk(
                text=current_chunk.strip(),
                chunk_type=chunk_type,
                position=ContentPosition(
                    page_number=None,
                    paragraph_index=chunk_index,
                    char_start=0,
                ),
                metadata={"source": "excel_processor", "chunk_index": chunk_index},
            )
            chunks.append(chunk)

        return chunks

    def _extract_hierarchy(self, wb: Workbook, document_id: str) -> DocumentHierarchy:
        """
        Extract document hierarchy from Excel workbook structure.

        Args:
            wb: Workbook instance
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        return DocumentHierarchy(
            title=Path(wb.path).stem if hasattr(wb, "path") and wb.path else "Untitled",
            level=0,
            content_ids=[],
            children_ids=[],
            metadata={
                "sheet_names": [sheet.title for sheet in wb.worksheets],
                "sheet_count": len(wb.worksheets),
                "defined_names": (
                    list(wb.defined_names.definedName)
                    if hasattr(wb, "defined_names")
                    else []
                ),
            },
        )

    def _extract_sheet_text(self, sheet: Worksheet) -> str:
        """
        Extract text from a worksheet.

        Args:
            sheet: Worksheet instance

        Returns:
            Concatenated text from all cells
        """
        text_parts = []

        for row in sheet.iter_rows():
            row_values = []
            for cell in row:
                if cell.value is not None:
                    row_values.append(str(cell.value))

            if row_values:
                text_parts.append(" | ".join(row_values))

        return "\n".join(text_parts)

    def _extract_tables_from_sheet(
        self, sheet: Worksheet, sheet_index: int, document_id: str, wb: Workbook
    ) -> list[TableContent]:
        """
        Extract tables from an Excel worksheet.

        Args:
            sheet: Worksheet instance
            sheet_index: Sheet index
            document_id: Document identifier
            wb: Workbook instance for cross-sheet references

        Returns:
            List of TableContent objects
        """
        tables: list[TableContent] = []

        # Define table regions (simplified - could use actual Excel tables)
        # For now, treat entire sheet as one table if it has data

        # Find data boundaries
        max_row = sheet.max_row
        max_col = sheet.max_column

        if max_row < 2:  # Need at least header + 1 data row
            return tables

        # Extract data
        data_rows: list[list[str]] = []
        for row in sheet.iter_rows(min_row=1, max_row=max_row, max_col=max_col):
            row_data = []
            for cell in row:
                # Handle different data types
                if cell.value is None:
                    row_data.append("")
                else:
                    row_data.append(str(cell.value))
            data_rows.append(row_data)

        if not data_rows or len(data_rows) < 2:
            return tables

        # First row as headers
        headers = data_rows[0]
        rows = data_rows[1:]

        # Extract formula dependencies and comments
        formula_deps: list[str] = []
        arrows: list[dict[str, Any]] = []
        comments: dict[str, str] = {}

        if self.extract_formulas:
            formula_deps = self._extract_formula_dependencies(sheet)

        if self.extract_comments:
            comments = self._extract_comments(sheet)

        # Create TableContent
        table = TableContent(
            id=str(uuid4()),
            element_type=ContentElementType.TABLE,
            headers=headers,
            rows=rows,
            position=ContentPosition(
                page_number=sheet_index,
                paragraph_index=0,
                char_start=0,
            ),
            metadata={
                "source": "excel_sheet",
                "sheet_name": sheet.title,
                "sheet_index": sheet_index,
                "formula_dependencies": formula_deps,
                "arrows": arrows,  # Would require drawing extraction
                "comments": comments,
                "max_row": max_row,
                "max_col": max_col,
            },
        )
        tables.append(table)

        return tables

    def _extract_formula_dependencies(self, sheet: Worksheet) -> list[str]:
        """
        Extract formula dependencies from worksheet cells.

        Args:
            sheet: Worksheet instance

        Returns:
            List of formula dependency strings
        """
        dependencies = []

        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == "f" and cell.value:  # Formula cell
                    # Extract cell references from formula
                    formula = str(cell.value)
                    # Find cell references (e.g., A1, B2:C5, Sheet2!A1)
                    refs = re.findall(r"[A-Z]+\d+(?::[A-Z]+\d+)?", formula)
                    refs.extend(
                        re.findall(r"['\w]+![A-Z]+\d+", formula)
                    )  # Cross-sheet refs

                    if refs:
                        dep_str = f"{cell.coordinate} -> {', '.join(set(refs))}"
                        dependencies.append(dep_str)

        return dependencies

    def _extract_comments(self, sheet: Worksheet) -> dict[str, str]:
        """
        Extract comments from worksheet cells.

        Args:
            sheet: Worksheet instance

        Returns:
            Dictionary mapping cell coordinates to comment text
        """
        comments = {}

        for row in sheet.iter_rows():
            for cell in row:
                if hasattr(cell, "comment") and cell.comment:
                    comment_text = (
                        cell.comment.text
                        if hasattr(cell.comment, "text")
                        else str(cell.comment)
                    )
                    comments[cell.coordinate] = comment_text

        return comments
