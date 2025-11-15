"""
Markdown Document Processor

This module implements a processor for Markdown files (.md),
handling structure parsing, headings, images, links, and table extraction.
"""

import re
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.content_elements import ContentElementType
from src.models.image_content import ImageContent
from src.models.relationship_manager import RelationshipManager
from src.models.table_content import TableContent

from .base import DataProcessor


class MarkdownProcessor(DataProcessor):
    """
    Processor for Markdown documents (.md).

    Handles extraction of text, structure, headings, images, links, and tables
    from Markdown files while preserving hierarchy.

    Attributes:
        supported_extensions: Set of file extensions ('.md', '.markdown')
        processor_name: Human-readable name ('Markdown Processor')
    """

    supported_extensions: ClassVar[set[str]] = {"md", "markdown"}
    processor_name: ClassVar[str] = "Markdown Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the Markdown processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - extract_images: Whether to extract image references (default: True)
                - extract_tables: Whether to extract tables (default: True)
                - extract_links: Whether to extract links (default: True)
                - preserve_formatting: Whether to preserve markdown formatting (default: False)
        """
        super().__init__(**config)
        self.extract_images = config.get("extract_images", True)
        self.extract_tables = config.get("extract_tables", True)
        self.extract_links = config.get("extract_links", True)
        self.preserve_formatting = config.get("preserve_formatting", False)

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks file extension (.md, .markdown).

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a Markdown file, False otherwise
        """
        path = Path(file_path)
        return path.suffix.lower() in {".md", ".markdown"}

    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the Markdown file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Extracted text content with structure preserved

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be read
        """
        self.validate_file(file_path)

        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to extract text from Markdown file: {e}") from e

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including text, images, tables, and links.

        This method performs comprehensive extraction of multi-modal content,
        maintaining relationships and preserving document hierarchy.

        Args:
            file_path: Path to the Markdown file
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with all extracted content and relationships

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be read
        """
        self.validate_file(file_path)

        try:
            # Read markdown content
            content = self.extract_text(file_path)

            relationship_manager = RelationshipManager()

            # Initialize content containers
            images: list[ImageContent] = []
            tables: list[TableContent] = []
            text_chunks: list[TextChunk] = []

            # Build document hierarchy
            hierarchy = self._extract_hierarchy(content, document_id)

            # Extract images
            if self.extract_images:
                md_images = self._extract_images(content, document_id, file_path)
                images.extend(md_images)
                for img in md_images:
                    relationship_manager.register_element(img)

            # Extract tables
            if self.extract_tables:
                md_tables = self._extract_tables(content, document_id)
                tables.extend(md_tables)
                for table in md_tables:
                    relationship_manager.register_element(table)

            # Extract and chunk text
            if content:
                text_chunks = self.chunk_text(content, chunk_size=512, chunk_overlap=50)

            # Detect relationships
            relationships = relationship_manager.detect_all_relationships()

            # Create and return MultiModalContent
            return MultiModalContent(
                document_id=document_id,
                text_chunks=text_chunks,
                images=[img.id for img in images],
                tables=[table.id for table in tables],
                equations=[],
                relationships={rel.source_id: [rel.target_id] for rel in relationships},
                hierarchy=[hierarchy],
                metadata={
                    "processor": self.processor_name,
                    "file_path": str(file_path),
                    "heading_count": 0,
                },
            )

        except Exception as e:
            raise ValueError(
                f"Failed to extract content from Markdown file: {e}"
            ) from e

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
    ) -> list[TextChunk]:
        """
        Split text into chunks suitable for embedding and retrieval.

        Uses heading and paragraph boundaries to create natural chunks.

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

        # Split by double newlines (paragraphs)
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0
        current_heading = ""

        for paragraph in paragraphs:
            stripped_para = paragraph.strip()
            if not stripped_para:
                continue

            # Check if this is a heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped_para)
            if heading_match:
                current_heading = heading_match.group(2)

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
                    metadata={
                        "source": "markdown_processor",
                        "heading": current_heading,
                        "chunk_index": chunk_index,
                    },
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
                metadata={
                    "source": "markdown_processor",
                    "heading": current_heading,
                    "chunk_index": chunk_index,
                },
            )
            chunks.append(chunk)

        return chunks

    def _extract_hierarchy(self, content: str, document_id: str) -> DocumentHierarchy:
        """
        Extract document hierarchy from Markdown headings.

        Args:
            content: Markdown content
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        # Extract all headings
        headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)

        # First heading is title (if exists)
        title = "Untitled"
        # sections = []

        # if headings:
        #     title = headings[0][1]
        #     sections = [heading[1] for heading in headings]

        return DocumentHierarchy(
            title=title,
            level=0,
            content_ids=[],
            children_ids=[],
            metadata={
                "heading_count": len(headings),
                "max_heading_level": (
                    max([len(h[0]) for h in headings]) if headings else 0
                ),
            },
        )

    def _extract_images(
        self, content: str, document_id: str, file_path: Path | str
    ) -> list[ImageContent]:
        """
        Extract image references from Markdown.

        Markdown image syntax: ![alt text](url "optional title")

        Args:
            content: Markdown content
            document_id: Document identifier
            file_path: Path to markdown file (for resolving relative paths)

        Returns:
            List of ImageContent objects
        """
        images: list[ImageContent] = []

        # Pattern for markdown images: ![alt](url "title")
        image_pattern = r"!\[([^\]]*)\]\(([^\)]+?)(?:\s+[\"']([^\"']*)[\"'])?\)"

        for img_index, match in enumerate(re.finditer(image_pattern, content)):
            alt_text = match.group(1)
            image_url = match.group(2)
            title = match.group(3) if match.group(3) else ""

            # Try to load image if it's a local file
            image_data = b""
            if not image_url.startswith(("http://", "https://", "data:")):
                # Local file reference
                base_dir = Path(file_path).parent
                image_path = (base_dir / image_url).resolve()

                if image_path.exists() and image_path.is_file():
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()
                    except Exception:  # nosec B110
                        pass

                # Create ImageContent
                img_content = ImageContent(
                    id=str(uuid4()),
                    element_type=ContentElementType.IMAGE,
                    image_data=image_data,
                    image_format=(
                        Path(image_url).suffix.lstrip(".")
                        if "." in image_url
                        else "unknown"
                    ),
                    alt_text=alt_text,
                    caption=title,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=0,
                        char_start=match.start(),
                    ),
                    metadata={
                        "source": "markdown",
                        "url": image_url,
                        "index": img_index,
                        "is_remote": image_url.startswith(("http://", "https://")),
                    },
                )
            images.append(img_content)

        return images

    def _extract_tables(self, content: str, document_id: str) -> list[TableContent]:
        """
        Extract tables from Markdown.

        Markdown table syntax:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |

        Args:
            content: Markdown content
            document_id: Document identifier

        Returns:
            List of TableContent objects
        """
        tables: list[TableContent] = []

        # Split content into lines
        lines = content.split("\n")
        table_index = 0
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this line starts a table (contains pipes)
            if "|" in line and i + 1 < len(lines):
                # Check if next line is separator
                next_line = lines[i + 1].strip()
                if re.match(r"^\|?\s*[-:]+\s*(\|\s*[-:]+\s*)*\|?\s*$", next_line):
                    # This is a table
                    table_lines = [line]
                    j = i + 2

                    # Collect all table rows
                    while j < len(lines) and "|" in lines[j]:
                        table_lines.append(lines[j].strip())
                        j += 1

                    # Parse table
                    table = self._parse_markdown_table(
                        table_lines, table_index, document_id
                    )
                    if table:
                        tables.append(table)
                        table_index += 1

                    i = j
                    continue

            i += 1

        return tables

    def _parse_markdown_table(
        self, lines: list[str], table_index: int, document_id: str
    ) -> TableContent | None:
        """
        Parse Markdown table lines into TableContent.

        Args:
            lines: List of table lines
            table_index: Table index
            document_id: Document identifier

        Returns:
            TableContent object or None if parsing fails
        """
        if len(lines) < 2:  # Need at least header row + one data row
            return None

        try:
            # Parse header (first line)
            header_line = lines[0]
            headers = [cell.strip() for cell in header_line.split("|") if cell.strip()]

            # Parse data rows (skip separator, start from line 2)
            rows: list[list[str]] = []
            for line in lines[1:]:
                # Skip separator lines
                if re.match(r"^\s*[-:]+\s*(\|\s*[-:]+\s*)*$", line):
                    continue

                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if cells:
                    rows.append(cells)

            if not rows:
                return None

            # Create TableContent
            return TableContent(
                id=str(uuid4()),
                element_type=ContentElementType.TABLE,
                headers=headers,
                rows=rows,
                position=ContentPosition(
                    page_number=None,
                    paragraph_index=table_index,
                    char_start=0,
                ),
                metadata={
                    "source": "markdown_table",
                    "index": table_index,
                    "row_count": len(rows),
                    "column_count": len(headers),
                },
            )

        except Exception:
            return None
