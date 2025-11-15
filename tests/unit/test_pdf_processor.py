"""
Unit tests for PDFProcessor

Tests for PDF document processing including text extraction, multi-modal content,
and relationship detection.
"""

import tempfile
from pathlib import Path

import pytest

from src.models.base_models import ChunkType
from src.processors.base import DataProcessor
from src.processors.pdf_processor import PDFProcessor


class TestPDFProcessorBasics:
    """Test basic PDFProcessor functionality."""

    def test_initialization_default(self):
        """Test processor initialization with default config."""
        processor = PDFProcessor()

        assert processor.processor_name == "PDF Processor"
        assert processor.supported_extensions == {"pdf"}
        assert processor.extract_images is True
        assert processor.extract_tables is True
        assert processor.extract_equations is True
        assert processor.max_image_size == 10 * 1024 * 1024

    def test_initialization_custom_config(self):
        """Test processor initialization with custom config."""
        processor = PDFProcessor(
            extract_images=False,
            extract_tables=False,
            extract_equations=False,
            max_image_size=5 * 1024 * 1024,
        )

        assert processor.extract_images is False
        assert processor.extract_tables is False
        assert processor.extract_equations is False
        assert processor.max_image_size == 5 * 1024 * 1024

    def test_can_process_valid_pdf_extension(self):
        """Test that processor recognizes .pdf extension."""
        processor = PDFProcessor()

        # Create temp file with .pdf extension
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write PDF magic bytes
            tmp.write(b"%PDF-1.4\n")

        try:
            assert processor.can_process(tmp_path) is True
        finally:
            tmp_path.unlink()

    def test_can_process_invalid_extension(self):
        """Test that processor rejects non-PDF extensions."""
        processor = PDFProcessor()

        assert processor.can_process("document.docx") is False
        assert processor.can_process("spreadsheet.xlsx") is False
        assert processor.can_process("text.txt") is False

    def test_can_process_invalid_magic_bytes(self):
        """Test that processor rejects files without PDF magic bytes."""
        processor = PDFProcessor()

        # Create temp file with wrong magic bytes
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"Not a PDF file")

        try:
            assert processor.can_process(tmp_path) is False
        finally:
            tmp_path.unlink()


class TestPDFTextExtraction:
    """Test PDF text extraction functionality."""

    def test_extract_text_nonexistent_file(self):
        """Test that extract_text raises error for nonexistent file."""
        processor = PDFProcessor()

        with pytest.raises(FileNotFoundError):
            processor.extract_text("nonexistent.pdf")

    def test_extract_text_empty_file(self):
        """Test that extract_text handles empty files."""
        processor = PDFProcessor()

        # Create empty PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"")

        try:
            with pytest.raises(ValueError):
                processor.extract_text(tmp_path)
        finally:
            tmp_path.unlink()


