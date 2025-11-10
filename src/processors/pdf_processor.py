"""
PDF Document Processor

This module implements a processor for PDF files, handling text extraction,
multi-modal content (images, tables, equations), and relationship preservation.
"""

import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from pypdf import PdfReader

from src.models.base_models import (
    ChunkType,
    ContentPosition,
    DocumentHierarchy,
    MultiModalContent,
    TextChunk,
)
from src.models.content_elements import ContentElementType
from src.models.equation_content import EquationContent
from src.models.image_content import ImageContent
from src.models.relationship_manager import RelationshipManager
from src.models.table_content import TableContent

from .base import DataProcessor


class PDFProcessor(DataProcessor):
    """
    Processor for PDF documents.

    Handles extraction of text, images, tables, and equations from PDF files,
    maintaining relationships between elements and preserving document hierarchy.

    Attributes:
        supported_extensions: Set of file extensions ('.pdf')
        processor_name: Human-readable name ('PDF Processor')
    """

    supported_extensions = {"pdf"}
    processor_name = "PDF Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the PDF processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - extract_images: Whether to extract images (default: True)
                - extract_tables: Whether to extract tables (default: True)
                - extract_equations: Whether to extract equations (default: True)
                - max_image_size: Maximum image size in bytes (default: 10MB)
        """
        super().__init__(**config)
        self.extract_images = config.get("extract_images", True)
        self.extract_tables = config.get("extract_tables", True)
        self.extract_equations = config.get("extract_equations", True)
        self.max_image_size = config.get("max_image_size", 10 * 1024 * 1024)

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks both file extension (.pdf) and magic bytes (PDF signature).

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a PDF, False otherwise
        """
        path = Path(file_path)

        # Check extension first
        if path.suffix.lower() != ".pdf":
            return False

        # If file doesn't exist, rely on extension check only
        if not path.exists():
            return True

        # Check magic bytes for PDF signature
        try:
            with open(path, "rb") as f:
                magic_bytes = f.read(4)
                return magic_bytes == b"%PDF"
        except OSError:
            return False

    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content with paragraph breaks preserved

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the PDF is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            reader = PdfReader(str(file_path))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n\n".join(text_parts)

        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}") from e

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including text, images, tables, and equations.

        This method performs comprehensive extraction of multi-modal content,
        maintaining relationships between elements and preserving document structure.

        Args:
            file_path: Path to the PDF file
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with all extracted content and relationships

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the PDF is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            reader = PdfReader(str(file_path))
            relationship_manager = RelationshipManager()

            # Initialize content containers
            images: list[ImageContent] = []
            tables: list[TableContent] = []
            equations: list[EquationContent] = []
            text_chunks: list[TextChunk] = []

            # Build document hierarchy
            hierarchy = self._extract_hierarchy(reader, document_id)

            # Process each page
            for page_num, page in enumerate(reader.pages, start=1):
                # Extract text
                page_text = page.extract_text() or ""

                # Extract images from page
                if self.extract_images:
                    page_images = self._extract_images_from_page(
                        page, page_num, document_id
                    )
                    images.extend(page_images)
                    for img in page_images:
                        relationship_manager.register_element(img)

                # Extract tables from page
                if self.extract_tables:
                    page_tables = self._extract_tables_from_page(
                        page, page_text, page_num, document_id
                    )
                    tables.extend(page_tables)
                    for table in page_tables:
                        relationship_manager.register_element(table)

                # Extract equations from page
                if self.extract_equations:
                    page_equations = self._extract_equations_from_page(
                        page_text, page_num, document_id
                    )
                    equations.extend(page_equations)
                    for eq in page_equations:
                        relationship_manager.register_element(eq)

                # Create text chunks for page
                if page_text:
                    page_chunks = self.chunk_text(
                        page_text, chunk_size=512, chunk_overlap=50
                    )
                    # Update chunk positions with page number
                    for chunk in page_chunks:
                        if chunk.position:
                            chunk.position.page_number = page_num
                    text_chunks.extend(page_chunks)

            # Detect relationships between elements
            relationships = relationship_manager.detect_all_relationships()

            # Create and return MultiModalContent
            return MultiModalContent(
                document_id=document_id,
                text_chunks=text_chunks,
                images=images,
                tables=tables,
                equations=equations,
                relationships=relationships,
                hierarchy=hierarchy,
                metadata={
                    "processor": self.processor_name,
                    "page_count": len(reader.pages),
                    "file_path": str(file_path),
                },
            )

        except Exception as e:
            raise ValueError(f"Failed to extract content from PDF: {e}") from e

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: ChunkType = ChunkType.PARAGRAPH,
    ) -> list[TextChunk]:
        """
        Split text into chunks suitable for embedding and retrieval.

        Uses sentence and paragraph boundaries to create natural chunks
        with overlap for context preservation.

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

        # Split into paragraphs first
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # Create chunk from current content
                chunk = TextChunk(
                    chunk_id=str(uuid4()),
                    text=current_chunk.strip(),
                    chunk_type=chunk_type,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=chunk_index,
                        char_start=0,
                    ),
                    metadata={"source": "pdf_processor", "chunk_index": chunk_index},
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if chunk_overlap > 0:
                    # Take last chunk_overlap characters for overlap
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + " " + paragraph
                else:
                    current_chunk = paragraph
            # Add paragraph to current chunk
            elif current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

        # Add final chunk if there's remaining content
        if current_chunk:
            chunk = TextChunk(
                chunk_id=str(uuid4()),
                text=current_chunk.strip(),
                chunk_type=chunk_type,
                position=ContentPosition(
                    page_number=None,
                    paragraph_index=chunk_index,
                    char_start=0,
                ),
                metadata={"source": "pdf_processor", "chunk_index": chunk_index},
            )
            chunks.append(chunk)

        return chunks

    def _extract_hierarchy(
        self, reader: PdfReader, document_id: str
    ) -> DocumentHierarchy:
        """
        Extract document hierarchy from PDF metadata and structure.

        Args:
            reader: PdfReader instance
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        metadata = reader.metadata or {}

        return DocumentHierarchy(
            document_id=document_id,
            title=metadata.get("/Title", "Untitled"),
            sections=[],
            metadata={
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
            },
        )

    def _extract_images_from_page(
        self, page: Any, page_num: int, document_id: str
    ) -> list[ImageContent]:
        """
        Extract images from a PDF page.

        Args:
            page: PDF page object
            page_num: Page number
            document_id: Document identifier

        Returns:
            List of ImageContent objects
        """
        images: list[ImageContent] = []

        try:
            # pypdf provides images through the images property
            if hasattr(page, "images"):
                for img_index, image in enumerate(page.images):
                    try:
                        # Get image data
                        image_data = image.data
                        if len(image_data) > self.max_image_size:
                            continue

                        # Create ImageContent
                        img_content = ImageContent(
                            element_id=str(uuid4()),
                            element_type=ContentElementType.IMAGE,
                            image_data=image_data,
                            format=(
                                image.name.split(".")[-1]
                                if "." in image.name
                                else "unknown"
                            ),
                            position=ContentPosition(
                                page_number=page_num,
                                paragraph_number=0,
                                character_offset=img_index,
                            ),
                            metadata={
                                "source": "pdf_page",
                                "page": page_num,
                                "index": img_index,
                            },
                        )
                        images.append(img_content)

                    except Exception:
                        # Skip problematic images
                        continue

        except Exception:
            # If image extraction fails, continue without images
            pass

        return images

    def _extract_tables_from_page(
        self, page: Any, page_text: str, page_num: int, document_id: str
    ) -> list[TableContent]:
        """
        Extract tables from a PDF page using text patterns.

        This is a basic implementation that detects table-like structures
        in the text. For production use, consider using specialized libraries
        like camelot-py or tabula-py.

        Args:
            page: PDF page object
            page_text: Extracted text from the page
            page_num: Page number
            document_id: Document identifier

        Returns:
            List of TableContent objects
        """
        tables: list[TableContent] = []

        # Simple table detection using text patterns
        # Look for rows with consistent delimiters (tabs, multiple spaces, pipes)
        lines = page_text.split("\n")
        table_lines: list[str] = []
        table_index = 0

        for line in lines:
            # Check if line looks like a table row (multiple columns)
            if re.search(r"(\t|\s{2,}|\|)", line) and len(line.strip()) > 10:
                table_lines.append(line)
            elif table_lines and len(table_lines) >= 2:
                # End of table - create TableContent
                table = self._create_table_from_lines(
                    table_lines, page_num, table_index, document_id
                )
                if table:
                    tables.append(table)
                    table_index += 1
                table_lines = []

        # Handle final table
        if table_lines and len(table_lines) >= 2:
            table = self._create_table_from_lines(
                table_lines, page_num, table_index, document_id
            )
            if table:
                tables.append(table)

        return tables

    def _create_table_from_lines(
        self, lines: list[str], page_num: int, table_index: int, document_id: str
    ) -> TableContent | None:
        """
        Create a TableContent object from text lines.

        Args:
            lines: List of text lines that form a table
            page_num: Page number
            table_index: Table index on page
            document_id: Document identifier

        Returns:
            TableContent object or None if parsing fails
        """
        try:
            # Parse lines into rows
            rows: list[list[str]] = []
            for line in lines:
                # Split by tabs, multiple spaces, or pipes
                cells = re.split(r"\t|\s{2,}|\|", line.strip())
                cells = [cell.strip() for cell in cells if cell.strip()]
                if cells:
                    rows.append(cells)

            if not rows or len(rows) < 2:
                return None

            # First row is likely the header
            headers = rows[0]
            data_rows = rows[1:]

            return TableContent(
                element_id=str(uuid4()),
                element_type=ContentElementType.TABLE,
                headers=headers,
                rows=data_rows,
                position=ContentPosition(
                    page_number=page_num,
                    paragraph_number=table_index,
                    character_offset=0,
                ),
                metadata={
                    "source": "pdf_text_parsing",
                    "page": page_num,
                    "index": table_index,
                },
            )

        except Exception:
            return None

    def _extract_equations_from_page(
        self, page_text: str, page_num: int, document_id: str
    ) -> list[EquationContent]:
        """
        Extract equations from page text using pattern matching.

        Looks for LaTeX-style equations and mathematical expressions.

        Args:
            page_text: Extracted text from the page
            page_num: Page number
            document_id: Document identifier

        Returns:
            List of EquationContent objects
        """
        equations: list[EquationContent] = []

        # Pattern for inline LaTeX equations: $...$
        inline_pattern = r"\$([^$]+)\$"

        # Pattern for display equations: $$...$$ or \[...\]
        display_pattern = r"\$\$(.+?)\$\$|\\\[(.+?)\\\]"

        # Find all equations
        eq_index = 0

        # Display equations
        for match in re.finditer(display_pattern, page_text, re.DOTALL):
            latex_code = match.group(1) or match.group(2)
            if latex_code:
                # Extract context (surrounding text)
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(page_text), match.end() + 100)
                context = page_text[start_pos:end_pos]

                equation = EquationContent(
                    element_id=str(uuid4()),
                    element_type=ContentElementType.EQUATION,
                    latex_code=latex_code.strip(),
                    position=ContentPosition(
                        page_number=page_num,
                        paragraph_number=0,
                        character_offset=match.start(),
                    ),
                    context=context,
                    metadata={
                        "source": "pdf_latex_extraction",
                        "page": page_num,
                        "type": "display",
                        "index": eq_index,
                    },
                )
                equations.append(equation)
                eq_index += 1

        # Inline equations
        for match in re.finditer(inline_pattern, page_text):
            latex_code = match.group(1)
            if latex_code and len(latex_code) > 2:  # Skip very short matches
                # Extract context
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(page_text), match.end() + 100)
                context = page_text[start_pos:end_pos]

                equation = EquationContent(
                    element_id=str(uuid4()),
                    element_type=ContentElementType.EQUATION,
                    latex_code=latex_code.strip(),
                    position=ContentPosition(
                        page_number=page_num,
                        paragraph_number=0,
                        character_offset=match.start(),
                    ),
                    context=context,
                    metadata={
                        "source": "pdf_latex_extraction",
                        "page": page_num,
                        "type": "inline",
                        "index": eq_index,
                    },
                )
                equations.append(equation)
                eq_index += 1

        return equations
