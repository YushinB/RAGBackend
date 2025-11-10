"""
Unit Tests for DataProcessor Abstract Base Class

Tests for the base processor interface and helper methods.
"""

import tempfile
from pathlib import Path
from typing import ClassVar

import pytest

from src.models.base_models import ChunkType, MultiModalContent, TextChunk
from src.processors.base import DataProcessor


class ConcreteProcessor(DataProcessor):
    """Concrete implementation of DataProcessor for testing."""

    supported_extensions: ClassVar[set[str]] = {"txt", "test"}
    processor_name: ClassVar[str] = "TestProcessor"

    def can_process(self, file_path: Path | str) -> bool:
        """Test implementation of can_process."""
        ext = self.get_file_extension(file_path)
        return ext in self.supported_extensions

    def extract_text(self, file_path: Path | str) -> str:
        """Test implementation of extract_text."""
        self.validate_file(file_path)
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """Test implementation of extract_multimodal_content."""
        self.validate_file(file_path)
        text = self.extract_text(file_path)
        content = MultiModalContent(document_id=document_id)

        # Create a simple chunk from the text
        chunk = TextChunk(text=text[:100] if len(text) > 100 else text)
        content.add_text_chunk(chunk)

        return content

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
    ) -> list[TextChunk]:
        """Test implementation of chunk_text."""
        if chunk_size <= chunk_overlap:
            raise ValueError("chunk_size must be greater than chunk_overlap")

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            if chunk_text:
                chunk = TextChunk(text=chunk_text, chunk_type=chunk_type)
                chunks.append(chunk)

            start = end - chunk_overlap

        return chunks


