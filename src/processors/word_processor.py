"""
Word Document Processor

This module implements a processor for Microsoft Word documents (.docx),
handling text extraction, images, tables, equations, and cross-references.
"""

from pathlib import Path
from typing import Any
from uuid import uuid4

from docx import Document

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


class WordProcessor(DataProcessor):
    """
    Processor for Microsoft Word documents (.docx).

    Handles extraction of text, images, tables, equations, and cross-references
    while maintaining document structure and relationships.

    Attributes:
        supported_extensions: Set of file extensions ('.docx')
        processor_name: Human-readable name ('Word Processor')
    """

    supported_extensions = {"docx"}
    processor_name = "Word Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the Word processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - extract_images: Whether to extract images (default: True)
                - extract_tables: Whether to extract tables (default: True)
                - extract_equations: Whether to extract equations (default: True)
                - preserve_formatting: Whether to preserve text formatting (default: False)
        """
        super().__init__(**config)
        self.extract_images = config.get("extract_images", True)
        self.extract_tables = config.get("extract_tables", True)
        self.extract_equations = config.get("extract_equations", True)
        self.preserve_formatting = config.get("preserve_formatting", False)

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks file extension (.docx) and attempts to open as Word document.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a valid Word document, False otherwise
        """
        path = Path(file_path)

        # Check extension first
        if path.suffix.lower() != ".docx":
            return False

        # If file doesn't exist, rely on extension check only
        if not path.exists():
            return True

        # Try to open as Word document
        try:
            Document(str(path))
            return True
        except Exception:
            return False

    def extract_text(self, file_path: Path | str) -> str:
        """
        Extract all text content from the Word document.

        Args:
            file_path: Path to the Word document

        Returns:
            Extracted text content with paragraph breaks preserved

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the document is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            doc = Document(str(file_path))
            text_parts = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)

        except Exception as e:
            raise ValueError(f"Failed to extract text from Word document: {e}") from e

    def extract_multimodal_content(
        self, file_path: Path | str, document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including text, images, tables, and equations.

        This method performs comprehensive extraction of multi-modal content,
        maintaining relationships and preserving document structure.

        Args:
            file_path: Path to the Word document
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with all extracted content and relationships

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the document is invalid or corrupted
        """
        self.validate_file(file_path)

        try:
            doc = Document(str(file_path))
            relationship_manager = RelationshipManager()

            # Initialize content containers
            images: list[ImageContent] = []
            tables: list[TableContent] = []
            equations: list[EquationContent] = []
            text_chunks: list[TextChunk] = []

            # Build document hierarchy
            hierarchy = self._extract_hierarchy(doc, document_id)

            # Extract images
            if self.extract_images:
                doc_images = self._extract_images(doc, document_id)
                images.extend(doc_images)
                for img in doc_images:
                    relationship_manager.register_element(img)

            # Extract tables
            if self.extract_tables:
                doc_tables = self._extract_tables(doc, document_id)
                tables.extend(doc_tables)
                for table in doc_tables:
                    relationship_manager.register_element(table)

            # Extract equations
            if self.extract_equations:
                doc_equations = self._extract_equations(doc, document_id)
                equations.extend(doc_equations)
                for eq in doc_equations:
                    relationship_manager.register_element(eq)

            # Extract and chunk text
            full_text = self.extract_text(file_path)
            if full_text:
                text_chunks = self.chunk_text(
                    full_text, chunk_size=512, chunk_overlap=50
                )

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
                    "paragraph_count": len(doc.paragraphs),
                    "table_count": len(doc.tables),
                    "file_path": str(file_path),
                },
            )

        except Exception as e:
            raise ValueError(
                f"Failed to extract content from Word document: {e}"
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

        Uses paragraph boundaries to create natural chunks with overlap.

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

        # Split into paragraphs
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # Create chunk
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    chunk_type=chunk_type,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=chunk_index,
                        char_start=0,
                    ),
                    metadata={"source": "word_processor", "chunk_index": chunk_index},
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + " " + paragraph
                else:
                    current_chunk = paragraph
            # Add to current chunk
            elif current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

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
                metadata={"source": "word_processor", "chunk_index": chunk_index},
            )
            chunks.append(chunk)

        return chunks

    def _extract_hierarchy(self, doc: Document, document_id: str) -> DocumentHierarchy:
        """
        Extract document hierarchy from Word document structure.

        Args:
            doc: Document instance
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        # Extract title from core properties
        title = "Untitled"
        if hasattr(doc.core_properties, "title") and doc.core_properties.title:
            title = doc.core_properties.title

        return DocumentHierarchy(
            document_id=document_id,
            title=title,
            sections=[],
            metadata={
                "author": doc.core_properties.author or "",
                "subject": doc.core_properties.subject or "",
                "created": (
                    str(doc.core_properties.created)
                    if doc.core_properties.created
                    else ""
                ),
                "modified": (
                    str(doc.core_properties.modified)
                    if doc.core_properties.modified
                    else ""
                ),
            },
        )

    def _extract_images(self, doc: Document, document_id: str) -> list[ImageContent]:
        """
        Extract images from Word document.

        Args:
            doc: Document instance
            document_id: Document identifier

        Returns:
            List of ImageContent objects
        """
        images: list[ImageContent] = []
        img_index = 0

        # Extract images from document relationships
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.target_ref:
                try:
                    # Get image data
                    image_part = rel.target_part
                    image_data = image_part.blob

                    # Determine format from content type
                    content_type = image_part.content_type or ""
                    format_str = (
                        content_type.split("/")[-1]
                        if "/" in content_type
                        else "unknown"
                    )

                    # Create ImageContent
                    img_content = ImageContent(
                        id=str(uuid4()),
                        element_type=ContentElementType.IMAGE,
                        image_data=image_data,
                        image_format=format_str,
                        position=ContentPosition(
                            page_number=None,
                            paragraph_index=0,
                            char_start=img_index,
                        ),
                        metadata={
                            "source": "word_document",
                            "relationship_id": rel_id,
                            "index": img_index,
                        },
                    )
                    images.append(img_content)
                    img_index += 1

                except Exception:
                    # Skip problematic images
                    continue

        return images

    def _extract_tables(self, doc: Document, document_id: str) -> list[TableContent]:
        """
        Extract tables from Word document.

        Args:
            doc: Document instance
            document_id: Document identifier

        Returns:
            List of TableContent objects
        """
        tables: list[TableContent] = []

        for table_index, table in enumerate(doc.tables):
            try:
                # Extract table data
                rows_data: list[list[str]] = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    rows_data.append(row_data)

                if not rows_data or len(rows_data) < 2:
                    continue

                # First row as headers
                headers = rows_data[0]
                data_rows = rows_data[1:]

                # Create TableContent
                table_content = TableContent(
                    id=str(uuid4()),
                    element_type=ContentElementType.TABLE,
                    headers=headers,
                    rows=data_rows,
                    position=ContentPosition(
                        page_number=None,
                        paragraph_index=table_index,
                        char_start=0,
                    ),
                    metadata={
                        "source": "word_document",
                        "index": table_index,
                        "row_count": len(data_rows),
                        "column_count": len(headers),
                    },
                )
                tables.append(table_content)

            except Exception:
                # Skip problematic tables
                continue

        return tables

    def _extract_equations(
        self, doc: Document, document_id: str
    ) -> list[EquationContent]:
        """
        Extract equations from Word document.

        Looks for OMML (Office Math Markup Language) equations.

        Args:
            doc: Document instance
            document_id: Document identifier

        Returns:
            List of EquationContent objects
        """
        equations: list[EquationContent] = []
        eq_index = 0

        # Iterate through paragraphs looking for math elements
        for para_index, paragraph in enumerate(doc.paragraphs):
            # Check for math elements in paragraph
            if hasattr(paragraph, "_element"):
                # Look for math elements (OMML)
                math_elements = paragraph._element.findall(
                    ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/math}oMath"
                )

                for math_elem in math_elements:
                    try:
                        # Extract math text (simplified - OMML is complex)
                        math_text = "".join(math_elem.itertext())

                        if math_text and len(math_text) > 2:
                            # Get surrounding context
                            para_text = paragraph.text
                            context = (
                                para_text[:500] if len(para_text) > 500 else para_text
                            )

                            # Create EquationContent
                            equation = EquationContent(
                                id=str(uuid4()),
                                element_type=ContentElementType.EQUATION,
                                latex_code=math_text,  # This is OMML, not LaTeX
                                position=ContentPosition(
                                    page_number=None,
                                    paragraph_index=para_index,
                                    char_start=0,
                                ),
                                context=context,
                                metadata={
                                    "source": "word_omml",
                                    "paragraph_index": para_index,
                                    "index": eq_index,
                                    "format": "omml",
                                },
                            )
                            equations.append(equation)
                            eq_index += 1

                    except Exception:
                        # Skip problematic equations
                        continue

        return equations
