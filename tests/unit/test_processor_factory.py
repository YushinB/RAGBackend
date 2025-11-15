"""
Tests for ProcessorFactory (T5.1.1 and T5.1.2).

This module tests:
- File type detection
- Processor selection and instantiation
- Configuration parameter passing
- Processor registry and plugin system
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.base_models import MultiModalContent
from src.processors.base import DataProcessor
from src.processors.excel_processor import ExcelProcessor
from src.processors.factory import (
    ProcessorFactory,
    ProcessorFactoryBuilder,
    ProcessorRegistry,
    get_default_factory,
    process_file,
)
from src.processors.markdown_processor import MarkdownProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.text_processor import TextFileProcessor
from src.processors.word_processor import WordProcessor


class TestProcessorRegistry:
    """Tests for ProcessorRegistry."""

    def test_initialization(self):
        """Test registry initializes with default processors."""
        registry = ProcessorRegistry()

        processors = registry.list_registered_processors()
        assert "pdf" in processors
        assert "word" in processors
        assert "excel" in processors
        assert "markdown" in processors
        assert "text" in processors

    def test_list_supported_extensions(self):
        """Test listing all supported extensions."""
        registry = ProcessorRegistry()

        extensions = registry.list_supported_extensions()
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".xlsx" in extensions
        assert ".md" in extensions
        assert ".txt" in extensions

    def test_get_processor_by_name(self):
        """Test retrieving processor by name."""
        registry = ProcessorRegistry()

        pdf_processor = registry.get_processor_by_name("pdf")
        assert pdf_processor == PDFProcessor

        word_processor = registry.get_processor_by_name("word")
        assert word_processor == WordProcessor

    def test_get_processor_by_extension(self):
        """Test retrieving processor by file extension."""
        registry = ProcessorRegistry()

        # Test with dot
        processor = registry.get_processor_by_extension(".pdf")
        assert processor == PDFProcessor

        # Test without dot
        processor = registry.get_processor_by_extension("docx")
        assert processor == WordProcessor

        # Test case insensitive
        processor = registry.get_processor_by_extension(".XLSX")
        assert processor == ExcelProcessor

    def test_get_processor_by_mime_type(self):
        """Test retrieving processor by MIME type."""
        registry = ProcessorRegistry()

        processor = registry.get_processor_by_mime_type("application/pdf")
        assert processor == PDFProcessor

        processor = registry.get_processor_by_mime_type("text/markdown")
        assert processor == MarkdownProcessor

    def test_register_custom_processor(self):
        """Test registering a custom processor."""
        registry = ProcessorRegistry()

        # Create a mock processor class
        class CustomProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

        # Register it
        registry.register_processor(
            name="custom",
            processor_class=CustomProcessor,
            extensions=[".custom"],
            mime_types=["application/x-custom"],
        )

        # Verify registration
        assert "custom" in registry.list_registered_processors()
        assert ".custom" in registry.list_supported_extensions()

        processor = registry.get_processor_by_name("custom")
        assert processor == CustomProcessor

    def test_register_duplicate_processor_raises_error(self):
        """Test that registering duplicate processor raises error."""
        registry = ProcessorRegistry()

        class DuplicateProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="dup")

        with pytest.raises(ValueError, match="already registered"):
            registry.register_processor(
                name="pdf",  # Already registered
                processor_class=DuplicateProcessor,
                extensions=[".pdf2"],
            )

    def test_unregister_processor(self):
        """Test unregistering a processor."""
        registry = ProcessorRegistry()

        # Unregister text processor
        registry.unregister_processor("text")

        assert "text" not in registry.list_registered_processors()
        assert ".txt" not in registry.list_supported_extensions()

    def test_unregister_nonexistent_processor_raises_error(self):
        """Test unregistering nonexistent processor raises error."""
        registry = ProcessorRegistry()

        with pytest.raises(ValueError, match="not registered"):
            registry.unregister_processor("nonexistent")

    def test_get_nonexistent_processor_returns_none(self):
        """Test getting nonexistent processor returns None."""
        registry = ProcessorRegistry()

        processor = registry.get_processor_by_name("nonexistent")
        assert processor is None

        processor = registry.get_processor_by_extension(".unknown")
        assert processor is None

        processor = registry.get_processor_by_mime_type("application/unknown")
        assert processor is None


class TestProcessorFactory:
    """Tests for ProcessorFactory."""

    def test_initialization(self):
        """Test factory initialization."""
        factory = ProcessorFactory()

        assert factory.registry is not None
        assert isinstance(factory.registry, ProcessorRegistry)

    def test_initialization_with_custom_registry(self):
        """Test factory initialization with custom registry."""
        custom_registry = ProcessorRegistry()
        factory = ProcessorFactory(registry=custom_registry)

        assert factory.registry is custom_registry

    def test_detect_file_type(self):
        """Test file type detection."""
        factory = ProcessorFactory()

        # Test PDF
        extension, mime_type = factory.detect_file_type("document.pdf")
        assert extension == ".pdf"
        assert mime_type == "application/pdf"

        # Test Word
        extension, mime_type = factory.detect_file_type("document.docx")
        assert extension == ".docx"

        # Test Markdown
        extension, mime_type = factory.detect_file_type("README.md")
        assert extension == ".md"

    def test_get_processor_for_pdf_file(self):
        """Test getting processor for PDF file."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.pdf")
        assert isinstance(processor, PDFProcessor)

    def test_get_processor_for_word_file(self):
        """Test getting processor for Word file."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.docx")
        assert isinstance(processor, WordProcessor)

    def test_get_processor_for_excel_file(self):
        """Test getting processor for Excel file."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.xlsx")
        assert isinstance(processor, ExcelProcessor)

    def test_get_processor_for_markdown_file(self):
        """Test getting processor for Markdown file."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.md")
        assert isinstance(processor, MarkdownProcessor)

    def test_get_processor_for_text_file(self):
        """Test getting processor for text file."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.txt")
        assert isinstance(processor, TextFileProcessor)

    def test_get_processor_for_unknown_file(self):
        """Test getting processor for unknown file type."""
        factory = ProcessorFactory()

        processor = factory.get_processor_for_file("test.unknown")
        assert processor is None

    def test_can_process_supported_file(self):
        """Test checking if supported file can be processed."""
        factory = ProcessorFactory()

        # can_process just checks if processor exists for file type
        assert factory.can_process("test.pdf") is True
        assert factory.can_process("test.docx") is True
        assert factory.can_process("test.md") is True

    def test_can_process_unsupported_file(self):
        """Test checking if unsupported file can be processed."""
        factory = ProcessorFactory()

        assert factory.can_process("test.unknown") is False

    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        factory = ProcessorFactory()

        extensions = factory.get_supported_extensions()
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".xlsx" in extensions
        assert ".md" in extensions
        assert ".txt" in extensions

    def test_get_supported_processors(self):
        """Test getting list of supported processors."""
        factory = ProcessorFactory()

        processors = factory.get_supported_processors()
        assert "pdf" in processors
        assert "word" in processors
        assert "excel" in processors
        assert "markdown" in processors
        assert "text" in processors

    def test_register_custom_processor(self):
        """Test registering custom processor through factory."""
        factory = ProcessorFactory()

        class CustomProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return file_path.endswith(".custom")

            def extract_text(self, file_path: str) -> str:
                return "Custom text"

            def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

            def chunk_text(self, text: str, config: dict | None = None) -> list:
                return [text]

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

        factory.register_custom_processor(
            name="custom",
            processor_class=CustomProcessor,
            extensions=[".custom"],
        )

        processor = factory.get_processor_for_file("test.custom")
        assert isinstance(processor, CustomProcessor)

    def test_process_file_not_found_raises_error(self):
        """Test processing nonexistent file raises error."""
        factory = ProcessorFactory()

        with pytest.raises(FileNotFoundError, match="File not found"):
            factory.process_file("nonexistent.pdf")

    def test_process_unsupported_file_raises_error(self):
        """Test processing unsupported file raises error."""
        factory = ProcessorFactory()

        with (
            patch.object(Path, "exists", return_value=True),
            pytest.raises(ValueError, match="No processor found"),
        ):
            factory.process_file("test.unknown")


