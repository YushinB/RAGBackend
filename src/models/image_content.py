"""
Image Content Model

This module defines the ImageContent class for handling image data extracted from documents.
ImageContent inherits from ContentElement and adds image-specific attributes and functionality.
"""

from dataclasses import dataclass
from typing import Any

from .content_elements import ContentElement, ContentElementType


@dataclass
class ImageContent(ContentElement):
    """
    Represents an image content element extracted from a document.

    This class extends ContentElement to handle image-specific data including
    the raw image bytes, format information, captions, and alternative text.

    Attributes:
        image_data: Raw image data as bytes (None if not loaded)
        image_format: Image format (e.g., 'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF')
        width: Image width in pixels (None if unknown)
        height: Image height in pixels (None if unknown)
        caption: Caption or title associated with the image
        alt_text: Alternative text description for accessibility
        file_path: Original file path or URL of the image
        size_bytes: Size of the image data in bytes

    Inherits from ContentElement:
        id: Unique identifier
        element_type: Automatically set to ContentElementType.IMAGE
        position: Position in the document
        metadata: Additional metadata
        relationships: Relationships to other elements
        confidence: Extraction confidence score
        created_at: Creation timestamp
        source_document: Source document identifier

    Example:
        >>> image = ImageContent(
        ...     image_data=b'\\x89PNG...',
        ...     caption="Figure 1: System Architecture",
        ...     alt_text="Diagram showing system components",
        ...     position=ContentPosition(page_number=5)
        ... )
        >>> image.detect_format()  # Auto-detects format from image_data
        'PNG'
    """

    # Image-specific attributes
    image_data: bytes | None = None
    image_format: str | None = None
    width: int | None = None
    height: int | None = None
    caption: str | None = None
    alt_text: str | None = None
    file_path: str | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        """Initialize and validate image content after creation."""
        # Set element type to IMAGE
        self.element_type = ContentElementType.IMAGE

        # Call parent validation
        super().__post_init__()

        # Validate image-specific attributes
        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("height must be positive")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")

        # Calculate size if image_data is provided
        if self.image_data is not None and self.size_bytes is None:
            self.size_bytes = len(self.image_data)

        # Auto-detect format if image_data is provided but format is not
        if self.image_data is not None and self.image_format is None:
            self.image_format = self.detect_format()

    def detect_format(self) -> str | None:
        """
        Detect image format from image data using magic bytes.

        This method examines the first few bytes of the image data to determine
        the image format. Supports PNG, JPEG, GIF, BMP, TIFF, and WebP.

        Returns:
            Image format string (e.g., 'PNG', 'JPEG') or None if cannot be detected

        Example:
            >>> image = ImageContent(image_data=b'\\x89PNG\\r\\n...')
            >>> image.detect_format()
            'PNG'
        """
        if self.image_data is None or len(self.image_data) < 12:
            return None

        # Check magic bytes for common image formats
        magic_bytes = self.image_data[:12]

        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if magic_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "PNG"

        # JPEG: FF D8 FF
        if magic_bytes[:3] == b"\xff\xd8\xff":
            return "JPEG"

        # GIF: 47 49 46 38 (GIF87a or GIF89a)
        if magic_bytes[:6] in (b"GIF87a", b"GIF89a"):
            return "GIF"

        # BMP: 42 4D
        if magic_bytes[:2] == b"BM":
            return "BMP"

        # TIFF: 49 49 2A 00 (little-endian) or 4D 4D 00 2A (big-endian)
        if magic_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            return "TIFF"

        # WebP: 52 49 46 46 ... 57 45 42 50
        if magic_bytes[:4] == b"RIFF" and magic_bytes[8:12] == b"WEBP":
            return "WEBP"

        # ICO: 00 00 01 00
        if magic_bytes[:4] == b"\x00\x00\x01\x00":
            return "ICO"

        return None

    def has_caption(self) -> bool:
        """
        Check if the image has a caption.

        Returns:
            True if caption exists and is non-empty, False otherwise
        """
        return bool(self.caption and self.caption.strip())

    def has_alt_text(self) -> bool:
        """
        Check if the image has alternative text.

        Returns:
            True if alt_text exists and is non-empty, False otherwise
        """
        return bool(self.alt_text and self.alt_text.strip())

    def has_image_data(self) -> bool:
        """
        Check if the image data is loaded.

        Returns:
            True if image_data is present, False otherwise
        """
        return self.image_data is not None and len(self.image_data) > 0

    def get_dimensions(self) -> tuple[int | None, int | None]:
        """
        Get image dimensions as a tuple.

        Returns:
            Tuple of (width, height), with None for unknown dimensions
        """
        return (self.width, self.height)

    def set_dimensions(self, width: int, height: int) -> None:
        """
        Set image dimensions.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Raises:
            ValueError: If width or height is not positive
        """
        if width <= 0:
            raise ValueError("width must be positive")
        if height <= 0:
            raise ValueError("height must be positive")

        self.width = width
        self.height = height

    def clear_image_data(self) -> None:
        """
        Clear image data to save memory while keeping metadata.

        This is useful when you want to preserve image information
        but don't need the actual image bytes anymore.
        """
        self.image_data = None
        self.size_bytes = 0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert image content to dictionary format.

        Note: image_data is not included in the dictionary to avoid
        large binary data in JSON serialization. Use has_image_data()
        to check if data is available.

        Returns:
            Dictionary representation of the image content
        """
        base_dict = super().to_dict()

        # Add image-specific fields (excluding image_data for serialization)
        image_dict = {
            "image_format": self.image_format,
            "width": self.width,
            "height": self.height,
            "caption": self.caption,
            "alt_text": self.alt_text,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "has_image_data": self.has_image_data(),
        }

        # Merge with base dictionary
        base_dict.update(image_dict)
        return base_dict

    def __repr__(self) -> str:
        """
        Return a string representation of the ImageContent.

        Returns:
            String representation with key attributes
        """
        dims = (
            f"{self.width}x{self.height}" if self.width and self.height else "unknown"
        )
        caption_preview = (
            f'"{self.caption[:30]}..."'
            if self.caption and len(self.caption) > 30
            else f'"{self.caption}"'
            if self.caption
            else "None"
        )
        return (
            f"ImageContent(id={self.id[:8]}..., format={self.image_format}, "
            f"dims={dims}, caption={caption_preview}, "
            f"has_data={self.has_image_data()})"
        )
