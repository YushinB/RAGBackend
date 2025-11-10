"""
Base Abstract Classes for Data Processors

This module defines abstract base classes for document processors that handle
different file formats (PDF, DOCX, XLSX, etc.) and extract multi-modal content.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from src.models.base_models import ChunkType, MultiModalContent, TextChunk


class DataProcessor(ABC):
    """
    Abstract base class for all document processors.

    This class defines the interface that all file format processors must implement.
    Each processor is responsible for:
    - Detecting if it can process a given file
    - Extracting text content from the file
    - Extracting multi-modal content (images, tables, equations)
    - Chunking text into appropriate segments

    Attributes:
        supported_extensions: Set of file extensions this processor can handle
        processor_name: Human-readable name of the processor
    """

    supported_extensions: ClassVar[set[str]] = set()
    processor_name: ClassVar[str] = "BaseProcessor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the processor with optional configuration.

        Args:
            **config: Configuration parameters specific to the processor
        """
        self.config = config

    @abstractmethod
    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        This method should check file extension, magic bytes, or other
        characteristics to determine compatibility.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this processor can handle the file, False otherwise

        Example:
            >>> processor = PDFProcessor()
            >>> processor.can_process("document.pdf")
            True
            >>> processor.can_process("document.docx")
            False
        """
        pass

    @abstractmethod
    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the file.

        This method extracts plain text from the document, preserving
        paragraph breaks and basic structure where possible.

        Args:
            file_path: Path to the file to process

        Returns:
            Extracted text content as a string

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be read
            ValueError: If the file format is invalid or corrupted

        Example:
            >>> processor = PDFProcessor()
            >>> text = processor.extract_text("document.pdf")
            >>> print(text[:100])
            'Chapter 1: Introduction\n\nThis document covers...'
        """
        pass

    @abstractmethod
    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including text, images, tables, and equations.

        This method performs comprehensive extraction of multi-modal content,
        maintaining relationships between elements and preserving document structure.

        Args:
            file_path: Path to the file to process
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object containing all extracted content with relationships

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be read
            ValueError: If the file format is invalid or corrupted
            MemoryError: If the file is too large to process

        Example:
            >>> processor = PDFProcessor()
            >>> content = processor.extract_multimodal_content("doc.pdf", "doc-123")
            >>> print(f"Extracted {len(content.text_chunks)} chunks")
            >>> print(f"Found {len(content.images)} images")
            >>> print(f"Found {len(content.tables)} tables")
        """
        pass

    @abstractmethod
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
    ) -> list[TextChunk]:
        """
        Split text into chunks suitable for embedding and retrieval.

        This method divides text into manageable chunks while respecting
        boundaries (sentences, paragraphs) and maintaining context through overlap.

        Args:
            text: The text content to chunk
            chunk_size: Target size for each chunk (in characters or tokens)
            chunk_overlap: Number of characters/tokens to overlap between chunks
            chunk_type: Type classification for the chunks

        Returns:
            List of TextChunk objects with appropriate metadata

        Raises:
            ValueError: If chunk_size <= chunk_overlap or invalid parameters

        Example:
            >>> processor = PDFProcessor()
            >>> text = "Long document text..."
            >>> chunks = processor.chunk_text(text, chunk_size=512, chunk_overlap=50)
            >>> print(f"Created {len(chunks)} chunks")
            >>> print(f"First chunk: {chunks[0].text[:100]}")
        """
        pass

    def validate_file(self, file_path: Path | str) -> None:
        """
        Validate that the file exists and is readable.

        Args:
            file_path: Path to the file to validate

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be read
            ValueError: If the path is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        if not path.stat().st_size > 0:
            raise ValueError(f"File is empty: {file_path}")

        # Try to open the file to check permissions
        try:
            with open(path, "rb") as f:
                f.read(1)
        except PermissionError as e:
            raise PermissionError(f"Cannot read file: {file_path}") from e

    def get_file_extension(self, file_path: Path | str) -> str:
        """
        Get the lowercase file extension without the dot.

        Args:
            file_path: Path to the file

        Returns:
            File extension in lowercase (e.g., 'pdf', 'docx', 'txt')
        """
        return Path(file_path).suffix.lower().lstrip(".")

    def read_file_bytes(self, file_path: Path | str) -> bytes:
        """
        Read the entire file as bytes.

        Args:
            file_path: Path to the file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be read
        """
        self.validate_file(file_path)
        with open(file_path, "rb") as f:
            return f.read()

    def get_file_size(self, file_path: Path | str) -> int:
        """
        Get the size of the file in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes
        """
        return Path(file_path).stat().st_size

    def __repr__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(extensions={self.supported_extensions})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.processor_name