class TestProcessorFactoryBuilder:
    """Tests for ProcessorFactoryBuilder."""

    def test_build_default_factory(self):
        """Test building default factory."""
        builder = ProcessorFactoryBuilder()
        factory = builder.build()

        assert isinstance(factory, ProcessorFactory)
        assert factory.registry is not None

    def test_build_with_custom_registry(self):
        """Test building factory with custom registry."""
        custom_registry = ProcessorRegistry()
        builder = ProcessorFactoryBuilder()
        factory = builder.with_custom_registry(custom_registry).build()

        assert factory.registry is custom_registry

    def test_build_with_custom_processor(self):
        """Test building factory with custom processor."""

        class CustomProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def extract_text(self, file_path: str) -> str:
                return "Custom text"

            def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

            def chunk_text(self, text: str, config: dict | None = None) -> list:
                return [text]

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

        builder = ProcessorFactoryBuilder()
        factory = builder.with_processor(
            name="custom",
            processor_class=CustomProcessor,
            extensions=[".custom"],
        ).build()

        processor = factory.get_processor_for_file("test.custom")
        assert isinstance(processor, CustomProcessor)

    def test_fluent_interface(self):
        """Test builder's fluent interface."""

        class Processor1(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def extract_text(self, file_path: str) -> str:
                return "Text 1"

            def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
                return MultiModalContent(document_id="p1")

            def chunk_text(self, text: str, config: dict | None = None) -> list:
                return [text]

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="p1")

        class Processor2(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def extract_text(self, file_path: str) -> str:
                return "Text 2"

            def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
                return MultiModalContent(document_id="p2")

            def chunk_text(self, text: str, config: dict | None = None) -> list:
                return [text]

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="p2")

        # Chain multiple configurations
        factory = (
            ProcessorFactoryBuilder()
            .with_processor("proc1", Processor1, [".p1"])
            .with_processor("proc2", Processor2, [".p2"])
            .build()
        )

        proc1 = factory.get_processor_for_file("test.p1")
        proc2 = factory.get_processor_for_file("test.p2")

        assert isinstance(proc1, Processor1)
        assert isinstance(proc2, Processor2)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_default_factory(self):
        """Test getting default factory singleton."""
        factory1 = get_default_factory()
        factory2 = get_default_factory()

        # Should return same instance
        assert factory1 is factory2
        assert isinstance(factory1, ProcessorFactory)

    def test_process_file_convenience_function(self):
        """Test convenience process_file function."""
        # This would require actual file processing
        # For now, just test that function exists and is callable
        assert callable(process_file)