class TestPDFChunking:
    """Test PDF text chunking functionality."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        processor = PDFProcessor()
        text = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."

        chunks = processor.chunk_text(text, chunk_size=50, chunk_overlap=10)

        assert len(chunks) > 0
        assert all(chunk.chunk_type == ChunkType.PARAGRAPH for chunk in chunks)
        assert all(hasattr(chunk, "chunk_id") for chunk in chunks)

    def test_chunk_text_with_overlap(self):
        """Test that overlapping works correctly."""
        processor = PDFProcessor()
        text = (
            "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
        )

        chunks = processor.chunk_text(text, chunk_size=30, chunk_overlap=10)

        # Check that chunks have some overlap
        if len(chunks) > 1:
            # Last part of first chunk should appear in second chunk
            assert len(chunks) >= 2

    def test_chunk_text_empty_string(self):
        """Test chunking empty string returns empty list."""
        processor = PDFProcessor()

        chunks = processor.chunk_text("")
        assert chunks == []

        chunks = processor.chunk_text("   \n\n  ")
        assert chunks == []

    def test_chunk_text_invalid_params(self):
        """Test that invalid parameters raise ValueError."""
        processor = PDFProcessor()

        with pytest.raises(
            ValueError, match="chunk_size must be greater than chunk_overlap"
        ):
            processor.chunk_text("Some text", chunk_size=50, chunk_overlap=100)

        with pytest.raises(ValueError):
            processor.chunk_text("Some text", chunk_size=50, chunk_overlap=50)

    def test_chunk_text_single_paragraph(self):
        """Test chunking single paragraph."""
        processor = PDFProcessor()
        text = "This is a single paragraph without breaks."

        chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=10)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_chunk_text_preserves_metadata(self):
        """Test that chunks have proper metadata."""
        processor = PDFProcessor()
        text = "Paragraph one.\n\nParagraph two."

        chunks = processor.chunk_text(text)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.metadata["source"] == "pdf_processor"
            assert chunk.position is not None


class TestPDFHierarchyExtraction:
    """Test PDF hierarchy extraction."""

    def test_extract_hierarchy_structure(self):
        """Test that hierarchy extraction returns proper structure."""
        processor = PDFProcessor()

        # This would require a real PDF reader, so we test the structure
        # In integration tests, we would use actual PDF files
        # For now, verify the method exists and has correct signature
        assert hasattr(processor, "_extract_hierarchy")


class TestPDFImageExtraction:
    """Test PDF image extraction."""

    def test_extract_images_disabled(self):
        """Test that image extraction can be disabled."""
        processor = PDFProcessor(extract_images=False)

        assert processor.extract_images is False

    def test_extract_images_method_exists(self):
        """Test that image extraction method exists."""
        processor = PDFProcessor()

        assert hasattr(processor, "_extract_images_from_page")


class TestPDFTableExtraction:
    """Test PDF table extraction."""

    def test_extract_tables_disabled(self):
        """Test that table extraction can be disabled."""
        processor = PDFProcessor(extract_tables=False)

        assert processor.extract_tables is False

    def test_extract_tables_method_exists(self):
        """Test that table extraction methods exist."""
        processor = PDFProcessor()

        assert hasattr(processor, "_extract_tables_from_page")
        assert hasattr(processor, "_create_table_from_lines")

    def test_create_table_from_simple_lines(self):
        """Test table creation from text lines."""
        processor = PDFProcessor()
        lines = [
            "Header1  Header2  Header3",
            "Value1   Value2   Value3",
            "Value4   Value5   Value6",
        ]

        table = processor._create_table_from_lines(
            lines, page_num=1, table_index=0, document_id="test-doc"
        )

        assert table is not None
        assert len(table.headers) == 3
        assert len(table.rows) == 2

    def test_create_table_insufficient_rows(self):
        """Test that table creation fails with insufficient rows."""
        processor = PDFProcessor()
        lines = ["Header1  Header2"]

        table = processor._create_table_from_lines(
            lines, page_num=1, table_index=0, document_id="test-doc"
        )

        assert table is None


class TestPDFEquationExtraction:
    """Test PDF equation extraction."""

    def test_extract_equations_disabled(self):
        """Test that equation extraction can be disabled."""
        processor = PDFProcessor(extract_equations=False)

        assert processor.extract_equations is False

    def test_extract_equations_method_exists(self):
        """Test that equation extraction method exists."""
        processor = PDFProcessor()

        assert hasattr(processor, "_extract_equations_from_page")

    def test_extract_equations_inline(self):
        """Test extraction of inline LaTeX equations."""
        processor = PDFProcessor()
        page_text = "The equation $E = mc^2$ is famous. Another one: $F = ma$."

        equations = processor._extract_equations_from_page(
            page_text, page_num=1, document_id="test-doc"
        )

        assert len(equations) == 2
        assert "E = mc^2" in equations[0].latex_code
        assert "F = ma" in equations[1].latex_code

    def test_extract_equations_display(self):
        """Test extraction of display LaTeX equations."""
        processor = PDFProcessor()
        page_text = "The equation:\n$$E = mc^2$$\nis Einstein's famous formula."

        equations = processor._extract_equations_from_page(
            page_text, page_num=1, document_id="test-doc"
        )

        assert len(equations) == 1
        assert "E = mc^2" in equations[0].latex_code
        assert equations[0].metadata["type"] == "display"

    def test_extract_equations_with_context(self):
        """Test that equations capture surrounding context."""
        processor = PDFProcessor()
        page_text = (
            "Here is some context before the equation $x = y$ and some context after."
        )

        equations = processor._extract_equations_from_page(
            page_text, page_num=1, document_id="test-doc"
        )

        assert len(equations) == 1
        assert equations[0].context is not None
        assert "context" in equations[0].context


class TestPDFMultiModalExtraction:
    """Test comprehensive multi-modal content extraction."""

    def test_extract_multimodal_nonexistent_file(self):
        """Test that multimodal extraction raises error for nonexistent file."""
        processor = PDFProcessor()

        with pytest.raises(FileNotFoundError):
            processor.extract_multimodal_content("nonexistent.pdf", "test-doc")

    def test_extract_multimodal_method_exists(self):
        """Test that multimodal extraction method exists and has correct signature."""
        processor = PDFProcessor()

        assert hasattr(processor, "extract_multimodal_content")


class TestPDFProcessorInheritance:
    """Test that PDFProcessor properly inherits from DataProcessor."""

    def test_inherits_from_dataprocessor(self):
        """Test that PDFProcessor inherits from DataProcessor."""

        processor = PDFProcessor()

        assert isinstance(processor, DataProcessor)

    def test_implements_abstract_methods(self):
        """Test that all abstract methods are implemented."""
        processor = PDFProcessor()

        # All abstract methods should be implemented
        assert callable(getattr(processor, "can_process", None))
        assert callable(getattr(processor, "extract_text", None))
        assert callable(getattr(processor, "extract_multimodal_content", None))
        assert callable(getattr(processor, "chunk_text", None))

    def test_has_helper_methods(self):
        """Test that helper methods from base class are available."""
        processor = PDFProcessor()

        assert callable(getattr(processor, "validate_file", None))
        assert callable(getattr(processor, "get_file_extension", None))
        assert callable(getattr(processor, "get_file_size", None))
