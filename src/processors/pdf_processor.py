"""
PDF Document Processor

This module implements a processor for PDF files, handling text extraction,
multi-modal content (images, tables, equations), and relationship preservation.
"""

import re
import traceback
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

import fitz  # type: ignore  # PyMuPDF

from src.core.debug_logger import (
    PDFDebugLogger,
    debug_operation,
    get_debug_logger,
)
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

    supported_extensions: ClassVar[set[str]] = {"pdf"}
    processor_name: ClassVar[str] = "PDF Processor"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the PDF processor with optional configuration.

        Args:
            **config: Configuration parameters:
                - extract_images: Whether to extract images (default: True)
                - extract_tables: Whether to extract tables (default: True)
                - extract_equations: Whether to extract equations (default: True)
                - max_image_size: Maximum image size in bytes (default: 10MB)
                - debug: Enable debug logging (default: False)
                - debug_level: Debug logging level (default: "DEBUG")
        """
        super().__init__(**config)
        self.extract_images = config.get("extract_images", True)
        self.extract_tables = config.get("extract_tables", True)
        self.extract_equations = config.get("extract_equations", True)
        self.max_image_size = config.get("max_image_size", 10 * 1024 * 1024)

        # Initialize debug logging
        debug_enabled = config.get("debug", False)
        debug_level = config.get("debug_level", "DEBUG")
        if debug_enabled:
            self.debug_logger = PDFDebugLogger(level=debug_level)
            self.debug_logger.logger.info(
                "PDF Processor initialized with debug logging enabled"
            )
        else:
            self.debug_logger = get_debug_logger()

    def can_process(self, file_path: Path | str) -> bool:
        """
        Determine if this processor can handle the given file.

        Checks both file extension (.pdf) and uses PyMuPDF to validate PDF format.

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

        # Use PyMuPDF to validate PDF
        try:
            doc = fitz.open(str(path))
            doc.close()
            return True
        except Exception:
            return False

    @debug_operation("PDF Text Extraction")
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
            with self.debug_logger.debug_operation(
                "Open PDF Document", file_path=str(file_path)
            ):
                doc = fitz.open(str(file_path))
                self.debug_logger.debug_data("PDF Document", f"{len(doc)} pages")

            text_parts = []

            with self.debug_logger.debug_operation("Extract Text from Pages"):
                for page_num, page in enumerate(doc):
                    with self.debug_logger.debug_operation(f"Page {page_num + 1}"):
                        page_text = page.get_text()
                        if page_text:
                            text_parts.append(page_text)
                            self.debug_logger.debug_data(
                                f"Page {page_num + 1} text",
                                page_text,
                                preview_length=100,
                            )

            doc.close()

            full_text = "\n\n".join(text_parts)
            self.debug_logger.debug_data(
                "Full extracted text", full_text, preview_length=200
            )
            return full_text

        except Exception as e:
            self.debug_logger.debug_error(
                "PDF Text Extraction", e, file_path=str(file_path)
            )
            raise ValueError(f"Failed to extract text from PDF: {e}") from e

    @debug_operation("PDF Multimodal Content Extraction")
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
            with self.debug_logger.debug_operation(
                "Open PDF for multimodal extraction",
                file_path=str(file_path),
                document_id=document_id,
            ):
                doc = fitz.open(str(file_path))
                relationship_manager = RelationshipManager()

                # Initialize content containers
                images: list[ImageContent] = []
                tables: list[TableContent] = []
                equations: list[EquationContent] = []
                text_chunks: list[TextChunk] = []

                # Build document hierarchy
                with self.debug_logger.debug_operation("Extract document hierarchy"):
                    hierarchy = self._extract_hierarchy(doc, document_id)
                    self.debug_logger.debug_data("Document hierarchy", hierarchy)

                # Process each page
                with self.debug_logger.debug_operation(
                    "Process pages", total_pages=len(doc)
                ):
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        self._process_single_page(
                            page,
                            page_num,
                            document_id,
                            images,
                            tables,
                            equations,
                            text_chunks,
                            relationship_manager,
                        )

            # Detect relationships between elements
            relationship_list = relationship_manager.detect_all_relationships()

            # Convert relationships list to dict format expected by MultiModalContent
            # MultiModalContent expects dict[str, list[str]] mapping source_id to list of target_ids
            relationships_dict: dict[str, list[str]] = {}
            for rel in relationship_list:
                if rel.source_id not in relationships_dict:
                    relationships_dict[rel.source_id] = []
                relationships_dict[rel.source_id].append(rel.target_id)

            # Create and return MultiModalContent
            multimodal_content = MultiModalContent(
                document_id=document_id,
                text_chunks=text_chunks,
                images=[img.id for img in images],
                tables=[table.id for table in tables],
                equations=[eq.id for eq in equations],
                relationships=relationships_dict,
                hierarchy=[hierarchy],  # Wrap single hierarchy object in list
                metadata={
                    "processor": self.processor_name,
                    "page_count": len(doc),
                    "file_path": str(file_path),
                },
            )

            doc.close()
            return multimodal_content

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
            stripped_para = paragraph.strip()
            if not stripped_para:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(stripped_para) > chunk_size and current_chunk:
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
                    current_chunk = overlap_text + " " + stripped_para
                else:
                    current_chunk = stripped_para
            # Add paragraph to current chunk
            elif current_chunk:
                current_chunk += "\n\n" + stripped_para
            else:
                current_chunk = stripped_para

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
        self, doc: fitz.Document, document_id: str
    ) -> DocumentHierarchy:
        """
        Extract document hierarchy from PDF metadata and structure.

        Args:
            doc: PyMuPDF Document instance
            document_id: Document identifier

        Returns:
            DocumentHierarchy object
        """
        metadata = doc.metadata

        return DocumentHierarchy(
            level=0,  # Root level
            title=metadata.get("title", "Untitled Document"),
            section_number=None,
            metadata={
                "document_id": document_id,
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
            },
        )

    def _extract_images_from_page(
        self, page: fitz.Page, page_num: int, document_id: str
    ) -> list[ImageContent]:
        """
        Extract images from a PDF page using PyMuPDF.

        Supports both raster and vector images with better handling.

        Args:
            page: PyMuPDF Page object
            page_num: Page number
            document_id: Document identifier

        Returns:
            List of ImageContent objects
        """
        images: list[ImageContent] = []

        try:
            # Get all images from the page
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                try:
                    self.debug_logger.debug_stage(
                        f"Processing image {img_index + 1}/{len(image_list)}",
                        page=page_num,
                    )

                    # Get image reference
                    xref = img[0]
                    self.debug_logger.debug_data("Image xref", xref)

                    # Extract the image
                    pix = fitz.Pixmap(page.parent, xref)
                    self.debug_logger.debug_data(
                        "Pixmap created",
                        f"width={pix.width}, height={pix.height}, n={pix.n}, alpha={pix.alpha}",
                    )

                    # Get image dimensions before we potentially release memory
                    img_width = img[2] if len(img) > 2 else pix.width
                    img_height = img[3] if len(img) > 3 else pix.height
                    self.debug_logger.debug_data(
                        "Image dimensions", f"{img_width}x{img_height}"
                    )

                    # Convert to PNG if not already in a suitable format
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        self.debug_logger.debug_stage(
                            "Converting GRAY/RGB image to PNG"
                        )
                        image_data = pix.tobytes("png")
                        img_format = "png"
                    else:  # CMYK: convert to RGB first
                        self.debug_logger.debug_stage(
                            "Converting CMYK image to RGB then PNG"
                        )
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        image_data = pix1.tobytes("png")
                        img_format = "png"
                        pix1 = None  # Release memory

                    # Now we can safely release the original pixmap
                    pix = None  # Release memory

                    # Use specialized image processing debug logging
                    self.debug_logger.debug_image_processing(
                        img_index + 1,
                        xref,
                        img_width,
                        img_height,
                        img_format,
                        len(image_data),
                    )

                    # Check size limit
                    if len(image_data) > self.max_image_size:
                        self.debug_logger.debug_stage(
                            "Image too large, skipping",
                            size=len(image_data),
                            limit=self.max_image_size,
                        )
                        continue

                    # Try to get image rectangle on the page
                    img_rect = None
                    try:
                        self.debug_logger.debug_stage(
                            f"Getting image rectangles for xref {xref}"
                        )
                        img_rects = page.get_image_rects(xref)
                        if img_rects:
                            img_rect = img_rects[0]  # Get first occurrence
                            self.debug_logger.debug_data("Image rectangle", img_rect)
                        else:
                            self.debug_logger.debug_stage("No image rectangles found")
                    except Exception as rect_error:
                        self.debug_logger.debug_error(
                            "Get image rectangles", rect_error, xref=xref
                        )
                        # If get_image_rects fails, img_rect remains None
                        pass

                    print("Creating ImageContent object...")
                    # Create ImageContent
                    img_content = ImageContent(
                        id=str(uuid4()),
                        element_type=ContentElementType.IMAGE,
                        image_data=image_data,
                        image_format=img_format,
                        position=ContentPosition(
                            page_number=page_num,
                            paragraph_index=0,
                            char_start=img_index,
                        ),
                        metadata={
                            "source": "pdf_page",
                            "page": page_num,
                            "index": img_index,
                            "xref": xref,
                            "bbox": (
                                {
                                    "x0": img_rect.x0,
                                    "y0": img_rect.y0,
                                    "x1": img_rect.x1,
                                    "y1": img_rect.y1,
                                }
                                if img_rect
                                else None
                            ),
                            "width": img_width,
                            "height": img_height,
                        },
                    )
                    images.append(img_content)
                    print(f"Successfully processed image {img_index}")

                except Exception as img_error:
                    print(
                        f"ERROR processing image {img_index}: {type(img_error).__name__}: {img_error}"
                    )
                    traceback.print_exc()
                    # Skip problematic images
                    continue

        except Exception:  # nosec B110
            # If image extraction fails, continue without images
            pass

        return images

    def _extract_tables_from_page(
        self, page: fitz.Page, page_text: str, page_num: int, document_id: str
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
                id=str(uuid4()),
                element_type=ContentElementType.TABLE,
                headers=headers,
                rows=data_rows,
                position=ContentPosition(
                    page_number=page_num,
                    paragraph_index=table_index,
                    char_start=0,
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
                # Extract context for potential debugging (unused)
                # start_pos = max(0, match.start() - 100)
                # end_pos = min(len(page_text), match.end() + 100)

                equation = EquationContent(
                    id=str(uuid4()),
                    element_type=ContentElementType.EQUATION,
                    latex_code=latex_code.strip(),
                    position=ContentPosition(
                        page_number=page_num,
                        paragraph_index=0,
                        char_start=match.start(),
                    ),
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
                # Extract context for potential debugging (unused)
                # start_pos = max(0, match.start() - 100)
                # end_pos = min(len(page_text), match.end() + 100)

                equation = EquationContent(
                    id=str(uuid4()),
                    element_type=ContentElementType.EQUATION,
                    latex_code=latex_code.strip(),
                    position=ContentPosition(
                        page_number=page_num,
                        paragraph_index=0,
                        char_start=match.start(),
                    ),
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

    def _process_single_page(
        self,
        page: Any,
        page_num: int,
        document_id: str,
        images: list[ImageContent],
        tables: list[TableContent],
        equations: list[EquationContent],
        text_chunks: list[TextChunk],
        relationship_manager: Any,
    ) -> None:
        """
        Process a single page of the PDF document.

        Args:
            page: The PDF page object
            page_num: The page number (0-indexed)
            document_id: Document identifier
            images: List to append extracted images
            tables: List to append extracted tables
            equations: List to append extracted equations
            text_chunks: List to append text chunks
            relationship_manager: Manager for element relationships
        """
        with self.debug_logger.debug_operation(f"Process page {page_num + 1}"):
            # Extract text
            page_text = page.get_text() or ""
            self.debug_logger.debug_data(
                f"Page {page_num + 1} text",
                page_text,
                preview_length=100,
            )

            # Extract images from page
            if self.extract_images:
                self._process_page_images(
                    page, page_num, document_id, images, relationship_manager
                )

            # Extract tables from page
            if self.extract_tables:
                self._process_page_tables(
                    page, page_text, page_num, document_id, tables, relationship_manager
                )

            # Extract equations from page
            if self.extract_equations:
                self._process_page_equations(
                    page_text, page_num, document_id, equations, relationship_manager
                )

            # Create text chunks for page
            if page_text:
                self._process_page_text_chunks(page_text, page_num, text_chunks)

    def _process_page_images(
        self,
        page: Any,
        page_num: int,
        document_id: str,
        images: list[ImageContent],
        relationship_manager: Any,
    ) -> None:
        """Process images from a single page."""
        with self.debug_logger.debug_operation("Extract images from page"):
            page_images = self._extract_images_from_page(
                page, page_num + 1, document_id
            )
            images.extend(page_images)
            self.debug_logger.debug_data(
                "Page images", f"Found {len(page_images)} images"
            )
            for img in page_images:
                relationship_manager.register_element(img)

    def _process_page_tables(
        self,
        page: Any,
        page_text: str,
        page_num: int,
        document_id: str,
        tables: list[TableContent],
        relationship_manager: Any,
    ) -> None:
        """Process tables from a single page."""
        with self.debug_logger.debug_operation("Extract tables from page"):
            page_tables = self._extract_tables_from_page(
                page, page_text, page_num + 1, document_id
            )
            tables.extend(page_tables)
            for table in page_tables:
                relationship_manager.register_element(table)

    def _process_page_equations(
        self,
        page_text: str,
        page_num: int,
        document_id: str,
        equations: list[EquationContent],
        relationship_manager: Any,
    ) -> None:
        """Process equations from a single page."""
        page_equations = self._extract_equations_from_page(
            page_text, page_num + 1, document_id
        )
        equations.extend(page_equations)
        for eq in page_equations:
            relationship_manager.register_element(eq)

    def _process_page_text_chunks(
        self, page_text: str, page_num: int, text_chunks: list[TextChunk]
    ) -> None:
        """Process text chunks from a single page."""
        page_chunks = self.chunk_text(page_text, chunk_size=512, chunk_overlap=50)
        # Update chunk positions with page number
        for chunk in page_chunks:
            if chunk.position:
                chunk.position.page_number = page_num + 1
        text_chunks.extend(page_chunks)