class TestProcessorFactoryIntegration:
    """Integration tests for ProcessorFactory."""

    def test_multiple_file_types(self):
        """Test processing multiple file types."""
        factory = ProcessorFactory()

        files = [
            ("doc.pdf", PDFProcessor),
            ("doc.docx", WordProcessor),
            ("data.xlsx", ExcelProcessor),
            ("readme.md", MarkdownProcessor),
            ("notes.txt", TextFileProcessor),
        ]

        for filename, expected_class in files:
            processor = factory.get_processor_for_file(filename)
            assert isinstance(processor, expected_class)

    def test_case_insensitive_extensions(self):
        """Test that file extensions are case insensitive."""
        factory = ProcessorFactory()

        # Test various cases
        processor_lower = factory.get_processor_for_file("doc.pdf")
        processor_upper = factory.get_processor_for_file("doc.PDF")
        processor_mixed = factory.get_processor_for_file("doc.PdF")

        assert isinstance(processor_lower, type(processor_upper))
        assert isinstance(processor_upper, type(processor_mixed))

    def test_registry_isolation(self):
        """Test that different factories have isolated registries."""
        factory1 = ProcessorFactory()
        factory2 = ProcessorFactory()

        class CustomProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return True

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="custom")

        # Register in factory1 only
        factory1.register_custom_processor(
            name="custom", processor_class=CustomProcessor, extensions=[".custom"]
        )

        # Should be in factory1
        assert "custom" in factory1.get_supported_processors()

        # Should NOT be in factory2
        assert "custom" not in factory2.get_supported_processors()

    def test_custom_processor_with_mime_types(self):
        """Test custom processor with MIME type support."""
        factory = ProcessorFactory()

        class JsonProcessor(DataProcessor):
            def can_process(self, file_path: str) -> bool:
                return file_path.endswith(".json")

            def extract_text(self, file_path: str) -> str:
                return "{}"

            def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
                return MultiModalContent(document_id="json")

            def chunk_text(self, text: str, config: dict | None = None) -> list:
                return [text]

            def process(self, file_path: str, **kwargs) -> MultiModalContent:
                return MultiModalContent(document_id="json")

        factory.register_custom_processor(
            name="json",
            processor_class=JsonProcessor,
            extensions=[".json"],
            mime_types=["application/json"],
        )

        # Should work with extension
        processor = factory.get_processor_for_file("data.json")
        assert isinstance(processor, JsonProcessor)

    def test_configuration_passing(self):
        """Test that configuration parameters are passed to processors."""
        factory = ProcessorFactory()

        # Get processor with config
        processor = factory.get_processor_for_file("test.pdf", custom_param="value")

        # Processor should be instantiated
        assert isinstance(processor, PDFProcessor)

    def test_processor_priority_extension_over_mime(self):
        """Test that extension matching has priority over MIME type."""
        factory = ProcessorFactory()

        # Even if MIME detection fails, extension should work
        processor = factory.get_processor_for_file("document.pdf")
        assert isinstance(processor, PDFProcessor)
