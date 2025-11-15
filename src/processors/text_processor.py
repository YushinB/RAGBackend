"""
Plain Text File Processor

This module implements a processor for plain text files (.txt),
handling encoding detection, structure inference, and basic content extraction.
"""

import re
from pathlib import Path
from typing import Any, ClassVar

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)

from .base import DataProcessor


class TextFileProcessor(DataProcessor):
    """
    Processor for plain text files (.txt).

    Handles encoding detection, text extraction, and basic structure inference
    from plain text files.

    Attributes:
        supported_extensions: Set of file extensions ('.txt', '.text')
        processor_name: Human-readable name ('Text File Processor')
    """

    supported_extensions: ClassVar[set[str]] = {"txt", "text", "log"}
    processor_name: ClassVar[str] = "Text File Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the text file processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - encoding: Specific encoding to use (default: auto-detect)
                - detect_structure: Whether to detect structure (default: True)
                - preserve_whitespace: Whether to preserve whitespace (default: False)
        """
        super().__init__(**config)
        self.encoding = config.get("encoding")
        self.detect_structure = config.get("detect_structure", True)
        self.preserve_whitespace = config.get("preserve_whitespace", False)

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks file extension (.txt, .text, .log).

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a text file, False otherwise
        """
        path = Path(file_path)
        return path.suffix.lower() in {".txt", ".text", ".log"}

    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the text file.

        Automatically detects encoding if not specified.

        Args:
            file_path: Path to the text file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be read
        """
        self.validate_file(file_path)

        # Detect encoding if not specified
        encoding = self.encoding or self._detect_encoding(file_path)

        try:
            with open(file_path, encoding=encoding) as f:
                content = f.read()

            # Handle whitespace based on configuration
            if not self.preserve_whitespace:
                # Normalize whitespace
                content = re.sub(r"\r\n", "\n", content)  # Normalize line endings
                content = re.sub(r"\t", "    ", content)  # Convert tabs to spaces

            return content

        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode text file with encoding {encoding}: {e}"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to extract text from file: {e}") from e

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract content from text file.

        Since text files only contain text, this method extracts and chunks
        the text content with minimal relationship detection.

        Args:
            file_path: Path to the text file
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with text chunks

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be read
        """
        self.validate_file(file_path)

        try:
            # Extract text content
            content = self.extract_text(file_path)

            # Build hierarchy (minimal for text files)
            hierarchy = self._extract_hierarchy(content, document_id)

            # Chunk text
            text_chunks: list[TextChunk] = []
            if content:
                text_chunks = self.chunk_text(content, chunk_size=512, chunk_overlap=50)

            # Create and return MultiModalContent
            return MultiModalContent(
                document_id=document_id,
                text_chunks=text_chunks,
                images=[],
                tables=[],
                equations=[],
                relationships={},  # No relationships for plain text
                hierarchy=[hierarchy],
                metadata={
                    "processor": self.processor_name,
                    "file_path": str(file_path),
                    "encoding": self.encoding or self._detect_encoding(file_path),
                    "line_count": content.count("\n") + 1 if content else 0,
                },
            )

        except Exception as e:
            raise ValueError(f"Failed to extract content from text file: {e}") from e

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
    ) -> list[TextChunk]:
        """
        Split text into chunks suitable for embedding and retrieval.

        Uses paragraph and sentence boundaries when available.

        Args:
            text: The text content to chunk
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
            chunk_type: Type classification for the chunks

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

        # Split by paragraph boundaries
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            stripped_para = paragraph.strip()
            if not stripped_para:
                continue

            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(stripped_para) > chunk_size and current_chunk:
                # Create chunk
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    chunk_type=chunk_type,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=chunk_index,
                        char_start=0,
                    ),
                    metadata={"source": "text_processor", "chunk_index": chunk_index},
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + stripped_para
                else:
                    current_chunk = stripped_para
            # Add to current chunk
            elif current_chunk:
                current_chunk += "\n\n" + stripped_para
            else:
                current_chunk = stripped_para

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
                metadata={"source": "text_processor", "chunk_index": chunk_index},
            )
            chunks.append(chunk)

        return chunks

    def _detect_encoding(self, file_path: Path | str) -> str:
        """
        Detect the encoding of a text file.

        Tries common encodings in order of likelihood.

        Args:
            file_path: Path to the text file

        Returns:
            Detected encoding name
        """
        # Common encodings to try
        encodings = [
            "utf-8",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "latin-1",
            "cp1252",
            "ascii",
        ]

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    # Try to read first 1KB
                    f.read(1024)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Default fallback
        return "utf-8"

    def _extract_hierarchy(self, content: str, document_id: str) -> DocumentHierarchy:
        """
        Extract basic hierarchy from text file.

        Attempts to identify title from first non-empty line and sections
        from lines that look like headings.

        Args:
            content: Text content
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        lines = content.split("\n")

        # Find first non-empty line as title
        title = "Untitled"
        for line in lines:
            if line.strip():
                title = line.strip()[:100]  # Limit title length
                break

        # Detect section-like lines (all caps, short lines, numbered sections)
        sections = []
        if self.detect_structure:
            section_patterns = [
                r"^[A-Z][A-Z\s]{5,50}$",  # All caps lines
                r"^\d+\.\s+[A-Z]",  # Numbered sections
                r"^[IVX]+\.\s+",  # Roman numerals
                r"^Chapter\s+\d+",  # Chapter headings
                r"^Section\s+\d+",  # Section headings
            ]

            for line in lines:
                stripped_line = line.strip()
                if (
                    not stripped_line
                    or len(stripped_line) < 5
                    or len(stripped_line) > 100
                ):
                    continue

                for pattern in section_patterns:
                    if re.match(pattern, stripped_line):
                        sections.append(stripped_line)
                        break

        return DocumentHierarchy(
            title=title,
            level=0,
            content_ids=[],
            children_ids=[],
            metadata={
                "section_count": len(sections),
                "has_structure": len(sections) > 0,
            },
        )
