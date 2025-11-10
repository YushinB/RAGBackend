"""
Integration tests for all document processors

Tests all five processors (PDF, Word, Excel, Markdown, Text) with common
functionality and cross-processor validation.
"""

import pytest

from src.processors import (
    ExcelProcessor,
    MarkdownProcessor,
    PDFProcessor,
    TextFileProcessor,
    WordProcessor,
)


class TestAllProcessorsBasics:
    """Test basic functionality across all processors."""

    @pytest.fixture
    def all_processors(self):
        """Fixture providing all processor instances."""
        return [
            PDFProcessor(),
            WordProcessor(),
            ExcelProcessor(),
            MarkdownProcessor(),
            TextFileProcessor(),
        ]

    def test_all_processors_have_name(self, all_processors):
        """Test that all processors have a name."""
        for processor in all_processors:
            assert hasattr(processor, "processor_name")
            assert isinstance(processor.processor_name, str)
            assert len(processor.processor_name) > 0

    def test_all_processors_have_extensions(self, all_processors):
        """Test that all processors define supported extensions."""
        for processor in all_processors:
            assert hasattr(processor, "supported_extensions")
            assert isinstance(processor.supported_extensions, set)
            assert len(processor.supported_extensions) > 0

    def test_all_processors_implement_interface(self, all_processors):
        """Test that all processors implement required methods."""
        required_methods = [
            "can_process",
            "extract_text",
            "extract_multimodal_content",
            "chunk_text",
        ]

        for processor in all_processors:
            for method_name in required_methods:
                assert hasattr(processor, method_name)
                assert callable(getattr(processor, method_name))

    def test_all_processors_reject_wrong_extensions(self, all_processors):
        """Test that processors reject incorrect file extensions."""
        test_files = [
            "test.wrong",
            "test.xyz",
            "test",
            "test.123",
        ]

        for processor in all_processors:
            for test_file in test_files:
                assert processor.can_process(test_file) is False

    def test_all_processors_chunk_text_validation(self, all_processors):
        """Test that all processors validate chunk parameters."""
        for processor in all_processors:
            with pytest.raises(ValueError):
                processor.chunk_text("text", chunk_size=50, chunk_overlap=100)


class TestPDFProcessor:
    """Quick tests for PDFProcessor."""

    def test_pdf_processor_extensions(self):
        """Test PDF processor supports .pdf."""
        processor = PDFProcessor()
        assert "pdf" in processor.supported_extensions

    def test_pdf_processor_config(self):
        """Test PDF processor configuration."""
        processor = PDFProcessor(
            extract_images=False,
            extract_tables=True,
            extract_equations=False,
        )
        assert processor.extract_images is False
        assert processor.extract_tables is True


class TestWordProcessor:
    """Quick tests for WordProcessor."""

    def test_word_processor_extensions(self):
        """Test Word processor supports .docx."""
        processor = WordProcessor()
        assert "docx" in processor.supported_extensions

    def test_word_processor_config(self):
        """Test Word processor configuration."""
        processor = WordProcessor(
            extract_images=True,
            extract_tables=True,
            preserve_formatting=True,
        )
        assert processor.extract_images is True
        assert processor.preserve_formatting is True


class TestExcelProcessor:
    """Quick tests for ExcelProcessor."""

    def test_excel_processor_extensions(self):
        """Test Excel processor supports .xlsx and .xlsm."""
        processor = ExcelProcessor()
        assert "xlsx" in processor.supported_extensions
        assert "xlsm" in processor.supported_extensions

    def test_excel_processor_config(self):
        """Test Excel processor configuration."""
        processor = ExcelProcessor(
            extract_formulas=True,
            extract_comments=True,
            include_hidden_sheets=True,
        )
        assert processor.extract_formulas is True
        assert processor.extract_comments is True
        assert processor.include_hidden_sheets is True


class TestMarkdownProcessor:
    """Quick tests for MarkdownProcessor."""

    def test_markdown_processor_extensions(self):
        """Test Markdown processor supports .md and .markdown."""
        processor = MarkdownProcessor()
        assert "md" in processor.supported_extensions
        assert "markdown" in processor.supported_extensions

    def test_markdown_processor_config(self):
        """Test Markdown processor configuration."""
        processor = MarkdownProcessor(
            extract_images=True,
            extract_tables=True,
            extract_links=False,
        )
        assert processor.extract_images is True
        assert processor.extract_links is False

    def test_markdown_can_process(self):
        """Test Markdown processor file detection."""
        processor = MarkdownProcessor()

        assert processor.can_process("file.md") is True
        assert processor.can_process("file.markdown") is True
        assert processor.can_process("file.txt") is False


class TestTextFileProcessor:
    """Quick tests for TextFileProcessor."""

    def test_text_processor_extensions(self):
        """Test Text processor supports .txt, .text, .log."""
        processor = TextFileProcessor()
        assert "txt" in processor.supported_extensions
        assert "text" in processor.supported_extensions
        assert "log" in processor.supported_extensions

    def test_text_processor_config(self):
        """Test Text processor configuration."""
        processor = TextFileProcessor(
            encoding="utf-8",
            detect_structure=True,
            preserve_whitespace=True,
        )
        assert processor.encoding == "utf-8"
        assert processor.detect_structure is True
        assert processor.preserve_whitespace is True

    def test_text_processor_can_process(self):
        """Test Text processor file detection."""
        processor = TextFileProcessor()

        assert processor.can_process("file.txt") is True
        assert processor.can_process("file.text") is True
        assert processor.can_process("file.log") is True
        assert processor.can_process("file.pdf") is False


class TestChunkingConsistency:
    """Test that chunking behavior is consistent across processors."""

    def test_all_processors_chunk_empty_text(self):
        """Test that all processors return empty list for empty text."""
        processors = [
            PDFProcessor(),
            WordProcessor(),
            ExcelProcessor(),
            MarkdownProcessor(),
            TextFileProcessor(),
        ]

        for processor in processors:
            chunks = processor.chunk_text("")
            assert chunks == []

            chunks = processor.chunk_text("   \n\n   ")
            assert chunks == []

    def test_all_processors_chunk_metadata(self):
        """Test that all processors add metadata to chunks."""
        text = "This is a test paragraph.\n\nThis is another paragraph."

        processors = [
            PDFProcessor(),
            WordProcessor(),
            ExcelProcessor(),
            MarkdownProcessor(),
            TextFileProcessor(),
        ]

        for processor in processors:
            chunks = processor.chunk_text(text)
            assert len(chunks) > 0

            for chunk in chunks:
                assert hasattr(chunk, "metadata")
                assert isinstance(chunk.metadata, dict)
                assert "source" in chunk.metadata


class TestProcessorFactoryPattern:
    """Test processor selection based on file type."""

    def test_select_processor_by_extension(self):
        """Test selecting appropriate processor based on file extension."""
        processors = {
            "pdf": PDFProcessor(),
            "docx": WordProcessor(),
            "xlsx": ExcelProcessor(),
            "md": MarkdownProcessor(),
            "txt": TextFileProcessor(),
        }

        test_files = {
            "document.pdf": "pdf",
            "report.docx": "docx",
            "data.xlsx": "xlsx",
            "notes.md": "md",
            "readme.txt": "txt",
        }

        for file_path, expected_ext in test_files.items():
            processor = processors[expected_ext]
            assert processor.can_process(file_path) is True

            # Check that other processors reject it
            for ext, other_processor in processors.items():
                if ext != expected_ext:
                    assert other_processor.can_process(file_path) is False