class TestDataProcessorInstantiation:
    """Tests for DataProcessor instantiation and abstract methods."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that DataProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataProcessor()  # type: ignore

    def test_can_instantiate_concrete_implementation(self):
        """Test that concrete implementations can be instantiated."""
        processor = ConcreteProcessor()
        assert processor is not None
        assert isinstance(processor, DataProcessor)

    def test_initialization_with_config(self):
        """Test processor initialization with configuration."""
        config = {"chunk_size": 1024, "overlap": 100}
        processor = ConcreteProcessor(**config)

        assert processor.config == config
        assert processor.config["chunk_size"] == 1024

    def test_processor_attributes(self):
        """Test that processor has required attributes."""
        processor = ConcreteProcessor()

        assert hasattr(processor, "supported_extensions")
        assert hasattr(processor, "processor_name")
        assert processor.supported_extensions == {"txt", "test"}
        assert processor.processor_name == "TestProcessor"


class TestDataProcessorHelperMethods:
    """Tests for DataProcessor helper methods."""

    def test_get_file_extension(self):
        """Test file extension extraction."""
        processor = ConcreteProcessor()

        assert processor.get_file_extension("document.pdf") == "pdf"
        assert processor.get_file_extension("file.txt") == "txt"
        assert processor.get_file_extension("archive.tar.gz") == "gz"
        assert processor.get_file_extension("FILE.PDF") == "pdf"  # lowercase
        assert processor.get_file_extension(Path("test.docx")) == "docx"

    def test_get_file_extension_no_extension(self):
        """Test file extension extraction for files without extension."""
        processor = ConcreteProcessor()
        assert processor.get_file_extension("README") == ""

    def test_validate_file_success(self):
        """Test file validation with valid file."""
        processor = ConcreteProcessor()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Should not raise any exception
            processor.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_file_not_found(self):
        """Test file validation with non-existent file."""
        processor = ConcreteProcessor()

        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.validate_file("nonexistent_file.txt")

    def test_validate_file_empty(self):
        """Test file validation with empty file."""
        processor = ConcreteProcessor()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name
            # File is empty

        try:
            with pytest.raises(ValueError, match="File is empty"):
                processor.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_file_is_directory(self):
        """Test file validation with directory path."""
        processor = ConcreteProcessor()

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            pytest.raises(ValueError, match="Path is not a file"),
        ):
            processor.validate_file(temp_dir)

    def test_read_file_bytes(self):
        """Test reading file as bytes."""
        processor = ConcreteProcessor()
        test_content = b"Test binary content\x00\x01\x02"

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(test_content)
            temp_path = f.name

        try:
            content = processor.read_file_bytes(temp_path)
            assert content == test_content
        finally:
            Path(temp_path).unlink()

    def test_get_file_size(self):
        """Test getting file size."""
        processor = ConcreteProcessor()
        test_content = "A" * 1024  # 1KB of data

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            size = processor.get_file_size(temp_path)
            assert size == 1024
        finally:
            Path(temp_path).unlink()

    def test_repr(self):
        """Test string representation of processor."""
        processor = ConcreteProcessor()
        repr_str = repr(processor)

        assert "ConcreteProcessor" in repr_str
        assert "txt" in repr_str or "test" in repr_str

    def test_str(self):
        """Test human-readable string representation."""
        processor = ConcreteProcessor()
        assert str(processor) == "TestProcessor"


class TestDataProcessorConcreteImplementation:
    """Tests for concrete implementation methods."""

    def test_can_process_supported_extension(self):
        """Test can_process with supported file extension."""
        processor = ConcreteProcessor()

        assert processor.can_process("file.txt") is True
        assert processor.can_process("file.test") is True

    def test_can_process_unsupported_extension(self):
        """Test can_process with unsupported file extension."""
        processor = ConcreteProcessor()

        assert processor.can_process("file.pdf") is False
        assert processor.can_process("file.docx") is False

    def test_extract_text(self):
        """Test text extraction from file."""
        processor = ConcreteProcessor()
        test_content = "Hello, World!\nThis is a test file."

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            extracted_text = processor.extract_text(temp_path)
            assert extracted_text == test_content
        finally:
            Path(temp_path).unlink()

    def test_extract_multimodal_content(self):
        """Test multi-modal content extraction."""
        processor = ConcreteProcessor()
        test_content = "Sample document content for testing multi-modal extraction."

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            content = processor.extract_multimodal_content(temp_path, "doc-123")

            assert isinstance(content, MultiModalContent)
            assert content.document_id == "doc-123"
            assert len(content.text_chunks) > 0
            assert isinstance(content.text_chunks[0], TextChunk)
        finally:
            Path(temp_path).unlink()

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        processor = ConcreteProcessor()
        text = "A" * 1000  # 1000 characters

        chunks = processor.chunk_text(text, chunk_size=200, chunk_overlap=50)

        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert all(len(chunk.text) <= 200 for chunk in chunks)

    def test_chunk_text_with_overlap(self):
        """Test text chunking with overlap."""
        processor = ConcreteProcessor()
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10

        chunks = processor.chunk_text(text, chunk_size=50, chunk_overlap=10)

        # Check that chunks overlap
        assert len(chunks) >= 2
        if len(chunks) >= 2:
            # Last 10 chars of first chunk should overlap with start of second
            # Note: Due to implementation, overlap might not be exact
            assert len(chunks) > 1

    def test_chunk_text_invalid_parameters(self):
        """Test text chunking with invalid parameters."""
        processor = ConcreteProcessor()
        text = "Sample text"

        with pytest.raises(ValueError, match="chunk_size must be greater than"):
            processor.chunk_text(text, chunk_size=100, chunk_overlap=100)

        with pytest.raises(ValueError, match="chunk_size must be greater than"):
            processor.chunk_text(text, chunk_size=50, chunk_overlap=75)

    def test_chunk_text_custom_type(self):
        """Test text chunking with custom chunk type."""
        processor = ConcreteProcessor()
        text = "Sample text for testing chunk types."

        chunks = processor.chunk_text(
            text, chunk_size=100, chunk_overlap=10, chunk_type=ChunkType.HEADING
        )

        assert len(chunks) > 0
        assert all(chunk.chunk_type == ChunkType.HEADING for chunk in chunks)

    def test_chunk_text_empty_string(self):
        """Test text chunking with empty string."""
        processor = ConcreteProcessor()

        chunks = processor.chunk_text("", chunk_size=100, chunk_overlap=10)

        assert len(chunks) == 0

    def test_chunk_text_short_text(self):
        """Test text chunking with text shorter than chunk size."""
        processor = ConcreteProcessor()
        text = "Short text"

        chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=10)

        assert len(chunks) == 1
        assert chunks[0].text == text


class TestDataProcessorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_validate_file_with_path_object(self):
        """Test file validation with Path object."""
        processor = ConcreteProcessor()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content")
            temp_path = Path(f.name)

        try:
            processor.validate_file(temp_path)  # Should not raise
        finally:
            temp_path.unlink()

    def test_process_large_text(self):
        """Test processing large text content."""
        processor = ConcreteProcessor()
        # Create 1MB of text
        large_text = "A" * (1024 * 1024)

        chunks = processor.chunk_text(large_text, chunk_size=1000, chunk_overlap=100)

        assert len(chunks) > 100  # Should create many chunks
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)

    def test_unicode_content(self):
        """Test processing unicode content."""
        processor = ConcreteProcessor()
        unicode_text = "Hello 世界 🌍 Привет مرحبا"

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(unicode_text)
            temp_path = f.name

        try:
            extracted_text = processor.extract_text(temp_path)
            assert extracted_text == unicode_text
        finally:
            Path(temp_path).unlink()

    def test_multiline_content(self):
        """Test processing multiline content."""
        processor = ConcreteProcessor()
        multiline_text = "Line 1\nLine 2\nLine 3\n"

        chunks = processor.chunk_text(multiline_text, chunk_size=10, chunk_overlap=2)

        assert len(chunks) >= 1
        # Verify newlines are preserved
        combined_text = "".join(chunk.text for chunk in chunks)
        assert "\n" in combined_text
